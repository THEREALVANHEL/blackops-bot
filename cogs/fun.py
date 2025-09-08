import discord
from discord.ext import commands
from discord import app_commands
import random

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="flip", description="Flip a coin - heads or tails.")
    async def flip(self, interaction: discord.Interaction):
        outcome = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{outcome}**!")

    @app_commands.command(name="spinwheel", description="Spin an enhanced wheel with arrow pointing to winner.")
    async def spinwheel(self, interaction: discord.Interaction):
        outcomes = ["Win 500 Coins", "Lose 100 Coins", "Win 100 XP", "Lose 50 XP", "Nothing", "Jackpot! (1000 Coins)"]
        winner = random.choice(outcomes)
        
        embed = discord.Embed(
            title="The Wheel is Spinning...",
            description="Good luck!",
            color=discord.Color.yellow()
        )
        embed.add_field(name="And the winner is...", value=f"🎉 **{winner}** 🎉", inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="rps", description="Play Rock, Paper, Scissors against the bot.")
    @app_commands.describe(choice="Your choice of Rock, Paper, or Scissors.")
    @app_commands.choices(
        choice=[
            discord.app_commands.Choice(name="Rock", value="rock"),
            discord.app_commands.Choice(name="Paper", value="paper"),
            discord.app_commands.Choice(name="Scissors", value="scissors")
        ]
    )
    async def rps(self, interaction: discord.Interaction, choice: str):
        bot_choice = random.choice(["rock", "paper", "scissors"])
        
        win_conditions = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }
        
        user_choice_display = choice.title()
        bot_choice_display = bot_choice.title()
        
        if choice == bot_choice:
            result = "It's a draw!"
            color = discord.Color.grey()
        elif win_conditions[choice] == bot_choice:
            result = "You win!"
            color = discord.Color.green()
        else:
            result = "You lose!"
            color = discord.Color.red()
            
        embed = discord.Embed(
            title="Rock, Paper, Scissors",
            color=color
        )
        embed.add_field(name=f"You chose:", value=user_choice_display, inline=True)
        embed.add_field(name=f"Bot chose:", value=bot_choice_display, inline=True)
        embed.set_footer(text=result)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="slots", description="Play a slot machine.")
    async def slots(self, interaction: discord.Interaction):
        # Placeholder for Slots command
        await interaction.response.send_message("This command is under development!")
        
    @app_commands.command(name="trivia", description="Start a trivia game.")
    async def trivia(self, interaction: discord.Interaction):
        # Placeholder for Trivia command
        await interaction.response.send_message("This command is under development!")
        
    @app_commands.command(name="tournament", description="Start a new tournament.")
    async def tournament(self, interaction: discord.Interaction):
        # Placeholder for Tournament command
        await interaction.response.send_message("This command is under development!")

    @app_commands.command(name="wordchain", description="Start a game of wordchain.")
    async def wordchain(self, interaction: discord.Interaction):
        # Placeholder for Wordchain command
        await interaction.response.send_message("This command is under development!")

    @app_commands.command(name="dailychallenge", description="Participate in the daily challenge.")
    async def dailychallenge(self, interaction: discord.Interaction):
        # Placeholder for Daily Challenge command
        await interaction.response.send_message("This command is under development!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
