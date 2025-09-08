import discord
from discord.ext import commands
from discord import app_commands
import database
import time

class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="profile", description="Shows a comprehensive user profile.")
    @app_commands.describe(user="The user whose profile you want to view (optional).")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        
        user_data = database.db.get_user_data(target_user.id)
        
        xp = user_data.get("xp", 0)
        level = user_data.get("level", 0)
        coins = user_data.get("coins", 0)
        cookies = user_data.get("cookies", 0)
        job = user_data.get("job", "Unemployed")
        daily_streak = user_data.get("daily_streak", 0)

        embed = discord.Embed(
            title=f"{target_user.display_name}'s Profile",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
        embed.add_field(name="Level", value=level, inline=True)
        embed.add_field(name="XP", value=xp, inline=True)
        embed.add_field(name="Job", value=job, inline=True)
        embed.add_field(name="Coins", value=f"💰 {coins:,}", inline=True)
        embed.add_field(name="Cookies", value=f"🍪 {cookies:,}", inline=True)
        embed.add_field(name="Daily Streak", value=f"🔥 {daily_streak} days", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="daily", description="Claim daily XP and coin bonus with streak rewards.")
    async def daily(self, interaction: discord.Interaction):
        result = database.db.claim_daily_bonus(interaction.user.id)

        if result["success"]:
            embed = discord.Embed(
                title="Daily Bonus Claimed!",
                description=f"You received **{result['coins_earned']}** coins and **{result['xp_earned']}** XP.",
                color=discord.Color.green()
            )
            embed.add_field(name="Current Streak", value=f"🔥 {result['streak']} days", inline=False)
            if result["level_up"]:
                embed.add_field(name="Level Up!", value=f"You are now level **{result['new_level']}**!", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(result["message"], ephemeral=True)
            
    @app_commands.command(name="myitems", description="View your active temporary purchases and their remaining time.")
    async def myitems(self, interaction: discord.Interaction):
        purchases = database.db.get_active_temporary_purchases(interaction.user.id)
        
        if not purchases:
            await interaction.response.send_message("You have no active temporary purchases.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Active Items",
            color=discord.Color.blue()
        )
        
        current_time = time.time()
        for item in purchases:
            item_type = item.get("item_type", "Unknown Item")
            time_left = item.get("expires_at", 0) - current_time
            
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            
            embed.add_field(
                name=f"• {item_type}",
                value=f"Time remaining: **{hours}h {minutes}m**",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="leaderboard", description="View server leaderboards with pagination.")
    @app_commands.describe(
        type="The type of leaderboard to view.",
        page="The page number to display."
    )
    @app_commands.choices(
        type=[
            discord.app_commands.Choice(name="XP & Levels", value="xp"),
            discord.app_commands.Choice(name="Cookies", value="cookies"),
            discord.app_commands.Choice(name="Coins", value="coins"),
            discord.app_commands.Choice(name="Daily Streaks", value="daily_streak")
        ]
    )
    async def leaderboard(self, interaction: discord.Interaction, type: str, page: int = 1):
        if type == "daily_streak":
            leaderboard_data = database.db.get_streak_leaderboard(page)
            title = "Daily Streaks Leaderboard"
            value_key = "daily_streak"
            emoji = "🔥"
        else:
            leaderboard_data = database.db.get_paginated_leaderboard(type, page)
            title = f"{type.replace('_', ' ').title()} Leaderboard"
            value_key = type
            emoji = "💰" if type == "coins" else "🍪" if type == "cookies" else "✨"

        if not leaderboard_data['users']:
            await interaction.response.send_message("No data found for this leaderboard.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{title} - Page {leaderboard_data['current_page']}/{leaderboard_data['total_pages']}",
            color=discord.Color.purple()
        )

        for i, entry in enumerate(leaderboard_data['users']):
            user_id = entry.get("user_id", "Unknown User")
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            user_display_name = user.display_name if user else "Unknown User"
            
            value = entry.get(value_key, 0)
            rank = (leaderboard_data['current_page'] - 1) * leaderboard_data['members_per_page'] + i + 1
            
            embed.add_field(
                name=f"#{rank} - {user_display_name}",
                value=f"{emoji} {value:,}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
