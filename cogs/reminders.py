import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import database


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._task = None
        self._watch_users = set()

    async def cog_load(self):
        try:
            if not self._task or self._task.done():
                self._task = self.bot.loop.create_task(self._scheduler())
        except Exception:
            pass

    @app_commands.command(name="remind", description="Set a reminder. Example: /remind in_minutes:30 text:Drink water")
    @app_commands.describe(in_minutes="How many minutes from now", text="Reminder text")
    async def remind(self, interaction: discord.Interaction, in_minutes: int, text: str):
        if in_minutes < 1 or in_minutes > 60 * 24 * 14:
            await interaction.response.send_message("❌ Minutes must be between 1 and 20160 (14 days).", ephemeral=True)
            return
        remind_at = time.time() + (in_minutes * 60)
        user_id = interaction.user.id
        user_data = database.db.get_user_data(user_id)
        reminders = user_data.get("reminders", [])
        reminders.append({
            "remind_at": remind_at,
            "text": text,
            "channel_id": interaction.channel.id
        })
        database.db.update_user_data(user_id, {"reminders": reminders})
        # ensure scheduler watches this user
        self._watch_users.add(user_id)
        await interaction.response.send_message(f"⏰ I'll remind you in {in_minutes} minutes.")

    async def _scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                now = time.time()
                for uid in list(self._watch_users):
                    user_data = database.db.get_user_data(uid)
                    user_reminders = user_data.get("reminders", [])
                    if not user_reminders:
                        # nothing to watch for this user anymore
                        self._watch_users.discard(uid)
                        continue
                    due = [r for r in user_reminders if r.get("remind_at", 0) <= now]
                    if not due:
                        continue
                    remaining = [r for r in user_reminders if r not in due]
                    database.db.update_user_data(uid, {"reminders": remaining})
                    for r in due:
                        try:
                            channel = self.bot.get_channel(r.get("channel_id"))
                            mention = f"<@{uid}>"
                            msg = f"⏰ {mention} Reminder: {r.get('text','(no text)')}"
                            if channel:
                                await channel.send(msg)
                            else:
                                user_obj = self.bot.get_user(uid)
                                if user_obj:
                                    await user_obj.send(msg)
                        except Exception:
                            pass
            except Exception:
                pass
            await asyncio.sleep(30)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))

