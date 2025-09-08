import discord
from discord.ext import commands
from discord import app_commands
import permissions
import database
import os
import asyncio

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open a Ticket", style=discord.ButtonStyle.green, emoji="🎫")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        
        # Check if the user already has a ticket open
        user_tickets = [
            channel for channel in guild.channels if channel.name.startswith(f"ticket-{member.id}")
        ]
        if user_tickets:
            await interaction.response.send_message("You already have a ticket open!", ephemeral=True)
            return

        # Create a private channel for the ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
        }
        
        # Try to get moderator role, but don't fail if it doesn't exist
        try:
            moderator_role = guild.get_role(int(os.getenv("MODERATOR_ROLE_ID")))
            if moderator_role:
                overwrites[moderator_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
        except (ValueError, TypeError):
            pass
        
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.id}",
            category=interaction.channel.category,
            overwrites=overwrites
        )
        
        await ticket_channel.send(f"Welcome {member.mention}! A moderator will be with you shortly. Please explain your issue here.")
        await interaction.response.send_message(f"Your ticket has been created at {ticket_channel.mention}!", ephemeral=True)

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ticket-panel", description="Create a simple ticket panel.")
    @discord.app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Ticket System",
            description="Click the button below to open a ticket.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=TicketView())

    @app_commands.command(name="closeticket", description="Close the current ticket.")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def closeticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        
        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message("This command can only be used in a ticket channel.", ephemeral=True)
            return
            
        await interaction.response.send_message("Closing this ticket in 5 seconds...")
        await asyncio.sleep(5)
        await channel.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
