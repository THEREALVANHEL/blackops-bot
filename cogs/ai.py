import os
import discord
from discord.ext import commands
from discord import app_commands
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from dotenv import load_dotenv
import asyncio
import random
import time
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Validate and configure the Gemini API (optional)
gemini_api_key = os.getenv("GEMINI_API_KEY")
AI_ENABLED = False
if genai is not None and gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        AI_ENABLED = True
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.warning(f"Failed to configure Gemini API, AI features disabled: {e}")
else:
    if genai is None:
        logger.warning("google-generativeai not installed; AI features disabled")
    else:
        logger.warning("GEMINI_API_KEY not set; AI features disabled")

class ConversationManager:
    """Manages AI conversations with memory limits and cleanup"""
    
    def __init__(self, max_users: int = 1000, max_messages_per_user: int = 20, cleanup_interval: int = 3600):
        self.conversations = OrderedDict()
        self.max_users = max_users
        self.max_messages_per_user = max_messages_per_user
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        self._lock = threading.RLock()
    
    def add_message(self, user_id: int, message_type: str, content: str):
        """Add a message to user's conversation history"""
        with self._lock:
            current_time = time.time()
            
            # Periodic cleanup
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_conversations()
                self.last_cleanup = current_time
            
            # Initialize user conversation if not exists
            if user_id not in self.conversations:
                self.conversations[user_id] = {
                    "messages": [],
                    "last_activity": current_time,
                    "created_at": current_time
                }
            
            # Update last activity
            self.conversations[user_id]["last_activity"] = current_time
            
            # Truncate content to prevent memory issues
            truncated_content = content[:1000] if content else ""
            
            # Add new message
            self.conversations[user_id]["messages"].append({
                "type": message_type,
                "content": truncated_content,
                "timestamp": current_time
            })
            
            # Limit messages per user
            messages = self.conversations[user_id]["messages"]
            if len(messages) > self.max_messages_per_user:
                self.conversations[user_id]["messages"] = messages[-self.max_messages_per_user:]
            
            # Move to end (LRU)
            self.conversations.move_to_end(user_id)
            
            # Limit total users
            if len(self.conversations) > self.max_users:
                self.conversations.popitem(last=False)
    
    def get_conversation_history(self, user_id: int, limit: int = 10) -> list:
        """Get recent conversation history for user"""
        with self._lock:
            if user_id not in self.conversations:
                return []
            
            messages = self.conversations[user_id]["messages"]
            return messages[-limit:] if len(messages) > limit else messages
    
    def clear_conversation(self, user_id: int) -> bool:
        """Clear conversation history for user"""
        with self._lock:
            if user_id in self.conversations:
                del self.conversations[user_id]
                return True
            return False
    
    def get_stats(self) -> dict:
        """Get conversation manager statistics"""
        with self._lock:
            total_messages = sum(len(conv["messages"]) for conv in self.conversations.values())
            active_users = len(self.conversations)
            
            return {
                "active_users": active_users,
                "total_messages": total_messages,
                "max_users": self.max_users,
                "max_messages_per_user": self.max_messages_per_user,
                "memory_usage_mb": self._estimate_memory_usage()
            }
    
    def _cleanup_old_conversations(self):
        """Remove conversations older than 24 hours"""
        current_time = time.time()
        cutoff_time = current_time - 86400  # 24 hours
        
        users_to_remove = []
        for user_id, conversation in self.conversations.items():
            if conversation["last_activity"] < cutoff_time:
                users_to_remove.append(user_id)
        
        for user_id in users_to_remove:
            del self.conversations[user_id]
        
        if users_to_remove:
            logger.info(f"Cleaned up {len(users_to_remove)} old conversations")
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            total_size = 0
            
            for conversation in self.conversations.values():
                total_size += sys.getsizeof(conversation)
                for message in conversation["messages"]:
                    total_size += sys.getsizeof(message)
                    if isinstance(message.get("content"), str):
                        total_size += sys.getsizeof(message["content"])
            
            return round(total_size / (1024 * 1024), 2)
        except Exception as e:
            logger.warning(f"Error estimating memory usage: {e}")
            return 0.0

# Global conversation manager
conversation_manager = ConversationManager()

