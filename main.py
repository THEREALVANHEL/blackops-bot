import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database
import permissions
from flask import Flask, jsonify, request
from threading import Thread
import asyncio
import logging
from datetime import datetime
import signal
import sys

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate required environment variables
required_vars = ['DISCORD_BOT_TOKEN', 'SERVER_ID']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# Define intents with all necessary permissions
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True

# Create the bot instance with enhanced configuration
class BlackOpsBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            case_insensitive=True,
            strip_after_prefix=True
        )
        self.start_time = datetime.utcnow()
        self.cogs_loaded = 0
        self.total_cogs = 0
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("🚀 Bot setup hook called")
        
        # Start database periodic tasks
        self.loop.create_task(database.periodic_cleanup())
        self.loop.create_task(database.periodic_health_check())
        
        # Load cogs
        await self.load_all_cogs()
        
        # Sync commands
        await self.sync_commands()

    async def load_all_cogs(self):
        """Load all cogs with enhanced error handling"""
        cog_list = [
            "core_user_system",      # User profiles, levels, basic commands
            "unified_economy",       # Economy, banking, investments
            "enhanced_pet_system",   # Advanced pet system
            "fixed_jobsystem",       # Career progression
            "cookies",               # Cookie management
            "moderation",           # Moderation tools
            "admin",                # Admin commands
            "events",               # Event management
            "fun",                  # Fun commands
            "ai",                   # AI integration
            "tickets",              # Support tickets
            "autologging",          # Auto logging
            "quicksetup"            # Server setup
        ]
        
        self.total_cogs = len(cog_list)
        
        for cog_name in cog_list:
            try:
                await self.load_extension(f"cogs.{cog_name}")
                self.cogs_loaded += 1
                logger.info(f"✅ Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load cog {cog_name}: {e}")
                # Continue loading other cogs even if one fails
        
        logger.info(f"📊 Loaded {self.cogs_loaded}/{self.total_cogs} cogs successfully")

    async def sync_commands(self):
        """Enhanced command syncing with error handling"""
        try:
            server_id = int(os.getenv("SERVER_ID"))
            guild = discord.Object(id=server_id)
            
            # Get total commands
            total_commands = len(self.tree.get_commands())
            logger.info(f"📋 Total commands to sync: {total_commands}")
            
            # Try guild sync first (faster for development)
            try:
                synced_guild = await self.tree.sync(guild=guild)
                logger.info(f"✅ Guild sync successful: {len(synced_guild)} commands synced to guild {server_id}")
            except discord.Forbidden:
                logger.warning(f"❌ Guild sync failed: Bot lacks permissions in guild {server_id}")
            except discord.HTTPException as e:
                logger.warning(f"❌ Guild sync failed: HTTP error {e}")
            except Exception as e:
                logger.warning(f"❌ Guild sync failed: {e}")
            
            # Global sync as backup (takes up to 1 hour to propagate)
            try:
                synced_global = await self.tree.sync()
                logger.info(f"✅ Global sync successful: {len(synced_global)} commands synced globally")
            except Exception as e:
                logger.error(f"❌ Global sync failed: {e}")
                
        except Exception as e:
            logger.error(f"❌ Command sync process failed: {e}")

    async def on_ready(self):
        """Enhanced on_ready event with comprehensive logging"""
        logger.info(f'✅ Bot connected as {self.user.name} (ID: {self.user.id})')
        logger.info(f'🏰 Connected to {len(self.guilds)} guilds')
        logger.info(f'👥 Can see {len(self.users):,} users')
        logger.info(f'📊 Loaded {self.cogs_loaded}/{self.total_cogs} cogs')
        logger.info(f'⚡ Commands available: {len(self.tree.get_commands())}')
        
        # Database health check
        health = database.db.get_database_health()
        if health.get("mongodb_connected"):
            logger.info("🗄️ Database: MongoDB connected")
        else:
            logger.warning("🗄️ Database: Using memory storage fallback")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help"
            ),
            status=discord.Status.online
        )
        
        logger.info("🎉 Bot is fully operational!")

    async def on_command_error(self, ctx, error):
        """Enhanced error handling"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Enhanced slash command error handling"""
        if isinstance(error, discord.app_commands.MissingPermissions):
            message = "❌ You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            message = "❌ I don't have the required permissions to execute this command."
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            message = f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        else:
            logger.error(f"Slash command error: {error}")
            message = "❌ An unexpected error occurred. Please try again later."
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except:
            pass  # Interaction might have already been handled

    async def on_guild_join(self, guild):
        """Handle bot joining new guild"""
        logger.info(f"🎉 Joined new guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members")
        
        # Initialize guild data
        database.db.get_guild_data(guild.id)
        
        # Update status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help"
            )
        )

    async def on_guild_remove(self, guild):
        """Handle bot leaving guild"""
        logger.info(f"👋 Left guild: {guild.name} (ID: {guild.id})")
        
        # Update status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"{len(self.guilds)} servers | /help"
            )
        )

