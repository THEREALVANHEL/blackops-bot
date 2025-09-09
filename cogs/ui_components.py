"""
Enhanced UI System for Professional Discord Bot Design
- Modern embed designs like MEE6
- Button-based pagination
- Professional styling
- Consistent color schemes
- Interactive components
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class BotColors:
    """Professional color scheme for consistent bot design"""
    PRIMARY = 0x5865F2      # Discord Blurple
    SUCCESS = 0x57F287      # Green
    WARNING = 0xFEE75C      # Yellow
    ERROR = 0xED4245        # Red
    INFO = 0x5DADE2         # Light Blue
    SECONDARY = 0x99AAB5    # Gray
    PREMIUM = 0xF1C40F      # Gold
    LEVEL_UP = 0xE74C3C     # Bright Red
    ECONOMY = 0x2ECC71      # Emerald Green
    MODERATION = 0xE67E22   # Orange

class EmbedBuilder:
    """Enhanced embed builder with modern design patterns"""
    
    @staticmethod
    def create_embed(
        title: str = None,
        description: str = None,
        color: int = BotColors.PRIMARY,
        author_name: str = None,
        author_icon: str = None,
        thumbnail: str = None,
        image: str = None,
        footer_text: str = None,
        footer_icon: str = None,
        timestamp: bool = True,
        url: str = None
    ) -> discord.Embed:
        """Create a professional embed with consistent styling"""
        
        embed = discord.Embed(color=color)
        
        if title:
            embed.title = title
        if description:
            embed.description = description
        if url:
            embed.url = url
            
        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)
            
        if footer_text:
            embed.set_footer(text=footer_text, icon_url=footer_icon)
        elif timestamp:
            embed.timestamp = datetime.now(timezone.utc)
            
        return embed
    
    @staticmethod
    def success_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a success embed"""
        return EmbedBuilder.create_embed(
            title=f"✅ {title}",
            description=description,
            color=BotColors.SUCCESS,
            **kwargs
        )
    
    @staticmethod
    def error_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an error embed"""
        return EmbedBuilder.create_embed(
            title=f"❌ {title}",
            description=description,
            color=BotColors.ERROR,
            **kwargs
        )
    
    @staticmethod
    def info_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an info embed"""
        return EmbedBuilder.create_embed(
            title=f"ℹ️ {title}",
            description=description,
            color=BotColors.INFO,
            **kwargs
        )
    
    @staticmethod
    def warning_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a warning embed"""
        return EmbedBuilder.create_embed(
            title=f"⚠️ {title}",
            description=description,
            color=BotColors.WARNING,
            **kwargs
        )
    
    @staticmethod
    def premium_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create a premium/special embed"""
        return EmbedBuilder.create_embed(
            title=f"✨ {title}",
            description=description,
            color=BotColors.PREMIUM,
            **kwargs
        )

class PaginationView(discord.ui.View):
    """Enhanced pagination view with modern design"""
    
    def __init__(self, embeds: List[discord.Embed], timeout: float = 300.0, user_id: int = None):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.max_pages = len(embeds)
        
        # Update buttons based on current page
        self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page"""
        self.first_page.disabled = (self.current_page == 0)
        self.prev_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page >= self.max_pages - 1)
        self.last_page.disabled = (self.current_page >= self.max_pages - 1)
        
        # Update page counter button
        self.page_counter.label = f"{self.current_page + 1}/{self.max_pages}"
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user can interact with buttons"""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ You cannot interact with this menu.", 
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first page"""
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="1/1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Page counter (disabled button for display)"""
        pass
    
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last page"""
        self.current_page = self.max_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Delete the message"""
        await interaction.response.defer()
        await interaction.delete_original_response()

