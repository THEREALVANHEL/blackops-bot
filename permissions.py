import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import logging
from typing import Optional, Union
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PermissionError(Exception):
    """Custom permission error"""
    pass

class PermissionManager:
    """Enhanced permission management system"""
    
    def __init__(self):
        self.role_hierarchy = {
            "forgotten_one": {"level": 100, "role_id": self._get_role_id("FORGOTTEN_ONE_ROLE_ID")},
            "overseer": {"level": 90, "role_id": self._get_role_id("OVERSEER_ROLE_ID")},
            "lead_moderator": {"level": 80, "role_id": self._get_role_id("LEAD_MODERATOR_ROLE_ID")},
            "moderator": {"level": 70, "role_id": self._get_role_id("MODERATOR_ROLE_ID")},
            "head_host": {"level": 60, "role_id": self._get_role_id("HEAD_HOST_ROLE_ID")},
            "host": {"level": 50, "role_id": self._get_role_id("HOST_ROLE_ID")},
            "cookies_manager": {"level": 40, "role_id": self._get_role_id("COOKIES_MANAGER_ROLE_ID")},
            "member": {"level": 10, "role_id": None}
        }
        
        # Cache for permission checks
        self._permission_cache = {}
        self._cache_timeout = 300  # 5 minutes
        
    def _get_role_id(self, env_var: str) -> Optional[int]:
        """Safely get role ID from environment"""
        try:
            role_id = os.getenv(env_var)
            return int(role_id) if role_id else None
        except (ValueError, TypeError):
            logger.warning(f"Invalid role ID in {env_var}: {os.getenv(env_var)}")
            return None
    
    def get_user_permission_level(self, user: discord.Member) -> int:
        """Get user's permission level"""
        # Check cache first
        cache_key = f"perm_level_{user.id}"
        if cache_key in self._permission_cache:
            cached_data = self._permission_cache[cache_key]
            if cached_data["expires"] > asyncio.get_event_loop().time():
                return cached_data["level"]
        
        max_level = 10  # Default member level
        
        # Check each role hierarchy
        for role_name, role_data in self.role_hierarchy.items():
            if role_data["role_id"] and any(role.id == role_data["role_id"] for role in user.roles):
                max_level = max(max_level, role_data["level"])
        
        # Check for administrator permission
        if user.guild_permissions.administrator:
            max_level = max(max_level, 85)  # Between moderator and overseer
        
        # Cache the result
        self._permission_cache[cache_key] = {
            "level": max_level,
            "expires": asyncio.get_event_loop().time() + self._cache_timeout
        }
        
        return max_level
    
    def has_permission_level(self, user: discord.Member, required_level: int) -> bool:
        """Check if user has required permission level"""
        return self.get_user_permission_level(user) >= required_level
    
    def clear_user_cache(self, user_id: int):
        """Clear cached permissions for user"""
        cache_key = f"perm_level_{user_id}"
        self._permission_cache.pop(cache_key, None)
    
    def get_role_info(self, role_name: str) -> Optional[dict]:
        """Get role information"""
        return self.role_hierarchy.get(role_name)

# Global permission manager
perm_manager = PermissionManager()

# ==================== PERMISSION DECORATORS ====================

def permission_required(required_level: int, error_message: str = None):
    """Decorator for permission-based command access"""
    def decorator(func):
        async def predicate(interaction: discord.Interaction) -> bool:
            if not interaction.guild:
                return False
            
            user_level = perm_manager.get_user_permission_level(interaction.user)
            
            if user_level >= required_level:
                return True
            
            # Send error message if provided
            if error_message:
                try:
                    await interaction.response.send_message(error_message, ephemeral=True)
                except:
                    pass  # Interaction might already be responded to
            
            return False
        
        return discord.app_commands.check(predicate)
    
    return decorator

# ==================== SPECIFIC ROLE CHECKS ====================

