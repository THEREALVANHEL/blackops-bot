import discord
from discord.ext import commands
from discord import app_commands
import permissions
import asyncio
import time
import database

# Store active events
active_events = {}

class EventJoinView(discord.ui.View):
    def __init__(self, event_id: str, event_data: dict):
        super().__init__(timeout=None)
        self.event_id = event_id
        self.event_data = event_data

    @discord.ui.button(label="Join Event", style=discord.ButtonStyle.green, emoji="✅")
    async def join_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        event = active_events.get(self.event_id)
        if not event:
            await interaction.response.send_message("❌ This event is no longer active!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        if user_id in event["participants"]:
            await interaction.response.send_message("❌ You're already joined this event!", ephemeral=True)
            return
        
        if len(event["participants"]) >= event.get("max_participants", 50):
            await interaction.response.send_message("❌ This event is full!", ephemeral=True)
            return
        
        # Add participant
        event["participants"][user_id] = {
            "name": interaction.user.display_name,
            "joined_at": time.time()
        }
        
        # Update embed
        embed = self.create_event_embed(event, interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation
        await interaction.followup.send(f"✅ **{interaction.user.display_name}** joined the event!", ephemeral=True)

    @discord.ui.button(label="Leave Event", style=discord.ButtonStyle.red, emoji="❌")
    async def leave_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        event = active_events.get(self.event_id)
        if not event:
            await interaction.response.send_message("❌ This event is no longer active!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        if user_id not in event["participants"]:
            await interaction.response.send_message("❌ You're not in this event!", ephemeral=True)
            return
        
        # Remove participant
        del event["participants"][user_id]
        
        # Update embed
        embed = self.create_event_embed(event, interaction.guild)
        await interaction.response.edit_message(embed=embed, view=self)
        
        # Send confirmation
        await interaction.followup.send(f"❌ **{interaction.user.display_name}** left the event!", ephemeral=True)

    @discord.ui.button(label="Event Info", style=discord.ButtonStyle.gray, emoji="ℹ️")
    async def event_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        event = active_events.get(self.event_id)
        if not event:
            await interaction.response.send_message("❌ This event is no longer active!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📋 Event Details: {event['title']}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="📝 Description", value=event["description"], inline=False)
        embed.add_field(name="👑 Host", value=f"<@{event['host_id']}>", inline=True)
        
        if event.get("co_host_id"):
            embed.add_field(name="🤝 Co-Host", value=f"<@{event['co_host_id']}>", inline=True)
        
        embed.add_field(name="⏰ Start Time", value=f"<t:{int(event['start_time'])}:F>", inline=False)
        embed.add_field(name="🕒 Time Until Start", value=f"<t:{int(event['start_time'])}:R>", inline=True)
        embed.add_field(name="👥 Participants", value=f"{len(event['participants'])}/{event.get('max_participants', 50)}", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    def create_event_embed(self, event: dict, guild: discord.Guild) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎉 {event['title']}",
            description=event["description"],
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        
        # Host info
        host = guild.get_member(event["host_id"])
        embed.add_field(name="👑 Host", value=host.mention if host else "Unknown", inline=True)
        
        if event.get("co_host_id"):
            co_host = guild.get_member(event["co_host_id"])
            embed.add_field(name="🤝 Co-Host", value=co_host.mention if co_host else "Unknown", inline=True)
        
        # Timing
        embed.add_field(name="⏰ Starts", value=f"<t:{int(event['start_time'])}:R>", inline=True)
        
        # Participants
        participant_count = len(event["participants"])
        max_participants = event.get("max_participants", 50)
        
        if participant_count > 0:
            participant_list = []
            for user_id, data in list(event["participants"].items())[:10]:  # Show first 10
                participant_list.append(f"• {data['name']}")
            
            participants_text = "\n".join(participant_list)
            if participant_count > 10:
                participants_text += f"\n*...and {participant_count - 10} more*"
        else:
            participants_text = "*No participants yet*"
        
        embed.add_field(
            name=f"👥 Participants ({participant_count}/{max_participants})",
            value=participants_text,
            inline=False
        )
        
        embed.set_footer(text=f"Event ID: {event.get('event_id', 'Unknown')}")
        return embed

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shout", description="Create a detailed event announcement with join system.")
    @app_commands.describe(
        title="Title of the event",
        description="Detailed description of the event",
        start_time="Minutes until event starts (e.g., 30 for 30 minutes)",
        max_participants="Maximum number of participants (default: 50)",
        co_host="Optional co-host for the event",
        medic="Optional medic for the event",
        guide="Optional guide for the event"
    )
    @permissions.is_any_host()
    async def shout(self, interaction: discord.Interaction, title: str, description: str, start_time: int, max_participants: int = 50, co_host: discord.Member = None, medic: discord.Member = None, guide: discord.Member = None):
        
        if start_time < 1 or start_time > 1440:  # 1 minute to 24 hours
            await interaction.response.send_message("❌ Start time must be between 1 and 1440 minutes (24 hours).", ephemeral=True)
            return
        
        if max_participants < 1 or max_participants > 100:
            await interaction.response.send_message("❌ Max participants must be between 1 and 100.", ephemeral=True)
            return
        
        # Create event ID
        event_id = f"event_{int(time.time())}_{interaction.user.id}"
        start_timestamp = time.time() + (start_time * 60)
        
        # Store event data
        event_data = {
            "event_id": event_id,
            "title": title,
            "description": description,
            "host_id": interaction.user.id,
            "co_host_id": co_host.id if co_host else None,
            "medic_id": medic.id if medic else None,
            "guide_id": guide.id if guide else None,
            "start_time": start_timestamp,
            "max_participants": max_participants,
            "participants": {},
            "channel_id": interaction.channel_id,
            "created_at": time.time()
        }
        
        active_events[event_id] = event_data
        
        # Create embed
        embed = discord.Embed(
            title=f"🎉 {title}",
            description=description,
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        # Event details
        embed.add_field(name="👑 Host", value=interaction.user.mention, inline=True)
        if co_host:
            embed.add_field(name="🤝 Co-Host", value=co_host.mention, inline=True)
        if medic:
            embed.add_field(name="🏥 Medic", value=medic.mention, inline=True)
        if guide:
            embed.add_field(name="🗺️ Guide", value=guide.mention, inline=True)
        
        embed.add_field(name="⏰ Starts In", value=f"<t:{int(start_timestamp)}:R>", inline=True)
        embed.add_field(name="📅 Start Time", value=f"<t:{int(start_timestamp)}:F>", inline=True)
        embed.add_field(name="👥 Max Participants", value=f"`{max_participants}` people", inline=True)
        embed.add_field(name="🎯 Status", value="🟢 **OPEN FOR REGISTRATION**", inline=False)
        
        embed.set_footer(text=f"Event ID: {event_id}")
        
        # Create view with join/leave buttons
        view = EventJoinView(event_id, event_data)
        
        await interaction.response.send_message(f"@everyone", embed=embed, view=view)
        
        # Schedule event start notification
        asyncio.create_task(self._schedule_event_start(event_id, start_timestamp, interaction.channel))

    @app_commands.command(name="gamelog", description="Log a completed game with enhanced details.")
    @app_commands.describe(
        game="The name of the game played",
        result="The result of the game (Win/Loss/Draw)",
        participants="Participants in the game",
        image="Optional image URL of game result",
        notes="Optional additional notes about the game"
    )
    @permissions.is_any_host()
    async def gamelog(self, interaction: discord.Interaction, game: str, result: str, participants: str, image: str = None, notes: str = None):
        
        embed = discord.Embed(
            title=f"🎮 Game Log: {game}",
            color=self._get_result_color(result),
            timestamp=discord.utils.utcnow()
        )
        
        # Result with emoji
        result_emoji = "🏆" if "win" in result.lower() else "❌" if "loss" in result.lower() else "🤝"
        embed.add_field(name="📊 Result", value=f"{result_emoji} **{result.upper()}**", inline=True)
        embed.add_field(name="🎯 Game", value=f"`{game}`", inline=True)
        embed.add_field(name="⏰ Date", value=f"<t:{int(time.time())}:F>", inline=True)
        
        embed.add_field(name="👥 Participants", value=participants, inline=False)
        
        if notes:
            embed.add_field(name="📝 Notes", value=notes, inline=False)
        
        if image:
            try:
                embed.set_image(url=image)
            except:
                embed.add_field(name="🖼️ Image", value=f"[View Image]({image})", inline=False)
        
        embed.set_author(name=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Game Statistics • BlackOps Gaming")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="announce", description="Create a professional announcement with points and optional image.")
    @app_commands.describe(
        title="The announcement title",
        content="Main announcement content",
        points="Bullet points separated by | (e.g., Point 1|Point 2|Point 3)",
        image="Optional image URL for the announcement",
        color="Choose announcement color theme"
    )
    @app_commands.choices(
        color=[
            discord.app_commands.Choice(name="🔴 Important (Red)", value="red"),
            discord.app_commands.Choice(name="🟡 Warning (Yellow)", value="yellow"),
            discord.app_commands.Choice(name="🟢 Good News (Green)", value="green"),
            discord.app_commands.Choice(name="🔵 Information (Blue)", value="blue"),
            discord.app_commands.Choice(name="🟣 Special (Purple)", value="purple"),
            discord.app_commands.Choice(name="🟠 Event (Orange)", value="orange")
        ]
    )
    async def announce(self, interaction: discord.Interaction, title: str, content: str, points: str = None, image: str = None, color: str = "blue"):
        
        # Color mapping
        color_map = {
            "red": discord.Color.red(),
            "yellow": discord.Color.yellow(), 
            "green": discord.Color.green(),
            "blue": discord.Color.blue(),
            "purple": discord.Color.purple(),
            "orange": discord.Color.orange()
        }
        
        embed = discord.Embed(
            title=f"📢 {title}",
            description=content.replace("\\n", "\n"),
            color=color_map.get(color, discord.Color.blue()),
            timestamp=discord.utils.utcnow()
        )
        
        # Add points if provided
        if points:
            point_list = points.split("|")
            formatted_points = []
            for i, point in enumerate(point_list[:10], 1):  # Limit to 10 points
                formatted_points.append(f"`{i}.` {point.strip()}")
            
            embed.add_field(
                name="📋 Key Points",
                value="\n".join(formatted_points),
                inline=False
            )
        
        # Add image if provided
        if image:
            try:
                embed.set_image(url=image)
            except:
                embed.add_field(name="🖼️ Image", value=f"[View Image]({image})", inline=False)
        
        embed.set_author(
            name=f"Announcement by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.set_footer(text="BlackOps Official Announcement")
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        
        await interaction.response.send_message("@everyone", embed=embed)

    async def _schedule_event_start(self, event_id: str, start_time: float, channel):
        """Schedule event start notification"""
        await asyncio.sleep(start_time - time.time())
        
        if event_id in active_events:
            event = active_events[event_id]
            
            embed = discord.Embed(
                title="🚀 EVENT STARTING NOW!",
                description=f"**{event['title']}** is beginning!",
                color=discord.Color.red()
            )
            
            participants = event.get("participants", {})
            if participants:
                participant_mentions = [f"<@{uid}>" for uid in participants.keys()]
                embed.add_field(
                    name=f"👥 Participants ({len(participants)})",
                    value=" ".join(participant_mentions[:20]) + ("..." if len(participants) > 20 else ""),
                    inline=False
                )
            
            embed.set_footer(text=f"Event ID: {event_id}")
            
            try:
                await channel.send(embed=embed)
            except:
                pass  # Channel might be deleted or bot lacks permissions
            
            # Remove event from active events after it starts
            del active_events[event_id]

    def _get_result_color(self, result: str) -> discord.Color:
        """Get color based on game result"""
        result_lower = result.lower()
        if "win" in result_lower:
            return discord.Color.green()
        elif "loss" in result_lower or "lose" in result_lower:
            return discord.Color.red()
        else:
            return discord.Color.yellow()

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
