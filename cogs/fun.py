import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_giveaways = {}

    @app_commands.command(name="flip", description="Flip a coin - heads or tails.")
    async def flip(self, interaction: discord.Interaction):
        outcome = random.choice(["Heads", "Tails"])
        await interaction.response.send_message(f"🪙 The coin landed on **{outcome}**!")

    @app_commands.command(name="spinwheel", description="Spin a wheel with up to 10 options and see the pointer.")
    @app_commands.describe(options="Comma-separated options (max 10). If empty, uses defaults.")
    async def spinwheel(self, interaction: discord.Interaction, options: str = None):
        defaults = [
            "Win 500 Coins", "Lose 100 Coins", "Win 100 XP", "Lose 50 XP",
            "Nothing", "Jackpot! (1000 Coins)", "+250 Coins", "-25 XP"
        ]
        choices = [o.strip() for o in options.split(",") if o.strip()] if options else defaults
        choices = choices[:10] if choices else defaults
        winner = random.choice(choices)

        file = None
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io, math
            size = 640
            base = Image.new("RGBA", (size, size), (255, 255, 255, 0))
            wheel = Image.new("RGBA", (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(wheel)
            center = (size // 2, size // 2)
            radius = size // 2 - 10
            n = len(choices)
            # Colors for slices
            palette = [(244, 67, 54), (33, 150, 243), (76, 175, 80), (255, 193, 7), (156, 39, 176), (255, 87, 34), (0, 188, 212), (205, 220, 57), (121, 85, 72), (63, 81, 181)]
            for i, label in enumerate(choices):
                start = 360 * i / n
                end = 360 * (i + 1) / n
                draw.pieslice([(10, 10), (size - 10, size - 10)], start, end, fill=palette[i % len(palette)])
            # Labels (optional minimal)
            font = None
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                pass
            for i, label in enumerate(choices):
                angle = math.radians((360 * (i + 0.5) / n) - 90)
                tx = center[0] + int(math.cos(angle) * (radius * 0.6))
                ty = center[1] + int(math.sin(angle) * (radius * 0.6))
                draw.text((tx - 20, ty - 8), label[:12], fill=(255, 255, 255), font=font)
            # Rotate wheel so that winner is at the top under the pointer
            winner_index = choices.index(winner)
            winner_center_angle = (360 * (winner_index + 0.5) / n)
            # We want winner center at 90 degrees (top). PIL rotates counter-clockwise.
            rotate_deg = 90 - winner_center_angle
            rotated = wheel.rotate(rotate_deg, resample=Image.BICUBIC)
            # Draw pointer on base image at the top
            base.paste(rotated, (0, 0), rotated)
            pointer_draw = ImageDraw.Draw(base)
            pointer = [(center[0] - 12, 6), (center[0] + 12, 6), (center[0], 48)]
            pointer_draw.polygon(pointer, fill=(0, 0, 0, 255))
            # Export image
            buf = io.BytesIO()
            base.save(buf, format="PNG")
            buf.seek(0)
            file = discord.File(buf, filename="wheel.png")
        except Exception:
            file = None

        embed = discord.Embed(title="🎡 Spin The Wheel", description="Good luck!", color=discord.Color.yellow())
        embed.add_field(name="Options", value="\n".join([f"• {c}" for c in choices]), inline=False)
        embed.add_field(name="Winner", value=f"🎉 **{winner}**", inline=False)
        if file:
            embed.set_image(url="attachment://wheel.png")
        await interaction.response.send_message(embed=embed, file=file if file else None)
        
    @app_commands.command(name="rps", description="Challenge another user to Rock-Paper-Scissors.")
    @app_commands.describe(opponent="The user you want to challenge")
    async def rps(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ Pick a different human opponent.", ephemeral=True)
            return
        view = Fun.RPSDuelView(interaction.user.id, opponent.id, timeout=120)
        embed = discord.Embed(title="🪨📄✂️ RPS Duel", description=f"{interaction.user.mention} vs {opponent.mention}\nPick your move using the buttons below.", color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed, view=view)
        try:
            view.message = await interaction.original_response()
        except Exception:
            pass

    # ==================== USER-VS-USER RPS DUEL ====================
    class RPSDuelView(discord.ui.View):
        def __init__(self, challenger_id: int, opponent_id: int, timeout: float = 60.0):
            super().__init__(timeout=timeout)
            self.challenger_id = challenger_id
            self.opponent_id = opponent_id
            self.choices = {}
            self.message = None
        
        async def _record_choice(self, interaction: discord.Interaction, user_choice: str):
            if interaction.user.id not in (self.challenger_id, self.opponent_id):
                await interaction.response.send_message("❌ You're not part of this duel.", ephemeral=True)
                return
            self.choices[interaction.user.id] = user_choice
            await interaction.response.send_message(f"✅ Choice locked.", ephemeral=True)
            if len(self.choices) == 2 and self.message:
                await self._resolve(interaction)
        
        async def _resolve(self, interaction: discord.Interaction):
            win_map = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
            c_choice = self.choices.get(self.challenger_id)
            o_choice = self.choices.get(self.opponent_id)
            if not c_choice or not o_choice:
                return
            if c_choice == o_choice:
                result = "It's a draw!"
                color = discord.Color.grey()
            elif win_map[c_choice] == o_choice:
                result = "Challenger wins!"
                color = discord.Color.green()
            else:
                result = "Opponent wins!"
                color = discord.Color.red()
            embed = discord.Embed(title="🪨📄✂️ RPS Duel Result", color=color, timestamp=datetime.now(datetime.UTC))
            embed.add_field(name="Challenger", value=c_choice.title(), inline=True)
            embed.add_field(name="Opponent", value=o_choice.title(), inline=True)
            embed.set_footer(text=result)
            for item in self.children:
                item.disabled = True
            await self.message.edit(embed=embed, view=self)
            self.stop()
        
        @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.secondary)
        async def choose_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._record_choice(interaction, "rock")
        
        @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.secondary)
        async def choose_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._record_choice(interaction, "paper")
        
        @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.secondary)
        async def choose_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._record_choice(interaction, "scissors")

    @app_commands.command(name="rpsduel", description="Challenge another user to Rock-Paper-Scissors.")
    @app_commands.describe(opponent="The user you want to challenge")
    async def rps_duel(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ Pick a different human opponent.", ephemeral=True)
            return
        view = Fun.RPSDuelView(interaction.user.id, opponent.id, timeout=120)
        embed = discord.Embed(title="🪨📄✂️ RPS Duel", description=f"{interaction.user.mention} vs {opponent.mention}\nPick your move using the buttons below.", color=discord.Color.blurple())
        msg = await interaction.response.send_message(embed=embed, view=view)
        try:
            # capture message reference for editing later
            view.message = await interaction.original_response()
        except Exception:
            pass

    # ==================== GIVEAWAY ====================
    class GiveawayView(discord.ui.View):
        def __init__(self, host_id: int, ends_at: float):
            super().__init__(timeout=None)
            self.host_id = host_id
            self.ends_at = ends_at
            self.participants = set()
            self.message = None
        
        @discord.ui.button(label="🎉 Join Giveaway", style=discord.ButtonStyle.success)
        async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.bot:
                await interaction.response.send_message("Bots cannot join.", ephemeral=True)
                return
            self.participants.add(interaction.user.id)
            await interaction.response.send_message("✅ You're in!", ephemeral=True)

    @app_commands.command(name="giveaway", description="Start a giveaway with a join button.")
    @app_commands.describe(duration_minutes="Minutes until it ends", prize="Prize description")
    async def giveaway(self, interaction: discord.Interaction, duration_minutes: int, prize: str):
        if duration_minutes < 1 or duration_minutes > 1440:
            await interaction.response.send_message("❌ Duration must be 1-1440 minutes.", ephemeral=True)
            return
        ends_at = asyncio.get_event_loop().time() + duration_minutes * 60
        view = Fun.GiveawayView(interaction.user.id, ends_at)
        embed = discord.Embed(title="🎉 Giveaway!", description=f"Prize: **{prize}**\nEnds: <t:{int(datetime.now(datetime.UTC).timestamp() + duration_minutes*60)}:R>", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=view)
        view.message = await interaction.original_response()
        async def conclude():
            await asyncio.sleep(duration_minutes * 60)
            if not view.participants:
                result = discord.Embed(title="🎉 Giveaway Ended", description="No valid participants.", color=discord.Color.red())
                await view.message.edit(embed=result, view=None)
                return
            import random as _r
            winner_id = _r.choice(list(view.participants))
            result = discord.Embed(title="🎉 Giveaway Winner!", description=f"Winner: <@{winner_id}>\nPrize: **{prize}**", color=discord.Color.green())
            await view.message.edit(embed=result, view=None)
        self.bot.loop.create_task(conclude())
        
    @app_commands.command(name="trivia", description="Start a trivia game.")
    async def trivia(self, interaction: discord.Interaction):
        # Placeholder for Trivia command
        await interaction.response.send_message("This command is under development!")
        
    @app_commands.command(name="tournament", description="Start a new tournament.")
    async def tournament(self, interaction: discord.Interaction):
        # Placeholder for Tournament command
        await interaction.response.send_message("This command is under development!")

    @app_commands.command(name="wordchain", description="Start a game of wordchain.")
    async def wordchain(self, interaction: discord.Interaction):
        # Placeholder for Wordchain command
        await interaction.response.send_message("This command is under development!")

    @app_commands.command(name="dailychallenge", description="Participate in the daily challenge.")
    async def dailychallenge(self, interaction: discord.Interaction):
        # Placeholder for Daily Challenge command
        await interaction.response.send_message("This command is under development!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