def is_forgotten_one():
    """Check if user is the forgotten one (super admin)"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            forgotten_one_role_id = perm_manager.role_hierarchy["forgotten_one"]["role_id"]
            if not forgotten_one_role_id:
                logger.warning("FORGOTTEN_ONE_ROLE_ID not configured")
                return False
            
            return any(role.id == forgotten_one_role_id for role in interaction.user.roles)
        except Exception as e:
            logger.error(f"Error checking forgotten one permission: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def is_any_moderator():
    """Check if user has any moderator role or higher"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            return perm_manager.has_permission_level(interaction.user, 70)  # Moderator level
        except Exception as e:
            logger.error(f"Error checking moderator permission: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def is_any_host():
    """Check if user has any host role or higher"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            return perm_manager.has_permission_level(interaction.user, 50)  # Host level
        except Exception as e:
            logger.error(f"Error checking host permission: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def is_cookies_manager():
    """Check if user is cookies manager or higher"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            return perm_manager.has_permission_level(interaction.user, 40)  # Cookies manager level
        except Exception as e:
            logger.error(f"Error checking cookies manager permission: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def is_admin():
    """Check if user is admin or higher"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            # Check for forgotten one first (highest level)
            if perm_manager.has_permission_level(interaction.user, 100):
                return True
            
            # Check for Discord administrator permission
            return interaction.user.guild_permissions.administrator
        except Exception as e:
            logger.error(f"Error checking admin permission: {e}")
            return False
    
    return discord.app_commands.check(predicate)

# ==================== ENHANCED PERMISSION CHECKS ====================

def requires_role(role_name: str, allow_higher: bool = True):
    """Check if user has specific role (with optional hierarchy)"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            role_info = perm_manager.get_role_info(role_name)
            if not role_info:
                logger.error(f"Unknown role: {role_name}")
                return False
            
            required_level = role_info["level"]
            user_level = perm_manager.get_user_permission_level(interaction.user)
            
            if allow_higher:
                return user_level >= required_level
            else:
                # Exact role match required
                role_id = role_info["role_id"]
                return role_id and any(role.id == role_id for role in interaction.user.roles)
        except Exception as e:
            logger.error(f"Error checking role {role_name}: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def requires_any_role(*role_names: str):
    """Check if user has any of the specified roles"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            for role_name in role_names:
                role_info = perm_manager.get_role_info(role_name)
                if role_info and role_info["role_id"]:
                    if any(role.id == role_info["role_id"] for role in interaction.user.roles):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking roles {role_names}: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def requires_permission_level(level: int):
    """Check if user has minimum permission level"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            return perm_manager.has_permission_level(interaction.user, level)
        except Exception as e:
            logger.error(f"Error checking permission level {level}: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def is_bot_owner():
    """Check if user is the bot owner"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            app_info = await interaction.client.application_info()
            return interaction.user.id == app_info.owner.id
        except Exception as e:
            logger.error(f"Error checking bot owner: {e}")
            return False
    
    return discord.app_commands.check(predicate)

def requires_guild_permissions(**permissions):
    """Check if user has specific Discord permissions"""
    async def predicate(interaction: discord.Interaction) -> bool:
        try:
            if not interaction.guild:
                return False
            
            user_perms = interaction.user.guild_permissions
            
            for perm_name, required in permissions.items():
                if required and not getattr(user_perms, perm_name, False):
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking guild permissions: {e}")
            return False
    
    return discord.app_commands.check(predicate)

# ==================== HELPER FUNCTIONS ====================

async def check_forgotten_one(interaction: discord.Interaction) -> bool:
    """Helper function to check if user is forgotten one"""
    try:
        forgotten_one_role_id = perm_manager.role_hierarchy["forgotten_one"]["role_id"]
        if not forgotten_one_role_id:
            return False
        
        return any(role.id == forgotten_one_role_id for role in interaction.user.roles)
    except Exception as e:
        logger.error(f"Error in check_forgotten_one: {e}")
        return False

async def get_user_permissions(user: discord.Member) -> dict:
    """Get detailed permission information for user"""
    try:
        user_level = perm_manager.get_user_permission_level(user)
        
        permissions = {
            "permission_level": user_level,
            "roles": [],
            "is_admin": user.guild_permissions.administrator,
            "can_moderate": user_level >= 70,
            "can_host": user_level >= 50,
            "can_manage_cookies": user_level >= 40
        }
        
        # Get role names
        for role_name, role_data in perm_manager.role_hierarchy.items():
            if role_data["role_id"] and any(role.id == role_data["role_id"] for role in user.roles):
                permissions["roles"].append(role_name)
        
        return permissions
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        return {"error": str(e)}

def clear_permission_cache(user_id: int = None):
    """Clear permission cache for user or all users"""
    try:
        if user_id:
            perm_manager.clear_user_cache(user_id)
        else:
            perm_manager._permission_cache.clear()
        
        logger.info(f"Cleared permission cache for {'user ' + str(user_id) if user_id else 'all users'}")
    except Exception as e:
        logger.error(f"Error clearing permission cache: {e}")

def get_role_hierarchy() -> dict:
    """Get the complete role hierarchy"""
    return perm_manager.role_hierarchy.copy()

def validate_permission_setup() -> dict:
    """Validate permission system setup"""
    issues = []
    warnings = []
    
    # Check environment variables
    env_vars = [
        "FORGOTTEN_ONE_ROLE_ID",
        "OVERSEER_ROLE_ID", 
        "LEAD_MODERATOR_ROLE_ID",
        "MODERATOR_ROLE_ID",
        "HEAD_HOST_ROLE_ID",
        "HOST_ROLE_ID",
        "COOKIES_MANAGER_ROLE_ID"
    ]
    
    for env_var in env_vars:
        value = os.getenv(env_var)
        if not value:
            warnings.append(f"Environment variable {env_var} not set")
        else:
            try:
                int(value)
            except ValueError:
                issues.append(f"Invalid role ID in {env_var}: {value}")
    
    # Check role hierarchy integrity
    levels = [role_data["level"] for role_data in perm_manager.role_hierarchy.values()]
    if len(levels) != len(set(levels)):
        issues.append("Duplicate permission levels found in role hierarchy")
    
    return {
        "status": "healthy" if not issues else "issues_found",
        "issues": issues,
        "warnings": warnings,
        "total_roles": len(perm_manager.role_hierarchy),
        "configured_roles": len([r for r in perm_manager.role_hierarchy.values() if r["role_id"]])
    }

# ==================== PERMISSION COMMANDS COG ====================

class PermissionCommands(commands.Cog):
    """Commands for managing permissions"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="mypermissions", description="Check your permission level and roles.")
    async def my_permissions(self, interaction: discord.Interaction):
        """Show user's permissions"""
        try:
            perms = await get_user_permissions(interaction.user)
            
            embed = discord.Embed(
                title="🔐 Your Permissions",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="Permission Level",
                value=f"`{perms['permission_level']}`",
                inline=True
            )
            
            embed.add_field(
                name="Administrator",
                value="✅ Yes" if perms['is_admin'] else "❌ No",
                inline=True
            )
            
            embed.add_field(
                name="Can Moderate",
                value="✅ Yes" if perms['can_moderate'] else "❌ No",
                inline=True
            )
            
            if perms['roles']:
                roles_text = "\n".join([f"• {role.replace('_', ' ').title()}" for role in perms['roles']])
                embed.add_field(name="Special Roles", value=roles_text, inline=False)
            
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="Permissions are cached for 5 minutes")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in mypermissions command: {e}")
            await interaction.response.send_message("❌ Error retrieving permissions.", ephemeral=True)
    
    @app_commands.command(name="checkpermissions", description="Check another user's permissions.")
    @app_commands.describe(user="User to check permissions for")
    @requires_permission_level(70)  # Moderator or higher
    async def check_permissions(self, interaction: discord.Interaction, user: discord.Member):
        """Check permissions for another user"""
        try:
            perms = await get_user_permissions(user)
            
            embed = discord.Embed(
                title=f"🔐 {user.display_name}'s Permissions",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="Permission Level",
                value=f"`{perms['permission_level']}`",
                inline=True
            )
            
            embed.add_field(
                name="Administrator",
                value="✅ Yes" if perms['is_admin'] else "❌ No",
                inline=True
            )
            
            embed.add_field(
                name="Can Moderate",
                value="✅ Yes" if perms['can_moderate'] else "❌ No",
                inline=True
            )
            
            if perms['roles']:
                roles_text = "\n".join([f"• {role.replace('_', ' ').title()}" for role in perms['roles']])
                embed.add_field(name="Special Roles", value=roles_text, inline=False)
            
            embed.set_thumbnail(url=user.display_avatar.url)
            embed.set_footer(text=f"Checked by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in checkpermissions command: {e}")
            await interaction.response.send_message("❌ Error retrieving permissions.", ephemeral=True)
    
    @app_commands.command(name="permissionsetup", description="Validate permission system setup.")
    @is_forgotten_one()
    async def permission_setup(self, interaction: discord.Interaction):
        """Validate permission system setup"""
        try:
            validation = validate_permission_setup()
            
            embed = discord.Embed(
                title="🔧 Permission System Validation",
                color=discord.Color.green() if validation["status"] == "healthy" else discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="Status",
                value=f"{'✅ Healthy' if validation['status'] == 'healthy' else '⚠️ Issues Found'}",
                inline=True
            )
            
            embed.add_field(
                name="Configured Roles",
                value=f"{validation['configured_roles']}/{validation['total_roles']}",
                inline=True
            )
            
            if validation["issues"]:
                issues_text = "\n".join([f"❌ {issue}" for issue in validation["issues"]])
                embed.add_field(name="Issues", value=issues_text, inline=False)
            
            if validation["warnings"]:
                warnings_text = "\n".join([f"⚠️ {warning}" for warning in validation["warnings"]])
                embed.add_field(name="Warnings", value=warnings_text, inline=False)
            
            # Show role hierarchy
            hierarchy_text = []
            for role_name, role_data in sorted(
                perm_manager.role_hierarchy.items(), 
                key=lambda x: x[1]["level"], 
                reverse=True
            ):
                status = "✅" if role_data["role_id"] else "❌"
                hierarchy_text.append(f"{status} {role_name.replace('_', ' ').title()} (Level {role_data['level']})")
            
            embed.add_field(name="Role Hierarchy", value="\n".join(hierarchy_text), inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in permissionsetup command: {e}")
            await interaction.response.send_message("❌ Error validating permissions.", ephemeral=True)

# ==================== EXPORT ====================

__all__ = [
    'is_forgotten_one',
    'is_any_moderator', 
    'is_any_host',
    'is_cookies_manager',
    'is_admin',
    'requires_role',
    'requires_any_role',
    'requires_permission_level',
    'is_bot_owner',
    'requires_guild_permissions',
    'permission_required',
    'check_forgotten_one',
    'get_user_permissions',
    'clear_permission_cache',
    'get_role_hierarchy',
    'validate_permission_setup',
    'perm_manager',
    'PermissionCommands'
]

logger.info("🔐 Enhanced permission system loaded successfully")