class ConfirmationView(discord.ui.View):
    """Professional confirmation dialog"""
    
    def __init__(self, user_id: int = None, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.result = None
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ You cannot interact with this confirmation.", 
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = False
        self.stop()
        await interaction.response.defer()

class FileUploadView(discord.ui.View):
    """File upload handler for images"""
    
    def __init__(self, user_id: int, callback_func):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.callback_func = callback_func
        self.uploaded_file = None
    
    @discord.ui.button(label="📁 Upload Image", style=discord.ButtonStyle.primary, emoji="📁")
    async def upload_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can upload files.", ephemeral=True)
            return
        
        # Create modal for file upload instructions
        class FileUploadModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Upload Image File")
            
            instructions = discord.ui.TextInput(
                label="Upload Instructions",
                default="Please attach an image file to your next message in this channel.",
                style=discord.TextStyle.paragraph,
                required=False
            )
            
            async def on_submit(self, modal_interaction):
                await modal_interaction.response.send_message(
                    "📁 **File Upload Ready**\n"
                    "Please send an image file in your next message in this channel.\n"
                    "Supported formats: PNG, JPG, GIF, WEBP\n"
                    "Maximum size: 8MB",
                    ephemeral=True
                )
        
        await interaction.response.send_modal(FileUploadModal())

def create_progress_bar(percentage: float, length: int = 20, filled_char: str = "█", empty_char: str = "░") -> str:
    """Create a visual progress bar"""
    filled = int(percentage / 100 * length)
    empty = length - filled
    
    bar = filled_char * filled + empty_char * empty
    return f"`{bar}` {percentage:.1f}%"

def format_currency(amount: int) -> str:
    """Format currency with appropriate suffixes"""
    if amount >= 1_000_000_000:
        return f"{amount/1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"{amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"{amount/1_000:.1f}K"
    else:
        return f"{amount:,}"

def format_time_remaining(seconds: int) -> str:
    """Format time remaining in human readable format"""
    if seconds <= 0:
        return "Ready now!"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

class LeaderboardView(discord.ui.View):
    """Enhanced leaderboard with pagination and filters"""
    
    def __init__(self, bot, guild_id: int, leaderboard_type: str, user_id: int = None):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.leaderboard_type = leaderboard_type
        self.user_id = user_id
        self.current_page = 1
        self.items_per_page = 10
        
    async def create_leaderboard_embed(self, page: int = 1):
        """Create leaderboard embed with current data"""
        import database
        
        if self.leaderboard_type == "daily_streak":
            leaderboard_data = database.db.get_streak_leaderboard(page, self.items_per_page)
        else:
            leaderboard_data = database.db.get_paginated_leaderboard(self.leaderboard_type, page, self.items_per_page)
        
        # Type mapping for titles and emojis
        type_info = {
            "xp": {"title": "⭐ XP Leaderboard", "emoji": "⭐"},
            "coins": {"title": "💰 Coins Leaderboard", "emoji": "💰"},
            "cookies": {"title": "🍪 Cookies Leaderboard", "emoji": "🍪"},
            "daily_streak": {"title": "🔥 Daily Streak Leaderboard", "emoji": "🔥"},
            "work_count": {"title": "💼 Work Sessions Leaderboard", "emoji": "💼"}
        }
        
        info = type_info.get(self.leaderboard_type, {"title": "📊 Leaderboard", "emoji": "📊"})
        
        embed = EmbedBuilder.create_embed(
            title=f"{info['title']} - Page {leaderboard_data['current_page']}/{leaderboard_data['total_pages']}",
            color=BotColors.PREMIUM
        )
        
        if not leaderboard_data['users']:
            embed.description = "No users found for this leaderboard."
            return embed
        
        # Create leaderboard text
        leaderboard_text = ""
        for i, entry in enumerate(leaderboard_data['users']):
            user_id = entry.get("user_id")
            user = self.bot.get_user(user_id)
            user_name = user.display_name if user else f"User {user_id}"
            
            rank = (leaderboard_data['current_page'] - 1) * self.items_per_page + i + 1
            value = entry.get(self.leaderboard_type, 0)
            
            # Special formatting based on type
            if self.leaderboard_type == "xp":
                level = entry.get("level", 1)
                leaderboard_text += f"`#{rank:2d}` **{user_name}** - Level {level} ({value:,} XP)\n"
            else:
                leaderboard_text += f"`#{rank:2d}` **{user_name}** - {info['emoji']} {value:,}\n"
        
        embed.description = leaderboard_text
        
        # Add user's position if they have data
        if self.user_id:
            import database
            user_data = database.db.get_user_data(self.user_id)
            user_value = user_data.get(self.leaderboard_type, 0)
            if user_value > 0:
                embed.add_field(
                    name="🎯 Your Stats",
                    value=f"**Score:** {info['emoji']} {user_value:,}",
                    inline=True
                )
        
        embed.add_field(
            name="📊 Stats",
            value=f"Page {leaderboard_data['current_page']} of {leaderboard_data['total_pages']}\n{leaderboard_data['total_users']:,} total users",
            inline=True
        )
        
        embed.set_footer(text="Updated in real-time • Use buttons to navigate")
        return embed
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1
        embed = await self.create_leaderboard_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(1, self.current_page - 1)
        embed = await self.create_leaderboard_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get max pages from current data
        import database
        if self.leaderboard_type == "daily_streak":
            data = database.db.get_streak_leaderboard(1, self.items_per_page)
        else:
            data = database.db.get_paginated_leaderboard(self.leaderboard_type, 1, self.items_per_page)
        
        max_pages = data['total_pages']
        self.current_page = min(max_pages, self.current_page + 1)
        embed = await self.create_leaderboard_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Get max pages from current data
        import database
        if self.leaderboard_type == "daily_streak":
            data = database.db.get_streak_leaderboard(1, self.items_per_page)
        else:
            data = database.db.get_paginated_leaderboard(self.leaderboard_type, 1, self.items_per_page)
        
        max_pages = data['total_pages']
        self.current_page = max_pages
        embed = await self.create_leaderboard_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.success, row=1)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self.create_leaderboard_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

class AnnouncementView(discord.ui.View):
    """Professional announcement builder"""
    
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.announcement_data = {
            "title": "",
            "description": "",
            "color": BotColors.INFO,
            "image": None,
            "fields": []
        }
    
    @discord.ui.button(label="📝 Edit Content", style=discord.ButtonStyle.primary)
    async def edit_content(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the announcement creator can edit this.", ephemeral=True)
            return
        
        class ContentModal(discord.ui.Modal):
            def __init__(self, current_data):
                super().__init__(title="Edit Announcement Content")
                self.current_data = current_data
            
            title = discord.ui.TextInput(
                label="Announcement Title",
                placeholder="Enter the announcement title...",
                required=True,
                max_length=256
            )
            
            description = discord.ui.TextInput(
                label="Main Content",
                placeholder="Enter the main announcement content...",
                style=discord.TextStyle.paragraph,
                required=True,
                max_length=2000
            )
            
            async def on_submit(self, modal_interaction):
                # Update announcement data
                interaction.client.get_cog("UITest").announcement_data["title"] = self.title.value
                interaction.client.get_cog("UITest").announcement_data["description"] = self.description.value
                
                embed = EmbedBuilder.info_embed(
                    title=self.title.value,
                    description=self.description.value
                )
                embed.set_footer(text="Use buttons below to customize further")
                
                await modal_interaction.response.edit_message(embed=embed)
        
        modal = ContentModal(self.announcement_data)
        modal.title.default = self.announcement_data.get("title", "")
        modal.description.default = self.announcement_data.get("description", "")
        
        await interaction.response.send_modal(modal)

# Export commonly used components
__all__ = [
    'BotColors', 'EmbedBuilder', 'PaginationView', 'ConfirmationView',
    'FileUploadView', 'LeaderboardView', 'AnnouncementView',
    'create_progress_bar', 'format_currency', 'format_time_remaining'
]
