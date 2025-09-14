import discord
from discord.ext import commands
from discord import app_commands
import traceback
import sys
import logging
from datetime import datetime
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

class ErrorHandler(commands.Cog):
    """Enhanced error handling system for the bot"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_log_channel_id = None  # Set this in your config
        
        # Error statistics
        self.error_stats = {
            "total_errors": 0,
            "command_errors": 0,
            "app_command_errors": 0,
            "listener_errors": 0,
            "last_error_time": None
        }
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle traditional command errors"""
        self.error_stats["command_errors"] += 1
        self.error_stats["total_errors"] += 1
        self.error_stats["last_error_time"] = datetime.utcnow()
        
        # Ignore certain errors
        ignored_errors = (commands.CommandNotFound, commands.DisabledCommand)
        if isinstance(error, ignored_errors):
            return
        
        # Handle specific errors with user-friendly messages
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join(error.missing_permissions),
                inline=False
            )
            await ctx.send(embed=embed, delete_after=10)
            
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have the required permissions to execute this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join(error.missing_permissions),
                inline=False
            )
            await ctx.send(embed=embed, delete_after=10)
            
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.2f} seconds before using this command again.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=5)
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Required Argument",
                description=f"Missing required argument: `{error.param.name}`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Command Usage",
                value=f"`{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}`",
                inline=False
            )
            await ctx.send(embed=embed, delete_after=15)
            
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description=str(error),
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            
        elif isinstance(error, commands.CheckFailure):
            embed = discord.Embed(
                title="❌ Command Check Failed",
                description="You don't meet the requirements to use this command.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, delete_after=10)
            
        else:
            # Unexpected error - log it and send generic message
            await self.handle_unexpected_error(error, ctx=ctx)
    
    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle slash command errors"""
        self.error_stats["app_command_errors"] += 1
        self.error_stats["total_errors"] += 1
        self.error_stats["last_error_time"] = datetime.utcnow()
        
        # Handle specific errors
        if isinstance(error, app_commands.MissingPermissions):
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join(error.missing_permissions),
                inline=False
            )
            
        elif isinstance(error, app_commands.BotMissingPermissions):
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description="I don't have the required permissions to execute this command.",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Required Permissions",
                value=", ".join(error.missing_permissions),
                inline=False
            )
            
        elif isinstance(error, app_commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏰ Command on Cooldown",
                description=f"Please wait {error.retry_after:.2f} seconds before using this command again.",
                color=discord.Color.orange()
            )
            
        elif isinstance(error, app_commands.CheckFailure):
            embed = discord.Embed(
                title="❌ Command Check Failed",
                description="You don't meet the requirements to use this command.",
                color=discord.Color.red()
            )
            
        else:
            # Unexpected error
            embed = discord.Embed(
                title="❌ Unexpected Error",
                description="An unexpected error occurred. The bot developers have been notified.",
                color=discord.Color.red()
            )
            await self.handle_unexpected_error(error, interaction=interaction)
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.NotFound:
            # Interaction expired, try to send to channel if possible
            if hasattr(interaction, 'channel') and interaction.channel:
                try:
                    await interaction.channel.send(embed=embed, delete_after=10)
                except Exception:
                    pass  # Give up if we can't send anywhere
    
    async def handle_unexpected_error(self, error, ctx=None, interaction=None):
        """Handle unexpected errors with logging and notification"""
        try:
            # Log the full error
            error_msg = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            logger.error(f"Unexpected error: {error_msg}")
            
            # Create error embed for logging
            embed = discord.Embed(
                title="🚨 Unexpected Error Occurred",
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            
            # Add context information
            if ctx:
                embed.add_field(name="Command", value=f"`{ctx.command}`", inline=True)
                embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=True)
                embed.add_field(name="Channel", value=f"{ctx.channel} ({ctx.channel.id})", inline=True)
                embed.add_field(name="Guild", value=f"{ctx.guild} ({ctx.guild.id})" if ctx.guild else "DM", inline=True)
            elif interaction:
                embed.add_field(name="Command", value=f"`{interaction.command}`", inline=True)
                embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=True)
                embed.add_field(name="Channel", value=f"{interaction.channel} ({interaction.channel.id})", inline=True)
                embed.add_field(name="Guild", value=f"{interaction.guild} ({interaction.guild.id})" if interaction.guild else "DM", inline=True)
            
            # Add error details (truncated)
            error_details = str(error)[:1000] + "..." if len(str(error)) > 1000 else str(error)
            embed.add_field(name="Error", value=f"```python\n{error_details}```", inline=False)
            
            # Send to error log channel if configured
            if self.error_log_channel_id:
                try:
                    error_channel = self.bot.get_channel(self.error_log_channel_id)
                    if error_channel:
                        await error_channel.send(embed=embed)
                except Exception as log_error:
                    logger.error(f"Failed to send error to log channel: {log_error}")
            
            # Send generic error message to user
            user_embed = discord.Embed(
                title="❌ Something went wrong",
                description="An unexpected error occurred. The bot developers have been notified and will investigate.",
                color=discord.Color.red()
            )
            user_embed.add_field(
                name="What you can do:",
                value="• Try the command again in a few minutes\n• Check if you have the required permissions\n• Contact a server administrator if the problem persists",
                inline=False
            )
            
            if ctx:
                try:
                    await ctx.send(embed=user_embed, delete_after=30)
                except Exception:
                    pass
            elif interaction and not interaction.response.is_done():
                try:
                    await interaction.response.send_message(embed=user_embed, ephemeral=True)
                except Exception:
                    pass
                    
        except Exception as handler_error:
            # If even the error handler fails, just log it
            logger.critical(f"Error handler itself failed: {handler_error}")
    
    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle errors in event listeners"""
        self.error_stats["listener_errors"] += 1
        self.error_stats["total_errors"] += 1
        self.error_stats["last_error_time"] = datetime.utcnow()
        
        error_info = sys.exc_info()
        if error_info[0] is not None:
            error_msg = ''.join(traceback.format_exception(*error_info))
            logger.error(f"Error in event {event}: {error_msg}")
            
            # Send to error log channel
            if self.error_log_channel_id:
                try:
                    error_channel = self.bot.get_channel(self.error_log_channel_id)
                    if error_channel:
                        embed = discord.Embed(
                            title=f"🚨 Event Error: {event}",
                            description=f"```python\n{error_msg[:1500]}```",
                            color=discord.Color.dark_red(),
                            timestamp=datetime.utcnow()
                        )
                        await error_channel.send(embed=embed)
                except Exception as log_error:
                    logger.error(f"Failed to send event error to log channel: {log_error}")
    
    @app_commands.command(name="errorstats", description="View bot error statistics.")
    @app_commands.describe(clear="Clear the error statistics (admin only)")
    async def error_stats(self, interaction: discord.Interaction, clear: bool = False):
        """Display error statistics"""
        try:
            if clear and interaction.user.guild_permissions.administrator:
                self.error_stats = {
                    "total_errors": 0,
                    "command_errors": 0,
                    "app_command_errors": 0,
                    "listener_errors": 0,
                    "last_error_time": None
                }
                
                embed = discord.Embed(
                    title="✅ Error Statistics Cleared",
                    description="All error statistics have been reset.",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📊 Bot Error Statistics",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="Total Errors", value=f"`{self.error_stats['total_errors']}`", inline=True)
            embed.add_field(name="Command Errors", value=f"`{self.error_stats['command_errors']}`", inline=True)
            embed.add_field(name="Slash Command Errors", value=f"`{self.error_stats['app_command_errors']}`", inline=True)
            embed.add_field(name="Event Listener Errors", value=f"`{self.error_stats['listener_errors']}`", inline=True)
            
            if self.error_stats["last_error_time"]:
                embed.add_field(
                    name="Last Error",
                    value=f"<t:{int(self.error_stats['last_error_time'].timestamp())}:R>",
                    inline=True
                )
            else:
                embed.add_field(name="Last Error", value="`No errors recorded`", inline=True)
            
            # Bot uptime
            if hasattr(self.bot, 'start_time'):
                uptime = datetime.utcnow() - self.bot.start_time
                embed.add_field(name="Bot Uptime", value=f"`{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m`", inline=True)
            
            embed.set_footer(text="Error statistics are reset when the bot restarts")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in errorstats command: {e}")
            await interaction.response.send_message("❌ Error retrieving statistics.", ephemeral=True)
    
    @app_commands.command(name="testerror", description="Test the error handling system (admin only).")
    async def test_error(self, interaction: discord.Interaction):
        """Test the error handling system"""
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ This command is for administrators only.", ephemeral=True)
            return
        
        await interaction.response.send_message("🧪 Testing error handler...", ephemeral=True)
        
        # Deliberately cause an error
        await asyncio.sleep(1)
        raise Exception("This is a test error for the error handling system")


async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))
