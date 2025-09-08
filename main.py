import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import database
import permissions
from flask import Flask, jsonify, request
import threading

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
        "banking"
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

def run_flask_server():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

@bot.event
async def on_ready():
    """Called when the bot connects to Discord."""
    print(f"Logged in as {bot.user.name}")
    await bot.change_presence(activity=discord.Game(name="with your data"))

    # Initialize the database
    database.db.initialize_database()

    # Load all command cogs
    await load_cogs()
    
    # Syncs all slash commands with Discord
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=int(os.getenv("SERVER_ID"))))
        print(f"✅ Synced {len(synced)} command(s).")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@bot.event
async def on_message(message):
    """Event to handle messages for XP gain."""
    if message.author.bot or not message.guild:
        return
    
    xp_gained_data = database.db.add_xp(message.author.id, 15)
    
    # Check for level up
    if xp_gained_data["leveled_up"]:
        await message.channel.send(f"🎉 Congrats {message.author.mention}, you leveled up to **Level {xp_gained_data['new_level']}**!")

    await bot.process_commands(message)

# Global commands
@bot.tree.command(name="test", description="Simple test command to verify bot functionality.")
async def test_command(interaction: discord.Interaction):
    await interaction.response.send_message("The bot is running correctly!")

@bot.tree.command(name="dbhealth", description="Check database sync status.")
@discord.app_commands.default_permissions(administrator=True)
async def db_health(interaction: discord.Interaction):
    health = database.db.get_database_health()
    if health["connected"]:
        await interaction.response.send_message("Database status: **Connected** (MongoDB)", ephemeral=True)
    else:
        await interaction.response.send_message("Database status: **Disconnected** (Using Memory Storage)", ephemeral=True)

@bot.tree.command(name="sync", description="Force sync all slash commands to the server.")
@discord.app_commands.default_permissions(administrator=True)
async def sync_commands(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        guild_id = int(os.getenv("SERVER_ID"))
        synced = await bot.tree.sync(guild=discord.Object(id=guild_id))
        await interaction.followup.send(f"✅ Synced **{len(synced)}** commands.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to sync commands: {e}", ephemeral=True)


if __name__ == '__main__':
    # Run the Flask server in a separate thread
    threading.Thread(target=run_flask_server).start()
    
    # Run the bot
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
