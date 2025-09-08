import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database
import permissions
from flask import Flask, jsonify, request
from threading import Thread

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
        "basic",
        "leveling",
        "economy",
        "cookies",
        "moderation",
        "admin",
        "events",
        "fun",
        "ai",
        "banking",
        "tickets",
        "settings",
        "jobs"
    ]
    for cog in cog_list:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

# Flask route for health check
@app.route('/')
def home():
    return "Bot is running!", 200

# The rest of your command definitions should remain the same

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))).start()

    # Run the bot
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
