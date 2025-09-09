import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random

# Define shop items with cost and duration in seconds
SHOP_ITEMS = {
    "xp_boost": {"price": 500, "duration": 3600, "emoji": "⚡", "description": "Double XP for 1 hour"}, 
    "lucky_charm": {"price": 1000, "duration": 86400, "emoji": "🍀", "description": "Better rewards for 24 hours"},
    "money_magnet": {"price": 750, "duration": 7200, "emoji": "🧲", "description": "+50% coin rewards for 2 hours"}
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
        bank = user_data.get("bank", 0)
        net_worth = coins + bank

        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Wallet",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="💵 Cash", value=f"`{coins:,}` coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{bank:,}` coins", inline=True)
        embed.add_field(name="💎 Net Worth", value=f"`{net_worth:,}` coins", inline=True)
        embed.add_field(name="🍪 Cookies", value=f"`{cookies:,}` cookies", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="work", description="Work at your job to earn coins and XP!")
    async def work(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if not database.db.can_work(user_id):
            next_work = database.db.get_user_data(user_id).get("last_work", 0) + 3600
            embed = discord.Embed(
                title="⏰ Still on Break!",
                description=f"You can work again <t:{int(next_work)}:R>",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Job progression system
        user_data = database.db.get_user_data(user_id)
        work_count = user_data.get("work_count", 0)
        
        # Job titles based on work count
        jobs = [
            {"title": "Intern", "min_works": 0, "base_pay": (50, 150)},
            {"title": "Junior Employee", "min_works": 10, "base_pay": (100, 250)},
            {"title": "Employee", "min_works": 25, "base_pay": (150, 350)},
            {"title": "Senior Employee", "min_works": 50, "base_pay": (200, 450)},
            {"title": "Team Lead", "min_works": 100, "base_pay": (300, 600)},
            {"title": "Manager", "min_works": 200, "base_pay": (400, 800)},
            {"title": "Director", "min_works": 500, "base_pay": (500, 1000)},
            {"title": "CEO", "min_works": 1000, "base_pay": (750, 1500)}
        ]
        
        current_job = jobs[0]
        for job in reversed(jobs):
            if work_count >= job["min_works"]:
                current_job = job
                break
        
        earnings = random.randint(*current_job["base_pay"])
        xp_gain = random.randint(15, 35)
        
        # Work activities
        activities = [
            "completed a major project",
            "impressed your boss",
            "solved a difficult problem",
            "helped a colleague",
            "attended an important meeting",
            "finished all tasks early",
            "received positive feedback"
        ]
        
        activity = random.choice(activities)
        
        result = database.db.process_work(user_id, current_job["title"], earnings)
        
        # Update work count
        database.db.update_user_data(user_id, {"work_count": work_count + 1})

        if result["success"]:
            embed = discord.Embed(
                title="💼 Work Complete!",
                description=f"**{interaction.user.display_name}** {activity} as a **{current_job['title']}**",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="💰 Earned", value=f"`{earnings}` coins", inline=True)
            embed.add_field(name="⭐ XP Gained", value=f"`{xp_gain}` XP", inline=True)
            embed.add_field(name="🔥 Work Streak", value=f"`{result['work_streak']}` days", inline=True)
            embed.set_footer(text=f"Total works completed: {work_count + 1}")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ An error occurred while processing your work.", ephemeral=True)

    @app_commands.command(name="shop", description="Browse the premium items shop.")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Premium Items Shop",
            description="Purchase temporary boosts and items with your coins!",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        for item_id, details in SHOP_ITEMS.items():
            duration_hours = int(details["duration"] / 3600)
            embed.add_field(
                name=f"{details['emoji']} {item_id.title().replace('_', ' ')}",
                value=f"**Price:** `{details['price']:,}` coins\n**Duration:** `{duration_hours}h`\n*{details['description']}*",
                inline=True
            )
        
        embed.set_footer(text="Use /buy <item> to purchase an item")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase temporary items with coins.")
    @app_commands.describe(item="The item you want to purchase.")
    @app_commands.choices(
        item=[
            discord.app_commands.Choice(name="⚡ XP Boost", value="xp_boost"),
            discord.app_commands.Choice(name="🍀 Lucky Charm", value="lucky_charm"),
            discord.app_commands.Choice(name="🧲 Money Magnet", value="money_magnet")
        ]
    )
    async def buy(self, interaction: discord.Interaction, item: str):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)
        
        item_details = SHOP_ITEMS.get(item)
        if not item_details:
            await interaction.response.send_message("❌ That item doesn't exist in the shop.", ephemeral=True)
            return
            
        cost = item_details["price"]
        duration = item_details["duration"]

        if user_data["coins"] < cost:
            needed = cost - user_data["coins"]
            embed = discord.Embed(
                title="💸 Insufficient Funds",
                description=f"You need `{needed:,}` more coins to buy this item.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Process the purchase
        database.db.remove_coins(user_id, cost)
        database.db.add_temporary_purchase(user_id, item, duration)

        embed = discord.Embed(
            title="🎉 Purchase Successful!",
            description=f"**{interaction.user.display_name}** purchased **{item_details['emoji']} {item.title().replace('_', ' ')}**",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="💰 Cost", value=f"`{cost:,}` coins", inline=True)
        embed.add_field(name="⏰ Duration", value=f"`{int(duration / 3600)}` hours", inline=True)
        embed.add_field(name="📝 Effect", value=item_details["description"], inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="Flip a coin and bet coins.")
    @app_commands.describe(amount="The amount of coins you want to bet.")
    async def coinflip(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)

        if amount <= 0:
            await interaction.response.send_message("❌ You must bet a positive amount of coins.", ephemeral=True)
            return
            
        if user_data["coins"] < amount:
            await interaction.response.send_message("❌ You don't have enough coins for that bet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        # Animated coin flip
        outcome = random.choice(["heads", "tails"])
        coin_gif = "https://media.giphy.com/media/3o7aCRloybJlXpNjSU/giphy.gif"
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"**{interaction.user.display_name}** flipped a coin betting `{amount:,}` coins!",
            color=discord.Color.gold()
        )
        embed.set_image(url=coin_gif)
        embed.set_footer(text="Flipping...")
        
        message = await interaction.followup.send(embed=embed)
        
        # Wait for suspense
        await asyncio.sleep(3)
        
        if outcome == "heads":
            database.db.add_coins(user_id, amount)
            new_balance = user_data['coins'] + amount
            
            embed = discord.Embed(
                title="🪙 HEADS - You Win!",
                description=f"**{interaction.user.display_name}** won `{amount:,}` coins!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="💰 New Balance", value=f"`{new_balance:,}` coins", inline=True)
            embed.set_thumbnail(url="https://i.imgur.com/YpTzj5Q.png")  # Heads coin image
        else:
            database.db.remove_coins(user_id, amount)
            new_balance = user_data['coins'] - amount
            
            embed = discord.Embed(
                title="🪙 TAILS - You Lose!",
                description=f"**{interaction.user.display_name}** lost `{amount:,}` coins!",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="💰 New Balance", value=f"`{new_balance:,}` coins", inline=True)
            embed.set_thumbnail(url="https://i.imgur.com/8XfzJ5Q.png")  # Tails coin image
        
        embed.set_footer(text=f"Bet: {amount:,} coins")
        await message.edit(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
