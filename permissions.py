import os
from discord.ext import commands
from discord import app_commands

def is_any_moderator():
    """Custom check to see if the user has any moderator role."""
    async def predicate(interaction: commands.Interaction) -> bool:
        moderator_roles = [
            int(os.getenv("OVERSEER_ROLE_ID", 0)),
            int(os.getenv("LEAD_MODERATOR_ROLE_ID", 0)),
            int(os.getenv("MODERATOR_ROLE_ID", 0)),
            int(os.getenv("COMMUNITY_MANAGER_ROLE_ID", 0)),
            int(os.getenv("COOKIES_MANAGER_ROLE_ID", 0)),
            int(os.getenv("EVENTS_HOST_ROLE_ID", 0)),
            int(os.getenv("EVENTS_COHOST_ROLE_ID", 0)),
            int(os.getenv("MEDIC_ROLE_ID", 0)),
            int(os.getenv("GUIDE_ROLE_ID", 0)),
        ]
        
        # Check if any of the user's roles are in the moderator list
        if any(role.id in moderator_roles for role in interaction.user.roles):
            return True
        else:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False

    return app_commands.check(predicate)

def is_any_host():
    """Custom check for hosts."""
    async def predicate(interaction: commands.Interaction) -> bool:
        host_roles = [
            int(os.getenv("OVERSEER_ROLE_ID", 0)),
            int(os.getenv("LEAD_MODERATOR_ROLE_ID", 0)),
            int(os.getenv("EVENTS_HOST_ROLE_ID", 0)),
            int(os.getenv("EVENTS_COHOST_ROLE_ID", 0)),
        ]
        if any(role.id in host_roles for role in interaction.user.roles):
            return True
        else:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
    return app_commands.check(predicate)

def is_forgotten_one():
    """Custom check for the 'forgotten one' role."""
    async def predicate(interaction: commands.Interaction) -> bool:
        role_id = int(os.getenv("FORGOTTEN_ONE_ROLE_ID", 0))
        if any(role.id == role_id for role in interaction.user.roles):
            return True
        else:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
    return app_commands.check(predicate)

# Combine the permissions for multiple roles
def is_moderator_or_forgotten_one():
    """Check if the user is a moderator or a 'forgotten one'."""
    async def predicate(interaction: commands.Interaction) -> bool:
        is_mod = await is_any_moderator().predicate(interaction)
        if is_mod:
            return True
        else:
            return await is_forgotten_one().predicate(interaction)
    return app_commands.check(predicate)
