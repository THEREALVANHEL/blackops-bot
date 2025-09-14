import discord
from discord.ext import commands
from discord import app_commands
import database
import os
from datetime import datetime

class SetupView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.setup_data = {}

    @discord.ui.button(label="📝 Logging Channels", style=discord.ButtonStyle.primary, emoji="📝")
    async def setup_logging(self, interaction: discord.Interaction, button: discord.ui.Button):
        class ChannelPicker(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.modlog = None
                self.joinleave = None
                self.messagelog = None
                
                self.add_item(self.ModlogSelect(self))
                self.add_item(self.JoinLeaveSelect(self))
                self.add_item(self.MessageLogSelect(self))
                self.add_item(self.SaveButton(self))
            
            class ModlogSelect(discord.ui.ChannelSelect):
                def __init__(self, parent):
                    super().__init__(placeholder="Select Moderation Log Channel", channel_types=[discord.ChannelType.text])
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    self.parent.modlog = self.values[0].id
                    await interaction.response.defer()
            
            class JoinLeaveSelect(discord.ui.ChannelSelect):
                def __init__(self, parent):
                    super().__init__(placeholder="Select Join/Leave Log Channel", channel_types=[discord.ChannelType.text])
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    self.parent.joinleave = self.values[0].id
                    await interaction.response.defer()
            
            class MessageLogSelect(discord.ui.ChannelSelect):
                def __init__(self, parent):
                    super().__init__(placeholder="Select Message Log Channel", channel_types=[discord.ChannelType.text])
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    self.parent.messagelog = self.values[0].id
                    await interaction.response.defer()
            
            class SaveButton(discord.ui.Button):
                def __init__(self, parent):
                    super().__init__(label="Save", style=discord.ButtonStyle.success)
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    try:
                        if not all([self.parent.modlog, self.parent.joinleave, self.parent.messagelog]):
                            await interaction.response.send_message("❌ Please select all three channels.", ephemeral=True)
                            return
                        database.db.update_guild_data(interaction.guild.id, {
                            "settings.modlog_channel": self.parent.modlog,
                            "settings.join_leave_channel": self.parent.joinleave,
                            "settings.message_log_channel": self.parent.messagelog,
                            "settings.logging_enabled": True
                        })
                        embed = discord.Embed(title="✅ Logging Channels Configured", color=discord.Color.green())
                        embed.add_field(name="Mod Logs", value=f"<#{self.parent.modlog}>", inline=True)
                        embed.add_field(name="Join/Leave", value=f"<#{self.parent.joinleave}>", inline=True)
                        embed.add_field(name="Message Logs", value=f"<#{self.parent.messagelog}>", inline=True)
                        await interaction.response.edit_message(embed=embed, view=None)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

        embed = discord.Embed(title="📝 Configure Logging", description="Pick channels for moderation, join/leave, and message logs.", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=ChannelPicker(), ephemeral=True)

    @discord.ui.button(label="🎫 Ticket System", style=discord.ButtonStyle.secondary, emoji="🎫")
    async def setup_tickets(self, interaction: discord.Interaction, button: discord.ui.Button):
        class TicketModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Setup Ticket System")
            
            ticket_category = discord.ui.TextInput(
                label="Ticket Category ID",
                placeholder="Category where tickets will be created",
                required=True
            )
            
            transcript_channel = discord.ui.TextInput(
                label="Transcript Channel",
                placeholder="Channel to send ticket transcripts",
                required=False
            )
            
            support_role = discord.ui.TextInput(
                label="Support Role ID", 
                placeholder="Role that can view all tickets",
                required=False
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    category_id = int(self.ticket_category.value)
                    transcript_id = int(self.transcript_channel.value) if self.transcript_channel.value else None
                    support_role_id = int(self.support_role.value) if self.support_role.value else None
                    
                    database.db.update_guild_data(interaction.guild.id, {
                        "settings.ticket_category": category_id,
                        "settings.transcript_channel": transcript_id,
                        "settings.support_role": support_role_id,
                        "settings.tickets_enabled": True
                    })
                    
                    embed = discord.Embed(
                        title="✅ Ticket System Configured",
                        description="Ticket system has been set up successfully!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Category", value=f"<#{category_id}>", inline=True)
                    if transcript_id:
                        embed.add_field(name="Transcripts", value=f"<#{transcript_id}>", inline=True)
                    if support_role_id:
                        embed.add_field(name="Support Role", value=f"<@&{support_role_id}>", inline=True)
                    
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error setting up tickets: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(TicketModal())

    @discord.ui.button(label="⭐ Starboard", style=discord.ButtonStyle.secondary, emoji="⭐")
    async def setup_starboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        class StarboardPicker(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.channel_id = None
                self.add_item(self.StarboardSelect(self))
                self.add_item(self.EmojiInput(self))
                self.add_item(self.ThresholdInput(self))
                self.add_item(self.SaveButton(self))
            class StarboardSelect(discord.ui.ChannelSelect):
                def __init__(self, parent):
                    super().__init__(placeholder="Select Starboard Channel", channel_types=[discord.ChannelType.text])
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    self.parent.channel_id = self.values[0].id
                    await interaction.response.defer()
            class EmojiInput(discord.ui.Button):
                def __init__(self, parent):
                    super().__init__(label="Set Emoji (⭐)", style=discord.ButtonStyle.secondary)
                    self.parent = parent
                    self.parent.emoji = "⭐"
                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.send_message("Reply with the emoji to use for starboard.", ephemeral=True)
            class ThresholdInput(discord.ui.Button):
                def __init__(self, parent):
                    super().__init__(label="Set Threshold (3)", style=discord.ButtonStyle.secondary)
                    self.parent = parent
                    self.parent.threshold = 3
                async def callback(self, interaction: discord.Interaction):
                    await interaction.response.send_message("Reply with the number of reactions required.", ephemeral=True)
            class SaveButton(discord.ui.Button):
                def __init__(self, parent):
                    super().__init__(label="Save", style=discord.ButtonStyle.success)
                    self.parent = parent
                async def callback(self, interaction: discord.Interaction):
                    if not self.parent.channel_id:
                        await interaction.response.send_message("❌ Select a channel first.", ephemeral=True)
                        return
                    database.db.update_guild_data(interaction.guild.id, {
                        "settings.starboard_channel": self.parent.channel_id,
                        "settings.starboard_emoji": getattr(self.parent, 'emoji', '⭐'),
                        "settings.starboard_threshold": getattr(self.parent, 'threshold', 3),
                        "settings.starboard_enabled": True
                    })
                    embed = discord.Embed(title="✅ Starboard Configured", color=discord.Color.gold())
                    embed.add_field(name="Channel", value=f"<#{self.parent.channel_id}>", inline=True)
                    embed.add_field(name="Emoji", value=getattr(self.parent, 'emoji', '⭐'), inline=True)
                    embed.add_field(name="Threshold", value=str(getattr(self.parent, 'threshold', 3)), inline=True)
                    await interaction.response.edit_message(embed=embed, view=None)
        embed = discord.Embed(title="⭐ Configure Starboard", description="Pick a channel and confirm settings.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=StarboardPicker(), ephemeral=True)

    @discord.ui.button(label="🎉 Welcome/Leave", style=discord.ButtonStyle.green, emoji="🎉")
    async def setup_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        class WelcomeModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Setup Welcome/Leave System")
            
            welcome_channel = discord.ui.TextInput(
                label="Welcome Channel",
                placeholder="#welcome or channel ID",
                required=True
            )
            
            welcome_message = discord.ui.TextInput(
                label="Welcome Message",
                placeholder="Welcome {user} to {server}! Use {user} and {server} placeholders",
                required=True,
                style=discord.TextStyle.paragraph
            )
            
            leave_message = discord.ui.TextInput(
                label="Leave Message", 
                placeholder="Goodbye {user}! They were with us for {days} days",
                required=True,
                style=discord.TextStyle.paragraph
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    if self.welcome_channel.value.startswith('<#'):
                        channel_id = int(self.welcome_channel.value[2:-1])
                    else:
                        channel_id = int(self.welcome_channel.value)
                    
                    database.db.update_guild_data(interaction.guild.id, {
                        "settings.welcome_channel": channel_id,
                        "settings.welcome_message": self.welcome_message.value,
                        "settings.leave_message": self.leave_message.value,
                        "settings.welcome_enabled": True,
                        "settings.join_gif": "https://cdn.discordapp.com/attachments/1370993458700877964/1375089295257370624/image0.gif",
                        "settings.leave_gif": "https://cdn.discordapp.com/attachments/1351560015483240459/1368427641564299314/image0.gif"
                    })
                    
                    embed = discord.Embed(
                        title="✅ Welcome/Leave System Configured",
                        description="Welcome and leave messages are now active!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Channel", value=f"<#{channel_id}>", inline=True)
                    embed.add_field(name="Welcome Message", value=self.welcome_message.value[:100] + "...", inline=False)
                    embed.add_field(name="Leave Message", value=self.leave_message.value[:100] + "...", inline=False)
                    
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error setting up welcome/leave: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(WelcomeModal())

    @discord.ui.button(label="🎮 Economy & Levels", style=discord.ButtonStyle.primary, emoji="🎮")
    async def setup_economy(self, interaction: discord.Interaction, button: discord.ui.Button):
        class EconomyModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Setup Economy & Leveling")
            
            levelup_channel = discord.ui.TextInput(
                label="Level Up Channel",
                placeholder="#level-ups or channel ID (optional)",
                required=False
            )
            
            daily_bonus = discord.ui.TextInput(
                label="Daily Bonus Amount",
                placeholder="100 (coins per daily claim)",
                required=True,
                max_length=10
            )
            
            work_cooldown = discord.ui.TextInput(
                label="Work Cooldown (minutes)",
                placeholder="60 (minutes between work commands)",
                required=True,
                max_length=10
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    levelup_id = None
                    if self.levelup_channel.value:
                        if self.levelup_channel.value.startswith('<#'):
                            levelup_id = int(self.levelup_channel.value[2:-1])
                        else:
                            levelup_id = int(self.levelup_channel.value)
                    
                    daily_amount = int(self.daily_bonus.value)
                    work_cd = int(self.work_cooldown.value) * 60  # Convert to seconds
                    
                    database.db.update_guild_data(interaction.guild.id, {
                        "settings.levelup_channel": levelup_id,
                        "economy.daily_bonus": daily_amount,
                        "economy.work_cooldown": work_cd,
                        "economy.enabled": True,
                        "leveling.enabled": True
                    })
                    
                    embed = discord.Embed(
                        title="✅ Economy & Leveling Configured",
                        description="Economy and leveling systems are now active!",
                        color=discord.Color.gold()
                    )
                    if levelup_id:
                        embed.add_field(name="Level Up Channel", value=f"<#{levelup_id}>", inline=True)
                    embed.add_field(name="Daily Bonus", value=f"{daily_amount:,} coins", inline=True)
                    embed.add_field(name="Work Cooldown", value=f"{self.work_cooldown.value} minutes", inline=True)
                    
                    await modal_interaction.response.send_message(embed=embed, ephemeral=True)
                    
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error setting up economy: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(EconomyModal())

    @discord.ui.button(label="📊 View Configuration", style=discord.ButtonStyle.gray, emoji="📊")
    async def view_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_data = database.db.get_guild_data(interaction.guild.id)
        settings = guild_data.get("settings", {})
        
        embed = discord.Embed(
            title="🔧 Current Bot Configuration",
            description=f"Configuration for **{interaction.guild.name}**",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Logging Configuration
        logging_config = ""
        if settings.get("logging_enabled"):
            if settings.get("modlog_channel"):
                logging_config += f"**Mod Logs:** <#{settings['modlog_channel']}>\n"
            if settings.get("join_leave_channel"):
                logging_config += f"**Join/Leave:** <#{settings['join_leave_channel']}>\n"
            if settings.get("message_log_channel"):
                logging_config += f"**Messages:** <#{settings['message_log_channel']}>\n"
        
        if logging_config:
            embed.add_field(name="📝 Logging", value=logging_config, inline=False)
        
        # Welcome System
        if settings.get("welcome_enabled"):
            welcome_config = f"**Channel:** <#{settings.get('welcome_channel', 'Not Set')}>\n"
            welcome_config += f"**Status:** {'✅ Enabled' if settings.get('welcome_enabled') else '❌ Disabled'}"
            embed.add_field(name="🎉 Welcome/Leave", value=welcome_config, inline=True)
        
        # Ticket System
        if settings.get("tickets_enabled"):
            ticket_config = f"**Category:** <#{settings.get('ticket_category', 'Not Set')}>\n"
            if settings.get("transcript_channel"):
                ticket_config += f"**Transcripts:** <#{settings['transcript_channel']}>\n"
            embed.add_field(name="🎫 Tickets", value=ticket_config, inline=True)
        
        # Starboard
        if settings.get("starboard_enabled"):
            starboard_config = f"**Channel:** <#{settings.get('starboard_channel', 'Not Set')}>\n"
            starboard_config += f"**Emoji:** {settings.get('starboard_emoji', '⭐')}\n"
            starboard_config += f"**Threshold:** {settings.get('starboard_threshold', 3)} reactions"
            embed.add_field(name="⭐ Starboard", value=starboard_config, inline=True)
        
        # Economy
        economy = guild_data.get("economy", {})
        if economy.get("enabled"):
            economy_config = f"**Daily Bonus:** {economy.get('daily_bonus', 100):,} coins\n"
            economy_config += f"**Work Cooldown:** {economy.get('work_cooldown', 3600)//60} minutes"
            embed.add_field(name="🎮 Economy", value=economy_config, inline=True)
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Use the buttons above to configure different systems")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="quicksetup", description="Complete bot setup wizard with all systems.")
    @discord.app_commands.default_permissions(administrator=True)
    async def quick_setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🚀 BlackOps Bot - Complete Setup Wizard",
            description="Welcome to the comprehensive bot configuration system!\n\nClick the buttons below to set up different systems:",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 **Logging System**",
            value="• Moderation logs\n• Join/leave tracking\n• Message deletion logs\n• Role change logs",
            inline=True
        )
        
        embed.add_field(
            name="🎫 **Ticket System**", 
            value="• Support tickets\n• Transcript generation\n• Staff role integration\n• Priority management",
            inline=True
        )
        
        embed.add_field(
            name="⭐ **Starboard**",
            value="• Highlight great messages\n• Custom emoji & threshold\n• Automatic posting",
            inline=True
        )
        
        embed.add_field(
            name="🎉 **Welcome/Leave**",
            value="• Custom welcome messages\n• Leave notifications\n• Animated GIFs\n• Join date tracking",
            inline=True
        )
        
        embed.add_field(
            name="🎮 **Economy & Levels**",
            value="• Coin system\n• XP and leveling\n• Work commands\n• Daily bonuses",
            inline=True
        )
        
        embed.add_field(
            name="📊 **Configuration**",
            value="• View current settings\n• Export configuration\n• System status",
            inline=True
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Each system can be configured independently • Configuration is saved to database")
        
        view = SetupView(interaction.guild.id)
        await interaction.response.send_message(embed=embed, view=view)

    # Keep existing starboard and viewsettings commands for backward compatibility
    @app_commands.command(name="starboard", description="Configure starboard settings.")
    @app_commands.describe(channel="The channel for the starboard.", emoji="The emoji to count.", threshold="The number of reactions required.")
    @discord.app_commands.default_permissions(administrator=True)
    async def starboard(self, interaction: discord.Interaction, channel: discord.TextChannel, emoji: str, threshold: int):
        guild_id = interaction.guild_id
        
        # Save starboard settings to the database
        database.db.update_guild_data(guild_id, {
            "settings.starboard_channel": channel.id,
            "settings.starboard_emoji": emoji,
            "settings.starboard_threshold": threshold,
            "settings.starboard_enabled": True
        })
        
        embed = discord.Embed(
            title="⭐ Starboard Configured!",
            description=f"Messages with **{threshold}** `{emoji}` reactions will be sent to {channel.mention}",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="viewsettings", description="View current server configuration.")
    async def view_settings(self, interaction: discord.Interaction):
        guild_data = database.db.get_guild_data(interaction.guild_id)
        settings = guild_data.get("settings", {})
        economy = guild_data.get("economy", {})
        
        embed = discord.Embed(
            title="⚙️ Server Configuration Overview",
            description=f"Current settings for **{interaction.guild.name}**",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        
        # System Status Overview
        systems = [
            ("📝 Logging", settings.get("logging_enabled", False)),
            ("🎉 Welcome/Leave", settings.get("welcome_enabled", False)),
            ("🎫 Tickets", settings.get("tickets_enabled", False)),
            ("⭐ Starboard", settings.get("starboard_enabled", False)),
            ("🎮 Economy", economy.get("enabled", True)),
            ("📊 Leveling", settings.get("leveling", {}).get("enabled", True))
        ]
        
        status_text = ""
        for system, enabled in systems:
            status_text += f"{system}: {'✅ Enabled' if enabled else '❌ Disabled'}\n"
        
        embed.add_field(name="🔧 System Status", value=status_text, inline=True)
        
        # Channel Configuration
        channels_text = ""
        if settings.get("welcome_channel"):
            channels_text += f"**Welcome:** <#{settings['welcome_channel']}>\n"
        if settings.get("modlog_channel"):
            channels_text += f"**Mod Logs:** <#{settings['modlog_channel']}>\n"
        if settings.get("starboard_channel"):
            channels_text += f"**Starboard:** <#{settings['starboard_channel']}>\n"
        
        if channels_text:
            embed.add_field(name="📺 Channels", value=channels_text, inline=True)
        
        # Economy Settings
        if economy.get("enabled"):
            economy_text = f"**Daily Bonus:** {economy.get('daily_bonus', 100):,} coins\n"
            economy_text += f"**Work Cooldown:** {economy.get('work_cooldown', 3600)//60}min"
            embed.add_field(name="💰 Economy", value=economy_text, inline=True)
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Use /quicksetup to modify these settings")

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Enhanced starboard functionality with MongoDB sync"""
        if payload.user_id == self.bot.user.id:
            return
        
        guild_data = database.db.get_guild_data(payload.guild_id)
        settings = guild_data.get("settings", {})
        
        if not settings.get("starboard_enabled"):
            return
        
        starboard_channel_id = settings.get("starboard_channel")
        starboard_emoji_name = settings.get("starboard_emoji")
        starboard_threshold = settings.get("starboard_threshold", 3)

        if not all([starboard_channel_id, starboard_emoji_name, starboard_threshold]):
            return
        
        if str(payload.emoji) == starboard_emoji_name:
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                return

            try:
                message = await channel.fetch_message(payload.message_id)
            except discord.NotFound:
                return

            # Check if the message is already in the starboard
            starboard_channel = self.bot.get_channel(starboard_channel_id)
            if not starboard_channel:
                return
                
            # Check existing starboard messages in database
            existing_starboard = guild_data.get("starboard_messages", {})
            if str(message.id) in existing_starboard:
                return

            # Check if reaction count meets threshold
            for reaction in message.reactions:
                if str(reaction.emoji) == starboard_emoji_name and reaction.count >= starboard_threshold:
                    embed = discord.Embed(
                        title="⭐ Starboard Message",
                        description=message.content,
                        color=discord.Color.gold(),
                        url=message.jump_url,
                        timestamp=message.created_at
                    )
                    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                    embed.add_field(name="Channel", value=channel.mention, inline=True)
                    embed.add_field(name="Reactions", value=f"{starboard_emoji_name} {reaction.count}", inline=True)
                    
                    if message.attachments:
                        attachment = message.attachments[0]
                        if attachment.width:  # Is an image
                            embed.set_image(url=attachment.url)
                    
                    embed.set_footer(text=f"Message ID: {message.id}")
                    
                    try:
                        starboard_msg = await starboard_channel.send(embed=embed)
                        
                        # Save to database
                        existing_starboard[str(message.id)] = {
                            "starboard_message_id": starboard_msg.id,
                            "original_channel_id": channel.id,
                            "reaction_count": reaction.count,
                            "created_at": datetime.utcnow().timestamp()
                        }
                        
                        database.db.update_guild_data(payload.guild_id, {
                            "starboard_messages": existing_starboard
                        })
                        
                    except discord.Forbidden:
                        pass  # Bot lacks permissions
                    
                    return


async def setup(bot: commands.Bot):
    await bot.add_cog(Settings(bot))