class AI(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.personalities = {
            "nephew": {
                "name": "BleckNephew",
                "prompt": "You are BleckNephew, a smart-aleck, know-it-all nephew. Your responses should be brief, witty, slightly sarcastic, and end with a condescending but playful tone. You're intelligent but act like a typical sassy nephew who thinks they know everything. Keep responses under 200 words.",
                "emoji": "😏",
                "color": discord.Color.orange()
            },
            "friendly": {
                "name": "Bleky", 
                "prompt": "You are Bleky, a casual, friendly, and helpful AI assistant. Keep responses conversational, supportive, and engaging. You're like a cool older sibling who's always ready to help and chat about anything. Be warm and approachable. Keep responses under 300 words.",
                "emoji": "😊",
                "color": discord.Color.blue()
            },
            "expert": {
                "name": "Professor Bleck",
                "prompt": "You are Professor Bleck, a highly knowledgeable and professional AI. Provide detailed, accurate, and well-structured responses. You're scholarly but not boring, explaining complex topics in an accessible way. Use proper terminology but remain understandable. Keep responses under 400 words.",
                "emoji": "🎓",
                "color": discord.Color.purple()
            }
        }
        
        # Rate limiting
        self.user_cooldowns = {}
        self.cooldown_duration = 5  # 5 seconds between requests
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_responses": 0,
            "errors": 0,
            "personality_usage": {"nephew": 0, "friendly": 0, "expert": 0},
            "start_time": time.time()
        }
        
        # API rate limiting
        self.api_calls_per_minute = 0
        self.api_minute_start = time.time()
        self.max_api_calls_per_minute = 50
        
        # Start background tasks
        self.cleanup_task = None

    async def cog_load(self):
        """Initialize when cog is loaded"""
        logger.info("AI cog loaded successfully")
        self.cleanup_task = self.bot.loop.create_task(self._periodic_cleanup())

    async def cog_unload(self):
        """Clean up when cog is unloaded"""
        try:
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Clear all conversations
            with conversation_manager._lock:
                conversation_manager.conversations.clear()
            
            # Clear cooldowns
            self.user_cooldowns.clear()
            
            logger.info("AI cog cleanup completed")
        except Exception as e:
            logger.error(f"Error during AI cog cleanup: {e}")

    async def _periodic_cleanup(self):
        """Periodic cleanup task"""
        while not self.bot.is_closed():
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Cleanup old cooldowns
                current_time = time.time()
                expired_users = [
                    user_id for user_id, timestamp in self.user_cooldowns.items()
                    if current_time - timestamp > 3600  # 1 hour old
                ]
                
                for user_id in expired_users:
                    del self.user_cooldowns[user_id]
                
                if expired_users:
                    logger.info(f"Cleaned up {len(expired_users)} expired cooldowns")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in AI periodic cleanup: {e}")

    async def _check_cooldown(self, user_id: int) -> bool:
        """Check if user is on cooldown"""
        current_time = time.time()
        if user_id in self.user_cooldowns:
            time_passed = current_time - self.user_cooldowns[user_id]
            if time_passed < self.cooldown_duration:
                return False
        
        self.user_cooldowns[user_id] = current_time
        return True

    async def _check_api_rate_limit(self) -> bool:
        """Check if we're hitting API rate limits"""
        current_time = time.time()
        
        # Reset counter if a minute has passed
        if current_time - self.api_minute_start >= 60:
            self.api_calls_per_minute = 0
            self.api_minute_start = current_time
        
        if self.api_calls_per_minute >= self.max_api_calls_per_minute:
            return False
        
        self.api_calls_per_minute += 1
        return True

    def _truncate_for_embed(self, text: str, max_length: int = 4000) -> str:
        """Truncate text to fit in Discord embed"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    async def _generate_ai_response(self, prompt: str, personality: dict) -> str:
        """Generate AI response with enhanced error handling"""
        try:
            # Check API rate limit
            if not await self._check_api_rate_limit():
                return f"{personality['emoji']} I'm getting too many requests right now. Please try again in a minute!"
            
            # Validate personality
            if not isinstance(personality, dict) or 'name' not in personality:
                raise ValueError("Invalid personality configuration")
            
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Enhanced prompt with safety guidelines
            enhanced_prompt = f"""
            {personality.get('prompt', '')}
            
            IMPORTANT GUIDELINES:
            - Keep responses appropriate and family-friendly
            - Stay in character as {personality.get('name', 'AI')}
            - Be helpful and constructive
            - Avoid generating harmful, offensive, or inappropriate content
            - If asked about illegal activities, politely decline and suggest alternatives
            - Keep responses under the specified word limit
            
            User question: {prompt}
            
            Respond as {personality.get('name', 'AI')}:
            """
            
            # Generate response with timeout
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None, 
                    lambda: model.generate_content(enhanced_prompt)
                ),
                timeout=15.0  # 15 second timeout
            )
            
            if response and hasattr(response, 'text') and response.text:
                self.stats["successful_responses"] += 1
                return response.text.strip()
            else:
                raise Exception("Empty response from AI model")
                
        except asyncio.TimeoutError:
            self.stats["errors"] += 1
            logger.warning("AI request timed out")
            return f"{personality.get('emoji', '🤖')} Sorry, I'm thinking too hard right now. Try again in a moment!"
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"AI generation error: {e}")
            
            error_responses = [
                f"{personality.get('emoji', '🤖')} My brain just blue-screened! 🤖💥",
                f"{personality.get('emoji', '🤖')} Error 404: Smartness not found! 🔍",
                f"{personality.get('emoji', '🤖')} I'm having a senior moment... 🧓",
                f"{personality.get('emoji', '🤖')} My circuits are fried! ⚡"
            ]
            return random.choice(error_responses)

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
        # Check cooldown
        if not await self._check_cooldown(interaction.user.id):
            remaining_time = self.cooldown_duration - (time.time() - self.user_cooldowns[interaction.user.id])
            await interaction.response.send_message(
                f"⏰ Please wait {remaining_time:.1f} more seconds before asking another question!",
                ephemeral=True
            )
            return

        # Validate input
        question = question.strip()
        if len(question) < 3:
            await interaction.response.send_message(
                "❌ Please ask a more detailed question!",
                ephemeral=True
            )
            return

        if len(question) > 1000:
            await interaction.response.send_message(
                "❌ Question too long! Please keep it under 1000 characters.",
                ephemeral=True
            )
            return

        # Validate mode
        if mode not in self.personalities:
            mode = "friendly"

        await interaction.response.defer()
        
        try:
            self.stats["total_requests"] += 1
            self.stats["personality_usage"][mode] += 1
            personality = self.personalities[mode]
            
            # Get conversation context (last 3 messages)
            context_messages = conversation_manager.get_conversation_history(interaction.user.id, 3)
            
            # Build context string
            context = ""
            if context_messages:
                context_parts = []
                for msg in context_messages:
                    if msg["type"] == "question":
                        context_parts.append(f"Previous Q: {msg['content'][:100]}")
                    elif msg["type"] == "answer":
                        context_parts.append(f"Previous A: {msg['content'][:100]}")
                
                if context_parts:
                    context = "\n".join(context_parts[-4:]) + "\n\n"  # Last 4 context parts
            
            # Create full prompt with context
            full_prompt = f"{context}Current question: {question}"
            
            # Generate response
            ai_response = await self._generate_ai_response(full_prompt, personality)
            
            # Truncate response if too long for embed
            ai_response = self._truncate_for_embed(ai_response)
            
            # Store conversation
            conversation_manager.add_message(interaction.user.id, "question", question)
            conversation_manager.add_message(interaction.user.id, "answer", ai_response)
            
            # Create response embed
            embed = discord.Embed(
                title=f"{personality['emoji']} {personality['name']} Responds",
                description=ai_response,
                color=personality['color'],
                timestamp=datetime.now(datetime.UTC)
            )
            
            # Truncate long questions for display
            display_question = question[:150] + "..." if len(question) > 150 else question
            embed.add_field(
                name="❓ Question", 
                value=display_question, 
                inline=False
            )
            
            # Safe avatar URL handling
            try:
                avatar_url = interaction.user.display_avatar.url
            except Exception:
                avatar_url = None
            
            embed.set_author(
                name=interaction.user.display_name, 
                icon_url=avatar_url
            )
            
            embed.set_footer(text=f"Mode: {personality['name']} • Use different modes for varied responses!")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in ask command: {e}")
            await interaction.followup.send(
                "❌ Something went wrong while processing your question. Please try again!",
                ephemeral=True
            )

    # Pruned: chat command removed to simplify AI features

    # Pruned: clearchat command removed

    # Pruned: aistats command removed

    # Pruned: aihelp command removed

    # Pruned: aitrouble command removed


async def setup(bot: commands.Bot):
    """Setup function for the AI cog"""
    if not AI_ENABLED:
        logger.warning("Skipping AI cog setup because AI is disabled")
        return
    try:
        await bot.add_cog(AI(bot))
        logger.info("AI cog added successfully")
    except Exception as e:
        logger.error(f"Failed to add AI cog: {e}")
        raise
