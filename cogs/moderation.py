import discord
from discord.ext import commands
from discord import app_commands
import database
import permissions
import time
from datetime import datetime

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="warn", description="Warn a user for a specific reason.")
    @app_commands.describe(user="The user to warn.", reason="The reason for the warning.")
    @permissions.is_any_moderator()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        warning_data = {
            "moderator_id": interaction.user.id,
            "moderator_name": interaction.user.name,
            "reason": reason,
            "timestamp": time.time()
        }
        database.db.add_warning(user.id, warning_data)
        
        embed = discord.Embed(
            title="User Warned",
            description=f"{user.mention} has been warned by {interaction.user.mention}.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="warnlist", description="Check warnings for a user.")
    @app_commands.describe(user="The user whose warnings you want to check.")
    async def warnlist(self, interaction: discord.Interaction, user: discord.Member):
        warnings = database.db.get_warnings(user.id)
        
        if not warnings:
            await interaction.response.send_message(f"{user.display_name} has no warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{user.display_name}'s Warnings",
            color=discord.Color.red()
        )
        
        for i, warn in enumerate(warnings):
            mod = self.bot.get_user(warn.get("moderator_id"))
            mod_name = mod.name if mod else "Unknown Moderator"
            reason = warn.get("reason", "No reason provided")
            warn_time = datetime.fromtimestamp(warn.get("timestamp", 0))
            
            embed.add_field(
                name=f"Warning #{i+1}",
                value=f"**Reason:** {reason}\n**Moderator:** {mod_name}\n**Date:** {warn_time.strftime('%Y-%m-%d')}",
                inline=False
            )
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="removewarnlist", description="Remove or clear warnings for a user.")
    @app_commands.describe(user="The user whose warnings to remove.", warning_index="The index of the warning to remove (e.g., 1 for the first warning).", reason="The reason for removing the warning.")
    @permissions.is_any_moderator()
    async def remove_warnlist(self, interaction: discord.Interaction, user: discord.Member, warning_index: int, reason: str):
        user_data = database.db.get_user_data(user.id)
        warnings = user_data.get("warnings", [])

        if not warnings or warning_index <= 0 or warning_index > len(warnings):
            await interaction.response.send_message("Invalid warning index.", ephemeral=True)
            return

        removed_warning = warnings.pop(warning_index - 1)
        user_data["warnings"] = warnings
        database.db.update_user_data(user.id, user_data)

        embed = discord.Embed(
            title="Warning Removed",
            description=f"Warning #{warning_index} for {user.mention} was removed by {interaction.user.mention}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Original Warning", value=f"Reason: {removed_warning['reason']}", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="modclear", description="Delete messages (1-100).")
    @app_commands.describe(amount="The number of messages to delete (1-100).")
    @permissions.is_any_moderator()
    async def modclear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("You can only delete between 1 and 100 messages.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted_messages = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Deleted **{len(deleted_messages)}** messages.", ephemeral=True)

    @app_commands.command(name="setlog", description="Set a channel for moderation and logging.")
    @app_commands.describe(channel="The channel to set as the log channel.")
    @permissions.is_any_moderator()
    async def setlog(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild_id
        database.db.update_guild_data(guild_id, {"settings.modlog_channel": channel.id})
        await interaction.response.send_message(f"✅ Moderation log channel set to {channel.mention}.", ephemeral=True)

async def setup(bot: commands.Cog):
    await bot.add_cog(Moderation(bot))
