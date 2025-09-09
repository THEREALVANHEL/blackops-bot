# This is the enhanced work command that should REPLACE the work command in economy.py
# It integrates with the jobs system for career progression

@app_commands.command(name="work", description="Work at your job to earn coins, XP, and advance your career!")
async def work(self, interaction: discord.Interaction):
    user_id = interaction.user.id
    
    if not database.db.can_work(user_id):
        user_data = database.db.get_user_data(user_id)
        next_work = user_data.get("last_work", 0) + 3600
        embed = discord.Embed(
            title="⏰ Still on Break!",
            description=f"You can work again <t:{int(next_work)}:R>",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    user_data = database.db.get_user_data(user_id)
    job_data = user_data.get("job", {})
    
    # Check if user has a job
    if not job_data.get("career_path"):
        embed = discord.Embed(
            title="💼 No Job Found",
            description="You need to get a job first before you can work!",
            color=discord.Color.red()
        )
        embed.add_field(name="🚀 Get Started", value="Use `/career` to choose a career path and get hired!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Get job information
    career_path = job_data["career_path"]
    current_level = job_data.get("current_level", 0)
    work_xp = job_data.get("work_xp", 0)
    performance = job_data.get("performance_rating", 3.0)
    
    # Import career paths from jobs system
    from cogs.jobs import CAREER_PATHS, JOB_ACTIVITIES
    
    path_data = CAREER_PATHS[career_path]
    current_job = path_data["jobs"][current_level]
    
    # Calculate earnings based on job level and performance
    base_salary = random.randint(*current_job["salary"])
    performance_multiplier = 0.5 + (performance / 5.0)  # 0.5 to 1.0 multiplier
    final_earnings = int(base_salary * performance_multiplier)
    
    # Calculate XP gain (both regular XP and work XP)
    base_xp = random.randint(15, 35)
    work_xp_gain = random.randint(10, 25)
    
    # Performance affects XP gain
    total_xp = int(base_xp * performance_multiplier)
    total_work_xp = int(work_xp_gain * performance_multiplier)
    
    # Get work activity
    activities = JOB_ACTIVITIES.get(career_path, ["completed daily tasks"])
    activity = random.choice(activities)
    
    # Process the work
    result = database.db.process_work(user_id, current_job["title"], final_earnings)
    
    if not result["success"]:
        await interaction.response.send_message("❌ An error occurred while processing your work.", ephemeral=True)
        return
    
    # Update job-specific data
    new_work_xp = work_xp + total_work_xp
    new_performance = min(5.0, performance + random.uniform(0.01, 0.05))  # Gradual improvement
    total_earnings = job_data.get("total_earnings", 0) + final_earnings
    
    # Update work count for general progression
    work_count = user_data.get("work_count", 0) + 1
    
    database.db.update_user_data(user_id, {
        "job.work_xp": new_work_xp,
        "job.performance_rating": new_performance,
        "job.total_earnings": total_earnings,
        "work_count": work_count
    })
    
    # Add regular XP too
    database.db.add_xp(user_id, total_xp)
    
    # Check if promotion is available
    next_job = None
    promotion_available = False
    if current_level + 1 < len(path_data["jobs"]):
        next_job = path_data["jobs"][current_level + 1]
        if new_work_xp >= next_job["xp_req"] and new_performance >= 3.0:
            promotion_available = True

    # Create response embed
    embed = discord.Embed(
        title=f"💼 Work Complete!",
        description=f"**{interaction.user.display_name}** {activity} as a **{current_job['title']}**",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    
    # Earnings and XP
    embed.add_field(name="💰 Earned", value=f"`{final_earnings:,}` coins", inline=True)
    embed.add_field(name="⭐ XP Gained", value=f"`{total_xp}` XP", inline=True)
    embed.add_field(name="🎯 Work XP", value=f"`+{total_work_xp}` ({new_work_xp:,} total)", inline=True)
    
    # Performance and streak
    embed.add_field(name="📊 Performance", value=f"`{new_performance:.2f}/5.00`", inline=True)
    embed.add_field(name="🔥 Work Streak", value=f"`{result['work_streak']}` days", inline=True)
    embed.add_field(name="🏢 Career", value=f"{path_data['emoji']} {path_data['name']}", inline=True)
    
    # Show promotion availability
    if promotion_available:
        embed.add_field(
            name="🎉 Promotion Available!", 
            value=f"You can be promoted to **{next_job['title']}**!\nUse `/promote` to advance your career.", 
            inline=False
        )
        embed.color = discord.Color.gold()
    elif next_job:
        xp_needed = next_job["xp_req"] - new_work_xp
        embed.add_field(
            name="🔄 Next Promotion", 
            value=f"**{next_job['title']}** - Need `{xp_needed:,}` more Work XP", 
            inline=False
        )
    
    # Performance bonus for exceptional workers
    if new_performance >= 4.5:
        bonus = int(final_earnings * 0.2)
        database.db.add_coins(user_id, bonus)
        embed.add_field(
            name="🌟 Excellence Bonus!", 
            value=f"Outstanding performance earned you an extra `{bonus:,}` coins!", 
            inline=False
        )
        embed.color = discord.Color.gold()
    
    embed.set_footer(text=f"Total career earnings: {total_earnings:,} coins • Works completed: {work_count:,}")
    
    await interaction.response.send_message(embed=embed)
import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random
from datetime import datetime, timedelta

# Job progression system
CAREER_PATHS = {
    "technology": {
        "name": "Technology",
        "emoji": "💻",
        "jobs": [
            {"title": "Intern", "level": 0, "salary": (50, 100), "xp_req": 0},
            {"title": "Junior Developer", "level": 1, "salary": (100, 200), "xp_req": 100},
            {"title": "Software Developer", "level": 2, "salary": (200, 350), "xp_req": 300},
            {"title": "Senior Developer", "level": 3, "salary": (350, 500), "xp_req": 600},
            {"title": "Team Lead", "level": 4, "salary": (500, 700), "xp_req": 1000},
            {"title": "Engineering Manager", "level": 5, "salary": (700, 900), "xp_req": 1500},
            {"title": "VP of Engineering", "level": 6, "salary": (900, 1200), "xp_req": 2500},
            {"title": "CTO", "level": 7, "salary": (1200, 1500), "xp_req": 4000}
        ]
    },
    "business": {
        "name": "Business",
        "emoji": "💼",
        "jobs": [
            {"title": "Trainee", "level": 0, "salary": (40, 80), "xp_req": 0},
            {"title": "Junior Analyst", "level": 1, "salary": (80, 150), "xp_req": 100},
            {"title": "Business Analyst", "level": 2, "salary": (150, 280), "xp_req": 300},
            {"title": "Senior Analyst", "level": 3, "salary": (280, 400), "xp_req": 600},
            {"title": "Manager", "level": 4, "salary": (400, 600), "xp_req": 1000},
            {"title": "Director", "level": 5, "salary": (600, 800), "xp_req": 1500},
            {"title": "VP of Operations", "level": 6, "salary": (800, 1100), "xp_req": 2500},
            {"title": "CEO", "level": 7, "salary": (1100, 1400), "xp_req": 4000}
        ]
    },
    "creative": {
        "name": "Creative Arts",
        "emoji": "🎨",
        "jobs": [
            {"title": "Apprentice", "level": 0, "salary": (30, 70), "xp_req": 0},
            {"title": "Junior Designer", "level": 1, "salary": (70, 140), "xp_req": 100},
            {"title": "Graphic Designer", "level": 2, "salary": (140, 250), "xp_req": 300},
            {"title": "Senior Designer", "level": 3, "salary": (250, 380), "xp_req": 600},
            {"title": "Art Director", "level": 4, "salary": (380, 550), "xp_req": 1000},
            {"title": "Creative Director", "level": 5, "salary": (550, 750), "xp_req": 1500},
            {"title": "VP of Creative", "level": 6, "salary": (750, 1000), "xp_req": 2500},
            {"title": "Chief Creative Officer", "level": 7, "salary": (1000, 1300), "xp_req": 4000}
        ]
    },
    "healthcare": {
        "name": "Healthcare",
        "emoji": "🏥",
        "jobs": [
            {"title": "Volunteer", "level": 0, "salary": (60, 120), "xp_req": 0},
            {"title": "Medical Assistant", "level": 1, "salary": (120, 220), "xp_req": 100},
            {"title": "Nurse", "level": 2, "salary": (220, 400), "xp_req": 300},
            {"title": "Senior Nurse", "level": 3, "salary": (400, 600), "xp_req": 600},
            {"title": "Nurse Practitioner", "level": 4, "salary": (600, 800), "xp_req": 1000},
            {"title": "Doctor", "level": 5, "salary": (800, 1000), "xp_req": 1500},
            {"title": "Specialist", "level": 6, "salary": (1000, 1300), "xp_req": 2500},
            {"title": "Chief of Medicine", "level": 7, "salary": (1300, 1600), "xp_req": 4000}
        ]
    }
}

JOB_ACTIVITIES = {
    "technology": [
        "fixed a critical bug", "deployed new features", "optimized database queries",
        "conducted code reviews", "mentored junior developers", "architected a new system"
    ],
    "business": [
        "analyzed market trends", "presented to stakeholders", "closed a major deal",
        "optimized business processes", "led team meetings", "developed strategic plans"
    ],
    "creative": [
        "designed marketing materials", "created brand concepts", "led creative sessions",
        "produced visual content", "collaborated with clients", "developed creative strategies"
    ],
    "healthcare": [
        "treated patients", "conducted medical research", "performed surgeries",
        "educated patients", "collaborated with specialists", "saved lives"
    ]
}

class JobApplicationView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Choose your career path...",
        options=[
            discord.SelectOption(
                label=path_data["name"],
                value=path_key,
                emoji=path_data["emoji"],
                description=f"Start as {path_data['jobs'][0]['title']}"
            ) for path_key, path_data in CAREER_PATHS.items()
        ]
    )
    async def career_select(self, interaction: discord.Interaction, select):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your job application!", ephemeral=True)
            return
        
        career_path = select.values[0]
        path_data = CAREER_PATHS[career_path]
        starting_job = path_data["jobs"][0]
        
        # Update user's job information
        database.db.update_user_data(self.user_id, {
            "job.career_path": career_path,
            "job.current_level": 0,
            "job.title": starting_job["title"],
            "job.work_xp": 0,
            "job.hired_date": time.time(),
            "job.performance_rating": 3.0,  # Start with average rating
            "job.total_earnings": 0
        })
        
        embed = discord.Embed(
            title=f"{path_data['emoji']} Career Profile",
            description=f"**{interaction.user.display_name}** - {current_job['title']}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Current Position
        embed.add_field(name="💼 Current Position", value=current_job["title"], inline=True)
        embed.add_field(name="🏢 Department", value=path_data["name"], inline=True)
        embed.add_field(name="📊 Level", value=f"{current_level + 1}/{len(path_data['jobs'])}", inline=True)
        
        # Performance & Stats
        embed.add_field(name="⭐ Performance", value=f"{performance:.1f}/5.0", inline=True)
        embed.add_field(name="🎯 Work XP", value=f"{work_xp:,}", inline=True)
        embed.add_field(name="💰 Total Earned", value=f"{total_earnings:,} coins", inline=True)
        
        # Employment Duration
        days_employed = int((time.time() - hired_date) / 86400)
        embed.add_field(name="📅 Employment", value=f"{days_employed} days", inline=True)
        
        # Salary Range
        embed.add_field(name="💵 Salary Range", value=f"{current_job['salary'][0]:,}-{current_job['salary'][1]:,} coins", inline=True)
        
        # Next Promotion
        if next_job:
            xp_needed = next_job["xp_req"] - work_xp
            if xp_needed <= 0:
                embed.add_field(name="🎉 Promotion Available!", value="Use `/promote` to advance!", inline=True)
            else:
                embed.add_field(name="🔄 Next Promotion", value=f"{next_job['title']}\n*Need {xp_needed:,} more XP*", inline=True)
        else:
            embed.add_field(name="👑 Career Peak", value="You've reached the top!", inline=True)
        
        # Performance indicators
        performance_text = ""
        if performance >= 4.5:
            performance_text = "🌟 Exceptional Employee"
        elif performance >= 4.0:
            performance_text = "⭐ Outstanding Performer"
        elif performance >= 3.5:
            performance_text = "✅ Above Average"
        elif performance >= 2.5:
            performance_text = "📊 Meeting Expectations"
        else:
            performance_text = "⚠️ Needs Improvement"
        
        embed.add_field(name="📈 Status", value=performance_text, inline=True)
        embed.set_footer(text="Keep working to advance your career!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="promote", description="Apply for a promotion if eligible.")
    async def promote(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        job_data = user_data.get("job", {})
        
        if not job_data.get("career_path"):
            await interaction.response.send_message("❌ You need to get a job first! Use `/career` to apply.", ephemeral=True)
            return
        
        career_path = job_data["career_path"]
        current_level = job_data.get("current_level", 0)
        work_xp = job_data.get("work_xp", 0)
        performance = job_data.get("performance_rating", 3.0)
        
        path_data = CAREER_PATHS[career_path]
        
        # Check if at max level
        if current_level >= len(path_data["jobs"]) - 1:
            await interaction.response.send_message("👑 You've already reached the highest position in your career path!", ephemeral=True)
            return
        
        next_job = path_data["jobs"][current_level + 1]
        
        # Check XP requirement
        if work_xp < next_job["xp_req"]:
            needed_xp = next_job["xp_req"] - work_xp
            embed = discord.Embed(
                title="❌ Promotion Not Available",
                description=f"You need {needed_xp:,} more work XP to be eligible for promotion to {next_job['title']}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Check performance requirement (minimum 3.0 for promotion)
        if performance < 3.0:
            embed = discord.Embed(
                title="❌ Promotion Denied",
                description=f"Your performance rating ({performance:.1f}/5.0) is too low for promotion. Improve your performance by working consistently!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Promote the user!
        new_level = current_level + 1
        promotion_bonus = next_job["salary"][1] * 2  # Double max salary as bonus
        
        database.db.update_user_data(interaction.user.id, {
            "job.current_level": new_level,
            "job.title": next_job["title"],
            "job.performance_rating": min(5.0, performance + 0.2)  # Small performance boost
        })
        
        database.db.add_coins(interaction.user.id, promotion_bonus)
        
        embed = discord.Embed(
            title="🎉 PROMOTION!",
            description=f"**{interaction.user.display_name}** has been promoted!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="🆙 New Position", value=next_job["title"], inline=True)
        embed.add_field(name="📊 Level", value=f"{new_level + 1}/{len(path_data['jobs'])}", inline=True)
        embed.add_field(name="💰 Promotion Bonus", value=f"{promotion_bonus:,} coins", inline=True)
        embed.add_field(name="💵 New Salary Range", value=f"{next_job['salary'][0]:,}-{next_job['salary'][1]:,} coins", inline=True)
        embed.add_field(name="⭐ Performance Boost", value=f"{performance:.1f} → {min(5.0, performance + 0.2):.1f}", inline=True)
        embed.set_footer(text="Congratulations on your career advancement!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="work-policy", description="View comprehensive work policy and career information.")
    async def work_policy(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📋 Work Policy & Career Guide",
            description="Everything you need to know about working and career advancement",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="⏰ Work Schedule",
            value="• Work cooldown: **1 hour**\n• Earnings vary by job level\n• XP gained with each work session",
            inline=False
        )
        
        embed.add_field(
            name="📈 Career Progression",
            value="• Start as entry-level employee\n• Gain Work XP through `/work`\n• Promote when XP requirements met\n• Performance affects promotion eligibility",
            inline=False
        )
        
        embed.add_field(
            name="🏢 Available Career Paths",
            value="\n".join([f"{data['emoji']} **{data['name']}** - {len(data['jobs'])} levels" 
                           for data in CAREER_PATHS.values()]),
            inline=False
        )
        
        embed.add_field(
            name="⭐ Performance System",
            value="• Rating: 1.0 - 5.0 stars\n• Affects promotion eligibility\n• Improves with consistent work\n• Minimum 3.0 required for promotion",
            inline=False
        )
        
        embed.add_field(
            name="💰 Benefits",
            value="• Salary increases with promotions\n• Promotion bonuses\n• Performance bonuses\n• Job security",
            inline=False
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="Use /career to start your professional journey!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="job-overview", description="Management overview of server employment statistics.")
    @app_commands.describe(career_path="Filter by specific career path (optional)")
    @app_commands.choices(
        career_path=[
            discord.app_commands.Choice(name="💻 Technology", value="technology"),
            discord.app_commands.Choice(name="💼 Business", value="business"),
            discord.app_commands.Choice(name="🎨 Creative Arts", value="creative"),
            discord.app_commands.Choice(name="🏥 Healthcare", value="healthcare")
        ]
    )
    async def job_overview(self, interaction: discord.Interaction, career_path: str = None):
        # This would need to be implemented with proper database aggregation
        # For now, we'll show a placeholder with the structure
        
        embed = discord.Embed(
            title="📊 Employment Overview",
            description="Server-wide employment statistics",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if career_path:
            path_data = CAREER_PATHS[career_path]
            embed.title = f"📊 {path_data['emoji']} {path_data['name']} Overview"
            
            # Show job level distribution for this career path
            embed.add_field(
                name="📈 Career Levels",
                value="\n".join([f"**{job['title']}** - Level {i+1}" 
                               for i, job in enumerate(path_data['jobs'])]),
                inline=False
            )
        else:
            # Show overall statistics
            embed.add_field(
                name="🏢 Career Paths",
                value=f"Available: **{len(CAREER_PATHS)}** paths\nTotal positions: **{sum(len(path['jobs']) for path in CAREER_PATHS.values())}**",
                inline=True
            )
            
            embed.add_field(
                name="👥 Employment Stats",
                value="*Statistics would show here*\n• Total employed users\n• Average performance rating\n• Most popular career path",
                inline=True
            )
        
        embed.add_field(
            name="💼 Top Performers",
            value="*Leaderboard would show here*\n• Highest level employees\n• Best performance ratings\n• Total career earnings",
            inline=False
        )
        
        embed.set_footer(text="This feature will be enhanced with live database statistics")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resign", description="Resign from your current job.")
    async def resign(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        job_data = user_data.get("job", {})
        
        if not job_data.get("career_path"):
            await interaction.response.send_message("❌ You don't currently have a job to resign from!", ephemeral=True)
            return
        
        career_path = job_data["career_path"]
        current_title = job_data.get("title", "Employee")
        total_earnings = job_data.get("total_earnings", 0)
        days_employed = int((time.time() - job_data.get("hired_date", time.time())) / 86400)
        
        # Confirmation view
        class ResignConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
            
            @discord.ui.button(label="Confirm Resignation", style=discord.ButtonStyle.red, emoji="✅")
            async def confirm_resign(self, button_interaction, button):
                # Clear job data
                database.db.update_user_data(interaction.user.id, {
                    "job": {}
                })
                
                embed = discord.Embed(
                    title="📤 Resignation Accepted",
                    description=f"**{interaction.user.display_name}** has resigned from their position.",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="📋 Former Position", value=current_title, inline=True)
                embed.add_field(name="⏱️ Employment Duration", value=f"{days_employed} days", inline=True)
                embed.add_field(name="💰 Total Career Earnings", value=f"{total_earnings:,} coins", inline=True)
                embed.add_field(name="🔄 Re-employment", value="Use `/career` to apply for a new job anytime!", inline=False)
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                
                await button_interaction.response.edit_message(embed=embed, view=None)
            
            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.gray, emoji="❌")
            async def cancel_resign(self, button_interaction, button):
                await button_interaction.response.edit_message(content="Resignation cancelled.", embed=None, view=None)
        
        path_data = CAREER_PATHS[career_path]
        embed = discord.Embed(
            title="⚠️ Confirm Resignation",
            description=f"Are you sure you want to resign from your position as **{current_title}** in {path_data['emoji']} {path_data['name']}?",
            color=discord.Color.yellow()
        )
        embed.add_field(name="📊 Current Stats", 
                       value=f"• Position: {current_title}\n• Days employed: {days_employed}\n• Total earned: {total_earnings:,} coins", 
                       inline=False)
        embed.add_field(name="⚠️ Warning", 
                       value="Resigning will reset all job progress and you'll need to reapply for employment.", 
                       inline=False)
        
        view = ResignConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    def calculate_work_performance(self, user_data: dict) -> float:
        """Calculate performance rating based on work consistency"""
        job_data = user_data.get("job", {})
        work_streak = user_data.get("work_streak", 0)
        daily_streak = user_data.get("daily_streak", 0)
        current_performance = job_data.get("performance_rating", 3.0)
        
        # Performance factors
        streak_bonus = min(1.0, work_streak * 0.02)  # Max 1.0 bonus from streaks
        consistency_bonus = min(0.5, daily_streak * 0.01)  # Max 0.5 from daily consistency
        
        # Calculate new performance (gradually improve)
        new_performance = min(5.0, current_performance + 0.05 + (streak_bonus * 0.1) + (consistency_bonus * 0.1))
        
        return new_performance

    def get_work_activity(self, career_path: str) -> str:
        """Get random work activity based on career path"""
        activities = JOB_ACTIVITIES.get(career_path, ["completed daily tasks"])
        return random.choice(activities)


async def setup(bot: commands.Bot):
    await bot.add_cog(Jobs(bot))="🎉 Congratulations!",
            description=f"**{interaction.user.display_name}** has been hired!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🏢 Career Path", value=f"{path_data['emoji']} {path_data['name']}", inline=True)
        embed.add_field(name="💼 Position", value=starting_job["title"], inline=True)
        embed.add_field(name="💰 Salary Range", value=f"{starting_job['salary'][0]}-{starting_job['salary'][1]} coins", inline=True)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Use /work to start earning and gaining experience!")
        
        await interaction.response.edit_message(embed=embed, view=None)

class Jobs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="career", description="View your career progression and job information.")
    async def career(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        job_data = user_data.get("job", {})
        
        if not job_data.get("career_path"):
            # User doesn't have a job
            embed = discord.Embed(
                title="💼 Career Center",
                description="You're currently unemployed! Choose a career path to start your professional journey.",
                color=discord.Color.orange()
            )
            
            # Show available career paths
            for path_key, path_data in CAREER_PATHS.items():
                starting_job = path_data["jobs"][0]
                embed.add_field(
                    name=f"{path_data['emoji']} {path_data['name']}",
                    value=f"**Start as:** {starting_job['title']}\n**Salary:** {starting_job['salary'][0]}-{starting_job['salary'][1]} coins",
                    inline=True
                )
            
            view = JobApplicationView(interaction.user.id)
            await interaction.response.send_message(embed=embed, view=view)
            return
        
        # User has a job - show career info
        career_path = job_data["career_path"]
        current_level = job_data.get("current_level", 0)
        work_xp = job_data.get("work_xp", 0)
        performance = job_data.get("performance_rating", 3.0)
        total_earnings = job_data.get("total_earnings", 0)
        hired_date = job_data.get("hired_date", time.time())
        
        path_data = CAREER_PATHS[career_path]
        current_job = path_data["jobs"][current_level]
        next_job = path_data["jobs"][current_level + 1] if current_level + 1 < len(path_data["jobs"]) else None
        
        embed = discord.Embed(
            title
