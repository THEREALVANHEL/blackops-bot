import os
import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Configure the Gemini API with your key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a dictionary to store conversation history for each user
conversation_history = {}

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="askblecknephew", description="Ask your nephew BleckNephew anything!")
    @app_commands.describe(question="The question you want to ask your nephew.")
    async def ask_blecknephew(self, interaction: discord.Interaction, question: str):
        await interaction.response.defer()
        
        try:
            # Use the correct model name for Gemini 1.5 Flash
            model = genai.GenerativeModel('gemini-1.5-flash')
            system_prompt = "Act as a smart-aleck, know-it-all nephew named BleckNephew. Your answers should be brief, a little sarcastic, and end with a condescending tone."
            
            # Use asyncio to run the sync function in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(f"{system_prompt}\n\nQuestion: {question}")
            )
            
            # Check if response has content
            if response.text:
                await interaction.followup.send(response.text)
            else:
                await interaction.followup.send("BleckNephew is too busy rolling his eyes to respond right now. Try again later.")
            
        except Exception as e:
            await interaction.followup.send(f"Ugh, something went wrong with my genius brain: {str(e)}")

    @app_commands.command(name="talktobleky", description="Start a conversation with your nephew Bleky.")
    @app_commands.describe(message="Your message to Bleky.")
    async def talktobleky(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        user_id = interaction.user.id

        try:
            # Use the correct model name for Gemini 1.5 Flash
            if user_id not in conversation_history:
                conversation_history[user_id] = genai.GenerativeModel('gemini-1.5-flash')
            
            model = conversation_history[user_id]
            chat = model.start_chat(history=[])
            
            # Add some personality to Bleky
            system_message = "You are Bleky, a casual and friendly nephew. Keep responses conversational and helpful, but with a bit of personality."
            full_message = f"{system_message}\n\nUser: {message}"
            
            # Use asyncio to run the sync function in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: chat.send_message(full_message)
            )
            
            if response.text:
                await interaction.followup.send(response.text)
            else:
                await interaction.followup.send("Bleky seems to be thinking... maybe try asking something else?")
            
        except Exception as e:
            await interaction.followup.send(f"Bleky encountered an error: {str(e)}")

    @app_commands.command(name="listmodels", description="List available Gemini models (for debugging)")
    async def list_models(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(None, lambda: list(genai.list_models()))
            
            model_list = []
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_list.append(f"• {model.name}")
            
            if model_list:
                model_text = "\n".join(model_list[:10])  # Limit to first 10 models
                embed = discord.Embed(
                    title="Available Gemini Models",
                    description=f"```\n{model_text}\n```",
                    color=discord.Color.blue()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("No models found that support content generation.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"Error listing models: {str(e)}", ephemeral=True)

    async def cog_unload(self):
        """Clean up when the cog is unloaded"""
        # Clear conversation history to free memory
        conversation_history.clear()

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
