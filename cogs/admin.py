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
        # Add input validation
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
            return
            
        try:
            result = database.db.add_xp(user.id, amount)
            if result.get("leveled_up"):  # Use .get() to avoid KeyError
                await interaction.response.send_message(
                    f"✅ Added **{amount}** XP to {user.mention}. They are now at level **{result['new_level']}**!", 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(f"✅ Added **{amount}** XP to {user.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding XP: {str(e)}", ephemeral=True)
            
    @app_commands.command(name="removexp", description="Remove XP from a user.")
    @app_commands.describe(user="The user to remove XP from.", amount="The amount of XP to remove.")
    @discord.app_commands.default_permissions(administrator=True)
    async def remove_xp(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Add input validation
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
            return
            
        try:
            # FIXED: Use negative amount properly and handle level down
            result = database.db.add_xp(user.id, -amount)
            
            # Check if user leveled down
            if result.get("leveled_down") or result.get("level_changed"):
                await interaction.response.send_message(
                    f"✅ Removed **{amount}** XP from {user.mention}. They are now at level **{result.get('new_level', 'unknown')}**.", 
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(f"✅ Removed **{amount}** XP from {user.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing XP: {str(e)}", ephemeral=True)

    @app_commands.command(name="addcoins", description="Add coins to a user.")
    @app_commands.describe(user="The user to add coins to.", amount="The amount of coins to add.")
    @discord.app_commands.default_permissions(administrator=True)
    async def add_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Add input validation
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
            return
            
        try:
            database.db.add_coins(user.id, amount)
            await interaction.response.send_message(f"✅ Added **{amount}** coins to {user.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error adding coins: {str(e)}", ephemeral=True)

    @app_commands.command(name="removecoins", description="Remove coins from a user.")
    @app_commands.describe(user="The user to remove coins from.", amount="The amount of coins to remove.")
    @discord.app_commands.default_permissions(administrator=True)
    async def remove_coins(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        # Add input validation
        if amount <= 0:
            await interaction.response.send_message("❌ Amount must be greater than 0.", ephemeral=True)
            return
            
        try:
            if database.db.remove_coins(user.id, amount):
                await interaction.response.send_message(f"✅ Removed **{amount}** coins from {user.mention}.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ User does not have enough coins.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error removing coins: {str(e)}", ephemeral=True)

    @app_commands.command(name="updateroles", description="Update a user's roles based on level and cookies.")
    @app_commands.describe(user="The user whose roles you want to update.")
    @discord.app_commands.default_permissions(administrator=True)
    async def update_roles(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)  # FIXED: Use defer for potentially long operations
        
        try:
            # Get user data from database
            user_data = database.db.get_user_data(user.id)  # Assuming this method exists
            
            # Example role update logic (you'll need to implement based on your requirements)
            level = user_data.get("level", 0)
            coins = user_data.get("coins", 0)
            
            # Define your role thresholds here
            role_thresholds = {
                "Newbie": 0,
                "Regular": 5,
                "Veteran": 15,
                "Elite": 25
            }
            
            # Find the highest role the user qualifies for
            qualified_role = None
            for role_name, threshold in sorted(role_thresholds.items(), key=lambda x: x[1], reverse=True):
                if level >= threshold:
                    qualified_role = role_name
                    break
            
            if qualified_role:
                # Get the role object
                role = discord.utils.get(interaction.guild.roles, name=qualified_role)
                if role and role not in user.roles:
                    await user.add_roles(role)
                    await interaction.followup.send(f"✅ Added **{qualified_role}** role to {user.mention}.", ephemeral=True)
                else:
                    await interaction.followup.send(f"✅ {user.mention} already has the appropriate role or role not found.", ephemeral=True)
            else:
                await interaction.followup.send(f"✅ No role changes needed for {user.mention}.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error updating roles: {str(e)}", ephemeral=True)

    @app_commands.command(name="sync", description="Force sync all slash commands to the server.")
    @discord.app_commands.default_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            server_id = os.getenv("SERVER_ID")
            if not server_id:
                await interaction.followup.send("❌ SERVER_ID environment variable not set.", ephemeral=True)
                return
                
            guild_id = int(server_id)  # FIXED: Added error handling for int conversion
            synced = await self.bot.tree.sync(guild=discord.Object(id=guild_id))
            await interaction.followup.send(f"✅ Synced **{len(synced)}** commands.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("❌ Invalid SERVER_ID in environment variables.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to sync commands: {str(e)}", ephemeral=True)

    @app_commands.command(name="dbhealth", description="Check database sync status.")
    @discord.app_commands.default_permissions(administrator=True)
    async def db_health(self, interaction: discord.Interaction):
        try:
            health = database.db.get_database_health()
            if health.get("connected"):  # FIXED: Use .get() to avoid KeyError
                status_msg = "Database status: **Connected** ✅"
                if "db_type" in health:
                    status_msg += f" ({health['db_type']})"
                await interaction.response.send_message(status_msg, ephemeral=True)
            else:
                await interaction.response.send_message("Database status: **Disconnected** ❌ (Using Memory Storage)", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error checking database health: {str(e)}", ephemeral=True)

# FIXED: Corrected function signature
async def setup(bot: commands.Bot):  # Changed from commands.Cog to commands.Bot
    await bot.add_cog(Admin(bot))
