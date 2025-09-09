import discord
from discord.ext import commands
import database
from datetime import datetime
import asyncio

class AutoLogging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cache for before/after message states
        self.message_cache = {}

    def get_log_channel(self, guild_id: int, log_type: str) -> discord.TextChannel:
        """Get appropriate log channel based on type"""
        guild_data = database.db.get_guild_data(guild_id)
        settings = guild_data.get("settings", {})
        
        if not settings.get("logging_enabled"):
            return None
        
        channel_mapping = {
            "moderation": "modlog_channel",
            "member": "join_leave_channel", 
            "message": "message_log_channel",
            "general": "modlog_channel"  # Fallback
        }
        
        channel_id = settings.get(channel_mapping.get(log_type, "modlog_channel"))
        if channel_id:
            return self.bot.get_channel(channel_id)
        return None

    # ==================== MEMBER EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Handle member joins with welcome message and logging"""
        guild_data = database.db.get_guild_data(member.guild.id)
        settings = guild_data.get("settings", {})
        
        # Store join data in database
        database.db.update_user_data(member.id, {
            "guild_join_date": datetime.utcnow().timestamp(),
            "guild_id": member.guild.id
        })
        
        # Welcome Message
        if settings.get("welcome_enabled"):
            welcome_channel_id = settings.get("welcome_channel")
            if welcome_channel_id:
                welcome_channel = self.bot.get_channel(welcome_channel_id)
                if welcome_channel:
                    welcome_message = settings.get("welcome_message", "Welcome {user} to {server}!")
                    join_gif = settings.get("join_gif", "https://cdn.discordapp.com/attachments/1370993458700877964/1375089295257370624/image0.gif")
                    
                    # Replace placeholders
                    message_content = welcome_message.format(
                        user=member.mention,
                        server=member.guild.name,
                        name=member.display_name
                    )
                    
                    embed = discord.Embed(
                        title="🎉 Welcome to the Server!",
                        description=message_content,
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="👤 Member", value=member.mention, inline=True)
                    embed.add_field(name="🆔 User ID", value=f"`{member.id}`", inline=True)
                    embed.add_field(name="📅 Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
                    embed.add_field(name="👥 Member Count", value=f"`{member.guild.member_count}`", inline=True)
                    embed.set_image(url=join_gif)
                    embed.set_footer(text=f"Welcome to {member.guild.name}!")
                    
                    try:
                        await welcome_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        
        # Join Logging
        log_channel = self.get_log_channel(member.guild.id, "member")
        if log_channel:
            embed = discord.Embed(
                title="📥 Member Joined",
                description=f"{member.mention} joined the server",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="📅 Account Age", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="👥 Total Members", value=f"`{member.guild.member_count}`", inline=True)
            
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaves with goodbye message and logging"""
        guild_data = database.db.get_guild_data(member.guild.id)
        settings = guild_data.get("settings", {})
        user_data = database.db.get_user_data(member.id)
        
        # Calculate days in server
        join_date = user_data.get("guild_join_date")
        days_in_server = 0
        if join_date:
            days_in_server = int((datetime.utcnow().timestamp() - join_date) / 86400)
        
        # Leave Message
        if settings.get("welcome_enabled"):
            welcome_channel_id = settings.get("welcome_channel")
            if welcome_channel_id:
                welcome_channel = self.bot.get_channel(welcome_channel_id)
                if welcome_channel:
                    leave_message = settings.get("leave_message", "Goodbye {user}! They were with us for {days} days.")
                    leave_gif = settings.get("leave_gif", "https://cdn.discordapp.com/attachments/1351560015483240459/1368427641564299314/image0.gif")
                    
                    message_content = leave_message.format(
                        user=member.display_name,
                        server=member.guild.name,
                        days=days_in_server
                    )
                    
                    embed = discord.Embed(
                        title="👋 Member Left",
                        description=message_content,
                        color=discord.Color.orange(),
                        timestamp=datetime.utcnow()
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.add_field(name="👤 Member", value=f"{member} ({member.id})", inline=True)
                    embed.add_field(name="⏱️ Time in Server", value=f"`{days_in_server}` days", inline=True)
                    embed.add_field(name="👥 Members Left", value=f"`{member.guild.member_count}`", inline=True)
                    embed.set_image(url=leave_gif)
                    embed.set_footer(text=f"Goodbye from {member.guild.name}")
                    
                    try:
                        await welcome_channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        
        # Leave Logging
        log_channel = self.get_log_channel(member.guild.id, "member")
        if log_channel:
            embed = discord.Embed(
                title="📤 Member Left",
                description=f"{member} left the server",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 User", value=f"{member} ({member.id})", inline=True)
            embed.add_field(name="⏱️ Time in Server", value=f"`{days_in_server}` days", inline=True)
            embed.add_field(name="👥 Members Remaining", value=f"`{member.guild.member_count}`", inline=True)
            
            # Show roles they had
            if member.roles[1:]:  # Exclude @everyone
                roles = [role.mention for role in member.roles[1:]]
                embed.add_field(name="🎭 Roles", value=" ".join(roles[:5]), inline=False)
            
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # ==================== MESSAGE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Cache messages for edit/delete logging"""
        if message.author.bot or not message.guild:
            return
        
        # Cache message for potential edit/delete logging
        self.message_cache[message.id] = {
            "content": message.content,
            "author": message.author,
            "channel": message.channel,
            "attachments": [att.url for att in message.attachments],
            "timestamp": datetime.utcnow()
        }
        
        # Keep cache size manageable
        if len(self.message_cache) > 1000:
            # Remove oldest entries
            oldest_keys = list(self.message_cache.keys())[:200]
            for key in oldest_keys:
                del self.message_cache[key]

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Log deleted messages"""
        if message.author.bot or not message.guild:
            return
        
        log_channel = self.get_log_channel(message.guild.id, "message")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name="👤 Author", value=f"{message.author.mention} ({message.author.id})", inline=True)
        embed.add_field(name="📺 Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="🆔 Message ID", value=f"`{message.id}`", inline=True)
        
        if message.content:
            content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
            embed.add_field(name="📝 Content", value=f"```{content}```", inline=False)
        
        if message.attachments:
            attachments = "\n".join([f"• {att.filename}" for att in message.attachments[:5]])
            embed.add_field(name="📎 Attachments", value=attachments, inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Log edited messages"""
        if before.author.bot or not before.guild or before.content == after.content:
            return
        
        log_channel = self.get_log_channel(before.guild.id, "message")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="✏️ Message Edited",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name="👤 Author", value=f"{before.author.mention} ({before.author.id})", inline=True)
        embed.add_field(name="📺 Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="🔗 Jump to Message", value=f"[Click Here]({after.jump_url})", inline=True)
        
        # Show before and after content
        if before.content:
            before_content = before.content[:500] + "..." if len(before.content) > 500 else before.content
            embed.add_field(name="📝 Before", value=f"```{before_content}```", inline=False)
        
        if after.content:
            after_content = after.content[:500] + "..." if len(after.content) > 500 else after.content
            embed.add_field(name="📝 After", value=f"```{after_content}```", inline=False)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    # ==================== ROLE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Log role changes and nickname changes"""
        if before.bot:
            return
        
        log_channel = self.get_log_channel(before.guild.id, "moderation")
        if not log_channel:
            return
        
        # Check for role changes
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="🎭 Member Roles Updated",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.set_author(name=str(after), icon_url=after.display_avatar.url)
                embed.add_field(name="👤 Member", value=f"{after.mention} ({after.id})", inline=True)
                
                if added_roles:
                    roles_text = " ".join([role.mention for role in added_roles])
                    embed.add_field(name="✅ Roles Added", value=roles_text, inline=False)
                
                if removed_roles:
                    roles_text = " ".join([role.mention for role in removed_roles])
                    embed.add_field(name="❌ Roles Removed", value=roles_text, inline=False)
                
                try:
                    await log_channel.send(embed=embed)
                except discord.Forbidden:
                    pass
        
        # Check for nickname changes
        if before.display_name != after.display_name:
            embed = discord.Embed(
                title="📝 Nickname Changed",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.add_field(name="👤 Member", value=f"{after.mention} ({after.id})", inline=True)
            embed.add_field(name="📝 Before", value=f"`{before.display_name}`", inline=True)
            embed.add_field(name="📝 After", value=f"`{after.display_name}`", inline=True)
            
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                pass

    # ==================== CHANNEL EVENTS ====================
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        log_channel = self.get_log_channel(channel.guild.id, "moderation")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="📺 Channel Created",
            description=f"New channel: {channel.mention}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📺 Channel", value=f"{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="🗂️ Type", value=channel.type.name.title(), inline=True)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="📁 Category", value=channel.category.name, inline=True)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        log_channel = self.get_log_channel(channel.guild.id, "moderation")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🗑️ Channel Deleted",
            description=f"Deleted channel: **{channel.name}**",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="📺 Channel", value=f"{channel.name} ({channel.id})", inline=True)
        embed.add_field(name="🗂️ Type", value=channel.type.name.title(), inline=True)
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    # ==================== VOICE EVENTS ====================
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Log voice channel joins/leaves"""
        if member.bot:
            return
        
        log_channel = self.get_log_channel(member.guild.id, "member")
        if not log_channel:
            return
        
        # Member joined a voice channel
        if before.channel is None and after.channel is not None:
            embed = discord.Embed(
                title="🔊 Voice Channel Joined",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="👤 Member", value=member.mention, inline=True)
            embed.add_field(name="🔊 Channel", value=after.channel.name, inline=True)
            
        # Member left a voice channel
        elif before.channel is not None and after.channel is None:
            embed = discord.Embed(
                title="🔇 Voice Channel Left",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="👤 Member", value=member.mention, inline=True)
            embed.add_field(name="🔊 Channel", value=before.channel.name, inline=True)
            
        # Member switched voice channels
        elif before.channel != after.channel and before.channel is not None and after.channel is not None:
            embed = discord.Embed(
                title="🔄 Voice Channel Switched",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name="👤 Member", value=member.mention, inline=True)
            embed.add_field(name="🔊 From", value=before.channel.name, inline=True)
            embed.add_field(name="🔊 To", value=after.channel.name, inline=True)
        else:
            return  # No relevant change
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    # ==================== MODERATION EVENTS ====================
    
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Log member bans"""
        log_channel = self.get_log_channel(guild.id, "moderation")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🔨 Member Banned",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=True)
        embed.add_field(name="📅 Account Created", value=f"<t:{int(user.created_at.timestamp())}:R>", inline=True)
        
        # Try to get ban reason from audit log
        try:
            await asyncio.sleep(1)  # Wait for audit log entry
            async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="👮 Banned By", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="📝 Reason", value=entry.reason, inline=False)
                    break
        except discord.Forbidden:
            pass
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """Log member unbans"""
        log_channel = self.get_log_channel(guild.id, "moderation")
        if not log_channel:
            return
        
        embed = discord.Embed(
            title="🔓 Member Unbanned",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=True)
        
        # Try to get unban reason from audit log
        try:
            await asyncio.sleep(1)
            async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
                if entry.target.id == user.id:
                    embed.add_field(name="👮 Unbanned By", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="📝 Reason", value=entry.reason, inline=False)
                    break
        except discord.Forbidden:
            pass
        
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            pass

    # ==================== UTILITY COMMANDS ====================
    
    @commands.command(name="toggle_logging")
    @commands.has_permissions(administrator=True)
    async def toggle_logging(self, ctx, system: str = None):
        """Toggle logging systems on/off"""
        guild_data = database.db.get_guild_data(ctx.guild.id)
        settings = guild_data.get("settings", {})
        
        if not system:
            current_status = settings.get("logging_enabled", False)
            new_status = not current_status
            
            database.db.update_guild_data(ctx.guild.id, {
                "settings.logging_enabled": new_status
            })
            
            status = "enabled" if new_status else "disabled"
            await ctx.send(f"✅ Auto-logging has been **{status}** for this server.")
        else:
            await ctx.send("Use `/quicksetup` to configure specific logging systems.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoLogging(bot))
