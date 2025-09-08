import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random

PET_TYPES = ["Dog", "Cat", "Dragon", "Phoenix"]

class PetSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pet", description="Manage your pet.")
    async def pet(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])

        if not pets:
            await interaction.response.send_message("You don't have a pet yet! Use `/adopt` to get one.", ephemeral=True)
            return

        # For simplicity, we'll assume a user only has one pet for now.
        pet_data = pets[0]
        pet_name = pet_data.get("name", "Your Pet")
        pet_type = pet_data.get("type", "Unknown")
        hunger = pet_data.get("hunger", 0)
        happiness = pet_data.get("happiness", 0)

        embed = discord.Embed(
            title=f"{pet_name}'s Status",
            description=f"Type: {pet_type}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Hunger", value=f"{hunger}/100", inline=True)
        embed.add_field(name="Happiness", value=f"{happiness}/100", inline=True)
        embed.set_footer(text="Use /feed or /play to interact with your pet.")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="adopt", description="Adopt a new pet.")
    @app_commands.describe(name="The name you want to give your new pet.")
    async def adopt(self, interaction: discord.Interaction, name: str):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])

        if pets:
            await interaction.response.send_message("You already have a pet!", ephemeral=True)
            return
        
        pet_type = random.choice(PET_TYPES)
        pet_data = {
            "name": name,
            "type": pet_type,
            "hunger": 50,
            "happiness": 50
        }

        database.db.add_pet(interaction.user.id, pet_data)

        embed = discord.Embed(
            title="Congratulations!",
            description=f"You have adopted a new **{pet_type}** named **{name}**!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="feed", description="Feed your pet.")
    async def feed(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])

        if not pets:
            await interaction.response.send_message("You don't have a pet to feed!", ephemeral=True)
            return

        pet_data = pets[0]
        pet_name = pet_data.get("name")
        
        current_hunger = pet_data.get("hunger", 0)
        if current_hunger >= 100:
            await interaction.response.send_message(f"{pet_name} is already full!", ephemeral=True)
            return

        new_hunger = min(current_hunger + 25, 100)
        pet_data["hunger"] = new_hunger
        
        database.db.update_user_data(interaction.user.id, {"pets": [pet_data]})
        
        await interaction.response.send_message(f"You fed **{pet_name}**. Their hunger is now {new_hunger}/100.")

    @app_commands.command(name="play", description="Play with your pet.")
    async def play(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])

        if not pets:
            await interaction.response.send_message("You don't have a pet to play with!", ephemeral=True)
            return

        pet_data = pets[0]
        pet_name = pet_data.get("name")

        current_happiness = pet_data.get("happiness", 0)
        if current_happiness >= 100:
            await interaction.response.send_message(f"{pet_name} is already as happy as can be!", ephemeral=True)
            return

        new_happiness = min(current_happiness + 25, 100)
        pet_data["happiness"] = new_happiness

        database.db.update_user_data(interaction.user.id, {"pets": [pet_data]})

        await interaction.response.send_message(f"You played with **{pet_name}**. Their happiness is now {new_happiness}/100.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PetSystem(bot))
