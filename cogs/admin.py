import discord
from discord.ext import commands
from discord import app_commands
import database
import permissions
import os

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="addxp", description="Add XP to a user.")
    @app_commands.describe(user="The user to add XP to.", amount="The amount of XP to add.")
    @discord.app_commands.default_permissions(administrator=True)
    async def add_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        result = database.db.add_xp(user.id, amount)
        if result["leveled_up"]:
            await interaction.response.send_message(f"✅ Added **{amount}** XP to {user.mention}. They are now at level **{result['new_level']}**!", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ Added **{amount}** XP to {user.mention}.", ephemeral=True)
            
    @app_commands.command(name="removexp", description="Remove XP from a user.")
    @app_commands.describe(user="The user to remove XP from.", amount="The amount of XP to remove.")
    @discord.app_commands.default_permissions(administrator=True)
    async def remove_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        result = database.db.add_xp(user.id, -amount)
        await interaction.response.send_message(f"✅ Removed **{amount}** XP from {user.mention}.", ephemeral=True)

    @app_commands.command(name="addcoins", description="Add coins to a user.")
    @app_commands.describe(user="The user to add coins to.", amount="The amount of coins to add.")
    @discord.app_commands.default_permissions(administrator=True)
    async def add_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        database.db.add_coins(user.id, amount)
        await interaction.response.send_message(f"✅ Added **{amount}** coins to {user.mention}.", ephemeral=True)

    @app_commands.command(name="removecoins", description="Remove coins from a user.")
    @app_commands.describe(user="The user to remove coins from.", amount="The amount of coins to remove.")
    @discord.app_commands.default_permissions(administrator=True)
    async def remove_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if database.db.remove_coins(user.id, amount):
            await interaction.response.send_message(f"✅ Removed **{amount}** coins from {user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ User does not have enough coins.", ephemeral=True)

    @app_commands.command(name="updateroles", description="Update a user's roles based on level and cookies.")
    @app_commands.describe(user="The user whose roles you want to update.")
    @discord.app_commands.default_permissions(administrator=True)
    async def update_roles(self, interaction: discord.Interaction, user: discord.Member):
        # This is a placeholder for a more complex system.
        # You would add logic here to check the user's XP and cookies from the database
        # and then apply or remove specific roles based on pre-defined thresholds.
        # Example: if user_data["level"] > 10, add a "Veteran" role.
        await interaction.response.send_message(f"Updating roles for {user.mention}...", ephemeral=True)
        await interaction.followup.send("Roles updated (placeholder functionality).", ephemeral=True)

    @app_commands.command(name="sync", description="Force sync all slash commands to the server.")
    @discord.app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            guild_id = int(os.getenv("SERVER_ID"))
            synced = await self.bot.tree.sync(guild=discord.Object(id=guild_id))
            await interaction.followup.send(f"✅ Synced **{len(synced)}** commands.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to sync commands: {e}", ephemeral=True)

    @app_commands.command(name="dbhealth", description="Check database sync status.")
    @discord.app_commands.default_permissions(administrator=True)
    async def db_health(self, interaction: discord.Interaction):
        health = database.db.get_database_health()
        if health["connected"]:
            await interaction.response.send_message("Database status: **Connected** (MongoDB)", ephemeral=True)
        else:
            await interaction.response.send_message("Database status: **Disconnected** (Using Memory Storage)", ephemeral=True)
            
async def setup(bot: commands.Cog):
    await bot.add_cog(Admin(bot))
