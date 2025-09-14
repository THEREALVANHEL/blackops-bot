import discord
from discord.ext import commands
from discord import app_commands
import database
import logging

logger = logging.getLogger(__name__)

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def format_channel_setting(self, channel_id, default="Not Set"):
        """Helper to format channel settings properly"""
        if channel_id and str(channel_id) != "Not Set":
            try:
                channel_id_int = int(channel_id)
                return f"<#{channel_id_int}>"
            except (ValueError, TypeError):
                return default
        return default

    @app_commands.command(name="starboard", description="Configure starboard settings.")
    @app_commands.describe(channel="The channel for the starboard.", emoji="The emoji to count.", threshold="The number of reactions required.")
    @discord.app_commands.default_permissions(administrator=True)
    async def starboard(self, interaction: discord.Interaction, channel: discord.TextChannel, emoji: str, threshold: int):
        try:
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
                description=f"Messages with **{threshold}** `{emoji}` reactions will now be sent to {channel.mention}.",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Channel", value=channel.mention, inline=True)
            embed.add_field(name="Emoji", value=emoji, inline=True)
            embed.add_field(name="Threshold", value=f"{threshold} reactions", inline=True)
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error configuring starboard: {e}")
            await interaction.response.send_message("❌ Error configuring starboard. Please try again.", ephemeral=True)

    @app_commands.command(name="viewsettings", description="View current server settings.")
    async def view_settings(self, interaction: discord.Interaction):
        try:
            guild_data = database.db.get_guild_data(interaction.guild_id)
            settings = guild_data.get("settings", {})
            economy = guild_data.get("economy", {})
            
            embed = discord.Embed(
                title="⚙️ Server Settings Overview",
                description=f"Current configuration for **{interaction.guild.name}**",
                color=discord.Color.teal(),
                timestamp=discord.utils.utcnow()
            )
            
            # General Settings
            general_text = f"**Prefix:** `!`\n"
            general_text += f"**Welcome Channel:** {self.format_channel_setting(settings.get('welcome_channel'))}\n"
            general_text += f"**Modlog Channel:** {self.format_channel_setting(settings.get('modlog_channel'))}"
            
            embed.add_field(name="🔧 General", value=general_text, inline=False)
            
            # Starboard Settings
            if settings.get("starboard_enabled"):
                starboard_channel = settings.get("starboard_channel")
                starboard_emoji = settings.get("starboard_emoji", "⭐")
                starboard_threshold = settings.get("starboard_threshold", 3)
                
                starboard_text = f"**Channel:** {self.format_channel_setting(starboard_channel)}\n"
                starboard_text += f"**Emoji:** {starboard_emoji}\n"
                starboard_text += f"**Threshold:** {starboard_threshold} reactions"
                
                embed.add_field(name="⭐ Starboard", value=starboard_text, inline=True)
            
            # Leveling Settings
            leveling_settings = settings.get("leveling", {})
            leveling_enabled = leveling_settings.get("enabled", True)
            xp_per_message = leveling_settings.get("xp_per_message", 15)
            
            leveling_text = f"**Enabled:** {'✅ Yes' if leveling_enabled else '❌ No'}\n"
            leveling_text += f"**XP per Message:** {xp_per_message}"
            
            embed.add_field(name="📊 Leveling", value=leveling_text, inline=True)
            
            # Economy Settings
            if economy.get("enabled", True):
                daily_bonus = economy.get("daily_bonus", 100)
                work_cooldown = economy.get("work_cooldown", 3600) // 60  # Convert to minutes
                
                economy_text = f"**Daily Bonus:** {daily_bonus:,} coins\n"
                economy_text += f"**Work Cooldown:** {work_cooldown} minutes"
                
                embed.add_field(name="💰 Economy", value=economy_text, inline=True)
            
            # System Status
            systems = []
            if settings.get("logging_enabled"):
                systems.append("📝 Logging")
            if settings.get("welcome_enabled"):
                systems.append("🎉 Welcome/Leave")
            if settings.get("starboard_enabled"):
                systems.append("⭐ Starboard")
            if settings.get("tickets_enabled"):
                systems.append("🎫 Tickets")
            if economy.get("enabled", True):
                systems.append("💰 Economy")
            
            if systems:
                embed.add_field(name="✅ Active Systems", value=" • ".join(systems), inline=False)
            
            embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            embed.set_footer(text="Use /quicksetup to modify these settings")

            await interaction.response.send_message(embed=embed)
        except Exception as e:
            logger.error(f"Error viewing settings: {e}")
            await interaction.response.send_message("❌ Error retrieving settings. Please try again.", ephemeral=True)

    @app_commands.command(name="quicksetup", description="Enhanced setup wizard for all bot functions.")
    @discord.app_commands.default_permissions(administrator=True)
    async def quick_setup(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(
                title="🚀 Quick Setup Wizard",
                description="This is a simplified setup. For the complete setup wizard with all features, use `/quicksetup` from the QuickSetup cog.",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📝 Available Quick Actions",
                value="• `/starboard` - Configure starboard\n• `/viewsettings` - View current settings",
                inline=False
            )
            
            embed.add_field(
                name="🔧 Advanced Setup",
                value="For complete bot configuration including logging, tickets, welcome messages, and more, please use the `/quicksetup` command from the main setup system.",
                inline=False
            )
            
            embed.set_footer(text="This command provides basic setup only")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in quick_setup: {e}")
            await interaction.response.send_message("❌ Error loading setup wizard.", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Enhanced starboard functionality with proper error handling"""
        if payload.user_id == self.bot.user.id:
            return
        
        try:
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
                except discord.Forbidden:
                    logger.warning(f"No permission to fetch message in {channel.name}")
                    return

                # Check if the message is already in the starboard to avoid duplicates
                starboard_channel = self.bot.get_channel(starboard_channel_id)
                if not starboard_channel:
                    logger.warning(f"Starboard channel not found: {starboard_channel_id}")
                    return
                
                # Check existing starboard messages
                existing_starboard = guild_data.get("starboard_messages", {})
                if str(message.id) in existing_starboard:
                    return  # Message already on starboard

                # Check if reaction count meets the threshold
                for reaction in message.reactions:
                    if str(reaction.emoji) == starboard_emoji_name and reaction.count >= starboard_threshold:
                        embed = discord.Embed(
                            title="⭐ Starboard",
                            color=discord.Color.gold(),
                            description=message.content or "*No text content*",
                            url=message.jump_url,
                            timestamp=message.created_at
                        )
                        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
                        embed.add_field(name="Channel", value=channel.mention, inline=True)
                        embed.add_field(name="Reactions", value=f"{starboard_emoji_name} {reaction.count}", inline=True)
                        embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=True)
                        
                        if message.attachments:
                            attachment = message.attachments[0]
                            if attachment.content_type and attachment.content_type.startswith('image/'):
                                embed.set_image(url=attachment.url)
                            else:
                                embed.add_field(name="📎 Attachment", value=f"[{attachment.filename}]({attachment.url})", inline=False)
                        
                        embed.set_footer(text=f"Original Message ID: {message.id}")
                        
                        try:
                            starboard_msg = await starboard_channel.send(embed=embed)
                            
                            # Update database to track starboard messages
                            existing_starboard[str(message.id)] = {
                                "starboard_message_id": starboard_msg.id,
                                "original_channel_id": channel.id,
                                "reaction_count": reaction.count,
                                "created_at": discord.utils.utcnow().timestamp()
                            }
                            
                            database.db.update_guild_data(payload.guild_id, {
                                "starboard_messages": existing_starboard
                            })
                            
                        except discord.Forbidden:
                            logger.warning(f"No permission to send to starboard channel {starboard_channel.name}")
                        except Exception as e:
                            logger.error(f"Error sending starboard message: {e}")
                        
                        return
        except Exception as e:
            logger.error(f"Error in starboard reaction handler: {e}")


async def setup(bot: commands.Cog):
    await bot.add_cog(Settings(bot))
