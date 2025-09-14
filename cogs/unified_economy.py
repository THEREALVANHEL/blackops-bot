import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random
import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from cogs.ui_components import EconomyDisplay, ElegantEmbed, ModernColors, AnimatedProgressBar

# Enhanced shop items with more variety
PREMIUM_SHOP_ITEMS = {
    "xp_boost": {
        "price": 500, "duration": 3600, "emoji": "⚡", 
        "description": "Double XP for 1 hour", "tier": "common"
    },
    "lucky_charm": {
        "price": 1000, "duration": 86400, "emoji": "🍀", 
        "description": "Better rewards for 24 hours", "tier": "uncommon"
    },
    "money_magnet": {
        "price": 750, "duration": 7200, "emoji": "🧲", 
        "description": "+50% coin rewards for 2 hours", "tier": "common"
    },
    "premium_boost": {
        "price": 2500, "duration": 604800, "emoji": "💎", 
        "description": "All boosts combined for 7 days", "tier": "legendary"
    },
    "work_energizer": {
        "price": 300, "duration": 1800, "emoji": "⚡", 
        "description": "No work cooldown for 30 minutes", "tier": "common"
    },
    "gambling_luck": {
        "price": 1500, "duration": 14400, "emoji": "🎰", 
        "description": "Increased gambling odds for 4 hours", "tier": "rare"
    }
}

# Investment options with risk/reward profiles
INVESTMENT_OPTIONS = {
    "stocks": {
        "name": "Stock Market",
        "emoji": "📈", 
        "risk": 0.3, 
        "min_return": -0.25, 
        "max_return": 0.50, 
        "time": 3600,
        "description": "High risk, high reward stock investments"
    },
    "realestate": {
        "name": "Real Estate",
        "emoji": "🏠", 
        "risk": 0.15, 
        "min_return": 0.02, 
        "max_return": 0.18, 
        "time": 7200,
        "description": "Stable property investments"
    },
    "crypto": {
        "name": "Cryptocurrency",
        "emoji": "₿", 
        "risk": 0.5, 
        "min_return": -0.40, 
        "max_return": 1.0, 
        "time": 1800,
        "description": "Extremely volatile digital assets"
    },
    "bonds": {
        "name": "Government Bonds",
        "emoji": "🏛️", 
        "risk": 0.02, 
        "min_return": 0.01, 
        "max_return": 0.08, 
        "time": 14400,
        "description": "Safe, guaranteed returns"
    },
    "commodities": {
        "name": "Commodities",
        "emoji": "🥇", 
        "risk": 0.25, 
        "min_return": -0.15, 
        "max_return": 0.35, 
        "time": 5400,
        "description": "Gold, oil, and agricultural products"
    }
}

# Credit card tiers with enhanced benefits
CREDIT_CARD_TIERS = {
    "Bronze": {
        "limit": 2000, "coins_req": 1000, "cashback": 0.05, "fee": 0,
        "color": discord.Color.from_rgb(205, 127, 50), "perks": ["Basic cashback"]
    },
    "Silver": {
        "limit": 7500, "coins_req": 5000, "cashback": 0.03, "fee": 100,
        "color": discord.Color.from_rgb(192, 192, 192), "perks": ["Travel insurance", "Purchase protection"]
    },
    "Gold": {
        "limit": 20000, "coins_req": 15000, "cashback": 0.02, "fee": 250,
        "color": discord.Color.gold(), "perks": ["Airport lounge access", "Concierge service"]
    },
    "Platinum": {
        "limit": 50000, "coins_req": 40000, "cashback": 0.015, "fee": 500,
        "color": discord.Color.from_rgb(229, 228, 226), "perks": ["Elite status", "Premium rewards"]
    },
    "Black": {
        "limit": 100000, "coins_req": 100000, "cashback": 0.01, "fee": 1000,
        "color": discord.Color.from_rgb(0, 0, 0), "perks": ["Unlimited benefits", "Personal banker"]
    }
}

# Loan types with detailed terms
LOAN_TYPES = {
    "Personal": {
        "apr": 0.12, "duration_days": 30, "max_amount": 10000, "min_score": 400,
        "description": "Quick personal loans for immediate needs"
    },
    "Business": {
        "apr": 0.10, "duration_days": 60, "max_amount": 50000, "min_score": 500,
        "description": "Fund your business ventures"
    },
    "Emergency": {
        "apr": 0.18, "duration_days": 14, "max_amount": 5000, "min_score": 300,
        "description": "Fast approval for emergencies"
    },
    "Education": {
        "apr": 0.08, "duration_days": 90, "max_amount": 25000, "min_score": 450,
        "description": "Invest in your education and future"
    },
    "Mortgage": {
        "apr": 0.06, "duration_days": 180, "max_amount": 100000, "min_score": 650,
        "description": "Long-term property financing"
    },
    "Auto": {
        "apr": 0.09, "duration_days": 120, "max_amount": 30000, "min_score": 500,
        "description": "Vehicle financing with competitive rates"
    }
}

