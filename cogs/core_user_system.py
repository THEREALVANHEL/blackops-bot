import discord
from discord.ext import commands
from discord import app_commands
import database
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class ProfileView(discord.ui.View):
    """Interactive view for user profiles"""
    def __init__(self, user_id: int, target_user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.target_user_id = target_user_id

    @discord.ui.button(label="🏆 Achievements", style=discord.ButtonStyle.secondary)
    async def show_achievements(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your profile!", ephemeral=True)
            return
        
        user_data = database.db.get_user_data(self.target_user_id)
        achievements = user_data.get("achievements", [])
        
        embed = discord.Embed(
            title="🏆 User Achievements",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        if achievements:
            achievement_list = "\n".join([f"🏅 {achievement}" for achievement in achievements[:10]])
            embed.add_field(name="Unlocked Achievements", value=achievement_list, inline=False)
        else:
            embed.add_field(name="No Achievements Yet", value="Complete activities to unlock achievements!", inline=False)
        
        embed.add_field(name="Total Achievements", value=f"`{len(achievements)}`", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📊 Detailed Stats", style=discord.ButtonStyle.primary)
    async def show_detailed_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_data = database.db.get_user_data(self.target_user_id)
        
        embed = discord.Embed(
            title="📊 Detailed Statistics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Economy stats
        total_earned = user_data.get("economy", {}).get("total_earned", 0)
        total_spent = user_data.get("economy", {}).get("total_spent", 0)
        
        embed.add_field(name="💰 Economy", 
                       value=f"**Earned:** {total_earned:,} coins\n**Spent:** {total_spent:,} coins\n**Net:** {total_earned - total_spent:+,} coins", 
                       inline=True)
        
        # Work stats
        work_count = user_data.get("work_count", 0)
        work_streak = user_data.get("work_streak", 0)
        
        embed.add_field(name="💼 Work Stats", 
                       value=f"**Total Works:** {work_count:,}\n**Current Streak:** {work_streak} days", 
                       inline=True)
        
        # Pet stats
        pets = user_data.get("pets", [])
        if pets:
            total_battles = sum(pet.get("battles_total", 0) for pet in pets)
            total_wins = sum(pet.get("battles_won", 0) for pet in pets)
            win_rate = (total_wins / total_battles * 100) if total_battles > 0 else 0
            
            embed.add_field(name="🐾 Pet Stats", 
                           value=f"**Pets Owned:** {len(pets)}\n**Battle Wins:** {total_wins}/{total_battles}\n**Win Rate:** {win_rate:.1f}%", 
                           inline=True)
        
        # Social stats
        social_data = user_data.get("social", {})
        friends = len(social_data.get("friends", []))
        reputation = social_data.get("reputation", 0)
        
        embed.add_field(name="👥 Social", 
                       value=f"**Friends:** {friends}\n**Reputation:** {reputation:+}", 
                       inline=True)
        
        # Activity stats
        stats = user_data.get("stats", {})
        commands_used = stats.get("commands_used", 0)
        messages_sent = stats.get("messages_sent", 0)
        
        embed.add_field(name="📈 Activity", 
                       value=f"**Commands Used:** {commands_used:,}\n**Messages Sent:** {messages_sent:,}", 
                       inline=True)
        
        # Account info
        created_at = user_data.get("created_at", datetime.utcnow())
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        days_active = (datetime.utcnow() - created_at).days
        embed.add_field(name="📅 Account", 
                       value=f"**Days Active:** {days_active}\n**Member Since:** <t:{int(created_at.timestamp())}:R>", 
                       inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class CoreUserSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ==================== BASIC COMMANDS ====================

    @app_commands.command(name="hello", description="Get a personalized greeting with your current status.")
    async def hello(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        level = user_data.get("level", 1)
        streak = user_data.get("daily_streak", 0)
        
        # Personalized greetings based on level and streak
        greetings = [
            f"Hello there, {interaction.user.display_name}!",
            f"Hey {interaction.user.display_name}! Ready for another adventure?",
            f"Greetings, Level {level} adventurer!",
            f"Welcome back, {interaction.user.display_name}!"
        ]
        
        if streak > 7:
            greetings.append(f"Hello, streak master! {streak} days strong! 🔥")
        if level > 50:
            greetings.append(f"Greetings, legendary user! Level {level} is impressive! ⭐")
        
        greeting = greetings[0] if level == 1 and streak == 0 else random.choice(greetings)
        
        embed = discord.Embed(
            title="👋 Personal Greeting",
            description=greeting,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="📊 Quick Stats", 
                       value=f"**Level:** {level}\n**Daily Streak:** {streak} days\n**Coins:** {user_data.get('coins', 0):,}", 
                       inline=True)
        
        # Show next daily claim time
        last_daily = user_data.get("last_daily", 0)
        next_daily = last_daily + 86400
        if time.time() < next_daily:
            embed.add_field(name="⏰ Next Daily", value=f"<t:{int(next_daily)}:R>", inline=True)
        else:
            embed.add_field(name="🎁 Daily Available", value="Use `/daily` to claim!", inline=True)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check bot latency and system status.")
    async def ping(self, interaction: discord.Interaction):
        # Measure response time
        start_time = time.time()
        await interaction.response.defer()
        response_time = (time.time() - start_time) * 1000
        
        # Get bot latency
        bot_latency = round(self.bot.latency * 1000)
        
        # Database health check
        db_health = database.db.get_database_health()
        db_status = "🟢 Connected" if db_health["connected"] else "🟡 Memory Mode"
        
        embed = discord.Embed(
            title="🏓 Pong! System Status",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🤖 Bot Latency", value=f"`{bot_latency}ms`", inline=True)
        embed.add_field(name="⚡ Response Time", value=f"`{response_time:.0f}ms`", inline=True)
        embed.add_field(name="🗄️ Database", value=db_status, inline=True)
        
        # System info
        embed.add_field(name="📊 Guilds", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="👥 Users", value=f"`{len(self.bot.users):,}`", inline=True)
        embed.add_field(name="⚡ Commands", value=f"`{len(self.bot.tree.get_commands())}`", inline=True)
        
        # Performance indicators
        if bot_latency < 100:
            performance = "🟢 Excellent"
        elif bot_latency < 250:
            performance = "🟡 Good"
        else:
            performance = "🔴 Poor"
        
        embed.add_field(name="📈 Performance", value=performance, inline=True)
        
        embed.set_footer(text="All systems operational!")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="info", description="Comprehensive bot information and statistics.")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 BlackOps Bot Information",
            description="A comprehensive Discord bot with economy, pets, jobs, and more!",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        # Bot owner info
        if self.bot.owner_id:
            owner = self.bot.get_user(self.bot.owner_id)
            embed.add_field(name="👑 Developer", value=owner.mention if owner else f"<@{self.bot.owner_id}>", inline=True)
        
        embed.add_field(name="🏓 Latency", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)
        embed.add_field(name="📊 Commands", value=f"`{len(self.bot.tree.get_commands())}`", inline=True)
        
        # Database stats
        db_stats = database.db.get_database_stats()
        embed.add_field(name="🗄️ Database", value=f"`{db_stats['users']:,}` users\n`{db_stats['guilds']}` guilds\n{db_stats['storage']}", inline=True)
        
        # Features
        features = [
            "💰 Advanced Economy System",
            "🐾 Pet System with Breeding",
            "💼 Career Progression",
            "🏦 Banking & Investments", 
            "🎰 Gambling Games",
            "⚔️ Pet Battles",
            "🤖 AI Chat Integration",
            "📊 Comprehensive Statistics"
        ]
        
        embed.add_field(name="✨ Features", value="\n".join(features[:4]), inline=True)
        embed.add_field(name="🎮 Games & Fun", value="\n".join(features[4:]), inline=True)
        
        # System status
        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None
        if uptime:
            embed.add_field(name="⏱️ Uptime", value=f"`{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m`", inline=True)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Thank you for using BlackOps Bot!")
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="serverinfo", description="Comprehensive server information and statistics.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(
            title=f"🏰 {guild.name} Server Information",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Basic server info
        embed.add_field(name="👑 Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="👥 Members", value=f"`{guild.member_count:,}`", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        
        # Channel and role counts
        embed.add_field(name="📺 Channels", value=f"`{len(guild.channels)}`", inline=True)
        embed.add_field(name="🎭 Roles", value=f"`{len(guild.roles)}`", inline=True)
        embed.add_field(name="😀 Emojis", value=f"`{len(guild.emojis)}`", inline=True)
        
        # Server statistics
        online_members = len([m for m in guild.members if m.status != discord.Status.offline])
        bot_count = len([m for m in guild.members if m.bot])
        human_count = guild.member_count - bot_count
        
        embed.add_field(name="🟢 Online Members", value=f"`{online_members:,}`", inline=True)
        embed.add_field(name="👤 Humans", value=f"`{human_count:,}`", inline=True)
        embed.add_field(name="🤖 Bots", value=f"`{bot_count:,}`", inline=True)
        
        # Server features
        features = []
        if guild.premium_tier > 0:
            features.append(f"💎 Nitro Level {guild.premium_tier}")
        if guild.premium_subscription_count > 0:
            features.append(f"🚀 {guild.premium_subscription_count} Boosts")
        if guild.verification_level:
            features.append(f"🔒 Verification: {guild.verification_level.name.title()}")
        
        if features:
            embed.add_field(name="✨ Server Features", value="\n".join(features), inline=False)
        
        # Creation date and age
        created_at = guild.created_at
        days_old = (datetime.utcnow() - created_at.replace(tzinfo=None)).days
        
        embed.add_field(name="📅 Created", value=f"<t:{int(created_at.timestamp())}:F>", inline=True)
        embed.add_field(name="🗓️ Age", value=f"`{days_old:,}` days old", inline=True)
        
        # Top roles (by member count)
        top_roles = sorted([r for r in guild.roles if not r.is_default()], key=lambda r: len(r.members), reverse=True)[:3]
        if top_roles:
            roles_text = "\n".join([f"{role.mention} (`{len(role.members)}` members)" for role in top_roles])
            embed.add_field(name="🎭 Top Roles", value=roles_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

    # ==================== LEVELING COMMANDS ====================

    @app_commands.command(name="profile", description="View comprehensive user profile with statistics.")
    @app_commands.describe(user="The user whose profile you want to view (optional).")
    async def profile(self, interaction: discord.Interaction, user: discord.Member = None):
        target_user = user or interaction.user
        user_data = database.db.get_user_data(target_user.id)
        
        # Basic stats
        xp = user_data.get("xp", 0)
        level = user_data.get("level", 1)
        coins = user_data.get("coins", 0)
        cookies = user_data.get("cookies", 0)
        daily_streak = user_data.get("daily_streak", 0)
        
        # Calculate XP for next level
        current_level_xp = (level ** 2) * 100
        next_level_xp = ((level + 1) ** 2) * 100
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress_percentage = (xp_progress / xp_needed) * 100
        
        embed = discord.Embed(
            title=f"👤 {target_user.display_name}'s Profile",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Level progress bar
        progress_bar = self._create_progress_bar(progress_percentage)
        embed.add_field(
            name=f"⭐ Level {level}",
            value=f"{progress_bar}\n`{xp_progress:,}/{xp_needed:,}` XP ({progress_percentage:.1f}%)",
            inline=False
        )
        
        # Financial overview
        bank_balance = user_data.get("bank", 0)
        net_worth = coins + bank_balance
        
        embed.add_field(name="💰 Wealth", 
                       value=f"**Coins:** `{coins:,}`\n**Bank:** `{bank_balance:,}`\n**Net Worth:** `{net_worth:,}`", 
                       inline=True)
        
        # Activity stats
        work_count = user_data.get("work_count", 0)
        embed.add_field(name="📊 Activity", 
                       value=f"**Total XP:** `{xp:,}`\n**Work Sessions:** `{work_count:,}`\n**Daily Streak:** `{daily_streak}` 🔥", 
                       inline=True)
        
        # Job information
        job_data = user_data.get("job", {})
        if job_data.get("career_path"):
            job_title = job_data.get("title", "Employee")
            job_level = job_data.get("current_level", 0) + 1
            job_performance = job_data.get("performance_rating", 3.0)
            
            embed.add_field(name="💼 Career", 
                           value=f"**Position:** {job_title}\n**Level:** {job_level}\n**Performance:** {job_performance:.1f}/5.0", 
                           inline=True)
        else:
            embed.add_field(name="💼 Career", value="*Unemployed*\nUse `/career` to find a job!", inline=True)
        
        # Pet information
        pets = user_data.get("pets", [])
        if pets:
            pet_info = []
            for pet in pets[:3]:  # Show first 3 pets
                pet_level = pet.get("level", 1)
                pet_info.append(f"{pet['emoji']} {pet['name']} (Lv.{pet_level})")
            
            embed.add_field(name="🐾 Pets", 
                           value="\n".join(pet_info) + (f"\n*+{len(pets)-3} more*" if len(pets) > 3 else ""), 
                           inline=True)
        else:
            embed.add_field(name="🐾 Pets", value="*No pets*\nUse `/adopt` to get one!", inline=True)
        
        # Special items and achievements
        temp_purchases = database.db.get_active_temporary_purchases(target_user.id)
        active_boosts = len(temp_purchases)
        achievements = user_data.get("achievements", [])
        
        embed.add_field(name="✨ Special", 
                       value=f"**Active Boosts:** `{active_boosts}`\n**Cookies:** `{cookies:,}` 🍪\n**Achievements:** `{len(achievements)}`", 
                       inline=True)
        
        # Account age and activity
        created_at = user_data.get("created_at", datetime.utcnow())
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        last_seen = user_data.get("last_seen", datetime.utcnow())
        if isinstance(last_seen, str):
            last_seen = datetime.fromisoformat(last_seen)
        
        days_active = (datetime.utcnow() - created_at).days
        
        embed.add_field(name="📅 Account Info", 
                       value=f"**Member Since:** <t:{int(created_at.timestamp())}:R>\n**Days Active:** `{days_active}`\n**Last Seen:** <t:{int(last_seen.timestamp())}:R>", 
                       inline=False)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        # Add interactive view
        view = ProfileView(interaction.user.id, target_user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="myitems", description="View your active items, boosts, and temporary purchases.")
    async def myitems(self, interaction: discord.Interaction):
        purchases = database.db.get_active_temporary_purchases(interaction.user.id)
        
        embed = discord.Embed(
            title=f"✨ {interaction.user.display_name}'s Active Items",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        if not purchases:
            embed.add_field(
                name="📦 No Active Items",
                value="You don't have any active boosts or items.\nVisit `/shop` to purchase some!",
                inline=False
            )
            embed.color = discord.Color.orange()
        else:
            current_time = time.time()
            item_groups = {}
            
            # Group items by type
            for item in purchases:
                item_type = item.get("item_type", "Unknown Item")
                if item_type not in item_groups:
                    item_groups[item_type] = []
                item_groups[item_type].append(item)
            
            for item_type, items in item_groups.items():
                total_time_left = sum(max(0, item.get("expires_at", 0) - current_time) for item in items)
                hours = int(total_time_left // 3600)
                minutes = int((total_time_left % 3600) // 60)
                
                # Get item emoji and description
                from cogs.unified_economy import PREMIUM_SHOP_ITEMS
                item_data = PREMIUM_SHOP_ITEMS.get(item_type, {"emoji": "✨", "description": "Special item"})
                
                embed.add_field(
                    name=f"{item_data['emoji']} {item_type.title().replace('_', ' ')}",
                    value=f"**Quantity:** {len(items)}\n**Time Left:** {hours}h {minutes}m\n*{item_data['description']}*",
                    inline=True
                )
            
            embed.add_field(
                name="💡 Tip",
                value="Stack multiple items of the same type to extend duration!",
                inline=False
            )
        
        embed.set_footer(text="Items expire automatically when time runs out")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View server leaderboards with enhanced pagination.")
    @app_commands.describe(
        type="The type of leaderboard to view.",
        page="The page number to display."
    )
    @app_commands.choices(
        type=[
            discord.app_commands.Choice(name="⭐ XP & Levels", value="xp"),
            discord.app_commands.Choice(name="🍪 Cookies", value="cookies"),
            discord.app_commands.Choice(name="💰 Coins", value="coins"),
            discord.app_commands.Choice(name="🔥 Daily Streaks", value="daily_streak"),
            discord.app_commands.Choice(name="💼 Work Sessions", value="work_count"),
            discord.app_commands.Choice(name="🏦 Net Worth", value="net_worth")
        ]
    )
    async def leaderboard(self, interaction: discord.Interaction, type: str, page: int = 1):
        if page < 1:
            page = 1
        
        # Special handling for net worth (calculated field)
        if type == "net_worth":
            # For now, use coins as fallback since net worth requires calculation
            leaderboard_data = database.db.get_paginated_leaderboard("coins", page)
            title = "💎 Net Worth Leaderboard"
            emoji = "💎"
        elif type == "daily_streak":
            leaderboard_data = database.db.get_streak_leaderboard(page)
            title = "🔥 Daily Streaks Leaderboard"
            emoji = "🔥"
        else:
            leaderboard_data = database.db.get_paginated_leaderboard(type, page)
            title_map = {
                "xp": "⭐ XP & Levels Leaderboard",
                "coins": "💰 Coins Leaderboard", 
                "cookies": "🍪 Cookies Leaderboard",
                "work_count": "💼 Work Sessions Leaderboard"
            }
            title = title_map.get(type, f"{type.title()} Leaderboard")
            emoji_map = {"xp": "⭐", "coins": "💰", "cookies": "🍪", "work_count": "💼"}
            emoji = emoji_map.get(type, "📊")

        if not leaderboard_data['users']:
            embed = discord.Embed(
                title="📊 No Data Found",
                description="No users found for this leaderboard category.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{title} - Page {leaderboard_data['current_page']}/{leaderboard_data['total_pages']}",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow()
        )

        leaderboard_text = ""
        for i, entry in enumerate(leaderboard_data['users']):
            user_id = entry.get("user_id", "Unknown User")
            user = self.bot.get_user(user_id)
            user_display_name = user.display_name if user else f"User {user_id}"
            
            # Get the value for display
            if type == "net_worth":
                # Calculate net worth on the fly
                coins = entry.get("coins", 0)
                bank = entry.get("bank", 0)
                value = coins + bank
            else:
                value = entry.get(type, 0)
            
            rank = (leaderboard_data['current_page'] - 1) * leaderboard_data['members_per_page'] + i + 1
            
            # Special formatting for XP leaderboard
            if type == "xp":
                level = entry.get("level", 1)
                leaderboard_text += f"`#{rank:2d}` **{user_display_name}** - Level {level} ({value:,} XP)\n"
            else:
                leaderboard_text += f"`#{rank:2d}` **{user_display_name}** - {emoji} {value:,}\n"
        
        embed.description = leaderboard_text
        
        # Add pagination info
        embed.add_field(
            name="📄 Navigation",
            value=f"Page {leaderboard_data['current_page']} of {leaderboard_data['total_pages']}\nShowing {len(leaderboard_data['users'])} of {leaderboard_data['total_users']:,} users",
            inline=True
        )
        
        # Find user's rank if they're not on current page
        user_data = database.db.get_user_data(interaction.user.id)
        user_value = user_data.get(type, 0) if type != "net_worth" else user_data.get("coins", 0) + user_data.get("bank", 0)
        
        if user_value > 0:
            # Rough estimate of user's rank (not perfectly accurate but good enough)
            user_rank = "Not ranked"
            for i, entry in enumerate(leaderboard_data['users']):
                if entry.get("user_id") == interaction.user.id:
                    actual_rank = (leaderboard_data['current_page'] - 1) * leaderboard_data['members_per_page'] + i + 1
                    user_rank = f"#{actual_rank}"
                    break
            
            embed.add_field(
                name="🎯 Your Stats",
                value=f"**Rank:** {user_rank}\n**Score:** {emoji} {user_value:,}",
                inline=True
            )
        
        embed.set_footer(text="Updated in real-time • Use different page numbers to navigate")
        await interaction.response.send_message(embed=embed)

    def _create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Create a visual progress bar"""
        filled = int(percentage / 100 * length)
        empty = length - filled
        
        bar = "█" * filled + "░" * empty
        return f"`{bar}` {percentage:.1f}%"

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_message(self, message):
        """Award XP for messages and update activity stats"""
        if message.author.bot or not message.guild:
            return
        
        # Basic XP reward for messages
        xp_gained = random.randint(5, 15)
        result = database.db.add_xp(message.author.id, xp_gained)
        
        # Update message count
        user_data = database.db.get_user_data(message.author.id)
        stats = user_data.get("stats", {})
        stats["messages_sent"] = stats.get("messages_sent", 0) + 1
        stats["last_message"] = time.time()
        
        database.db.update_user_data(message.author.id, {
            "stats": stats,
            "last_seen": datetime.utcnow()
        })
        
        # Level up notification
        if result.get("leveled_up"):
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"**{message.author.display_name}** reached level **{result['new_level']}**!",
                color=discord.Color.gold()
            )
            embed.add_field(name="⭐ New Level", value=result["new_level"], inline=True)
            embed.add_field(name="📊 Total XP", value=f"{result['total_xp']:,}", inline=True)
            
            # Level rewards
            level_rewards = self._calculate_level_rewards(result["new_level"])
            if level_rewards:
                embed.add_field(name="🎁 Level Rewards", value=level_rewards, inline=False)
                
                # Award level rewards
                if "coins" in level_rewards:
                    coins = int(level_rewards.split(" ")[0])
                    database.db.add_coins(message.author.id, coins)
            
            try:
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass  # Can't send messages in this channel

    def _calculate_level_rewards(self, level: int) -> str:
        """Calculate rewards for reaching a new level"""
        rewards = []
        
        # Coin rewards
        base_coins = level * 100
        rewards.append(f"{base_coins} coins")
        
        # Special milestone rewards
        if level % 10 == 0:  # Every 10 levels
            rewards.append("Bonus XP boost")
        
        if level % 25 == 0:  # Every 25 levels
            rewards.append("Lucky charm")
            
        if level == 50:
            rewards.append("Premium shop access")
            
        if level == 100:
            rewards.append("Legendary pet egg")
        
        return " + ".join(rewards) if rewards else "Experience and prestige!"

async def setup(bot: commands.Bot):
    await bot.add_cog(CoreUserSystem(bot))
