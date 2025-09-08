import os
import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
from dotenv import load_dotenv

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
            model = genai.GenerativeModel('gemini-pro')
            system_prompt = "Act as a smart-aleck, know-it-all nephew named BleckNephew. Your answers should be brief, a little sarcastic, and end with a condescending tone."
            
            response = await model.generate_content(f"{system_prompt}\n\nQuestion: {question}")
            
            await interaction.followup.send(response.text)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    @app_commands.command(name="talktobleky", description="Start a conversation with your nephew Bleky.")
    @app_commands.describe(message="Your message to Bleky.")
    async def talktobleky(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        user_id = interaction.user.id

        # Check if a conversation already exists, otherwise create a new one
        if user_id not in conversation_history:
            conversation_history[user_id] = genai.GenerativeModel('gemini-pro')
        
        try:
            chat = conversation_history[user_id].start_chat(history=[])
            
            response = chat.send_message(message)
            
            await interaction.followup.send(response.text)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
