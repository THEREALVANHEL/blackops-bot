import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random

# Define shop items with cost and duration in seconds
SHOP_ITEMS = {
    "xp_boost": {"price": 500, "duration": 3600}, # 1 hour
    "lucky_charm": {"price": 1000, "duration": 86400} # 24 hours
}

class Economy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Check your shiny coin and cookie balance.")
    @app_commands.describe(user="The user whose balance you want to check (optional).")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = database.db.get_user_data(target_user.id)
        
        coins = user_data.get("coins", 0)
        cookies = user_data.get("cookies", 0)

        embed = discord.Embed(
            title=f"{target_user.display_name}'s Balance",
            color=discord.Color.gold()
        )
        embed.add_field(name="Shiny Coins", value=f"💰 {coins:,}", inline=False)
        embed.add_field(name="Delicious Cookies", value=f"🍪 {cookies:,}", inline=False)
        embed.set_footer(text="Permission: Everyone")
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="work", description="Independent career progression system - work your way up!")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if not database.db.can_work(user_id):
            await interaction.response.send_message("You are still on cooldown! You can work again in an hour.", ephemeral=True)
            return

        earnings = random.randint(100, 500)
        
        result = database.db.process_work(user_id, "Standard Job", earnings)

        if result["success"]:
            embed = discord.Embed(
                title="Successful Work!",
                description=f"You worked hard and earned **{result['earnings']}** coins and **{result['xp_gained']}** XP.",
                color=discord.Color.green()
            )
            embed.add_field(name="Work Streak", value=f"🔥 {result['work_streak']} days", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("An error occurred while processing your work.", ephemeral=True)

    @app_commands.command(name="shop", description="View the premium temporary items shop.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Premium Temporary Items Shop",
            description="Purchase temporary boosts and items with your coins!",
            color=discord.Color.blue()
        )
        
        for item, details in SHOP_ITEMS.items():
            duration_hours = int(details["duration"] / 3600)
            embed.add_field(
                name=f"• {item.title().replace('_', ' ')}",
                value=f"**Price:** 💰 {details['price']:,}\n**Duration:** {duration_hours} hours",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase temporary items with coins.")
    @app_commands.describe(
        item="The item you want to purchase.",
        duration="The duration of the item (e.g., '1h', '24h')."
    )
    @app_commands.choices(
        item=[
            discord.app_commands.Choice(name="XP Boost", value="xp_boost"),
            discord.app_commands.Choice(name="Lucky Charm", value="lucky_charm")
        ]
    )
    async def buy(self, interaction: discord.Interaction, item: str):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)
        
        item_details = SHOP_ITEMS.get(item)
        if not item_details:
            await interaction.response.send_message("That item does not exist in the shop.", ephemeral=True)
            return
            
        cost = item_details["price"]
        duration = item_details["duration"]

        if user_data["coins"] < cost:
            await interaction.response.send_message("You don't have enough coins to purchase this item.", ephemeral=True)
            return

        # Process the purchase
        database.db.remove_coins(user_id, cost)
        database.db.add_temporary_purchase(user_id, item, duration)

        embed = discord.Embed(
            title="Purchase Successful!",
            description=f"You have purchased a **{item.title().replace('_', ' ')}** for **{cost}** coins.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"The item will last for {int(duration / 3600)} hours.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin and bet coins.")
    @app_commands.describe(amount="The amount of coins you want to bet.")
    async def coinflip(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)

        if amount <= 0:
            await interaction.response.send_message("You must bet a positive amount of coins.", ephemeral=True)
            return
            
        if user_data["coins"] < amount:
            await interaction.response.send_message("You don't have enough coins for that bet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        outcome = random.choice(["win", "lose"])
        
        if outcome == "win":
            database.db.add_coins(user_id, amount)
            await interaction.followup.send(f"🪙 You won the coinflip and gained **{amount}** coins! Your new balance is {user_data['coins'] + amount:,}.")
        else:
            database.db.remove_coins(user_id, amount)
            await interaction.followup.send(f"😔 You lost the coinflip and lost **{amount}** coins. Your new balance is {user_data['coins'] - amount:,}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
