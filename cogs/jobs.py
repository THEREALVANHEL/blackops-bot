import discord
from discord.ext import commands
from discord import app_commands
import permissions

class Jobs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="work-policy", description="View 24-hour work policy and requirements.")
    async def work_policy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Work Policy",
            description="Here are the rules for the work command.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Cooldown", value="You can work once every **hour**.", inline=False)
        embed.add_field(name="XP and Coins", value="Each successful work session grants a random amount of coins and a small amount of XP.", inline=False)
        embed.set_footer(text="Permission: Everyone")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="job-overview", description="Management overview of all job role activity.")
    @permissions.is_any_moderator()
    async def job_overview(self, interaction: discord.Interaction):
        # This is a placeholder for a more complex command.
        # It would require aggregating data from the database to show
        # which jobs are most popular, how much money has been earned, etc.
        await interaction.response.send_message("Job overview feature is under development.", ephemeral=True)

async def setup(bot: commands.Cog):
    await bot.add_cog(Jobs(bot))
