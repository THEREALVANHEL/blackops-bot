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
        "pet_system"
    ]
    
    loaded_count = 0
    for cog in cog_list:
        try:
            await bot.load_extension(f"cogs.{cog}")
            print(f"✅ Loaded cog: {cog}")
            loaded_count += 1
        except Exception as e:
            print(f"❌ Failed to load cog {cog}: {e}")
    
    print(f"📊 Loaded {loaded_count}/{len(cog_list)} cogs successfully")
    return loaded_count

@bot.event
async def on_ready():
    print(f"🤖 Bot connected as {bot.user.name}")
    print(f"🆔 Bot ID: {bot.user.id}")
    print(f"🏰 Connected to {len(bot.guilds)} guilds")
    
    # Load cogs first
    await load_cogs()
    
    # Get total commands before sync
    total_commands = len(bot.tree.get_commands())
    print(f"📋 Total commands to sync: {total_commands}")
    
    try:
        server_id = int(os.getenv("SERVER_ID"))
        guild = discord.Object(id=server_id)
        
        print(f"🎯 Attempting to sync to guild: {server_id}")
        
        # Try guild sync first
        try:
            synced_guild = await bot.tree.sync(guild=guild)
            print(f"✅ Guild sync successful: {len(synced_guild)} commands synced to guild {server_id}")
        except discord.Forbidden:
            print(f"❌ Guild sync failed: Bot lacks permissions in guild {server_id}")
        except discord.HTTPException as e:
            print(f"❌ Guild sync failed: HTTP error {e}")
        except Exception as e:
            print(f"❌ Guild sync failed: {e}")
        
        # Try global sync
        try:
            synced_global = await bot.tree.sync()
            print(f"✅ Global sync successful: {len(synced_global)} commands synced globally")
        except Exception as e:
            print(f"❌ Global sync failed: {e}")
            
        print("\n📝 Commands registered:")
        for command in bot.tree.get_commands():
            print(f"  • /{command.name}")
            
    except Exception as e:
        print(f"❌ Sync process failed: {e}")
    
    print("\n🎉 Sync process completed! Shutting down...")
    await asyncio.sleep(2)  # Give time for any pending operations
    await bot.close()

async def main():
    try:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            print("❌ DISCORD_BOT_TOKEN not found in environment variables")
            return
            
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Invalid bot token")
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
