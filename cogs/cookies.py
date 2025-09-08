import discord
from discord.ext import commands
from discord import app_commands
import database
import permissions

class Cookies(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="addcookies", description="Add cookies to a user.")
    @app_commands.describe(user="The user to add cookies to.", amount="The amount of cookies to add.")
    @permissions.is_cookies_manager()
    async def add_cookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        database.db.add_cookies(user.id, amount)
        await interaction.response.send_message(f"✅ Added **{amount:,}** cookies to {user.mention}.", ephemeral=True)
    
    @app_commands.command(name="removecookies", description="Remove cookies from a user.")
    @app_commands.describe(user="The user to remove cookies from.", amount="The amount of cookies to remove.")
    @permissions.is_cookies_manager()
    async def remove_cookies(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        user_data = database.db.get_user_data(user.id)
        current_cookies = user_data.get("cookies", 0)
        
        if current_cookies < amount:
            await interaction.response.send_message("❌ User does not have enough cookies.", ephemeral=True)
            return
            
        new_cookies = current_cookies - amount
        database.db.update_user_data(user.id, {"cookies": new_cookies})
        
        await interaction.response.send_message(f"✅ Removed **{amount:,}** cookies from {user.mention}.", ephemeral=True)
        
    @app_commands.command(name="cookiesgiveall", description="Give cookies to everyone.")
    @app_commands.describe(amount="The amount of cookies to give everyone.")
    @permissions.is_cookies_manager()
    async def cookies_give_all(self, interaction: discord.Interaction, amount: int):
        # This is a powerful command, so we will use a database function to update everyone
        # For simplicity, we will simulate a loop over all users
        # The database.py file has a get_user_data that will create a user if they don't exist
        
        guild_members = interaction.guild.members
        users_updated = 0
        
        for member in guild_members:
            if not member.bot:
                database.db.add_cookies(member.id, amount)
                users_updated += 1
                
        await interaction.response.send_message(f"🍪 Gave **{amount:,}** cookies to **{users_updated}** users.", ephemeral=True)

    @app_commands.command(name="removecookiesall", description="Remove cookies from everyone.")
    @app_commands.describe(amount="The amount of cookies to remove from everyone.")
    @permissions.is_cookies_manager()
    async def remove_cookies_all(self, interaction: discord.Interaction, amount: int):
        # Similar to the giveall command, but removes cookies.
        guild_members = interaction.guild.members
        users_updated = 0
        
        for member in guild_members:
            if not member.bot:
                user_data = database.db.get_user_data(member.id)
                current_cookies = user_data.get("cookies", 0)
                new_cookies = max(0, current_cookies - amount)
                database.db.update_user_data(member.id, {"cookies": new_cookies})
                users_updated += 1

        await interaction.response.send_message(f"🍪 Removed **{amount:,}** cookies from **{users_updated}** users.", ephemeral=True)


async def setup(bot: commands.Cog):
    await bot.add_cog(Cookies(bot))
