import discord
from discord.ext import commands
from discord import app_commands
import database

class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="starboard", description="Configure starboard settings.")
    @app_commands.describe(channel="The channel for the starboard.", emoji="The emoji to count.", threshold="The number of reactions required.")
    @discord.app_commands.default_permissions(administrator=True)
    async def starboard(self, interaction: discord.Interaction, channel: discord.TextChannel, emoji: str, threshold: int):
        guild_id = interaction.guild_id
        
        # Save starboard settings to the database
        database.db.update_guild_data(guild_id, {
            "settings.starboard_channel": channel.id,
            "settings.starboard_emoji": emoji,
            "settings.starboard_threshold": threshold
        })
        
        await interaction.response.send_message(f"✅ Starboard configured! Messages with **{threshold}** `{emoji}` reactions will now be sent to {channel.mention}.", ephemeral=True)

    @app_commands.command(name="viewsettings", description="View current server settings.")
    async def view_settings(self, interaction: discord.Interaction):
        guild_data = database.db.get_guild_data(interaction.guild_id)
        settings = guild_data.get("settings", {})
        
        embed = discord.Embed(
            title="Server Settings Overview",
            color=discord.Color.teal()
        )
        
        # General Settings
        embed.add_field(name="General", value="**Prefix:** `!`\n**Welcome Channel:** <#{}>\n**Modlog Channel:** <#{}>".format(
            settings.get("welcome_channel", "Not Set"),
            settings.get("modlog_channel", "Not Set")
        ), inline=False)
        
        # Starboard Settings
        starboard_channel = settings.get("starboard_channel", "Not Set")
        starboard_emoji = settings.get("starboard_emoji", "Not Set")
        starboard_threshold = settings.get("starboard_threshold", "Not Set")
        embed.add_field(name="Starboard", value=f"**Channel:** <#{starboard_channel}>\n**Emoji:** {starboard_emoji}\n**Threshold:** {starboard_threshold}", inline=False)
        
        # Leveling Settings
        leveling_enabled = settings.get("leveling", {}).get("enabled", True)
        xp_per_message = settings.get("leveling", {}).get("xp_per_message", 15)
        embed.add_field(name="Leveling", value=f"**Enabled:** {leveling_enabled}\n**XP per Message:** {xp_per_message}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="quicksetup", description="Enhanced setup wizard for all bot functions.")
    @discord.app_commands.default_permissions(administrator=True)
    async def quick_setup(self, interaction: discord.Interaction):
        # This is a placeholder for a more complex interactive setup wizard.
        await interaction.response.send_message("The quick setup wizard is under development!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # This listener handles the starboard functionality
        guild_data = database.db.get_guild_data(payload.guild_id)
        settings = guild_data.get("settings", {})
        
        starboard_channel_id = settings.get("starboard_channel")
        starboard_emoji_name = settings.get("starboard_emoji")
        starboard_threshold = settings.get("starboard_threshold")

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

            # Check if the message is already in the starboard to avoid duplicates
            starboard_channel = self.bot.get_channel(starboard_channel_id)
            async for old_message in starboard_channel.history(limit=50):
                if old_message.embeds and old_message.embeds[0].footer.text == f"Original Message ID: {message.id}":
                    return # Message already exists in starboard

            # Check if reaction count meets the threshold
            for reaction in message.reactions:
                if str(reaction.emoji) == starboard_emoji_name and reaction.count >= starboard_threshold:
                    embed = discord.Embed(
                        title="⭐ Starboard",
                        color=discord.Color.yellow(),
                        description=message.content,
                        url=message.jump_url
                    )
                    embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else None)
                    if message.attachments and message.attachments[0].width:
                        embed.set_image(url=message.attachments[0].url)
                    embed.set_footer(text=f"Original Message ID: {message.id}")
                    await starboard_channel.send(embed=embed)
                    return

async def setup(bot: commands.Cog):
    await bot.add_cog(Settings(bot))
