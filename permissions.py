import os
import discord
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define permission classes and decorators

def is_overseer():
    async def predicate(interaction: discord.Interaction) -> bool:
        overseer_role_id = int(os.getenv("OVERSEER_ROLE_ID"))
        return any(role.id == overseer_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_forgotten_one():
    async def predicate(interaction: discord.Interaction) -> bool:
        forgotten_one_role_id = int(os.getenv("FORGOTTEN_ONE_ROLE_ID"))
        return any(role.id == forgotten_one_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_lead_moderator():
    async def predicate(interaction: discord.Interaction) -> bool:
        lead_moderator_role_id = int(os.getenv("LEAD_MODERATOR_ROLE_ID"))
        return any(role.id == lead_moderator_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_moderator():
    async def predicate(interaction: discord.Interaction) -> bool:
        moderator_role_id = int(os.getenv("MODERATOR_ROLE_ID"))
        return any(role.id == moderator_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_head_host():
    async def predicate(interaction: discord.Interaction) -> bool:
        head_host_role_id = int(os.getenv("HEAD_HOST_ROLE_ID"))
        return any(role.id == head_host_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_host():
    async def predicate(interaction: discord.Interaction) -> bool:
        host_role_id = int(os.getenv("HOST_ROLE_ID"))
        return any(role.id == host_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

def is_cookies_manager():
    async def predicate(interaction: discord.Interaction) -> bool:
        cookies_manager_role_id = int(os.getenv("COOKIES_MANAGER_ROLE_ID"))
        return any(role.id == cookies_manager_role_id for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

# Add a check to combine all moderator roles
def is_any_moderator():
    async def predicate(interaction: discord.Interaction) -> bool:
        moderator_role_id = int(os.getenv("MODERATOR_ROLE_ID"))
        lead_moderator_role_id = int(os.getenv("LEAD_MODERATOR_ROLE_ID"))
        overseer_role_id = int(os.getenv("OVERSEER_ROLE_ID"))
        forgotten_one_role_id = int(os.getenv("FORGOTTEN_ONE_ROLE_ID"))

        allowed_roles = [moderator_role_id, lead_moderator_role_id, overseer_role_id, forgotten_one_role_id]
        return any(role.id in allowed_roles for role in interaction.user.roles)
    return discord.app_commands.check(predicate)

# Add a check for all host roles
def is_any_host():
    async def predicate(interaction: discord.Interaction) -> bool:
        host_role_id = int(os.getenv("HOST_ROLE_ID"))
        head_host_role_id = int(os.getenv("HEAD_HOST_ROLE_ID"))
        
        allowed_roles = [host_role_id, head_host_role_id]
        return any(role.id in allowed_roles for role in interaction.user.roles)
    return discord.app_commands.check(predicate)
