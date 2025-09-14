import discord
from discord.ext import commands
from discord import app_commands
import database
import time
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Enhanced pet types with stats and rarities
PET_SPECIES = {
    "common": {
        "Dog": {"emoji": "🐕", "base_stats": {"hp": 100, "attack": 20, "defense": 15, "speed": 10}, "evolution": "Wolf"},
        "Cat": {"emoji": "🐱", "base_stats": {"hp": 80, "attack": 25, "defense": 10, "speed": 20}, "evolution": "Tiger"},
        "Bird": {"emoji": "🐦", "base_stats": {"hp": 60, "attack": 15, "defense": 8, "speed": 30}, "evolution": "Eagle"},
        "Fish": {"emoji": "🐠", "base_stats": {"hp": 50, "attack": 10, "defense": 12, "speed": 25}, "evolution": "Shark"}
    },
    "uncommon": {
        "Wolf": {"emoji": "🐺", "base_stats": {"hp": 150, "attack": 35, "defense": 25, "speed": 20}, "evolution": "Werewolf"},
        "Tiger": {"emoji": "🐅", "base_stats": {"hp": 120, "attack": 45, "defense": 20, "speed": 30}, "evolution": "Saber Tiger"},
        "Eagle": {"emoji": "🦅", "base_stats": {"hp": 100, "attack": 30, "defense": 15, "speed": 50}, "evolution": "Phoenix"},
        "Shark": {"emoji": "🦈", "base_stats": {"hp": 130, "attack": 40, "defense": 25, "speed": 35}, "evolution": "Megalodon"}
    },
    "rare": {
        "Werewolf": {"emoji": "🐺", "base_stats": {"hp": 200, "attack": 55, "defense": 40, "speed": 35}, "evolution": None},
        "Saber Tiger": {"emoji": "🐅", "base_stats": {"hp": 180, "attack": 65, "defense": 30, "speed": 45}, "evolution": None},
        "Phoenix": {"emoji": "🔥", "base_stats": {"hp": 160, "attack": 50, "defense": 25, "speed": 70}, "evolution": None},
        "Megalodon": {"emoji": "🦈", "base_stats": {"hp": 220, "attack": 60, "defense": 45, "speed": 40}, "evolution": None}
    },
    "legendary": {
        "Dragon": {"emoji": "🐉", "base_stats": {"hp": 300, "attack": 80, "defense": 60, "speed": 50}, "evolution": None},
        "Unicorn": {"emoji": "🦄", "base_stats": {"hp": 250, "attack": 60, "defense": 50, "speed": 80}, "evolution": None},
        "Kraken": {"emoji": "🐙", "base_stats": {"hp": 350, "attack": 90, "defense": 70, "speed": 30}, "evolution": None},
        "Griffin": {"emoji": "🦅", "base_stats": {"hp": 280, "attack": 70, "defense": 55, "speed": 60}, "evolution": None}
    },
    "mythic": {
        "Celestial Dragon": {"emoji": "✨", "base_stats": {"hp": 500, "attack": 120, "defense": 100, "speed": 80}, "evolution": None},
        "Shadow Beast": {"emoji": "👹", "base_stats": {"hp": 450, "attack": 140, "defense": 80, "speed": 90}, "evolution": None},
        "Crystal Phoenix": {"emoji": "💎", "base_stats": {"hp": 400, "attack": 100, "defense": 90, "speed": 120}, "evolution": None}
    }
}

# Pet personalities affecting behavior and stats
PET_PERSONALITIES = {
    "Brave": {"attack": 1.2, "defense": 0.9, "description": "Courageous in battle"},
    "Timid": {"attack": 0.8, "defense": 1.1, "description": "Cautious and defensive"},
    "Energetic": {"speed": 1.3, "hp": 0.9, "description": "Full of energy and speed"},
    "Lazy": {"speed": 0.7, "hp": 1.2, "description": "Slow but sturdy"},
    "Intelligent": {"attack": 1.1, "defense": 1.1, "description": "Smart and adaptable"},
    "Aggressive": {"attack": 1.3, "defense": 0.8, "description": "Fierce and offensive"},
    "Gentle": {"hp": 1.2, "attack": 0.9, "description": "Kind and resilient"},
    "Playful": {"speed": 1.1, "hp": 1.1, "description": "Fun-loving and healthy"}
}

