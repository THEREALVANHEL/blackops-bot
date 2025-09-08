import discord
from discord.ext import commands
from discord import app_commands

class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="hello", description="Basic hello command and response test")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hello, {interaction.user.mention}!")

    @app_commands.command(name="ping", description="Check bot latency and response time")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! Latency: **{latency}ms**")

    @app_commands.command(name="info", description="Show bot information and status")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Bot Information", color=discord.Color.blue())
        embed.add_field(name="Developer", value=f"<@{self.bot.owner_id}>", inline=False)
        embed.add_field(name="Bot Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=False)
        embed.add_field(name="Commands Synced", value=len(self.bot.tree.get_commands()), inline=False)
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="serverinfo", description="Shows server stats and information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"{guild.name} Server Information", color=discord.Color.green())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"), inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Basic(bot))
