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
                    embed.add_field(name="📅 Account Created", value=f"<t:{int(member
