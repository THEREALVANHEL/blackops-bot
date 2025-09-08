import discord
from discord.ext import commands
from discord import app_commands
import permissions
import asyncio

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shout", description="Create a detailed event announcement.")
    @app_commands.describe(
        title="Title of the event.",
        description="A detailed description of the event.",
        host="The main host of the event.",
        co_host="The co-host(s) of the event.",
        medic="The medic for the event.",
        guide="The guide for the event."
    )
    @permissions.is_any_host()
    async def shout(self, interaction: discord.Interaction, title: str, description: str, host: discord.Member, co_host: discord.Member = None, medic: discord.Member = None, guide: discord.Member = None):
        embed = discord.Embed(
            title=f"📢 Event Announcement: {title}",
            description=description,
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.add_field(name="Host", value=host.mention, inline=True)
        if co_host:
            embed.add_field(name="Co-Host", value=co_host.mention, inline=True)
        if medic:
            embed.add_field(name="Medic", value=medic.mention, inline=True)
        if guide:
            embed.add_field(name="Guide", value=guide.mention, inline=True)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Event announcement created!", ephemeral=True)

    @app_commands.command(name="gamelog", description="Log a completed game with details.")
    @app_commands.describe(
        game="The name of the game played.",
        result="The result of the game (e.g., 'Win', 'Loss', 'Draw').",
        participants="Mentions of the participants.",
        image="A URL to an image of the game result."
    )
    @permissions.is_any_host()
    async def gamelog(self, interaction: discord.Interaction, game: str, result: str, participants: str, image: str = None):
        embed = discord.Embed(
            title=f"Game Log: {game}",
            description=f"Result: **{result}**",
            color=discord.Color.blue()
        )
        embed.add_field(name="Participants", value=participants, inline=False)
        
        if image:
            embed.set_image(url=image)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Game log created!", ephemeral=True)

    @app_commands.command(name="giveaway", description="Start a giveaway.")
    @app_commands.describe(duration="Duration of the giveaway (e.g., 1h, 30m).", winners="Number of winners.", prize="The prize of the giveaway.")
    async def giveaway(self, interaction: discord.Interaction, duration: str, winners: int, prize: str):
        # Placeholder functionality for now. A full giveaway system requires more robust logic and storage.
        await interaction.response.send_message("Giveaway feature is under development.")

    @app_commands.command(name="announce", description="Creates a professional pointwise announcement.")
    @app_commands.describe(title="The title of the announcement.", content="The content of the announcement.")
    async def announce(self, interaction: discord.Interaction, title: str, content: str):
        embed = discord.Embed(
            title=f"Announcement: {title}",
            description=content.replace("\\n", "\n"), # Allows for newlines using \n in the command
            color=discord.Color.purple()
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)

    @app_commands.command(name="remind", description="Set a reminder for yourself.")
    @app_commands.describe(time="When to remind you (e.g., 1h, 30m).", message="The reminder message.")
    async def remind(self, interaction: discord.Interaction, time: str, message: str):
        units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        
        try:
            amount = int(time[:-1])
            unit = time[-1].lower()
            if unit not in units:
                raise ValueError
            
            seconds = amount * units[unit]
            
            await interaction.response.send_message(f"✅ I will remind you in **{amount}{unit}**!", ephemeral=True)
            await asyncio.sleep(seconds)
            
            await interaction.followup.send(f"🔔 Reminder for {interaction.user.mention}: {message}")
            
        except (ValueError, IndexError):
            await interaction.response.send_message("Invalid time format. Please use a number followed by s, m, h, or d (e.g., `30m`).", ephemeral=True)

    @app_commands.command(name="suggest", description="Submit a suggestion with optional media.")
    @app_commands.describe(suggestion="Your suggestion.", media="A URL to media for your suggestion (optional).")
    async def suggest(self, interaction: discord.Interaction, suggestion: str, media: str = None):
        # A full suggestion system would require a dedicated channel ID stored in the database.
        # For now, we will send to the current channel and add a placeholder for a dedicated channel.
        embed = discord.Embed(
            title="New Suggestion",
            description=suggestion,
            color=discord.Color.yellow()
        )
        embed.set_author(name=f"Submitted by {interaction.user.display_name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        if media:
            embed.set_image(url=media)
        
        await interaction.response.send_message("✅ Your suggestion has been submitted!", ephemeral=True)
        await interaction.channel.send(embed=embed)


async def setup(bot: commands.Cog):
    await bot.add_cog(Events(bot))
