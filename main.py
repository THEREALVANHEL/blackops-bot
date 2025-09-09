import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database
import permissions
from flask import Flask, jsonify, request
from threading import Thread
import asyncio

# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# Create Flask app
app = Flask(__name__)

# Load cogs from the 'cogs' folder
async def load_cogs():
    cog_list = [
    "core_user_system",      # Replaces: basic, leveling
    "unified_economy",       # Replaces: economy, banking
    "enhanced_pet_system",   # Replaces: pet_system
    "fixed_jobsystem",       # Replaces: jobsystem, jobs
    "cookies",               # Keep as-is
    "moderation",           # Keep as-is
    "admin",                # Keep as-is
    "events",               # Keep as-is
    "fun",                  # Keep as-is
    "ai",                   # Keep as-is
    "tickets",              # Keep as-is
    "autologging",          # Keep as-is
    "quicksetup"            # Enhanced version coming
]
    for cog in cog_list:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    print(f'✅ Bot connected as {bot.user.name}')
    print(f'📊 Bot is in {len(bot.guilds)} guilds')
    
    # Load cogs when bot is ready
    await load_cogs()
    
    # Sync commands to your specific server
    try:
        guild = discord.Object(id=int(os.getenv("SERVER_ID")))
        synced = await bot.tree.sync(guild=guild)
        print(f"🔄 Synced {len(synced)} commands to guild {guild.id}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

# Flask route for health check
@app.route('/')
def home():
    return "Bot is running!", 200

@app.route('/status')
def status():
    return jsonify({
        "status": "online",
        "guilds": len(bot.guilds),
        "latency": round(bot.latency * 1000, 2)
    })

async def main():
    # Start the Flask server in a separate thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))).start()
    
    # Start the bot
    await bot.start(os.getenv("DISCORD_BOT_TOKEN"))

if __name__ == '__main__':
    asyncio.run(main())
