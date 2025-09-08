import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Define intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

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
        "jobs",
        "pet_system"  # Added missing cog
    ]
    for cog in cog_list:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Loaded cog: {cog}")
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user.name}. Starting command sync...")
    
    # Load cogs first
    await load_cogs()
    
    try:
        guild = discord.Object(id=int(os.getenv("SERVER_ID")))
        synced = await bot.tree.sync(guild=guild)
        print(f"✅ Synced {len(synced)} commands to guild {guild.id}.")
        
        # Also sync globally for testing
        global_synced = await bot.tree.sync()
        print(f"✅ Synced {len(global_synced)} commands globally.")
        
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    finally:
        await bot.close()

async def main():
    try:
        await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