class EconomyView(discord.ui.View):
    """Interactive view for economy commands"""
    def __init__(self, user_id: int, action_type: str):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.action_type = action_type

    @discord.ui.button(label="💰 Balance", style=discord.ButtonStyle.primary)
    async def show_balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your wallet!", ephemeral=True)
            return
        
        user_data = database.db.get_user_data(self.user_id)
        coins = user_data.get("coins", 0)
        bank = user_data.get("bank", 0)
        net_worth = coins + bank
        
        embed = discord.Embed(
            title="💰 Wallet Overview",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💵 Cash", value=f"`{coins:,}` coins", inline=True)
        embed.add_field(name="🏦 Bank", value=f"`{bank:,}` coins", inline=True)
        embed.add_field(name="💎 Net Worth", value=f"`{net_worth:,}` coins", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class UnifiedEconomy(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ==================== BASIC ECONOMY COMMANDS ====================

    @app_commands.command(name="balance", description="Check your comprehensive financial overview.")
    @app_commands.describe(user="The user whose balance you want to check (optional).")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = database.db.get_user_data(target_user.id)
        
        coins = user_data.get("coins", 0)
        cookies = user_data.get("cookies", 0)
        bank = user_data.get("bank", 0)
        net_worth = coins + bank

        # Calculate total investments value
        investments = user_data.get("investments", [])
        investment_value = sum(inv.get("amount", 0) for inv in investments)
        
        # Calculate total debt
        loans = user_data.get("loans", [])
        total_debt = sum(loan.get("total_payable", 0) for loan in loans)
        
        # Calculate credit limits
        credit_cards = user_data.get("credit_cards", [])
        total_credit_limit = sum(cc.get("limit", 0) for cc in credit_cards)

        embed = discord.Embed(
            title=f"💰 {target_user.display_name}'s Financial Portfolio",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Primary balances
        embed.add_field(name="💵 Cash", value=f"`{coins:,}` coins", inline=True)
        embed.add_field(name="🏦 Savings", value=f"`{bank:,}` coins", inline=True)
        embed.add_field(name="🍪 Cookies", value=f"`{cookies:,}` cookies", inline=True)
        
        # Advanced financial info
        if investment_value > 0:
            embed.add_field(name="📈 Investments", value=f"`{investment_value:,}` coins", inline=True)
        if total_debt > 0:
            embed.add_field(name="💳 Total Debt", value=f"`{total_debt:,}` coins", inline=True)
        if total_credit_limit > 0:
            embed.add_field(name="💎 Credit Limit", value=f"`{total_credit_limit:,}` coins", inline=True)
        
        # Net worth calculation
        true_net_worth = net_worth + investment_value - total_debt
        embed.add_field(name="💎 True Net Worth", value=f"`{true_net_worth:,}` coins", inline=False)
        
        # Credit score
        credit_score = self._calculate_credit_score(user_data)
        credit_rating = self._get_credit_rating(credit_score)
        embed.add_field(name="⭐ Credit Score", value=f"`{credit_score}` - {credit_rating}", inline=True)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        view = EconomyView(target_user.id, "balance")
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="profile", description="View a polished profile card with progress bars and stats.")
    @app_commands.describe(user="Whose profile to view (optional)")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user
        user_data = database.db.get_user_data(target.id)
        # Reuse UI components for modern display
        profile_embed = EconomyDisplay.create_balance_embed(target, user_data)
        # Add extra stats section
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        thresholds = database.db.get_level_thresholds(level)
        current_level_xp = thresholds["current_min_xp"]
        next_level_xp = thresholds["next_min_xp"]
        xp_bar = AnimatedProgressBar.xp_bar(max(0, xp - current_level_xp), max(1, next_level_xp - current_level_xp), level)
        profile_embed.add_field(name="⭐ XP Progress", value=xp_bar, inline=False)
        # Social and economy quick stats
        profile_embed.add_field(name="🎯 Commands Used", value=f"`{user_data.get('stats', {}).get('commands_used', 0):,}`", inline=True)
        profile_embed.add_field(name="🕒 Time Active", value=f"`{user_data.get('stats', {}).get('time_active', 0):,}`", inline=True)
        await interaction.response.send_message(embed=profile_embed)

    @app_commands.command(name="daily", description="Claim enhanced daily rewards with streak bonuses.")
    async def daily(self, interaction: discord.Interaction):
        result = database.db.claim_daily_bonus(interaction.user.id)

        if result["success"]:
            user_data = database.db.get_user_data(interaction.user.id)
            streak = result["streak"]
            
            # Calculate enhanced rewards based on streak
            streak_multiplier = min(1 + (streak * 0.1), 3.0)  # Max 3x multiplier
            bonus_coins = int(100 * streak_multiplier)
            bonus_xp = int(50 * streak_multiplier)
            
            embed = discord.Embed(
                title="🎉 Daily Rewards Claimed!",
                description=f"**{interaction.user.display_name}** claimed their daily bonus!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="💰 Coins Earned", value=f"`{result['coins_earned']:,}` coins", inline=True)
            embed.add_field(name="⭐ XP Gained", value=f"`{result['xp_earned']:,}` XP", inline=True)
            embed.add_field(name="🔥 Current Streak", value=f"`{streak}` days", inline=True)
            
            # Streak milestones
            milestone_rewards = self._get_streak_milestone(streak)
            if milestone_rewards:
                embed.add_field(name="🏆 Milestone Reward!", value=milestone_rewards, inline=False)
                embed.color = discord.Color.gold()
            
            if result["level_up"]:
                embed.add_field(name="🎊 Level Up!", value=f"You are now level **{result['new_level']}**!", inline=False)
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="Come back tomorrow for even better rewards!")
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(result["message"], ephemeral=True)

    # ==================== SHOPPING SYSTEM ====================

    @app_commands.command(name="shop", description="Browse the premium items shop with enhanced features.")
    @app_commands.describe(category="Filter items by category")
    @app_commands.choices(
        category=[
            discord.app_commands.Choice(name="⚡ Boosts", value="boosts"),
            discord.app_commands.Choice(name="🎰 Gambling", value="gambling"),
            discord.app_commands.Choice(name="💎 Premium", value="premium"),
            discord.app_commands.Choice(name="🔧 Tools", value="tools")
        ]
    )
    async def shop(self, interaction: discord.Interaction, category: str = None):
        embed = discord.Embed(
            title="🛒 Premium Items Shop",
            description="Purchase temporary boosts and premium items with your coins!",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Filter items by category if specified
        items_to_show = PREMIUM_SHOP_ITEMS
        if category:
            category_map = {
                "boosts": ["xp_boost", "money_magnet", "work_energizer"],
                "gambling": ["lucky_charm", "gambling_luck"],
                "premium": ["premium_boost"],
                "tools": ["work_energizer"]
            }
            items_to_show = {k: v for k, v in PREMIUM_SHOP_ITEMS.items() if k in category_map.get(category, [])}
        
        for item_id, details in items_to_show.items():
            duration_hours = int(details["duration"] / 3600)
            tier_emoji = {"common": "🟢", "uncommon": "🟡", "rare": "🟠", "legendary": "🟣"}.get(details["tier"], "⚪")
            
            embed.add_field(
                name=f"{details['emoji']} {item_id.title().replace('_', ' ')} {tier_emoji}",
                value=f"**Price:** `{details['price']:,}` coins\n**Duration:** `{duration_hours}h`\n*{details['description']}*",
                inline=True
            )
        
        embed.set_footer(text="Use /buy <item> to purchase an item")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase premium items with enhanced effects.")
    @app_commands.describe(item="The item you want to purchase.", quantity="How many to buy (default: 1)")
    @app_commands.choices(
        item=[
            discord.app_commands.Choice(name="⚡ XP Boost", value="xp_boost"),
            discord.app_commands.Choice(name="🍀 Lucky Charm", value="lucky_charm"),
            discord.app_commands.Choice(name="🧲 Money Magnet", value="money_magnet"),
            discord.app_commands.Choice(name="💎 Premium Boost", value="premium_boost"),
            discord.app_commands.Choice(name="⚡ Work Energizer", value="work_energizer"),
            discord.app_commands.Choice(name="🎰 Gambling Luck", value="gambling_luck")
        ]
    )
    async def buy(self, interaction: discord.Interaction, item: str, quantity: int = 1):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)
        
        item_details = PREMIUM_SHOP_ITEMS.get(item)
        if not item_details:
            await interaction.response.send_message("❌ That item doesn't exist in the shop.", ephemeral=True)
            return
        
        if quantity < 1 or quantity > 10:
            await interaction.response.send_message("❌ You can only buy 1-10 items at once.", ephemeral=True)
            return
            
        total_cost = item_details["price"] * quantity
        duration = item_details["duration"]

        if user_data["coins"] < total_cost:
            needed = total_cost - user_data["coins"]
            embed = discord.Embed(
                title="💸 Insufficient Funds",
                description=f"You need `{needed:,}` more coins to buy {quantity}x {item.replace('_', ' ').title()}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Process the purchase
        database.db.remove_coins(user_id, total_cost)
        
        # Stack duration if buying multiple
        total_duration = duration * quantity
        database.db.add_temporary_purchase(user_id, item, total_duration)

        tier_emoji = {"common": "🟢", "uncommon": "🟡", "rare": "🟠", "legendary": "🟣"}.get(item_details["tier"], "⚪")
        
        embed = discord.Embed(
            title="🎉 Purchase Successful!",
            description=f"**{interaction.user.display_name}** purchased {quantity}x **{item_details['emoji']} {item.title().replace('_', ' ')}** {tier_emoji}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💰 Total Cost", value=f"`{total_cost:,}` coins", inline=True)
        embed.add_field(name="⏰ Duration", value=f"`{int(total_duration / 3600)}` hours", inline=True)
        embed.add_field(name="🎯 Quantity", value=f"`{quantity}x`", inline=True)
        embed.add_field(name="📝 Effect", value=item_details["description"], inline=False)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    # ==================== ENHANCED GAMBLING ====================

    @app_commands.command(name="coinflip", description="Enhanced coinflip with better animations and rewards.")
    @app_commands.describe(amount="The amount of coins you want to bet.", side="Choose heads or tails")
    @app_commands.choices(
        side=[
            discord.app_commands.Choice(name="🪙 Heads", value="heads"),
            discord.app_commands.Choice(name="🪙 Tails", value="tails")
        ]
    )
    async def coinflip(self, interaction: discord.Interaction, amount: int, side: str = None):
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)

        if amount <= 0:
            await interaction.response.send_message("❌ You must bet a positive amount of coins.", ephemeral=True)
            return
            
        if user_data["coins"] < amount:
            await interaction.response.send_message("❌ You don't have enough coins for that bet.", ephemeral=True)
            return

        # Check for gambling luck boost
        active_purchases = database.db.get_active_temporary_purchases(user_id)
        luck_boost = any(p.get("item_type") == "gambling_luck" for p in active_purchases)
        
        await interaction.response.defer()
        
        # Determine outcome with luck boost
        win_chance = 0.52 if luck_boost else 0.50  # Slight edge with luck boost
        user_wins = random.random() < win_chance
        actual_outcome = side if user_wins else ("tails" if side == "heads" else "heads")
        
        # If no side chosen, pick random
        if not side:
            side = random.choice(["heads", "tails"])
            user_wins = actual_outcome == side

        # Animated coin flip
        coin_gif = "https://media.giphy.com/media/3o7aCRloybJlXpNjSU/giphy.gif"
        
        embed = discord.Embed(
            title="🪙 Enhanced Coin Flip",
            description=f"**{interaction.user.display_name}** bet `{amount:,}` coins on **{side.title()}**!",
            color=discord.Color.gold()
        )
        if luck_boost:
            embed.add_field(name="🍀 Gambling Luck Active", value="Increased win chances!", inline=False)
        embed.set_image(url=coin_gif)
        embed.set_footer(text="Flipping...")
        
        message = await interaction.followup.send(embed=embed)
        
        # Wait for suspense
        await asyncio.sleep(3)
        
        # Calculate winnings with multipliers
        if user_wins:
            base_winnings = amount
            luck_multiplier = 1.2 if luck_boost else 1.0
            final_winnings = int(base_winnings * luck_multiplier)
            
            database.db.add_coins(user_id, final_winnings)
            new_balance = user_data['coins'] + final_winnings
            
            embed = discord.Embed(
                title=f"🪙 {actual_outcome.upper()} - You Win!",
                description=f"**{interaction.user.display_name}** won `{final_winnings:,}` coins!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Winnings", value=f"`{final_winnings:,}` coins", inline=True)
            embed.add_field(name="💵 New Balance", value=f"`{new_balance:,}` coins", inline=True)
            if luck_boost:
                embed.add_field(name="🍀 Luck Bonus", value=f"+{int((luck_multiplier-1)*100)}%", inline=True)
            embed.set_thumbnail(url="https://i.imgur.com/YpTzj5Q.png" if actual_outcome == "heads" else "https://i.imgur.com/8XfzJ5Q.png")
        else:
            database.db.remove_coins(user_id, amount)
            new_balance = user_data['coins'] - amount
            
            embed = discord.Embed(
                title=f"🪙 {actual_outcome.upper()} - You Lose!",
                description=f"**{interaction.user.display_name}** lost `{amount:,}` coins!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💸 Lost", value=f"`{amount:,}` coins", inline=True)
            embed.add_field(name="💵 New Balance", value=f"`{new_balance:,}` coins", inline=True)
            embed.set_thumbnail(url="https://i.imgur.com/8XfzJ5Q.png" if actual_outcome == "tails" else "https://i.imgur.com/YpTzj5Q.png")
        
        embed.set_footer(text=f"You chose {side.title()} | Result: {actual_outcome.title()}")
        await message.edit(embed=embed)

    @app_commands.command(name="slots", description="Play enhanced slot machine with multiple paylines.")
    @app_commands.describe(bet="Amount to bet (minimum 50 coins)")
    async def slots(self, interaction: discord.Interaction, bet: int):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if bet < 50:
            await interaction.response.send_message("❌ Minimum bet is 50 coins.", ephemeral=True)
            return
        
        if user_data["coins"] < bet:
            await interaction.response.send_message("❌ You don't have enough coins for that bet.", ephemeral=True)
            return

        await interaction.response.defer()
        
        # Slot machine symbols with different rarities
        symbols = {
            "🍒": {"weight": 30, "multiplier": 2},
            "🍋": {"weight": 25, "multiplier": 3},
            "🍊": {"weight": 20, "multiplier": 4},
            "🍇": {"weight": 15, "multiplier": 5},
            "🔔": {"weight": 8, "multiplier": 10},
            "⭐": {"weight": 5, "multiplier": 15},
            "💎": {"weight": 2, "multiplier": 50},
            "🎰": {"weight": 1, "multiplier": 100}
        }
        
        # Create weighted symbol list
        symbol_pool = []
        for symbol, data in symbols.items():
            symbol_pool.extend([symbol] * data["weight"])
        
        # Spin the slots (3x3 grid)
        result = []
        for _ in range(3):
            row = [random.choice(symbol_pool) for _ in range(3)]
            result.append(row)
        
        # Check for wins
        winnings = 0
        win_lines = []
        
        # Check horizontal lines
        for i, row in enumerate(result):
            if row[0] == row[1] == row[2]:
                multiplier = symbols[row[0]]["multiplier"]
                line_win = bet * multiplier
                winnings += line_win
                win_lines.append(f"Row {i+1}: {row[0]}{row[1]}{row[2]} = {line_win:,} coins")
        
        # Check vertical lines
        for col in range(3):
            if result[0][col] == result[1][col] == result[2][col]:
                multiplier = symbols[result[0][col]]["multiplier"]
                line_win = bet * multiplier
                winnings += line_win
                win_lines.append(f"Col {col+1}: {result[0][col]}{result[1][col]}{result[2][col]} = {line_win:,} coins")
        
        # Check diagonals
        if result[0][0] == result[1][1] == result[2][2]:
            multiplier = symbols[result[1][1]]["multiplier"]
            line_win = bet * multiplier
            winnings += line_win
            win_lines.append(f"Diagonal: {result[0][0]}{result[1][1]}{result[2][2]} = {line_win:,} coins")
        
        if result[0][2] == result[1][1] == result[2][0]:
            multiplier = symbols[result[1][1]]["multiplier"]
            line_win = bet * multiplier
            winnings += line_win
            win_lines.append(f"Diagonal: {result[0][2]}{result[1][1]}{result[2][0]} = {line_win:,} coins")
        
        # Create slot display
        slot_display = "\n".join(["".join(row) for row in result])
        
        if winnings > 0:
            database.db.add_coins(interaction.user.id, winnings - bet)  # Net winnings
            embed = discord.Embed(
                title="🎰 JACKPOT! 🎰",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🎯 Result", value=f"```{slot_display}```", inline=False)
            embed.add_field(name="💰 Total Winnings", value=f"`{winnings:,}` coins", inline=True)
            embed.add_field(name="📈 Net Profit", value=f"`{winnings - bet:+,}` coins", inline=True)
            embed.add_field(name="🏆 Winning Lines", value="\n".join(win_lines) if win_lines else "None", inline=False)
        else:
            database.db.remove_coins(interaction.user.id, bet)
            embed = discord.Embed(
                title="🎰 Better Luck Next Time!",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🎯 Result", value=f"```{slot_display}```", inline=False)
            embed.add_field(name="💸 Lost", value=f"`{bet:,}` coins", inline=True)
        
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await interaction.followup.send(embed=embed)

    # ==================== BANKING SYSTEM ====================

    @app_commands.command(name="bank", description="Access your comprehensive banking dashboard.")
    async def bank(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        
        coins = user_data.get("coins", 0)
        bank_balance = user_data.get("bank", 0)
        net_worth = coins + bank_balance
        
        # Calculate interest earned (daily 1% on bank balance)
        last_interest = user_data.get("last_interest", time.time())
        days_passed = (time.time() - last_interest) / 86400
        interest_rate = 0.01  # 1% daily
        potential_interest = bank_balance * interest_rate * min(days_passed, 7)  # Max 7 days
        
        embed = discord.Embed(
            title=f"🏦 {interaction.user.display_name}'s Banking Dashboard",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Account Overview
        embed.add_field(name="💰 Cash", value=f"`{coins:,}` coins", inline=True)
        embed.add_field(name="🏦 Savings", value=f"`{bank_balance:,}` coins", inline=True)
        embed.add_field(name="💎 Net Worth", value=f"`{net_worth:,}` coins", inline=True)
        
        # Interest Information
        embed.add_field(name="📈 Pending Interest", value=f"`{potential_interest:.0f}` coins", inline=True)
        embed.add_field(name="📊 Interest Rate", value="`1%` per day", inline=True)
        embed.add_field(name="⏰ Last Claimed", value=f"<t:{int(last_interest)}:R>", inline=True)
        
        # Loans and Credit Cards
        loans = user_data.get("loans", [])
        credit_cards = user_data.get("credit_cards", [])
        
        if loans:
            total_debt = sum(loan.get("total_payable", 0) for loan in loans)
            embed.add_field(name="💳 Total Debt", value=f"`{total_debt:,}` coins", inline=True)
            embed.add_field(name="📄 Active Loans", value=f"`{len(loans)}`", inline=True)
        
        if credit_cards:
            total_credit_limit = sum(cc.get("limit", 0) for cc in credit_cards)
            embed.add_field(name="💳 Credit Limit", value=f"`{total_credit_limit:,}` coins", inline=True)
        
        # Credit Score
        credit_score = self._calculate_credit_score(user_data)
        credit_rating = self._get_credit_rating(credit_score)
        embed.add_field(name="⭐ Credit Score", value=f"`{credit_score}` - {credit_rating}", inline=False)
        
        embed.set_footer(text="Use /savings, /loan, /creditcard for more options")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="savings", description="Manage your savings account with compound interest.")
    @app_commands.describe(action="Deposit, withdraw, or claim interest.", amount="Amount to transfer.")
    @app_commands.choices(
        action=[
            discord.app_commands.Choice(name="💰 Deposit", value="deposit"),
            discord.app_commands.Choice(name="💸 Withdraw", value="withdraw"),
            discord.app_commands.Choice(name="📈 Claim Interest", value="interest")
        ]
    )
    async def savings(self, interaction: discord.Interaction, action: str, amount: int = 0):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if action == "interest":
            # Claim daily compound interest
            last_interest = user_data.get("last_interest", time.time())
            days_passed = (time.time() - last_interest) / 86400
            
            if days_passed < 1:
                next_claim = last_interest + 86400
                embed = discord.Embed(
                    title="⏰ Interest Not Ready",
                    description=f"You can claim interest again <t:{int(next_claim)}:R>",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            bank_balance = user_data.get("bank", 0)
            if bank_balance == 0:
                await interaction.response.send_message("❌ You need money in your savings to earn interest!", ephemeral=True)
                return
            
            # Compound interest calculation
            daily_rate = 0.01  # 1% daily
            days_to_apply = min(int(days_passed), 7)  # Max 7 days of interest
            final_amount = bank_balance * ((1 + daily_rate) ** days_to_apply)
            interest_earned = int(final_amount - bank_balance)
            
            new_bank_balance = bank_balance + interest_earned
            database.db.update_user_data(interaction.user.id, {
                "bank": new_bank_balance,
                "last_interest": time.time()
            })
            
            embed = discord.Embed(
                title="📈 Compound Interest Claimed!",
                description=f"**{interaction.user.display_name}** earned interest on their savings!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Interest Earned", value=f"`{interest_earned:,}` coins", inline=True)
            embed.add_field(name="🏦 New Balance", value=f"`{new_bank_balance:,}` coins", inline=True)
            embed.add_field(name="📊 Days Applied", value=f"`{days_to_apply}` days", inline=True)
            embed.add_field(name="📈 Effective Rate", value=f"`{((final_amount/bank_balance - 1)*100):.2f}%`", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            await interaction.response.send_message(embed=embed)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Please enter a positive amount.", ephemeral=True)
            return

        if action == "deposit":
            if user_data["coins"] < amount:
                needed = amount - user_data["coins"]
                embed = discord.Embed(
                    title="💸 Insufficient Funds",
                    description=f"You need `{needed:,}` more coins to make this deposit.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] - amount,
                "bank": user_data["bank"] + amount
            })
            
            embed = discord.Embed(
                title="🏦 Deposit Successful",
                description=f"**{interaction.user.display_name}** deposited money into savings!",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Deposited", value=f"`{amount:,}` coins", inline=True)
            embed.add_field(name="🏦 New Balance", value=f"`{user_data['bank'] + amount:,}` coins", inline=True)
            
            # Show potential interest
            daily_interest = (user_data['bank'] + amount) * 0.01
            embed.add_field(name="📈 Daily Interest", value=f"`{daily_interest:.0f}` coins/day", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
        elif action == "withdraw":
            if user_data["bank"] < amount:
                embed = discord.Embed(
                    title="🏦 Insufficient Savings",
                    description=f"You only have `{user_data['bank']:,}` coins in savings.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            database.db.update_user_data(interaction.user.id, {
                "coins": user_data["coins"] + amount,
                "bank": user_data["bank"] - amount
            })
            
            embed = discord.Embed(
                title="💸 Withdrawal Successful",
                description=f"**{interaction.user.display_name}** withdrew money from savings!",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="💰 Withdrawn", value=f"`{amount:,}` coins", inline=True)
            embed.add_field(name="🏦 Remaining", value=f"`{user_data['bank'] - amount:,}` coins", inline=True)
            embed.set_thumbnail(url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

    # ==================== INVESTMENT SYSTEM ====================

    @app_commands.command(name="invest", description="Invest in various markets with detailed risk analysis.")
    @app_commands.describe(
        investment_type="Type of investment",
        amount="Amount to invest"
    )
    @app_commands.choices(
        investment_type=[
            discord.app_commands.Choice(name="📈 Stocks (High Risk, High Reward)", value="stocks"),
            discord.app_commands.Choice(name="🏠 Real Estate (Medium Risk, Steady)", value="realestate"),
            discord.app_commands.Choice(name="₿ Cryptocurrency (Very High Risk)", value="crypto"),
            discord.app_commands.Choice(name="🏛️ Government Bonds (Low Risk, Low Reward)", value="bonds"),
            discord.app_commands.Choice(name="🥇 Commodities (Medium Risk, Inflation Hedge)", value="commodities")
        ]
    )
    async def invest(self, interaction: discord.Interaction, investment_type: str, amount: int):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if amount < 100:
            await interaction.response.send_message("❌ Minimum investment is 100 coins.", ephemeral=True)
            return
        
        if user_data["coins"] < amount:
            await interaction.response.send_message("❌ You don't have enough coins to invest.", ephemeral=True)
            return
        
        investment = INVESTMENT_OPTIONS[investment_type]
        
        # Create investment record with market conditions
        market_volatility = random.uniform(0.8, 1.2)  # Market conditions
        expected_return = random.uniform(investment["min_return"], investment["max_return"]) * market_volatility
        
        investment_data = {
            "type": investment_type,
            "amount": amount,
            "start_time": time.time(),
            "mature_time": time.time() + investment["time"],
            "expected_return": expected_return,
            "market_conditions": market_volatility
        }
        
        # Store investment
        user_investments = user_data.get("investments", [])
        user_investments.append(investment_data)
        
        database.db.update_user_data(interaction.user.id, {
            "coins": user_data["coins"] - amount,
            "investments": user_investments
        })
        
        mature_timestamp = int(investment_data["mature_time"])
        
        embed = discord.Embed(
            title=f"{investment['emoji']} Investment Made!",
            description=f"**{interaction.user.display_name}** invested in {investment['name']}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="💰 Invested", value=f"`{amount:,}` coins", inline=True)
        embed.add_field(name="⏰ Matures", value=f"<t:{mature_timestamp}:R>", inline=True)
        embed.add_field(name="📊 Risk Level", value=f"`{investment['risk']*100:.0f}%`", inline=True)
        
        # Show market analysis
        market_sentiment = "📈 Bullish" if market_volatility > 1.0 else "📉 Bearish"
        embed.add_field(name="🌐 Market Conditions", value=market_sentiment, inline=True)
        embed.add_field(name="🎯 Expected Return", value=f"`{expected_return*100:+.1f}%`", inline=True)
        embed.add_field(name="📝 Description", value=investment["description"], inline=False)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /portfolio to check your investments")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="portfolio", description="View and manage your investment portfolio with analytics.")
    async def portfolio(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        investments = user_data.get("investments", [])
        
        if not investments:
            embed = discord.Embed(
                title="📊 Investment Portfolio",
                description="You don't have any investments yet!\nUse `/invest` to start building your portfolio.",
                color=discord.Color.orange()
            )
            # Show available investment options
            embed.add_field(
                name="💡 Investment Options",
                value="\n".join([f"{inv['emoji']} **{inv['name']}** - {inv['description']}" 
                               for inv in INVESTMENT_OPTIONS.values()]),
                inline=False
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📊 Investment Portfolio",
            description=f"**{interaction.user.display_name}'s** Active Investments",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        total_invested = 0
        mature_investments = 0
        current_value = 0
        
        for i, inv in enumerate(investments[:10]):  # Show up to 10 investments
            total_invested += inv["amount"]
            is_mature = time.time() >= inv["mature_time"]
            
            if is_mature:
                mature_investments += 1
                # Calculate current value for mature investments
                return_rate = inv.get("expected_return", 0)
                value = int(inv["amount"] * (1 + return_rate))
                current_value += value
            else:
                current_value += inv["amount"]  # Assume no loss for pending
            
            investment_info = INVESTMENT_OPTIONS[inv["type"]]
            status = "✅ Ready" if is_mature else f"⏳ <t:{int(inv['mature_time'])}:R>"
            
            embed.add_field(
                name=f"{investment_info['emoji']} {investment_info['name']}",
                value=f"**Amount:** `{inv['amount']:,}` coins\n**Status:** {status}",
                inline=True
            )
        
        # Portfolio analytics
        profit_loss = current_value - total_invested
        roi_percentage = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        embed.add_field(name="💰 Total Invested", value=f"`{total_invested:,}` coins", inline=True)
        embed.add_field(name="💵 Current Value", value=f"`{current_value:,}` coins", inline=True)
        embed.add_field(name="📈 P&L", value=f"`{profit_loss:+,}` coins ({roi_percentage:+.1f}%)", inline=True)
        embed.add_field(name="✅ Ready to Claim", value=f"`{mature_investments}`", inline=True)
        embed.add_field(name="⏳ Pending", value=f"`{len(investments) - mature_investments}`", inline=True)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /claiminvestment to claim mature investments")
        
        await interaction.response.send_message(embed=embed)

    # ==================== HELPER METHODS ====================

    def _calculate_credit_score(self, user_data: dict) -> int:
        """Calculate credit score based on financial behavior"""
        base_score = 300
        
        # Factors that improve credit score
        bank_balance = user_data.get("bank", 0)
        coins = user_data.get("coins", 0)
        total_wealth = bank_balance + coins
        
        # Wealth factor (up to 200 points)
        wealth_score = min(200, total_wealth // 1000)
        
        # Daily streak factor (up to 150 points)  
        daily_streak = user_data.get("daily_streak", 0)
        streak_score = min(150, daily_streak * 3)
        
        # Work consistency (up to 100 points)
        work_streak = user_data.get("work_streak", 0)
        work_score = min(100, work_streak * 5)
        
        # Loan payment history (can subtract points)
        loans = user_data.get("loans", [])
        loan_penalty = len(loans) * 10  # Penalty for having loans
        
        # Calculate final score
        credit_score = base_score + wealth_score + streak_score + work_score - loan_penalty
        
        return max(300, min(850, credit_score))  # Keep in valid range

    def _get_credit_rating(self, score: int) -> str:
        """Get credit rating based on score"""
        if score >= 800:
            return "Excellent ⭐"
        elif score >= 740:
            return "Very Good 🌟"
        elif score >= 670:
            return "Good ✅"
        elif score >= 580:
            return "Fair ⚠️"
        else:
            return "Poor ❌"

    def _get_streak_milestone(self, streak: int) -> str:
        """Get milestone rewards for daily streaks"""
        milestones = {
            7: "🎉 Week Warrior! +500 bonus coins",
            30: "🏆 Monthly Master! +2000 bonus coins + Lucky Charm",
            100: "💎 Legendary Streak! +10000 bonus coins + Premium Boost",
            365: "👑 Annual Achievement! +50000 bonus coins + Black Credit Card"
        }
        return milestones.get(streak, "")

async def setup(bot: commands.Bot):
    await bot.add_cog(UnifiedEconomy(bot))
