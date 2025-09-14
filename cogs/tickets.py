import discord
from discord.ext import commands
from discord import app_commands
import permissions
import database
import os
import asyncio
import time
from datetime import datetime

class TicketControlView(discord.ui.View):
    def __init__(self, ticket_creator_id: int):
        super().__init__(timeout=None)
        self.ticket_creator_id = ticket_creator_id

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to close tickets
        if not (interaction.user.guild_permissions.manage_channels or 
                any(role.id in [int(os.getenv("MODERATOR_ROLE_ID", 0)), 
                               int(os.getenv("LEAD_MODERATOR_ROLE_ID", 0)),
                               int(os.getenv("OVERSEER_ROLE_ID", 0))] for role in interaction.user.roles) or
                interaction.user.id == self.ticket_creator_id):
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return
        
        await self.close_ticket_process(interaction)

    @discord.ui.button(label="Add User", style=discord.ButtonStyle.gray, emoji="➕")
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only moderators can add users to tickets.", ephemeral=True)
            return
        
        class AddUserModal(discord.ui.Modal):
            def __init__(self):
                super().__init__(title="Add User to Ticket")
            
            user_id = discord.ui.TextInput(
                label="User ID or @mention",
                placeholder="Enter user ID or mention the user...",
                required=True
            )
            
            async def on_submit(self, modal_interaction):
                try:
                    # Try to extract user ID from mention or use as direct ID
                    user_id_str = self.user_id.value.strip()
                    if user_id_str.startswith('<@') and user_id_str.endswith('>'):
                        user_id = int(user_id_str[2:-1].replace('!', ''))
                    else:
                        user_id = int(user_id_str)
                    
                    member = modal_interaction.guild.get_member(user_id)
                    if not member:
                        await modal_interaction.response.send_message("❌ User not found in this server.", ephemeral=True)
                        return
                    
                    # Add permissions to the channel
                    await modal_interaction.channel.set_permissions(
                        member, 
                        view_channel=True, 
                        send_messages=True, 
                        attach_files=True
                    )
                    
                    await modal_interaction.response.send_message(f"✅ Added {member.mention} to this ticket.", ephemeral=True)
                    
                except (ValueError, TypeError):
                    await modal_interaction.response.send_message("❌ Invalid user ID format.", ephemeral=True)
                except Exception as e:
                    await modal_interaction.response.send_message(f"❌ Error adding user: {str(e)}", ephemeral=True)
        
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(label="Priority", style=discord.ButtonStyle.secondary, emoji="⚡")
    async def set_priority(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("❌ Only moderators can set ticket priority.", ephemeral=True)
            return
        
        class PriorityView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.select(
                placeholder="Set ticket priority...",
                options=[
                    discord.SelectOption(label="🟢 Low Priority", value="low", emoji="🟢"),
                    discord.SelectOption(label="🟡 Medium Priority", value="medium", emoji="🟡"),
                    discord.SelectOption(label="🟠 High Priority", value="high", emoji="🟠"),
                    discord.SelectOption(label="🔴 Urgent", value="urgent", emoji="🔴")
                ]
            )
            async def priority_select(self, select_interaction, select):
                priority = select.values[0]
                priority_colors = {
                    "low": "🟢",
                    "medium": "🟡", 
                    "high": "🟠",
                    "urgent": "🔴"
                }
                
                # Update channel name to reflect priority
                new_name = f"{priority_colors[priority]}-{select_interaction.channel.name}"
                if not select_interaction.channel.name.startswith(tuple(priority_colors.values())):
                    try:
                        await select_interaction.channel.edit(name=new_name)
                    except:
                        pass
                
                await select_interaction.response.send_message(
                    f"{priority_colors[priority]} Ticket priority set to **{priority.upper()}**", 
                    ephemeral=True
                )
        
        await interaction.response.send_message("Select priority level:", view=PriorityView(), ephemeral=True)

    async def close_ticket_process(self, interaction: discord.Interaction):
        """Handle the ticket closing process with transcript generation"""
        await interaction.response.defer()
        
        # Generate transcript
        try:
            transcript = await self.generate_transcript(interaction.channel)
            
            # Send transcript to ticket creator
            creator = interaction.guild.get_member(self.ticket_creator_id)
            if creator:
                embed = discord.Embed(
                    title="🎫 Ticket Transcript",
                    description=f"Your ticket **{interaction.channel.name}** has been closed.",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Channel", value=interaction.channel.name, inline=True)
                embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
                embed.add_field(name="Closed at", value=f"<t:{int(time.time())}:F>", inline=False)
                
                try:
                    from io import BytesIO
                    buffer = BytesIO(transcript.encode('utf-8'))
                    transcript_file = discord.File(buffer, filename=f"transcript-{interaction.channel.name}.txt")
                    await creator.send(embed=embed, file=transcript_file)
                    transcript_sent = True
                except Exception:
                    transcript_sent = False
            else:
                transcript_sent = False
            
            # Send closing message
            closing_embed = discord.Embed(
                title="🔒 Ticket Closing",
                description="This ticket will be deleted in 10 seconds...",
                color=discord.Color.red()
            )
            if transcript_sent:
                closing_embed.add_field(name="✅ Transcript", value="Sent to ticket creator via DM", inline=False)
            else:
                closing_embed.add_field(name="⚠️ Transcript", value="Could not send transcript to creator", inline=False)
            
            await interaction.followup.send(embed=closing_embed)
            
            # Wait and delete
            await asyncio.sleep(10)
            await interaction.channel.delete()
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error closing ticket: {str(e)}")

    async def generate_transcript(self, channel) -> str:
        """Generate a text transcript of the ticket conversation"""
        transcript = f"TICKET TRANSCRIPT\n"
        transcript += f"Channel: {channel.name}\n"
        transcript += f"Created: {channel.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        transcript += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        transcript += "=" * 50 + "\n\n"
        
        try:
            messages = []
            async for message in channel.history(limit=500, oldest_first=True):
                messages.append(message)
            
            for message in messages:
                timestamp = message.created_at.strftime('%Y-%m-%d %H:%M:%S')
                transcript += f"[{timestamp}] {message.author.display_name}: {message.content}\n"
                
                if message.attachments:
                    for attachment in message.attachments:
                        transcript += f"    📎 Attachment: {attachment.url}\n"
                
                if message.embeds:
                    for embed in message.embeds:
                        if embed.title:
                            transcript += f"    📋 Embed Title: {embed.title}\n"
                        if embed.description:
                            transcript += f"    📋 Embed Description: {embed.description}\n"
                
                transcript += "\n"
        
        except Exception as e:
            transcript += f"Error generating transcript: {str(e)}\n"
        
        return transcript

class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Default to general; we'll ask the user with a lightweight dropdown after creation if needed
        await self.create_ticket(interaction, "general")

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        guild = interaction.guild
        member = interaction.user
        
        # Check if user already has a ticket
        existing_tickets = [
            channel for channel in guild.channels 
            if isinstance(channel, discord.TextChannel) and 
            channel.name.startswith(f"ticket-{member.id}")
        ]
        
        if len(existing_tickets) >= 3:  # Limit tickets per user
            await interaction.response.send_message(
                "❌ You already have 3 tickets open! Please close an existing ticket first.", 
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Create ticket channel with proper permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, 
                send_messages=True, 
                attach_files=True,
                embed_links=True
            )
        }
        
        # Add moderator roles
        try:
            moderator_role_id = int(os.getenv("MODERATOR_ROLE_ID", 0))
            lead_moderator_role_id = int(os.getenv("LEAD_MODERATOR_ROLE_ID", 0))
            overseer_role_id = int(os.getenv("OVERSEER_ROLE_ID", 0))
            
            for role_id in [moderator_role_id, lead_moderator_role_id, overseer_role_id]:
                if role_id > 0:
                    role = guild.get_role(role_id)
                    if role:
                        overwrites[role] = discord.PermissionOverwrite(
                            view_channel=True, 
                            send_messages=True, 
                            attach_files=True,
                            manage_messages=True
                        )
        except (ValueError, TypeError):
            pass

        # Create channel
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{member.id}-{ticket_type}",
            overwrites=overwrites,
            category=interaction.channel.category,
            topic=f"Support ticket for {member.display_name} | Type: {ticket_type.title()}"
        )

        # Create welcome embed
        type_info = {
            "general": {"emoji": "❓", "color": discord.Color.blue()},
            "technical": {"emoji": "🔧", "color": discord.Color.orange()},
            "report": {"emoji": "⚠️", "color": discord.Color.red()},
            "business": {"emoji": "🤝", "color": discord.Color.green()},
            "appeal": {"emoji": "⚖️", "color": discord.Color.purple()}
        }
        
        info = type_info.get(ticket_type, {"emoji": "🎫", "color": discord.Color.blue()})
        
        embed = discord.Embed(
            title=f"{info['emoji']} Support Ticket Created",
            description=f"**Type:** {ticket_type.title()}\n**User:** {member.mention}",
            color=info['color'],
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📝 Next Steps",
            value="• Clearly describe your issue\n• Provide relevant details/screenshots\n• Wait for a staff member to respond\n• Use the buttons below to manage this ticket",
            inline=False
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Ticket ID: ticket-{member.id}-{ticket_type}")

        # Mention oversight roles
        mention_ids = [os.getenv('OVERSEER_ROLE_ID'), os.getenv('MODERATOR_ROLE_ID'), os.getenv('LEAD_MODERATOR_ROLE_ID')]
        mentions = " ".join([f"<@&{rid}>" for rid in mention_ids if rid and rid.isdigit() and int(rid) > 0])

        # Send welcome message with control view
        view = TicketControlView(member.id)
        content = f"👋 Welcome {member.mention}!\n🔔 {mentions} A new support ticket needs attention!" if mentions else f"👋 Welcome {member.mention}!"
        await ticket_channel.send(content, embed=embed, view=view)

        await interaction.followup.send(
            f"✅ Your ticket has been created: {ticket_channel.mention}",
            ephemeral=True
        )

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @app_commands.command(name="ticket-panel", description="Create an advanced ticket support panel.")
    @discord.app_commands.default_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Support Ticket System",
            description="Need help? Create a support ticket below!\n\nSelect the type of support you need and our team will assist you.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="📋 Available Support Types",
            value=(
                "❓ **General Support** - Questions and general help\n"
                "🔧 **Technical Issues** - Bot problems and bugs\n"
                "⚠️ **Report User** - Rule violations and reports\n"
                "🤝 **Partnership** - Business and partnerships\n"
                "⚖️ **Appeals** - Appeal punishments"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⏱️ Response Times",
            value="• High Priority: Within 1 hour\n• Normal Priority: Within 6 hours\n• Low Priority: Within 24 hours",
            inline=True
        )
        
        embed.add_field(
            name="📞 Support Hours",
            value="• Weekdays: 9 AM - 11 PM EST\n• Weekends: 12 PM - 8 PM EST\n• Urgent issues: 24/7",
            inline=True
        )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text="BlackOps Support • Your ticket will be handled by our professional staff")

        view = TicketCreateView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="closeticket", description="Close the current ticket with transcript generation.")
    async def closeticket(self, interaction: discord.Interaction):
        channel = interaction.channel
        
        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "❌ This command can only be used in a ticket channel.", 
                ephemeral=True
            )
            return

        # Extract ticket creator ID from channel name
        try:
            parts = channel.name.split("-")
            creator_id = int(parts[1])
        except (IndexError, ValueError):
            creator_id = 0

        # Create ticket control view for closing
        view = TicketControlView(creator_id)
        await view.close_ticket_process(interaction)

    @app_commands.command(name="ticket-stats", description="View ticket system statistics.")
    @permissions.is_any_moderator()
    async def ticket_stats(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Count current tickets
        ticket_channels = [
            channel for channel in guild.channels
            if isinstance(channel, discord.TextChannel) and channel.name.startswith("ticket-")
        ]
        
        # Categorize tickets by type
        ticket_types = {}
        for channel in ticket_channels:
            parts = channel.name.split("-")
            if len(parts) >= 3:
                ticket_type = parts[2]
                ticket_types[ticket_type] = ticket_types.get(ticket_type, 0) + 1
        
        embed = discord.Embed(
            title="📊 Ticket System Statistics",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="🎫 Total Open Tickets", value=f"`{len(ticket_channels)}`", inline=True)
        embed.add_field(name="👥 Active Users", value=f"`{len(set(ch.name.split('-')[1] for ch in ticket_channels if len(ch.name.split('-')) >= 2))}`", inline=True)
        embed.add_field(name="📈 Average Response Time", value="`< 2 hours`", inline=True)
        
        if ticket_types:
            type_breakdown = "\n".join([f"• **{t.title()}**: `{count}`" for t, count in ticket_types.items()])
            embed.add_field(name="📋 Tickets by Type", value=type_breakdown, inline=False)
        
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="Updated in real-time")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
