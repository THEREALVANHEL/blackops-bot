import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the "super-user" check
def is_forgotten_one():
    async def predicate(interaction: discord.Interaction) -> bool:
        forgotten_one_role_id = int(os.getenv("FORGOTTEN_ONE_ROLE_ID"))
        return any(role.id == forgotten_one_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

# Now, we modify the other permission checks to include the super-user check.
def is_any_moderator():
    async def predicate(interaction: discord.Interaction) -> bool:
        # Check if the user is the "forgotten one" first
        if await is_forgotten_one().predicate(interaction):
            return True
            
        moderator_role_id = int(os.getenv("MODERATOR_ROLE_ID"))
        lead_moderator_role_id = int(os.getenv("LEAD_MODERATOR_ROLE_ID"))
        overseer_role_id = int(os.getenv("OVERSEER_ROLE_ID"))

        allowed_roles = [moderator_role_id, lead_moderator_role_id, overseer_role_id]
        return any(role.id in allowed_roles for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_any_host():
    async def predicate(interaction: discord.Interaction) -> bool:
        # Check if the user is the "forgotten one" first
        if await is_forgotten_one().predicate(interaction):
            return True

        host_role_id = int(os.getenv("HOST_ROLE_ID"))
        head_host_role_id = int(os.getenv("HEAD_HOST_ROLE_ID"))
        
        allowed_roles = [host_role_id, head_host_role_id]
        return any(role.id in allowed_roles for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_cookies_manager():
    async def predicate(interaction: discord.Interaction) -> bool:
        # Check if the user is the "forgotten one" first
        if await is_forgotten_one().predicate(interaction):
            return True

        cookies_manager_role_id = int(os.getenv("COOKIES_MANAGER_ROLE_ID"))
        return any(role.id == cookies_manager_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

# We can create a simpler wrapper for the is_admin check
def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await is_forgotten_one().predicate(interaction) or interaction.user.guild_permissions.administrator
    return discord.app_commands.check(predicate)
