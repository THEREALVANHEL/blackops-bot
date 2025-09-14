"""
Enhanced UI System for Professional Discord Bot Design
- Ultra-modern embed designs with visual flair
- Animated progress bars and dynamic elements
- Consistent branding and elegant styling
- Professional interactive components
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
import random
import math
import logging

logger = logging.getLogger(__name__)

class ModernColors:
    """Ultra-modern color palette with gradients and themes"""
    
    # Brand Colors (Enhanced)
    BRAND_PRIMARY = 0x5865F2      # Discord Blurple
    BRAND_GRADIENT = 0x7289DA     # Gradient Blurple
    BRAND_ACCENT = 0xFEE75C       # Discord Yellow
    BRAND_DARK = 0x2C2F33         # Dark Theme
    
    # Status Colors (Modern with gradients)
    SUCCESS = 0x00D166            # Vibrant Green
    SUCCESS_DARK = 0x00A85A       # Dark Green
    WARNING = 0xFF6B35            # Modern Orange
    WARNING_DARK = 0xE55A2B       # Dark Orange
    ERROR = 0xFF4757              # Modern Red
    ERROR_DARK = 0xE63946         # Dark Red
    INFO = 0x3742FA               # Electric Blue
    INFO_DARK = 0x2F3CE8          # Dark Blue
    
    # Premium & Special
    PREMIUM = 0xFFD700            # Gold
    PREMIUM_DARK = 0xDAA520       # Dark Gold
    LEGENDARY = 0x9B59B6          # Purple
    MYTHIC = 0xFF6B9D             # Pink
    
    # Economy Colors
    ECONOMY_GREEN = 0x27AE60      # Money Green
    ECONOMY_GOLD = 0xF39C12       # Gold Coins
    ECONOMY_SILVER = 0x95A5A6     # Silver
    
    # Level & XP Colors
    LEVEL_UP = 0xE74C3C           # Bright Red-Orange
    XP_BLUE = 0x3498DB            # Experience Blue
    STREAK_FIRE = 0xE67E22        # Fire Orange
    
    # Social Colors
    SOCIAL_PINK = 0xE91E63        # Social Pink
    SOCIAL_PURPLE = 0x9C27B0      # Social Purple
    
    # Utility Colors
    TRANSPARENT = 0x2C2F33        # For backgrounds
    BORDER = 0x40444B             # Border color

class ElegantEmbed:
    """Enhanced embed builder with modern design patterns"""
    
    @staticmethod
    def create_embed(
        title: str = None,
        description: str = None,
        color: int = ModernColors.BRAND_PRIMARY,
        author_name: str = None,
        author_icon: str = None,
        thumbnail: str = None,
        image: str = None,
        footer_text: str = None,
        footer_icon: str = None,
        timestamp: bool = True,
        url: str = None,
        style: str = "modern"  # modern, elegant, premium, gaming
    ) -> discord.Embed:
        """Create a professional embed with modern styling"""
        
        # Style-based color adjustments
        style_colors = {
            "modern": color,
            "elegant": ModernColors.BRAND_GRADIENT,
            "premium": ModernColors.PREMIUM,
            "gaming": ModernColors.LEGENDARY,
            "success": ModernColors.SUCCESS,
            "error": ModernColors.ERROR,
            "warning": ModernColors.WARNING,
            "info": ModernColors.INFO
        }
        
        embed_color = style_colors.get(style, color)
        embed = discord.Embed(color=embed_color)
        
        # Enhanced title with styling
        if title:
            # Add decorative elements based on style
            decorators = {
                "modern": "✦",
                "elegant": "◆",
                "premium": "♦",
                "gaming": "⚡",
                "success": "✅",
                "error": "❌",
                "warning": "⚠️",
                "info": "ℹ️"
            }
            
            decorator = decorators.get(style, "✦")
            embed.title = f"{decorator} {title} {decorator}"
        
        if description:
            # Add subtle formatting to description
            embed.description = f"```css\n{description}```" if len(description) < 50 else description
            
        if url:
            embed.url = url
            
        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon)
            
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if image:
            embed.set_image(url=image)
            
        if footer_text:
            embed.set_footer(text=f"✨ {footer_text}", icon_url=footer_icon)
        elif timestamp:
            embed.timestamp = datetime.now(timezone.utc)
            embed.set_footer(text="BlackOps Bot • Professional Discord Experience")
            
        return embed
    
    @staticmethod
    def success_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an elegant success embed"""
        return ElegantEmbed.create_embed(
            title=title,
            description=description,
            style="success",
            **kwargs
        )
    
    @staticmethod
    def error_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an elegant error embed"""
        return ElegantEmbed.create_embed(
            title=title,
            description=description,
            style="error",
            **kwargs
        )
    
    @staticmethod
    def info_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an elegant info embed"""
        return ElegantEmbed.create_embed(
            title=title,
            description=description,
            style="info",
            **kwargs
        )
    
    @staticmethod
    def warning_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an elegant warning embed"""
        return ElegantEmbed.create_embed(
            title=title,
            description=description,
            style="warning",
            **kwargs
        )
    
    @staticmethod
    def premium_embed(title: str, description: str = None, **kwargs) -> discord.Embed:
        """Create an elegant premium embed"""
        return ElegantEmbed.create_embed(
            title=title,
            description=description,
            style="premium",
            **kwargs
        )

class AnimatedProgressBar:
    """Create animated and visually appealing progress bars"""
    
    @staticmethod
    def create_bar(
        percentage: float, 
        length: int = 20, 
        style: str = "modern",
        show_percentage: bool = True,
        custom_chars: Dict[str, str] = None
    ) -> str:
        """Create a visual progress bar with different styles"""
        
        styles = {
            "modern": {"filled": "█", "empty": "░", "border": "▌▐"},
            "elegant": {"filled": "■", "empty": "□", "border": "┃┃"},
            "gaming": {"filled": "◆", "empty": "◇", "border": "║║"},
            "premium": {"filled": "♦", "empty": "♢", "border": "⟨⟩"},
            "fire": {"filled": "🔥", "empty": "💨", "border": "🌟🌟"},
            "water": {"filled": "💧", "empty": "💨", "border": "🌊🌊"},
            "lightning": {"filled": "⚡", "empty": "☁️", "border": "⚡⚡"},
        }
        
        chars = custom_chars or styles.get(style, styles["modern"])
        filled = int(percentage / 100 * length)
        empty = length - filled
        
        # Create the bar
        bar_filled = chars["filled"] * filled
        bar_empty = chars["empty"] * empty
        
        # Add borders if available
        if "border" in chars and len(chars["border"]) >= 2:
            left_border = chars["border"][0]
            right_border = chars["border"][1]
            bar = f"{left_border}{bar_filled}{bar_empty}{right_border}"
        else:
            bar = f"{bar_filled}{bar_empty}"
        
        if show_percentage:
            return f"`{bar}` **{percentage:.1f}%**"
        else:
            return f"`{bar}`"
    
    @staticmethod
    def health_bar(current: int, maximum: int, style: str = "gaming") -> str:
        """Create a health/HP progress bar"""
        percentage = (current / maximum * 100) if maximum > 0 else 0
        
        # Color coding based on health
        if percentage > 75:
            style = "modern"  # Green-ish
        elif percentage > 50:
            style = "premium"  # Yellow-ish
        elif percentage > 25:
            style = "gaming"   # Orange-ish
        else:
            style = "fire"     # Red-ish
        
        bar = AnimatedProgressBar.create_bar(percentage, 15, style, False)
        return f"{bar} **{current:,}/{maximum:,}** HP"
    
    @staticmethod
    def xp_bar(current_xp: int, needed_xp: int, level: int) -> str:
        """Create an XP progress bar for leveling"""
        percentage = (current_xp / needed_xp * 100) if needed_xp > 0 else 0
        bar = AnimatedProgressBar.create_bar(percentage, 18, "lightning", False)
        return f"**Level {level}** {bar} `{current_xp:,}/{needed_xp:,} XP`"

class ModernPagination(discord.ui.View):
    """Ultra-modern pagination with smooth animations"""
    
    def __init__(self, embeds: List[discord.Embed], timeout: float = 300.0, user_id: int = None, style: str = "modern"):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.user_id = user_id
        self.max_pages = len(embeds)
        self.style = style
        
        # Enhance embeds with page info
        self._enhance_embeds()
        self._update_buttons()
    
    def _enhance_embeds(self):
        """Add elegant page information to embeds"""
        for i, embed in enumerate(self.embeds):
            # Add page footer
            current_footer = embed.footer.text if embed.footer else ""
            page_info = f"Page {i + 1} of {self.max_pages}"
            
            if current_footer:
                new_footer = f"{current_footer} • {page_info}"
            else:
                new_footer = f"✨ {page_info} ✨"
            
            embed.set_footer(text=new_footer, icon_url=embed.footer.icon_url if embed.footer else None)
    
    def _update_buttons(self):
        """Update button states with modern styling"""
        # Disable/enable buttons based on current page
        self.first_page.disabled = (self.current_page == 0)
        self.prev_page.disabled = (self.current_page == 0)
        self.next_page.disabled = (self.current_page >= self.max_pages - 1)
        self.last_page.disabled = (self.current_page >= self.max_pages - 1)
        
        # Update page counter
        self.page_counter.label = f"📄 {self.current_page + 1}/{self.max_pages}"
        
        # Update button styles based on state
        if self.current_page == 0:
            self.prev_page.style = discord.ButtonStyle.secondary
        else:
            self.prev_page.style = discord.ButtonStyle.primary
            
        if self.current_page >= self.max_pages - 1:
            self.next_page.style = discord.ButtonStyle.secondary
        else:
            self.next_page.style = discord.ButtonStyle.primary
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Check if user can interact with buttons"""
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=ElegantEmbed.error_embed(
                    "Access Denied",
                    "You cannot interact with this menu."
                ),
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.secondary, row=0)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to first page"""
        self.current_page = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.primary, row=0)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page"""
        self.current_page = max(0, self.current_page - 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(label="📄 1/1", style=discord.ButtonStyle.secondary, disabled=True, row=0)
    async def page_counter(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Page counter (disabled button for display)"""
        pass
    
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.primary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page"""
        self.current_page = min(self.max_pages - 1, self.current_page + 1)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.secondary, row=0)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to last page"""
        self.current_page = self.max_pages - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="🔄", style=discord.ButtonStyle.success, row=1)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Refresh current page"""
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)
    
    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.danger, row=1)
    async def close_menu(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close the pagination menu"""
        embed = ElegantEmbed.info_embed(
            "Menu Closed",
            "This pagination menu has been closed."
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class ModernConfirmation(discord.ui.View):
    """Elegant confirmation dialog with modern styling"""
    
    def __init__(self, user_id: int = None, timeout: float = 60.0, style: str = "modern"):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.result = None
        self.style = style
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.user_id and interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=ElegantEmbed.error_embed(
                    "Access Denied",
                    "You cannot interact with this confirmation."
                ),
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.success, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = True
        embed = ElegantEmbed.success_embed(
            "Confirmed",
            "Action has been confirmed and will be processed."
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.danger, emoji="❌")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.result = False
        embed = ElegantEmbed.warning_embed(
            "Cancelled",
            "Action has been cancelled and no changes were made."
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class EconomyDisplay:
    """Modern economy displays with animations and styling"""
    
    @staticmethod
    def create_balance_embed(user: discord.Member, user_data: dict, style: str = "premium") -> discord.Embed:
        """Create an elegant balance display"""
        coins = user_data.get("coins", 0)
        bank = user_data.get("bank", 0)
        cookies = user_data.get("cookies", 0)
        level = user_data.get("level", 1)
        xp = user_data.get("xp", 0)
        daily_streak = user_data.get("daily_streak", 0)
        
        embed = ElegantEmbed.create_embed(
            title=f"{user.display_name}'s Financial Portfolio",
            color=ModernColors.ECONOMY_GOLD,
            style="premium",
            thumbnail=user.display_avatar.url
        )
        
        # Main balance section with visual separators
        balance_text = f"""
        ```yaml
        💰 Wallet: {coins:,} coins
        🏦 Bank: {bank:,} coins
        🍪 Cookies: {cookies:,}
        💎 Net Worth: {coins + bank:,} coins
        ```
        """
        embed.add_field(name="💼 Financial Overview", value=balance_text, inline=False)
        
        # XP Progress with animated bar
        try:
            import database
            thresholds = database.db.get_level_thresholds(level)
            current_level_xp = thresholds["current_min_xp"]
            next_level_xp = thresholds["next_min_xp"]
        except Exception:
            current_level_xp = (level ** 2) * 100
            next_level_xp = ((level + 1) ** 2) * 100
        xp_progress = max(0, xp - current_level_xp)
        xp_needed = max(1, next_level_xp - current_level_xp)
        
        xp_bar = AnimatedProgressBar.xp_bar(xp_progress, xp_needed, level)
        embed.add_field(name="⭐ Experience Progress", value=xp_bar, inline=False)
        
        # Daily streak with fire animation
        if daily_streak > 0:
            streak_display = "🔥 " * min(daily_streak, 10)  # Max 10 fire emojis
            if daily_streak > 10:
                streak_display += f" +{daily_streak - 10}"
            embed.add_field(name="🔥 Daily Streak", value=f"{streak_display}\n**{daily_streak} days strong!**", inline=True)
        
        # Add some flair
        embed.set_footer(
            text=f"✨ Premium Account • Last updated",
            icon_url="https://cdn.discordapp.com/emojis/852881450667081728.gif"  # Animated diamond
        )
        
        return embed
    
    @staticmethod
    def create_shop_embed(items: dict, style: str = "gaming") -> discord.Embed:
        """Create an elegant shop display"""
        embed = ElegantEmbed.create_embed(
            title="Premium Items Marketplace",
            description="✨ **Enhance your experience with premium items!** ✨",
            color=ModernColors.PREMIUM,
            style="premium"
        )
        
        for item_id, details in items.items():
            # Tier styling
            tier_styles = {
                "common": "🟢",
                "uncommon": "🟡", 
                "rare": "🟠",
                "legendary": "🟣",
                "mythic": "✨"
            }
            
            tier_emoji = tier_styles.get(details.get("tier", "common"), "⚪")
            duration_hours = int(details["duration"] / 3600)
            
            item_display = f"""
            {details['emoji']} **{item_id.title().replace('_', ' ')}** {tier_emoji}
            
            💰 **Price:** `{details['price']:,}` coins
            ⏰ **Duration:** `{duration_hours}h`
            📝 *{details['description']}*
            """
            
            embed.add_field(
                name=f"{tier_emoji} {item_id.title().replace('_', ' ')}", 
                value=item_display, 
                inline=True
            )
        
        embed.set_footer(text="💡 Use /buy <item> to purchase • Prices subject to change")
        return embed

class LevelUpAnimation:
    """Create animated level up displays"""
    
    @staticmethod
    def create_levelup_embed(user: discord.Member, old_level: int, new_level: int, rewards: dict = None) -> discord.Embed:
        """Create an epic level up animation embed"""
        
        # Level up gets more epic as levels increase
        if new_level >= 100:
            color = ModernColors.MYTHIC
            title_prefix = "🌟 LEGENDARY LEVEL UP! 🌟"
        elif new_level >= 50:
            color = ModernColors.LEGENDARY
            title_prefix = "💎 EPIC LEVEL UP! 💎"
        elif new_level >= 25:
            color = ModernColors.PREMIUM
            title_prefix = "⚡ AMAZING LEVEL UP! ⚡"
        else:
            color = ModernColors.LEVEL_UP
            title_prefix = "🎉 LEVEL UP! 🎉"
        
        embed = discord.Embed(
            title=title_prefix,
            description=f"**{user.display_name}** reached level **{new_level}**!",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Level progress display
        level_display = f"""
        ```diff
        - Level {old_level}
        + Level {new_level}
        ```
        """
        embed.add_field(name="📊 Level Progress", value=level_display, inline=True)
        
        # Rewards section
        if rewards:
            reward_text = []
            if rewards.get("coins"):
                reward_text.append(f"💰 {rewards['coins']:,} coins")
            if rewards.get("xp"):
                reward_text.append(f"⭐ {rewards['xp']:,} bonus XP")
            if rewards.get("items"):
                reward_text.append(f"🎁 {len(rewards['items'])} special items")
            
            if reward_text:
                embed.add_field(name="🎁 Level Rewards", value="\n".join(reward_text), inline=True)
        
        # Milestone achievements
        if new_level % 10 == 0:
            embed.add_field(
                name="🏆 Milestone Achievement!",
                value=f"You've reached level {new_level}! That's a major milestone! 🎊",
                inline=False
            )
        
        embed.set_footer(
            text="🚀 Keep gaining XP to reach even higher levels!",
            icon_url="https://cdn.discordapp.com/emojis/852881450667081728.gif"
        )
        
        return embed

def format_large_number(num: int) -> str:
    """Format large numbers with suffixes and emojis"""
    if num >= 1_000_000_000_000:
        return f"💎 {num/1_000_000_000_000:.1f}T"
    elif num >= 1_000_000_000:
        return f"💰 {num/1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"💸 {num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"💵 {num/1_000:.1f}K"
    else:
        return f"🪙 {num:,}"

def format_time_elegant(seconds: int) -> str:
    """Format time remaining in an elegant way"""
    if seconds <= 0:
        return "✅ **Ready Now!**"
    
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    
    if days > 0:
        return f"⏰ **{days}d {hours}h {minutes}m**"
    elif hours > 0:
        return f"⏰ **{hours}h {minutes}m**"
    else:
        return f"⏰ **{minutes}m {seconds%60}s**"

def get_status_emoji(percentage: float) -> str:
    """Get status emoji based on percentage"""
    if percentage >= 90:
        return "🟢"  # Excellent
    elif percentage >= 75:
        return "🟡"  # Good
    elif percentage >= 50:
        return "🟠"  # Average
    elif percentage >= 25:
        return "🔴"  # Poor
    else:
        return "⚫"  # Critical

# Modern command wrapper for easy integration
def create_modern_embed(embed_type: str = "info", **kwargs) -> discord.Embed:
    """Quick embed creator for modern styling"""
    creators = {
        "info": ElegantEmbed.info_embed,
        "success": ElegantEmbed.success_embed,
        "error": ElegantEmbed.error_embed,
        "warning": ElegantEmbed.warning_embed,
        "premium": ElegantEmbed.premium_embed,
    }
    
    creator = creators.get(embed_type, ElegantEmbed.info_embed)
    return creator(**kwargs)

# Export all the enhanced components
__all__ = [
    'ModernColors', 'ElegantEmbed', 'AnimatedProgressBar', 'ModernPagination',
    'ModernConfirmation', 'EconomyDisplay', 'LevelUpAnimation',
    'format_large_number', 'format_time_elegant', 'get_status_emoji', 'create_modern_embed'
]

# Demo command for testing the new UI
class UIDemo(commands.Cog):
    """Demo cog to showcase the new UI components"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ui-demo", description="Showcase the new elegant UI system")
    async def ui_demo(self, interaction: discord.Interaction):
        """Demonstrate the enhanced UI components"""
        
        # Create multiple demo embeds
        embeds = []
        
        # Demo 1: Modern embed
        embed1 = ElegantEmbed.create_embed(
            title="Modern UI System",
            description="This is a demonstration of our new elegant UI system with modern styling and visual flair!",
            style="modern",
            thumbnail=interaction.user.display_avatar.url
        )
        embed1.add_field(name="✨ Features", value="• Elegant embeds\n• Animated progress bars\n• Modern pagination\n• Beautiful colors", inline=True)
        embed1.add_field(name="🎨 Styling", value="• Consistent branding\n• Visual separators\n• Emoji integration\n• Professional layout", inline=True)
        embeds.append(embed1)
        
        # Demo 2: Progress bars
        embed2 = ElegantEmbed.create_embed(
            title="Animated Progress Bars",
            description="Check out these beautiful progress bars with different styles!",
            style="gaming"
        )
        
        embed2.add_field(
            name="🎮 Gaming Style", 
            value=AnimatedProgressBar.create_bar(75, 15, "gaming"), 
            inline=False
        )
        embed2.add_field(
            name="✨ Premium Style", 
            value=AnimatedProgressBar.create_bar(60, 15, "premium"), 
            inline=False
        )
        embed2.add_field(
            name="🔥 Fire Style", 
            value=AnimatedProgressBar.create_bar(90, 15, "fire"), 
            inline=False
        )
        embeds.append(embed2)
        
        # Demo 3: Economy display
        embed3 = EconomyDisplay.create_balance_embed(
            interaction.user, 
            {
                "coins": 125000,
                "bank": 250000, 
                "cookies": 1500,
                "level": 42,
                "xp": 180500,
                "daily_streak": 15
            }
        )
        embeds.append(embed3)
        
        # Create pagination view
        view = ModernPagination(embeds, user_id=interaction.user.id, style="modern")
        
        await interaction.response.send_message(
            embed=embeds[0],
            view=view
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(UIDemo(bot))