# Create bot instance
bot = BlackOpsBot()

# Create Flask app for health checks and monitoring
app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "bot_name": bot.user.name if bot.user else "Bot",
        "guilds": len(bot.guilds) if bot.is_ready() else 0,
        "users": len(bot.users) if bot.is_ready() else 0,
        "uptime": str(datetime.utcnow() - bot.start_time) if hasattr(bot, 'start_time') else "Unknown",
        "latency": round(bot.latency * 1000, 2) if bot.is_ready() else 0,
        "cogs_loaded": f"{bot.cogs_loaded}/{bot.total_cogs}",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/health')
def health():
    """Detailed health check"""
    db_health = database.db.get_database_health()
    
    return jsonify({
        "bot": {
            "status": "online" if bot.is_ready() else "offline",
            "guilds": len(bot.guilds) if bot.is_ready() else 0,
            "latency": round(bot.latency * 1000, 2) if bot.is_ready() else 0,
            "uptime_seconds": (datetime.utcnow() - bot.start_time).total_seconds() if hasattr(bot, 'start_time') else 0
        },
        "database": db_health,
        "system": {
            "cogs_loaded": f"{bot.cogs_loaded}/{bot.total_cogs}",
            "commands": len(bot.tree.get_commands()) if bot.is_ready() else 0
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/stats')
def stats():
    """Database statistics endpoint"""
    return jsonify(database.db.get_database_stats())

@app.route('/restart', methods=['POST'])
def restart():
    """Restart endpoint (for authorized use only)"""
    auth_key = request.headers.get('Authorization')
    if auth_key != os.getenv('RESTART_AUTH_KEY'):
        return jsonify({"error": "Unauthorized"}), 401
    
    logger.info("🔄 Restart requested via API")
    # Graceful shutdown
    asyncio.create_task(bot.close())
    return jsonify({"message": "Bot restart initiated"})

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    # Close database connections
    if database.db.mongodb_client:
        database.db.mongodb_client.close()
    
    # Close bot
    if bot.is_ready():
        asyncio.create_task(bot.close())
    
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

async def main():
    """Enhanced main function with comprehensive error handling"""
    try:
        # Validate bot token
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            logger.error("❌ DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        # Start Flask server in background thread
        flask_port = int(os.getenv("PORT", 5000))
        flask_thread = Thread(
            target=lambda: app.run(
                host='0.0.0.0', 
                port=flask_port, 
                debug=False,
                use_reloader=False
            ),
            daemon=True
        )
        flask_thread.start()
        logger.info(f"🌐 Flask server started on port {flask_port}")
        
        # Start the Discord bot
        logger.info("🤖 Starting Discord bot...")
        async with bot:
            await bot.start(token)
            
    except discord.LoginFailure:
        logger.error("❌ Invalid bot token provided")
    except discord.HTTPException as e:
        logger.error(f"❌ HTTP error occurred: {e}")
    except discord.ConnectionClosed:
        logger.error("❌ Connection to Discord was closed")
    except Exception as e:
        logger.error(f"❌ Unexpected error occurred: {e}")
    finally:
        logger.info("🔄 Bot shutdown complete")

if __name__ == '__main__':
    try:
        # Set up event loop policy for Windows compatibility
        if sys.platform.startswith('win'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Run the main function
        asyncio.run(main())
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        logger.info("👋 Goodbye!")
