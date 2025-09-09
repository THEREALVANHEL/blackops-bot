import os
import discord
from discord.ext import commands
from discord import app_commands
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio
import random

# Load environment variables
load_dotenv()

# Configure the Gemini API with your key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Store conversation context per user
user_conversations = {}

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.personalities = {
            "nephew": {
                "name": "BleckNephew",
                "prompt": "You are BleckNephew, a smart-aleck, know-it-all nephew. Your responses should be brief, witty, slightly sarcastic, and end with a condescending but playful tone. You're intelligent but act like a typical sassy nephew who thinks they know everything.",
                "emoji": "😏",
                "color": discord.Color.orange()
            },
            "friendly": {
                "name": "Bleky", 
                "prompt": "You are Bleky, a casual, friendly, and helpful AI assistant. Keep responses conversational, supportive, and engaging. You're like a cool older sibling who's always ready to help and chat about anything.",
                "emoji": "😊",
                "color": discord.Color.blue()
            },
            "expert": {
                "name": "Professor Bleck",
                "prompt": "You are Professor Bleck, a highly knowledgeable and professional AI. Provide detailed, accurate, and well-structured responses. You're scholarly but not boring, explaining complex topics in an accessible way.",
                "emoji": "🎓",
                "color": discord.Color.purple()
            }
        }

    @app_commands.command(name="ask", description="Ask the AI anything with different personality modes!")
    @app_commands.describe(
        question="Your question or message",
        mode="Choose the AI personality mode"
    )
    @app_commands.choices(
        mode=[
            discord.app_commands.Choice(name="😏 Sassy Nephew (BleckNephew)", value="nephew"),
            discord.app_commands.Choice(name="😊 Friendly Helper (Bleky)", value="friendly"),
            discord.app_commands.Choice(name="🎓 Expert Mode (Professor)", value="expert")
        ]
    )
    async def ask_ai(self, interaction: discord.Interaction, question: str, mode: str = "friendly"):
        await interaction.response.defer()
        
        try:
            personality = self.personalities[mode]
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Create context-aware prompt
            user_id = interaction.user.id
            if user_id not in user_conversations:
                user_conversations[user_id] = []
            
            # Keep last 5 messages for context
            context = ""
            if user_conversations[user_id]:
                recent_context = user_conversations[user_id][-3:]
                context = "\n".join([f"Previous: {msg}" for msg in recent_context])
                context += "\n\n"
            
            full_prompt = f"{personality['prompt']}\n\n{context}Current question: {question}"
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(full_prompt)
            )
            
            if response.text:
                # Store conversation
                user_conversations[user_id].append(f"Q: {question}")
                user_conversations[user_id].append(f"A: {response.text}")
                
                # Keep only last 10 entries to manage memory
                if len(user_conversations[user_id]) > 10:
                    user_conversations[user_id] = user_conversations[user_id][-10:]
                
                # Create fancy response embed
                embed = discord.Embed(
                    title=f"{personality['emoji']} {personality['name']} Responds",
                    description=response.text,
                    color=personality['color'],
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(
                    name="❓ Question", 
                    value=question[:100] + "..." if len(question) > 100 else question, 
                    inline=False
                )
                embed.set_author(
                    name=interaction.user.display_name, 
                    icon_url=interaction.user.display_avatar.url
                )
                embed.set_footer(text=f"Mode: {personality['name']} • Use different modes for varied responses!")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"{personality['emoji']} {personality['name']} seems to be thinking too hard right now. Try again!")
                
        except Exception as e:
            error_messages = [
                "My brain just blue-screened! 🤖💥",
                "Error 404: Smartness not found! 🔍",
                "I'm having a senior moment... 🧓",
                "My circuits are fried! ⚡"
            ]
            await interaction.followup.send(f"{random.choice(error_messages)}\n*Technical details: {str(e)}*")

    @app_commands.command(name="chat", description="Start a continuous conversation with the AI.")
    @app_commands.describe(
        message="Your message to start/continue the conversation",
        mode="Choose conversation style"
    )
    @app_commands.choices(
        mode=[
            discord.app_commands.Choice(name="😊 Casual Chat", value="friendly"),
            discord.app_commands.Choice(name="😏 Sassy Banter", value="nephew"), 
            discord.app_commands.Choice(name="🎓 Deep Discussion", value="expert")
        ]
    )
    async def chat(self, interaction: discord.Interaction, message: str, mode: str = "friendly"):
        await interaction.response.defer()
        
        try:
            personality = self.personalities[mode]
            model = genai.GenerativeModel('gemini-1.5-flash')
            user_id = interaction.user.id
            
            # Initialize or get conversation history
            if user_id not in user_conversations:
                user_conversations[user_id] = []
            
            # Build conversation context
            conversation_history = []
            for i, msg in enumerate(user_conversations[user_id]):
                if i % 2 == 0:  # Questions
                    conversation_history.append(f"User: {msg[2:]}")  # Remove "Q: "
                else:  # Answers
                    conversation_history.append(f"{personality['name']}: {msg[2:]}")  # Remove "A: "
            
            # Create chat context
            context = "\n".join(conversation_history[-6:]) if conversation_history else ""
            
            chat_prompt = f"""You are {personality['name']}. {personality['prompt']}
            
Previous conversation:
{context}

User: {message}
{personality['name']}:"""

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(chat_prompt)
            )
            
            if response.text:
                # Update conversation history
                user_conversations[user_id].append(f"Q: {message}")
                user_conversations[user_id].append(f"A: {response.text}")
                
                # Limit history size
                if len(user_conversations[user_id]) > 20:
                    user_conversations[user_id] = user_conversations[user_id][-20:]
                
                # Create response embed
                embed = discord.Embed(
                    description=response.text,
                    color=personality['color'],
                    timestamp=discord.utils.utcnow()
                )
                embed.set_author(
                    name=f"{personality['emoji']} {personality['name']}", 
                    icon_url=self.bot.user.display_avatar.url
                )
                embed.add_field(
                    name="💬 Conversation", 
                    value=f"`{len(user_conversations[user_id])//2}` messages exchanged", 
                    inline=True
                )
                embed.set_footer(text="Continue the conversation with /chat")
                
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"{personality['emoji']} *{personality['name']} is lost in thought...*")
                
        except Exception as e:
            await interaction.followup.send(f"🤖 Conversation interrupted! Error: {str(e)}")

    @app_commands.command(name="clearchat", description="Clear your conversation history with the AI.")
    async def clear_chat(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if user_id in user_conversations:
            messages_cleared = len(user_conversations[user_id]) // 2
            user_conversations[user_id] = []
            
            embed = discord.Embed(
                title="🧹 Chat History Cleared",
                description=f"Cleared `{messages_cleared}` conversation messages.\nYour next chat will start fresh!",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="🤷 Nothing to Clear",
                description="You don't have any conversation history yet.\nStart chatting with `/ask` or `/chat`!",
                color=discord.Color.orange()
            )
        
        embed.set_footer(text="Your conversation data is stored only during this session")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="aistats", description="View your AI interaction statistics.")
    async def ai_stats(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        if user_id in user_conversations and user_conversations[user_id]:
            total_messages = len(user_conversations[user_id]) // 2
            recent_activity = "Active" if total_messages > 0 else "No recent activity"
            
            embed = discord.Embed(
                title="🤖 AI Interaction Stats",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="💬 Messages Exchanged", value=f"`{total_messages}`", inline=True)
            embed.add_field(name="📊 Status", value=recent_activity, inline=True)
            embed.add_field(name="🔄 Session Active", value="Yes", inline=True)
            
            # Show available personalities
            personalities_list = "\n".join([
                f"{info['emoji']} **{info['name']}** - {info['prompt'][:50]}..."
                for info in self.personalities.values()
            ])
            embed.add_field(name="🎭 Available Personalities", value=personalities_list, inline=False)
            
        else:
            embed = discord.Embed(
                title="🤖 AI Interaction Stats", 
                description="You haven't started any conversations yet!\nUse `/ask` or `/chat` to begin.",
                color=discord.Color.orange()
            )
        
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Statistics reset when bot restarts")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        user_conversations.clear()


async def setup(bot: commands.Bot):
    await bot.add_cog(AI(bot))