# Activities that affect pet happiness and stats
PET_ACTIVITIES = {
    "training": {"cost": 100, "happiness": -5, "stat_boost": "attack", "boost_amount": 2, "description": "Increase attack power"},
    "playing": {"cost": 50, "happiness": 15, "stat_boost": "hp", "boost_amount": 1, "description": "Increase happiness and HP"},
    "grooming": {"cost": 75, "happiness": 10, "stat_boost": "defense", "boost_amount": 1, "description": "Increase defense and happiness"},
    "racing": {"cost": 80, "happiness": 5, "stat_boost": "speed", "boost_amount": 2, "description": "Increase speed"},
    "meditation": {"cost": 120, "happiness": 8, "stat_boost": "all", "boost_amount": 1, "description": "Small boost to all stats"}
}

class PetBattleView(discord.ui.View):
    def __init__(self, challenger_id: int, opponent_id: int, challenger_pet: dict, opponent_pet: dict):
        super().__init__(timeout=120)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.challenger_pet = challenger_pet
        self.opponent_pet = opponent_pet
        self.battle_accepted = False

    @discord.ui.button(label="Accept Battle", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Only the challenged player can accept this battle!", ephemeral=True)
            return
        
        self.battle_accepted = True
        await self.simulate_battle(interaction)

    @discord.ui.button(label="Decline Battle", style=discord.ButtonStyle.red, emoji="❌")
    async def decline_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message("❌ Only the challenged player can decline this battle!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🚫 Battle Declined",
            description=f"{interaction.user.display_name} declined the battle challenge.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def simulate_battle(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Battle simulation
        c_pet = self.challenger_pet.copy()
        o_pet = self.opponent_pet.copy()
        
        battle_log = []
        turn = 1
        
        # Determine turn order based on speed
        if c_pet["stats"]["speed"] >= o_pet["stats"]["speed"]:
            first_pet, second_pet = c_pet, o_pet
            first_user, second_user = self.challenger_id, self.opponent_id
        else:
            first_pet, second_pet = o_pet, c_pet
            first_user, second_user = self.opponent_id, self.challenger_id
        
        while first_pet["current_hp"] > 0 and second_pet["current_hp"] > 0 and turn <= 20:
            # First pet attacks
            if first_pet["current_hp"] > 0:
                damage = self.calculate_damage(first_pet, second_pet)
                second_pet["current_hp"] -= damage
                battle_log.append(f"Turn {turn}: {first_pet['name']} deals {damage} damage!")
                
                if second_pet["current_hp"] <= 0:
                    break
            
            # Second pet attacks
            if second_pet["current_hp"] > 0:
                damage = self.calculate_damage(second_pet, first_pet)
                first_pet["current_hp"] -= damage
                battle_log.append(f"Turn {turn}: {second_pet['name']} deals {damage} damage!")
            
            turn += 1
        
        # Determine winner
        if first_pet["current_hp"] > 0:
            winner_pet = first_pet
            winner_id = first_user
            loser_pet = second_pet
            loser_id = second_user
        elif second_pet["current_hp"] > 0:
            winner_pet = second_pet
            winner_id = second_user
            loser_pet = first_pet
            loser_id = first_user
        else:
            # Draw
            winner_pet = None
            winner_id = None
        
        # Create battle result embed
        embed = discord.Embed(
            title="⚔️ Pet Battle Results!",
            timestamp=datetime.utcnow()
        )
        
        if winner_pet:
            winner_user = interaction.guild.get_member(winner_id)
            loser_user = interaction.guild.get_member(loser_id)
            
            embed.color = discord.Color.gold()
            embed.add_field(
                name="🏆 Winner",
                value=f"{winner_user.display_name}'s {winner_pet['species']} {winner_pet['emoji']}\n**{winner_pet['name']}**",
                inline=True
            )
            embed.add_field(
                name="💔 Defeated",
                value=f"{loser_user.display_name}'s {loser_pet['species']} {loser_pet['emoji']}\n**{loser_pet['name']}**",
                inline=True
            )
            
            # Award experience and coins
            exp_gained = random.randint(50, 100)
            coins_won = random.randint(100, 500)
            
            # Update winner's pet
            self.update_pet_after_battle(winner_id, winner_pet, exp_gained, True)
            # Update loser's pet (less exp)
            self.update_pet_after_battle(loser_id, loser_pet, exp_gained // 2, False)
            
            database.db.add_coins(winner_id, coins_won)
            
            embed.add_field(
                name="💰 Rewards",
                value=f"**Winner:** {coins_won} coins, {exp_gained} exp\n**Loser:** {exp_gained//2} exp",
                inline=False
            )
        else:
            embed.color = discord.Color.orange()
            embed.add_field(name="🤝 Result", value="It's a draw! Both pets fought valiantly.", inline=False)
        
        # Show battle log (last 5 turns)
        if battle_log:
            log_text = "\n".join(battle_log[-5:])
            embed.add_field(name="📜 Battle Log (Last 5 Actions)", value=f"```{log_text}```", inline=False)
        
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, view=None)

    def calculate_damage(self, attacker: dict, defender: dict) -> int:
        """Calculate battle damage"""
        base_damage = attacker["stats"]["attack"]
        defense = defender["stats"]["defense"]
        
        # Add some randomness
        damage_roll = random.uniform(0.8, 1.2)
        critical = random.random() < 0.1  # 10% crit chance
        
        damage = int((base_damage - defense * 0.5) * damage_roll)
        if critical:
            damage = int(damage * 1.5)
        
        return max(1, damage)  # Minimum 1 damage

    def update_pet_after_battle(self, user_id: int, pet: dict, exp: int, won: bool):
        """Update pet stats after battle"""
        user_data = database.db.get_user_data(user_id)
        pets = user_data.get("pets", [])
        
        for i, p in enumerate(pets):
            if p.get("pet_id") == pet.get("pet_id"):
                pets[i]["experience"] = pets[i].get("experience", 0) + exp
                pets[i]["battles_won"] = pets[i].get("battles_won", 0) + (1 if won else 0)
                pets[i]["battles_total"] = pets[i].get("battles_total", 0) + 1
                
                # Level up check
                new_level = self.calculate_level(pets[i]["experience"])
                if new_level > pets[i].get("level", 1):
                    pets[i]["level"] = new_level
                    # Stat boost on level up
                    for stat in pets[i]["stats"]:
                        pets[i]["stats"][stat] += random.randint(1, 3)
                
                break
        
        database.db.update_user_data(user_id, {"pets": pets})

    def calculate_level(self, experience: int) -> int:
        """Calculate pet level from experience"""
        return min(100, int((experience / 100) ** 0.5) + 1)

class PetAdoptionView(discord.ui.View):
    def __init__(self, user_id: int, available_pets: List[dict]):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.available_pets = available_pets
        
        # Add pet selection dropdown
        options = []
        for i, pet_info in enumerate(available_pets):
            rarity = pet_info["rarity"]
            species = pet_info["species"]
            pet_data = PET_SPECIES[rarity][species]
            
            options.append(discord.SelectOption(
                label=f"{species} ({rarity.title()})",
                value=str(i),
                emoji=pet_data["emoji"],
                description=f"HP: {pet_data['base_stats']['hp']}, ATK: {pet_data['base_stats']['attack']}"
            ))
        
        self.pet_select = discord.ui.Select(
            placeholder="Choose a pet to adopt...",
            options=options,
            min_values=1,
            max_values=1
        )
        self.pet_select.callback = self.pet_selected
        self.add_item(self.pet_select)

    async def pet_selected(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your adoption center!", ephemeral=True)
            return
        
        selected_index = int(self.pet_select.values[0])
        selected_pet_info = self.available_pets[selected_index]
        
        # Show pet naming modal
        class PetNamingModal(discord.ui.Modal):
            def __init__(self, pet_info):
                super().__init__(title=f"Name your {pet_info['species']}")
                self.pet_info = pet_info
            
            pet_name = discord.ui.TextInput(
                label="Pet Name",
                placeholder="Enter a name for your new pet...",
                required=True,
                max_length=20
            )
            
            async def on_submit(self, modal_interaction):
                await self.adopt_pet(modal_interaction, self.pet_name.value)
            
            async def adopt_pet(self, modal_interaction, name: str):
                rarity = self.pet_info["rarity"]
                species = self.pet_info["species"]
                personality = random.choice(list(PET_PERSONALITIES.keys()))
                
                # Create new pet
                pet_data = PET_SPECIES[rarity][species]
                base_stats = pet_data["base_stats"].copy()
                
                # Apply personality modifiers
                personality_mods = PET_PERSONALITIES[personality]
                for stat, multiplier in personality_mods.items():
                    if stat in base_stats:
                        base_stats[stat] = int(base_stats[stat] * multiplier)
                
                new_pet = {
                    "pet_id": f"{interaction.user.id}_{int(time.time())}",
                    "name": name,
                    "species": species,
                    "rarity": rarity,
                    "emoji": pet_data["emoji"],
                    "personality": personality,
                    "level": 1,
                    "experience": 0,
                    "stats": base_stats,
                    "current_hp": base_stats["hp"],
                    "happiness": 50,
                    "hunger": 50,
                    "energy": 100,
                    "last_fed": time.time(),
                    "last_played": time.time(),
                    "battles_won": 0,
                    "battles_total": 0,
                    "breeding_available": True,
                    "achievements": [],
                    "adopted_date": datetime.utcnow().timestamp()
                }
                
                # Add pet to user's collection
                user_data = database.db.get_user_data(interaction.user.id)
                pets = user_data.get("pets", [])
                pets.append(new_pet)
                database.db.update_user_data(interaction.user.id, {"pets": pets})
                
                embed = discord.Embed(
                    title="🎉 Pet Adopted Successfully!",
                    description=f"**{interaction.user.display_name}** adopted a {rarity} **{species}**!",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                embed.add_field(name="🐾 Name", value=name, inline=True)
                embed.add_field(name="🎭 Personality", value=f"{personality} - {PET_PERSONALITIES[personality]['description']}", inline=True)
                embed.add_field(name="⭐ Rarity", value=rarity.title(), inline=True)
                
                # Show stats
                stats_text = "\n".join([f"**{stat.upper()}:** {value}" for stat, value in base_stats.items()])
                embed.add_field(name="📊 Base Stats", value=stats_text, inline=False)
                
                embed.add_field(name="💡 Next Steps", value="Use `/pet` to view your new companion!\nUse `/pet feed` and `/pet play` to keep them happy!", inline=False)
                embed.set_footer(text="Welcome to your new adventure together!")
                
                await modal_interaction.response.edit_message(embed=embed, view=None)
        
        await interaction.response.send_modal(PetNamingModal(selected_pet_info))

class EnhancedPetSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="adopt", description="Adopt a new pet companion with advanced features.")
    async def adopt(self, interaction: discord.Interaction):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])
        
        # Check pet limit
        max_pets = 5 + (user_data.get("level", 1) // 10)  # More pets with higher level
        if len(pets) >= max_pets:
            await interaction.response.send_message(f"❌ You can only have {max_pets} pets! Level up to increase your limit.", ephemeral=True)
            return
        
        # Check adoption cost
        adoption_cost = 1000
        if user_data.get("coins", 0) < adoption_cost:
            await interaction.response.send_message(f"❌ Adoption costs {adoption_cost} coins. You need {adoption_cost - user_data.get('coins', 0)} more coins.", ephemeral=True)
            return
        
        # Generate available pets based on rarity chances
        rarity_chances = {"common": 0.5, "uncommon": 0.3, "rare": 0.15, "legendary": 0.04, "mythic": 0.01}
        available_pets = []
        
        for _ in range(3):  # Offer 3 random pets
            roll = random.random()
            cumulative = 0
            selected_rarity = "common"
            
            for rarity, chance in rarity_chances.items():
                cumulative += chance
                if roll <= cumulative:
                    selected_rarity = rarity
                    break
            
            species_list = list(PET_SPECIES[selected_rarity].keys())
            selected_species = random.choice(species_list)
            
            available_pets.append({
                "rarity": selected_rarity,
                "species": selected_species,
                "cost": adoption_cost * ({"common": 1, "uncommon": 2, "rare": 4, "legendary": 8, "mythic": 15}[selected_rarity])
            })
        
        embed = discord.Embed(
            title="🏠 Pet Adoption Center",
            description="Welcome to the adoption center! Choose a pet to become your companion.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🎯 Your Stats",
            value=f"**Current Pets:** {len(pets)}/{max_pets}\n**Coins:** {user_data.get('coins', 0):,}",
            inline=True
        )
        
        embed.add_field(
            name="📋 Available Today",
            value="Select from the pets below using the dropdown menu!",
            inline=False
        )
        
        for i, pet_info in enumerate(available_pets):
            rarity = pet_info["rarity"]
            species = pet_info["species"]
            pet_data = PET_SPECIES[rarity][species]
            cost = pet_info["cost"]
            
            rarity_color = {"common": "🟢", "uncommon": "🟡", "rare": "🟠", "legendary": "🟣", "mythic": "✨"}[rarity]
            
            embed.add_field(
                name=f"{pet_data['emoji']} {species} {rarity_color}",
                value=f"**Rarity:** {rarity.title()}\n**Cost:** {cost:,} coins\n**Base HP:** {pet_data['base_stats']['hp']}",
                inline=True
            )
        
        embed.set_footer(text="Each pet comes with a unique personality that affects their stats!")
        
        # Deduct adoption fee
        database.db.remove_coins(interaction.user.id, adoption_cost)
        
        view = PetAdoptionView(interaction.user.id, available_pets)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="pet", description="View and manage your pet companions.")
    @app_commands.describe(action="Action to perform with your pet", pet_name="Name of the pet (if you have multiple)")
    @app_commands.choices(
        action=[
            discord.app_commands.Choice(name="📊 View Status", value="status"),
            discord.app_commands.Choice(name="🍖 Feed Pet", value="feed"),
            discord.app_commands.Choice(name="🎾 Play", value="play"),
            discord.app_commands.Choice(name="🏃 Train", value="train"),
            discord.app_commands.Choice(name="✨ Groom", value="groom"),
            discord.app_commands.Choice(name="🏁 Race", value="race"),
            discord.app_commands.Choice(name="🧘 Meditate", value="meditate")
        ]
    )
    async def pet_command(self, interaction: discord.Interaction, action: str = "status", pet_name: str = None):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])
        
        if not pets:
            embed = discord.Embed(
                title="🏠 No Pets Found",
                description="You don't have any pets yet! Use `/adopt` to get your first companion.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Select pet
        if pet_name:
            selected_pet = next((p for p in pets if p["name"].lower() == pet_name.lower()), None)
            if not selected_pet:
                await interaction.response.send_message(f"❌ You don't have a pet named '{pet_name}'.", ephemeral=True)
                return
        else:
            # If no pet specified and action is status, show a list of pets
            if action == "status":
                embed = discord.Embed(
                    title=f"🐾 {interaction.user.display_name}'s Pets",
                    description="Choose a pet name with `/pet status <pet_name>` or use the dropdown below in future updates.",
                    color=discord.Color.blurple(),
                    timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=interaction.user.display_avatar.url)
                pet_lines = []
                for p in pets:
                    pet_lines.append(f"{p.get('emoji','🐾')} **{p.get('name','Unnamed')}** — {p.get('species','Unknown')} (Lv.{p.get('level',1)})")
                embed.add_field(name="Your Pets", value="\n".join(pet_lines[:15]), inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            selected_pet = pets[0]  # Default to first pet for other actions
        
        if action == "status":
            await self.show_pet_status(interaction, selected_pet, pets)
        elif action in ["feed", "play", "train", "groom", "race", "meditate"]:
            await self.perform_pet_activity(interaction, selected_pet, action)

    async def show_pet_status(self, interaction: discord.Interaction, pet: dict, all_pets: list):
        embed = discord.Embed(
            title=f"{pet['emoji']} {pet['name']}'s Profile",
            description=f"**{pet['species']}** • Level {pet.get('level', 1)} • {pet['rarity'].title()}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Pet status bars
        happiness = pet.get("happiness", 50)
        hunger = pet.get("hunger", 50)
        energy = pet.get("energy", 100)
        
        status_bars = self.create_status_bars(happiness, hunger, energy)
        embed.add_field(name="💖 Status", value=status_bars, inline=False)
        
        # Stats
        stats = pet.get("stats", {})
        stats_text = "\n".join([f"**{stat.upper()}:** {value}" for stat, value in stats.items()])
        embed.add_field(name="📊 Stats", value=stats_text, inline=True)
        
        # Battle record
        battles_won = pet.get("battles_won", 0)
        battles_total = pet.get("battles_total", 0)
        win_rate = (battles_won / battles_total * 100) if battles_total > 0 else 0
        
        embed.add_field(
            name="⚔️ Battle Record",
            value=f"**Wins:** {battles_won}\n**Total:** {battles_total}\n**Win Rate:** {win_rate:.1f}%",
            inline=True
        )
        
        # Experience and personality
        experience = pet.get("experience", 0)
        next_level_exp = (pet.get("level", 1) ** 2) * 100
        personality = pet.get("personality", "Unknown")
        
        embed.add_field(
            name="🎭 Details",
            value=f"**Personality:** {personality}\n**Experience:** {experience:,}/{next_level_exp:,}\n**Adopted:** <t:{int(pet.get('adopted_date', time.time()))}:R>",
            inline=False
        )
        
        # Show evolution path
        current_species = pet["species"]
        evolution_info = ""
        for rarity, species_dict in PET_SPECIES.items():
            if current_species in species_dict:
                evolution = species_dict[current_species].get("evolution")
                if evolution:
                    evolution_info = f"**Next Evolution:** {evolution} (Level {pet.get('level', 1) + 10})"
                break
        
        if evolution_info:
            embed.add_field(name="🔄 Evolution", value=evolution_info, inline=False)
        
        # Show all pets if user has multiple
        if len(all_pets) > 1:
            other_pets = [f"{p['emoji']} {p['name']} (Lv.{p.get('level', 1)})" for p in all_pets if p != pet]
            embed.add_field(name="🐾 Other Pets", value="\n".join(other_pets[:5]), inline=False)
        
        embed.set_footer(text="Use /pet <action> <pet_name> to interact with your pets!")
        await interaction.response.send_message(embed=embed)

    async def perform_pet_activity(self, interaction: discord.Interaction, pet: dict, activity: str):
        user_data = database.db.get_user_data(interaction.user.id)
        
        if activity not in PET_ACTIVITIES:
            await interaction.response.send_message("❌ Invalid activity.", ephemeral=True)
            return
        
        activity_data = PET_ACTIVITIES[activity]
        cost = activity_data["cost"]
        
        # Check if user can afford the activity
        if user_data.get("coins", 0) < cost:
            await interaction.response.send_message(f"❌ {activity.title()} costs {cost} coins. You need {cost - user_data.get('coins', 0)} more coins.", ephemeral=True)
            return
        
        # Check cooldowns
        last_activity_key = f"last_{activity}"
        last_activity_time = pet.get(last_activity_key, 0)
        cooldown = 3600  # 1 hour cooldown for most activities
        
        if activity == "play":
            cooldown = 1800  # 30 minutes for playing
        elif activity == "feed":
            cooldown = 7200  # 2 hours for feeding
        
        if time.time() - last_activity_time < cooldown:
            next_time = last_activity_time + cooldown
            await interaction.response.send_message(f"⏰ You need to wait until <t:{int(next_time)}:R> before {activity}ing {pet['name']} again.", ephemeral=True)
            return
        
        # Perform activity
        database.db.remove_coins(interaction.user.id, cost)
        
        # Update pet stats
        pets = user_data.get("pets", [])
        for i, p in enumerate(pets):
            if p.get("pet_id") == pet.get("pet_id"):
                # Update happiness
                pets[i]["happiness"] = min(100, pets[i].get("happiness", 50) + activity_data["happiness"])
                
                # Update last activity time
                pets[i][last_activity_key] = time.time()
                
                # Apply stat boost
                stat_boost = activity_data["stat_boost"]
                boost_amount = activity_data["boost_amount"]
                
                if stat_boost == "all":
                    for stat in pets[i]["stats"]:
                        pets[i]["stats"][stat] += boost_amount
                elif stat_boost in pets[i]["stats"]:
                    pets[i]["stats"][stat_boost] += boost_amount
                
                # Special effects for feeding
                if activity == "feed":
                    pets[i]["hunger"] = min(100, pets[i].get("hunger", 50) + 30)
                    pets[i]["energy"] = min(100, pets[i].get("energy", 100) + 20)
                
                break
        
        database.db.update_user_data(interaction.user.id, {"pets": pets})
        
        embed = discord.Embed(
            title=f"{pet['emoji']} {activity.title()} Complete!",
            description=f"You spent time {activity}ing with **{pet['name']}**!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="💰 Cost", value=f"{cost} coins", inline=True)
        embed.add_field(name="😊 Happiness", value=f"{activity_data['happiness']:+} points", inline=True)
        embed.add_field(name="📈 Stat Boost", value=f"{stat_boost.title()}: +{boost_amount}", inline=True)
        embed.add_field(name="📝 Effect", value=activity_data["description"], inline=False)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"{pet['name']} enjoyed spending time with you!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="petbattle", description="Challenge another user's pet to battle!")
    @app_commands.describe(opponent="The user you want to challenge", your_pet="Name of your pet", opponent_pet="Name of their pet (optional)")
    async def pet_battle(self, interaction: discord.Interaction, opponent: discord.Member, your_pet: str, opponent_pet: str = None):
        if opponent.id == interaction.user.id:
            await interaction.response.send_message("❌ You can't battle yourself!", ephemeral=True)
            return
        
        if opponent.bot:
            await interaction.response.send_message("❌ You can't battle bots!", ephemeral=True)
            return
        
        # Get challenger's pet
        user_data = database.db.get_user_data(interaction.user.id)
        user_pets = user_data.get("pets", [])
        challenger_pet = next((p for p in user_pets if p["name"].lower() == your_pet.lower()), None)
        
        if not challenger_pet:
            await interaction.response.send_message(f"❌ You don't have a pet named '{your_pet}'.", ephemeral=True)
            return
        
        # Check if pet is healthy enough to battle
        if challenger_pet.get("happiness", 50) < 30:
            await interaction.response.send_message(f"❌ {challenger_pet['name']} is too unhappy to battle! Use `/pet play` to cheer them up.", ephemeral=True)
            return
        
        # Get opponent's pet
        opponent_data = database.db.get_user_data(opponent.id)
        opponent_pets = opponent_data.get("pets", [])
        
        if not opponent_pets:
            await interaction.response.send_message(f"❌ {opponent.display_name} doesn't have any pets!", ephemeral=True)
            return
        
        if opponent_pet:
            selected_opponent_pet = next((p for p in opponent_pets if p["name"].lower() == opponent_pet.lower()), None)
            if not selected_opponent_pet:
                await interaction.response.send_message(f"❌ {opponent.display_name} doesn't have a pet named '{opponent_pet}'.", ephemeral=True)
                return
        else:
            # Use their strongest pet
            selected_opponent_pet = max(opponent_pets, key=lambda p: sum(p.get("stats", {}).values()))
        
        # Initialize battle HP
        challenger_pet["current_hp"] = challenger_pet["stats"]["hp"]
        selected_opponent_pet["current_hp"] = selected_opponent_pet["stats"]["hp"]
        
        embed = discord.Embed(
            title="⚔️ Pet Battle Challenge!",
            description=f"**{interaction.user.display_name}** challenges **{opponent.display_name}** to a pet battle!",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name=f"{challenger_pet['emoji']} Challenger",
            value=f"**{challenger_pet['name']}** (Lv.{challenger_pet.get('level', 1)})\n{challenger_pet['species']} • {challenger_pet['rarity'].title()}",
            inline=True
        )
        
        embed.add_field(
            name=f"{selected_opponent_pet['emoji']} Defender", 
            value=f"**{selected_opponent_pet['name']}** (Lv.{selected_opponent_pet.get('level', 1)})\n{selected_opponent_pet['species']} • {selected_opponent_pet['rarity'].title()}",
            inline=True
        )
        
        embed.add_field(name="🏆 Stakes", value="Winner gets coins and experience!\nLoser gets participation experience.", inline=False)
        embed.set_footer(text="Battle will begin once accepted!")
        
        view = PetBattleView(interaction.user.id, opponent.id, challenger_pet, selected_opponent_pet)
        await interaction.response.send_message(f"{opponent.mention}, you've been challenged to a pet battle!", embed=embed, view=view)

    @app_commands.command(name="evolve", description="Evolve your pet to its next form!")
    @app_commands.describe(pet_name="Name of the pet you want to evolve")
    async def evolve_pet(self, interaction: discord.Interaction, pet_name: str):
        user_data = database.db.get_user_data(interaction.user.id)
        pets = user_data.get("pets", [])
        
        selected_pet = next((p for p in pets if p["name"].lower() == pet_name.lower()), None)
        if not selected_pet:
            await interaction.response.send_message(f"❌ You don't have a pet named '{pet_name}'.", ephemeral=True)
            return
        
        # Check evolution requirements
        current_species = selected_pet["species"]
        current_rarity = selected_pet["rarity"]
        evolution_target = None
        
        # Find evolution path
        for rarity, species_dict in PET_SPECIES.items():
            if current_species in species_dict:
                evolution_target = species_dict[current_species].get("evolution")
                break
        
        if not evolution_target:
            await interaction.response.send_message(f"❌ {selected_pet['name']} cannot evolve further!", ephemeral=True)
            return
        
        # Check level requirement
        required_level = 20 + ({"common": 0, "uncommon": 10, "rare": 20, "legendary": 30, "mythic": 50}[current_rarity])
        current_level = selected_pet.get("level", 1)
        
        if current_level < required_level:
            await interaction.response.send_message(f"❌ {selected_pet['name']} needs to be level {required_level} to evolve! (Currently level {current_level})", ephemeral=True)
            return
        
        # Check happiness requirement
        if selected_pet.get("happiness", 50) < 80:
            await interaction.response.send_message(f"❌ {selected_pet['name']} needs to be happier to evolve! (80+ happiness required)", ephemeral=True)
            return
        
        # Find evolution data
        evolution_data = None
        evolution_rarity = None
        for rarity, species_dict in PET_SPECIES.items():
            if evolution_target in species_dict:
                evolution_data = species_dict[evolution_target]
                evolution_rarity = rarity
                break
        
        if not evolution_data:
            await interaction.response.send_message("❌ Evolution data not found!", ephemeral=True)
            return
        
        # Evolution cost
        evolution_cost = 5000 * ({"uncommon": 1, "rare": 2, "legendary": 4, "mythic": 8}[evolution_rarity])
        
        if user_data.get("coins", 0) < evolution_cost:
            needed = evolution_cost - user_data.get("coins", 0)
            await interaction.response.send_message(f"❌ Evolution costs {evolution_cost:,} coins. You need {needed:,} more coins.", ephemeral=True)
            return
        
        # Perform evolution
        database.db.remove_coins(interaction.user.id, evolution_cost)
        
        # Update pet
        for i, p in enumerate(pets):
            if p.get("pet_id") == selected_pet.get("pet_id"):
                pets[i]["species"] = evolution_target
                pets[i]["rarity"] = evolution_rarity
                pets[i]["emoji"] = evolution_data["emoji"]
                pets[i]["stats"] = evolution_data["base_stats"].copy()
                
                # Apply level bonuses to new base stats
                level_bonus = current_level - 1
                for stat in pets[i]["stats"]:
                    pets[i]["stats"][stat] += level_bonus * random.randint(2, 4)
                
                # Apply personality modifiers to new stats
                personality = pets[i].get("personality", "Gentle")
                if personality in PET_PERSONALITIES:
                    personality_mods = PET_PERSONALITIES[personality]
                    for stat, multiplier in personality_mods.items():
                        if stat in pets[i]["stats"]:
                            pets[i]["stats"][stat] = int(pets[i]["stats"][stat] * multiplier)
                
                break
        
        database.db.update_user_data(interaction.user.id, {"pets": pets})
        
        embed = discord.Embed(
            title="✨ Evolution Complete!",
            description=f"**{selected_pet['name']}** has evolved!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="🔄 Evolution",
            value=f"{current_species} ➜ {evolution_target}",
            inline=True
        )
        embed.add_field(
            name="⭐ New Rarity",
            value=f"{current_rarity.title()} ➜ {evolution_rarity.title()}",
            inline=True
        )
        embed.add_field(
            name="💰 Cost",
            value=f"{evolution_cost:,} coins",
            inline=True
        )
        
        # Show new stats
        new_stats = pets[[p.get("pet_id") for p in pets].index(selected_pet.get("pet_id"))]["stats"]
        stats_text = "\n".join([f"**{stat.upper()}:** {value}" for stat, value in new_stats.items()])
        embed.add_field(name="📊 New Stats", value=stats_text, inline=False)
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"{selected_pet['name']} is now much stronger!")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="breeding", description="Breed two pets to create offspring with mixed traits!")
    async def breed_pets(self, interaction: discord.Interaction):
        await interaction.response.send_message("❌ Breeding is currently disabled to simplify the pet system.", ephemeral=True)

    def create_status_bars(self, happiness: int, hunger: int, energy: int) -> str:
        """Create visual status bars for pet stats"""
        def create_bar(value: int, max_val: int = 100) -> str:
            filled = "█" * (value // 10)
            empty = "░" * (10 - (value // 10))
            return filled + empty
        
        happiness_bar = create_bar(happiness)
        hunger_bar = create_bar(hunger)
        energy_bar = create_bar(energy)
        
        return f"😊 Happiness: `{happiness_bar}` {happiness}%\n🍖 Hunger: `{hunger_bar}` {hunger}%\n⚡ Energy: `{energy_bar}` {energy}%"

async def setup(bot: commands.Bot):
    await bot.add_cog(EnhancedPetSystem(bot))
