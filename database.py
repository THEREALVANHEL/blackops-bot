"""
Enhanced Discord Bot Database System
- Fixed MongoDB synchronization issues
- Added comprehensive error handling
- Implemented data validation
- Added backup and recovery mechanisms
- FIXED: Added missing methods for cookies and other functionality
"""

import os
import asyncio
import time
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import json
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import dependencies with fallbacks
try:
    from pymongo import MongoClient, errors as pymongo_errors
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
    logger.info("✅ MongoDB drivers available")
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("⚠️ MongoDB drivers not available, using memory storage")

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ Environment variables loaded")
except ImportError:
    logger.warning("⚠️ python-dotenv not available")

class DatabaseError(Exception):
    """Custom database error class"""
    pass

class DataValidator:
    """Validates data before database operations"""
    
    @staticmethod
    def validate_user_data(data: dict, operation: str = "update") -> bool:
        """Validate user data structure"""
        if operation == "create":
            required_fields = ["user_id"]
        else:
            required_fields = []
        
        for field in required_fields:
            if field not in data:
                raise DatabaseError(f"Missing required field: {field}")
        
        # Validate data types
        if "user_id" in data and not isinstance(data["user_id"], int):
            raise DatabaseError("user_id must be an integer")
        
        if "coins" in data and not isinstance(data["coins"], (int, float)):
            raise DatabaseError("coins must be a number")
        
        return True
    
    @staticmethod
    def validate_guild_data(data: dict) -> bool:
        """Validate guild data structure"""
        if "guild_id" in data and not isinstance(data["guild_id"], int):
            raise DatabaseError("guild_id must be an integer")
        
        return True

class DatabaseManager:
    """
    Enhanced Database Manager with improved error handling and data integrity
    """
    
    def __init__(self):
        self.mongodb_client = None
        self.mongodb_db = None
        self.users_collection = None
        self.guilds_collection = None
        self.connected_to_mongodb = False
        self.connection_lock = threading.Lock()
        
        # In-memory storage as fallback
        self.memory_users = {}
        self.memory_guilds = {}
        self.memory_lock = threading.Lock()
        
        # Data validation
        self.validator = DataValidator()
        
        # Connection retry settings
        self.max_retries = 3
        self.retry_delay = 5
        
        # Initialize connection
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                if self._attempt_mongodb_connection():
                    return
                    
                logger.warning(f"MongoDB connection attempt {attempt + 1} failed, retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"Critical error during database initialization: {e}")
                
        logger.warning("All MongoDB connection attempts failed, using memory storage")
        self.connected_to_mongodb = False
    
    def _attempt_mongodb_connection(self) -> bool:
        """Attempt to connect to MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI')
            
            if not MONGODB_AVAILABLE or not mongodb_uri:
                return False
            
            with self.connection_lock:
                # Create client with proper settings
                self.mongodb_client = MongoClient(
                    mongodb_uri,
                    serverSelectionTimeoutMS=10000,
                    connectTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    retryWrites=True,
                    maxPoolSize=10,
                    minPoolSize=1
                )
                
                # Test connection
                self.mongodb_client.admin.command('ping')
                
                # Setup database and collections
                db_name = os.getenv('MONGODB_DATABASE', 'blackops-bot')
                self.mongodb_db = self.mongodb_client[db_name]
                self.users_collection = self.mongodb_db.users
                self.guilds_collection = self.mongodb_db.guilds
                
                # Create indexes for performance
                self._create_indexes()
                
                self.connected_to_mongodb = True
                logger.info("🎯 MongoDB connection established successfully!")
                return True
                
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.connected_to_mongodb = False
            return False
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # User collection indexes
            self.users_collection.create_index("user_id", unique=True)
            self.users_collection.create_index("level")
            self.users_collection.create_index("coins")
            self.users_collection.create_index("daily_streak")
            
            # Guild collection indexes
            self.guilds_collection.create_index("guild_id", unique=True)
            
            logger.info("📊 Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    @contextmanager
    def _safe_operation(self, operation_name: str):
        """Context manager for safe database operations"""
        try:
            logger.debug(f"Starting operation: {operation_name}")
            yield
            logger.debug(f"Operation completed: {operation_name}")
        except pymongo_errors.PyMongoError as e:
            logger.error(f"MongoDB error in {operation_name}: {e}")
            raise DatabaseError(f"Database operation failed: {operation_name}")
        except Exception as e:
            logger.error(f"Unexpected error in {operation_name}: {e}")
            raise DatabaseError(f"Unexpected error in {operation_name}: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "mongodb_connected": False,
            "memory_storage": False,
            "total_users": 0,
            "total_guilds": 0,
            "last_check": datetime.now(timezone.utc).isoformat(),
            "errors": []
        }
        
        try:
            if self.connected_to_mongodb and self.mongodb_client:
                # Test MongoDB connection
                with self._safe_operation("health_check"):
                    self.mongodb_client.admin.command('ping')
                    health_status["mongodb_connected"] = True
                    health_status["total_users"] = self.users_collection.count_documents({})
                    health_status["total_guilds"] = self.guilds_collection.count_documents({})
        except Exception as e:
            health_status["errors"].append(f"MongoDB: {str(e)}")
            
        if not health_status["mongodb_connected"]:
            health_status["memory_storage"] = True
            with self.memory_lock:
                health_status["total_users"] = len(self.memory_users)
                health_status["total_guilds"] = len(self.memory_guilds)
        
        return health_status
    
    def get_database_health(self) -> Dict[str, Any]:
        """Get database health status (compatibility method)"""
        health = self.health_check()
        return {
            "connected": health["mongodb_connected"],
            "mongodb_connected": health["mongodb_connected"],
            "errors": health.get("errors", [])
        }
    
    def reconnect_mongodb(self) -> bool:
        """Attempt to reconnect to MongoDB"""
        logger.info("Attempting MongoDB reconnection...")
        if self._attempt_mongodb_connection():
            # Sync memory data to MongoDB
            self._sync_memory_to_mongodb()
            return True
        return False
    
    def _sync_memory_to_mongodb(self):
        """Sync memory data to MongoDB after reconnection"""
        if not self.connected_to_mongodb:
            return
            
        try:
            logger.info("Syncing memory data to MongoDB...")
            
            # Sync users
            with self.memory_lock:
                for user_id, user_data in self.memory_users.items():
                    try:
                        self.users_collection.replace_one(
                            {"user_id": user_id},
                            user_data,
                            upsert=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to sync user {user_id}: {e}")
                
                # Sync guilds
                for guild_id, guild_data in self.memory_guilds.items():
                    try:
                        self.guilds_collection.replace_one(
                            {"guild_id": guild_id},
                            guild_data,
                            upsert=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to sync guild {guild_id}: {e}")
            
            logger.info("Memory data sync completed")
            
        except Exception as e:
            logger.error(f"Failed to sync memory data: {e}")
    
    # ==================== USER DATA OPERATIONS ====================
    
    def get_user_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data with enhanced error handling"""
        try:
            # Try MongoDB first
            if self.connected_to_mongodb:
                with self._safe_operation(f"get_user_data_{user_id}"):
                    result = self.users_collection.find_one({"user_id": user_id})
                    if result:
                        # Remove MongoDB _id field
                        result.pop("_id", None)
                        return result
            
            # Fallback to memory
            with self.memory_lock:
                if user_id in self.memory_users:
                    return self.memory_users[user_id].copy()
            
            # Return default user data
            return self._create_default_user_data(user_id)
            
        except DatabaseError:
            logger.warning(f"Database error getting user {user_id}, using default data")
            return self._create_default_user_data(user_id)
        except Exception as e:
            logger.error(f"Unexpected error getting user data for {user_id}: {e}")
            return self._create_default_user_data(user_id)
    
    def update_user_data(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Update user data with validation and error handling"""
        try:
            # Validate data
            self.validator.validate_user_data(data, "update")
            
            # Add metadata
            data["last_updated"] = datetime.now(timezone.utc)
            
            # Try MongoDB first
            if self.connected_to_mongodb:
                with self._safe_operation(f"update_user_data_{user_id}"):
                    update_doc = {}
                    for key, value in data.items():
                        # Always set via $set, allowing dot-notation for nested fields
                        update_doc[key] = value
                    
                    result = self.users_collection.update_one(
                        {"user_id": user_id},
                        {"$set": update_doc},
                        upsert=True
                    )
                    
                    if result.acknowledged:
                        # Also update memory cache for consistency
                        with self.memory_lock:
                            if user_id not in self.memory_users:
                                self.memory_users[user_id] = self._create_default_user_data(user_id)
                            self.memory_users[user_id].update(data)
                        return True
            
            # Fallback to memory storage
            with self.memory_lock:
                if user_id not in self.memory_users:
                    self.memory_users[user_id] = self._create_default_user_data(user_id)
                
                # Handle nested updates
                for key, value in data.items():
                    if '.' in key:
                        # Handle nested field updates like "job.career_path"
                        keys = key.split('.')
                        current = self.memory_users[user_id]
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = value
                    else:
                        self.memory_users[user_id][key] = value
                
                return True
                
        except DatabaseError as e:
            logger.error(f"Database validation error updating user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating user data for {user_id}: {e}")
            return False
    
    def _create_default_user_data(self, user_id: int) -> Dict[str, Any]:
        """Create default user data structure"""
        return {
            "user_id": user_id,
            "coins": 1000,
            "bank": 0,
            "xp": 0,
            "level": 1,
            "daily_streak": 0,
            "last_daily": 0,
            "work_streak": 0,
            "work_count": 0,
            "last_work": 0,
            "inventory": {},
            "achievements": [],
            "temporary_purchases": [],
            "temporary_roles": [],
            "reminders": [],
            "pets": [],
            "stocks": {},
            "investments": [],
            "loans": [],
            "credit_cards": [],
            "cookies": 0,  # Added this field
            "last_cookie": 0,
            "warnings": [],
            "mutes": [],
            "bans": [],
            "tickets": [],
            "reputation": 0,
            "marriage": None,
            "job": {
                "career_path": None,
                "current_level": 0,
                "title": None,
                "work_xp": 0,
                "performance_rating": 3.0,
                "hired_date": None,
                "total_earnings": 0,
                "projects_completed": 0,
                "promotions": 0
            },
            "gambling_stats": {
                "wins": 0,
                "losses": 0,
                "total_bet": 0,
                "total_won": 0
            },
            "settings": {
                "notifications": True,
                "privacy": "public"
            },
            "stats": {
                "commands_used": 0,
                "messages_sent": 0,
                "time_active": 0
            },
            "economy": {
                "total_earned": 0,
                "total_spent": 0
            },
            "social": {
                "friends": [],
                "blocked": [],
                "reputation": 0
            },
            "moderation": {
                "warnings": [],
                "mutes": [],
                "notes": []
            },
            "last_interest": time.time(),
            "created_at": datetime.now(timezone.utc),
            "last_seen": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc)
        }
    
    # ==================== ENHANCED ECONOMY OPERATIONS ====================
    
    def add_coins(self, user_id: int, amount: int) -> bool:
        """Add coins with transaction safety"""
        if amount <= 0:
            return False
            
        try:
            user_data = self.get_user_data(user_id)
            new_balance = user_data.get("coins", 0) + amount
            total_earned = user_data.get("economy", {}).get("total_earned", 0) + amount
            
            return self.update_user_data(user_id, {
                "coins": new_balance,
                "economy.total_earned": total_earned
            })
            
        except Exception as e:
            logger.error(f"Error adding coins for user {user_id}: {e}")
            return False
    
    def remove_coins(self, user_id: int, amount: int) -> bool:
        """Remove coins with sufficient balance check"""
        if amount <= 0:
            return False
            
        try:
            user_data = self.get_user_data(user_id)
            current_balance = user_data.get("coins", 0)
            
            if current_balance < amount:
                return False
            
            new_balance = current_balance - amount
            total_spent = user_data.get("economy", {}).get("total_spent", 0) + amount
            
            return self.update_user_data(user_id, {
                "coins": new_balance,
                "economy.total_spent": total_spent
            })
            
        except Exception as e:
            logger.error(f"Error removing coins for user {user_id}: {e}")
            return False
    
    # ==================== COOKIES SYSTEM (MISSING METHODS) ====================
    
    def add_cookies(self, user_id: int, amount: int) -> bool:
        """Add cookies to user - FIXED: This method was missing"""
        if amount <= 0:
            return False
            
        try:
            user_data = self.get_user_data(user_id)
            current_cookies = user_data.get("cookies", 0)
            new_cookies = current_cookies + amount
            
            return self.update_user_data(user_id, {"cookies": new_cookies})
            
        except Exception as e:
            logger.error(f"Error adding cookies for user {user_id}: {e}")
            return False
    
    def remove_cookies(self, user_id: int, amount: int) -> bool:
        """Remove cookies from user"""
        if amount <= 0:
            return False
            
        try:
            user_data = self.get_user_data(user_id)
            current_cookies = user_data.get("cookies", 0)
            
            if current_cookies < amount:
                return False
            
            new_cookies = current_cookies - amount
            return self.update_user_data(user_id, {"cookies": new_cookies})
            
        except Exception as e:
            logger.error(f"Error removing cookies for user {user_id}: {e}")
            return False
    
    # ==================== WARNING SYSTEM (MISSING METHODS) ====================
    
    def add_warning(self, user_id: int, warning_data: dict) -> bool:
        """Add warning to user"""
        try:
            user_data = self.get_user_data(user_id)
            warnings = user_data.get("warnings", [])
            warnings.append(warning_data)
            
            return self.update_user_data(user_id, {"warnings": warnings})
            
        except Exception as e:
            logger.error(f"Error adding warning for user {user_id}: {e}")
            return False
    
    def get_warnings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get warnings for user"""
        try:
            user_data = self.get_user_data(user_id)
            return user_data.get("warnings", [])
        except Exception as e:
            logger.error(f"Error getting warnings for user {user_id}: {e}")
            return []
    
    # ==================== LEADERBOARD METHODS (MISSING) ====================
    
    def get_streak_leaderboard(self, page: int = 1, members_per_page: int = 10) -> Dict[str, Any]:
        """Get leaderboard for daily streaks - FIXED: This method was missing"""
        try:
            if self.connected_to_mongodb:
                with self._safe_operation(f"streak_leaderboard_{page}"):
                    skip = (page - 1) * members_per_page
                    
                    # Get total count
                    total_users = self.users_collection.count_documents(
                        {"daily_streak": {"$gt": 0}}
                    )
                    total_pages = max(1, (total_users + members_per_page - 1) // members_per_page)
                    
                    # Get paginated results
                    pipeline = [
                        {"$match": {"daily_streak": {"$gt": 0}}},
                        {"$sort": {"daily_streak": -1}},
                        {"$skip": skip},
                        {"$limit": members_per_page},
                        {"$project": {"_id": 0}}
                    ]
                    
                    cursor = self.users_collection.aggregate(pipeline)
                    users = list(cursor)
                    
                    return {
                        'users': users,
                        'total_pages': total_pages,
                        'total_users': total_users,
                        'current_page': page,
                        'members_per_page': members_per_page
                    }
            else:
                with self.memory_lock:
                    users = [user for user in self.memory_users.values() if user.get("daily_streak", 0) > 0]
                    users.sort(key=lambda x: x.get("daily_streak", 0), reverse=True)
                    
                    total_users = len(users)
                    total_pages = max(1, (total_users + members_per_page - 1) // members_per_page)
                    
                    start_idx = (page - 1) * members_per_page
                    end_idx = start_idx + members_per_page
                    paginated_users = users[start_idx:end_idx]
                    
                    return {
                        'users': paginated_users,
                        'total_pages': total_pages,
                        'total_users': total_users,
                        'current_page': page,
                        'members_per_page': members_per_page
                    }
                    
        except Exception as e:
            logger.error(f"Error getting streak leaderboard: {e}")
            return {
                'users': [],
                'total_pages': 1,
                'total_users': 0,
                'current_page': page,
                'members_per_page': members_per_page
            }
    
    def add_xp(self, user_id: int, amount: int) -> Dict[str, Any]:
        """Add XP and handle level ups with transaction safety"""
        try:
            user_data = self.get_user_data(user_id)
            old_level = user_data.get("level", 1)
            old_xp = user_data.get("xp", 0)
            new_xp = old_xp + amount
            new_level = self._calculate_level(new_xp)
            
            update_data = {
                "xp": new_xp,
                "level": new_level
            }
            
            # Add level-up rewards
            level_rewards = {}
            if new_level > old_level:
                level_rewards = self._calculate_level_rewards(new_level, old_level)
                if level_rewards.get("coins", 0) > 0:
                    current_coins = user_data.get("coins", 0)
                    update_data["coins"] = current_coins + level_rewards["coins"]
            
            success = self.update_user_data(user_id, update_data)
            
            return {
                "success": success,
                "xp_gained": amount,
                "total_xp": new_xp,
                "old_level": old_level,
                "new_level": new_level,
                "leveled_up": new_level > old_level,
                "level_rewards": level_rewards if new_level > old_level else {}
            }
            
        except Exception as e:
            logger.error(f"Error adding XP for user {user_id}: {e}")
            return {
                "success": False,
                "xp_gained": 0,
                "leveled_up": False
            }
    
    def _calculate_level(self, xp: int) -> int:
        """Calculate level based on XP with improved formula"""
        return int((xp / 100) ** 0.5) + 1
    
    def _calculate_level_rewards(self, new_level: int, old_level: int) -> Dict[str, Any]:
        """Calculate rewards for level ups"""
        levels_gained = new_level - old_level
        base_coins = 100
        
        rewards = {
            "coins": base_coins * levels_gained * new_level,
            "items": []
        }
        
        # Milestone rewards
        if new_level % 10 == 0:
            rewards["items"].append("xp_boost")
        if new_level % 25 == 0:
            rewards["items"].append("lucky_charm")
        if new_level == 50:
            rewards["items"].append("premium_boost")
        if new_level == 100:
            rewards["coins"] += 10000
            rewards["items"].append("legendary_pet_egg")
        
        return rewards
    
    # ==================== GUILD DATA OPERATIONS ====================
    
    def get_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Get guild data with error handling"""
        try:
            # Try MongoDB first
            if self.connected_to_mongodb:
                with self._safe_operation(f"get_guild_data_{guild_id}"):
                    result = self.guilds_collection.find_one({"guild_id": guild_id})
                    if result:
                        result.pop("_id", None)
                        return result
            
            # Fallback to memory
            with self.memory_lock:
                if guild_id in self.memory_guilds:
                    return self.memory_guilds[guild_id].copy()
            
            return self._create_default_guild_data(guild_id)
            
        except Exception as e:
            logger.error(f"Error getting guild data for {guild_id}: {e}")
            return self._create_default_guild_data(guild_id)
    
    def update_guild_data(self, guild_id: int, data: Dict[str, Any]) -> bool:
        """Update guild data with validation"""
        try:
            # Validate data
            self.validator.validate_guild_data(data)
            
            # Add metadata
            data["last_updated"] = datetime.now(timezone.utc)
            
            # Try MongoDB first
            if self.connected_to_mongodb:
                with self._safe_operation(f"update_guild_data_{guild_id}"):
                    update_doc = {}
                    for key, value in data.items():
                        # Always set via $set, allowing dot-notation for nested fields
                        update_doc[key] = value
                    
                    result = self.guilds_collection.update_one(
                        {"guild_id": guild_id},
                        {"$set": update_doc},
                        upsert=True
                    )
                    
                    if result.acknowledged:
                        # Update memory cache
                        with self.memory_lock:
                            if guild_id not in self.memory_guilds:
                                self.memory_guilds[guild_id] = self._create_default_guild_data(guild_id)
                            self.memory_guilds[guild_id].update(data)
                        return True
            
            # Fallback to memory
            with self.memory_lock:
                if guild_id not in self.memory_guilds:
                    self.memory_guilds[guild_id] = self._create_default_guild_data(guild_id)
                
                # Handle nested updates
                for key, value in data.items():
                    if '.' in key:
                        keys = key.split('.')
                        current = self.memory_guilds[guild_id]
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = value
                    else:
                        self.memory_guilds[guild_id][key] = value
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating guild data for {guild_id}: {e}")
            return False
    
    def _create_default_guild_data(self, guild_id: int) -> Dict[str, Any]:
        """Create default guild data structure"""
        return {
            "guild_id": guild_id,
            "settings": {
                "prefix": "!",
                "welcome_channel": None,
                "modlog_channel": None,
                "join_leave_channel": None,
                "message_log_channel": None,
                "starboard_channel": None,
                "starboard_emoji": "⭐",
                "starboard_threshold": 3,
                "starboard_enabled": False,
                "logging_enabled": False,
                "welcome_enabled": False,
                "welcome_message": "Welcome {user} to {server}!",
                "leave_message": "Goodbye {user}! They were with us for {days} days.",
                "join_gif": "https://cdn.discordapp.com/attachments/1370993458700877964/1375089295257370624/image0.gif",
                "leave_gif": "https://cdn.discordapp.com/attachments/1351560015483240459/1368427641564299314/image0.gif",
                "ticket_category": None,
                "transcript_channel": None,
                "support_role": None,
                "tickets_enabled": False,
                "levelup_channel": None,
                "autorole": None
            },
            "economy": {
                "enabled": True,
                "daily_bonus": 100,
                "work_cooldown": 3600
            },
            "moderation": {
                "auto_mod": False,
                "warn_threshold": 3,
                "mute_role": None
            },
            "leveling": {
                "enabled": True,
                "xp_per_message": 15,
                "level_up_channel": None
            },
            "starboard_messages": {},
            "created_at": datetime.now(timezone.utc),
            "last_updated": datetime.now(timezone.utc)
        }
    
    # ==================== ADVANCED OPERATIONS ====================
    
    def get_leaderboard(self, field: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard with improved performance"""
        try:
            if self.connected_to_mongodb:
                with self._safe_operation(f"leaderboard_{field}"):
                    # Use aggregation for better performance
                    pipeline = [
                        {"$match": {field: {"$exists": True, "$gt": 0}}},
                        {"$sort": {field: -1}},
                        {"$limit": limit},
                        {"$project": {"_id": 0}}
                    ]
                    
                    cursor = self.users_collection.aggregate(pipeline)
                    return list(cursor)
            else:
                with self.memory_lock:
                    users = [user for user in self.memory_users.values() if user.get(field, 0) > 0]
                    users.sort(key=lambda x: x.get(field, 0), reverse=True)
                    return users[:limit]
                    
        except Exception as e:
            logger.error(f"Error getting leaderboard for {field}: {e}")
            return []
    
    def get_paginated_leaderboard(self, field: str, page: int = 1, members_per_page: int = 10) -> Dict[str, Any]:
        """Enhanced paginated leaderboard with better performance"""
        try:
            if self.connected_to_mongodb:
                with self._safe_operation(f"paginated_leaderboard_{field}"):
                    skip = (page - 1) * members_per_page
                    
                    # Get total count
                    total_users = self.users_collection.count_documents(
                        {field: {"$exists": True, "$gt": 0}}
                    )
                    total_pages = max(1, (total_users + members_per_page - 1) // members_per_page)
                    
                    # Get paginated results
                    pipeline = [
                        {"$match": {field: {"$exists": True, "$gt": 0}}},
                        {"$sort": {field: -1}},
                        {"$skip": skip},
                        {"$limit": members_per_page},
                        {"$project": {"_id": 0}}
                    ]
                    
                    cursor = self.users_collection.aggregate(pipeline)
                    users = list(cursor)
                    
                    return {
                        'users': users,
                        'total_pages': total_pages,
                        'total_users': total_users,
                        'current_page': page,
                        'members_per_page': members_per_page
                    }
            else:
                with self.memory_lock:
                    users = [user for user in self.memory_users.values() if user.get(field, 0) > 0]
                    users.sort(key=lambda x: x.get(field, 0), reverse=True)
                    
                    total_users = len(users)
                    total_pages = max(1, (total_users + members_per_page - 1) // members_per_page)
                    
                    start_idx = (page - 1) * members_per_page
                    end_idx = start_idx + members_per_page
                    paginated_users = users[start_idx:end_idx]
                    
                    return {
                        'users': paginated_users,
                        'total_pages': total_pages,
                        'total_users': total_users,
                        'current_page': page,
                        'members_per_page': members_per_page
                    }
                    
        except Exception as e:
            logger.error(f"Error getting paginated leaderboard: {e}")
            return {
                'users': [],
                'total_pages': 1,
                'total_users': 0,
                'current_page': page,
                'members_per_page': members_per_page
            }
    
    # ==================== UTILITY METHODS ====================
    
    def cleanup_expired_data(self):
        """Clean up expired data with better performance"""
        try:
            current_time = time.time()
            logger.info("🧹 Starting comprehensive database cleanup...")
            
            if self.connected_to_mongodb:
                with self._safe_operation("cleanup_expired_data"):
                    # Clean temporary purchases
                    self.users_collection.update_many(
                        {},
                        {"$pull": {"temporary_purchases": {"expires_at": {"$lt": current_time}}}}
                    )
                    
                    # Clean temporary roles
                    self.users_collection.update_many(
                        {},
                        {"$pull": {"temporary_roles": {"expires_at": {"$lt": current_time}}}}
                    )
                    
                    # Clean old reminders
                    self.users_collection.update_many(
                        {},
                        {"$pull": {"reminders": {"remind_at": {"$lt": current_time}}}}
                    )
                    
                logger.info("✅ MongoDB cleanup completed")
            else:
                # Clean memory storage
                with self.memory_lock:
                    for user_data in self.memory_users.values():
                        # Clean temporary purchases
                        if "temporary_purchases" in user_data:
                            user_data["temporary_purchases"] = [
                                item for item in user_data["temporary_purchases"]
                                if item.get("expires_at", 0) > current_time
                            ]
                        
                        # Clean temporary roles
                        if "temporary_roles" in user_data:
                            user_data["temporary_roles"] = [
                                item for item in user_data["temporary_roles"]
                                if item.get("expires_at", 0) > current_time
                            ]
                        
                        # Clean reminders
                        if "reminders" in user_data:
                            user_data["reminders"] = [
                                item for item in user_data["reminders"]
                                if item.get("remind_at", 0) > current_time
                            ]
                
                logger.info("✅ Memory cleanup completed")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {
                "storage_type": "MongoDB" if self.connected_to_mongodb else "Memory",
                "connection_status": "Connected" if self.connected_to_mongodb else "Fallback",
                "users": 0,
                "guilds": 0,
                "total_coins": 0,
                "total_xp": 0,
                "active_pets": 0,
                "active_investments": 0,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            if self.connected_to_mongodb:
                with self._safe_operation("database_stats"):
                    stats["users"] = self.users_collection.count_documents({})
                    stats["guilds"] = self.guilds_collection.count_documents({})
                    
                    # Aggregate statistics
                    pipeline = [
                        {"$group": {
                            "_id": None,
                            "total_coins": {"$sum": "$coins"},
                            "total_xp": {"$sum": "$xp"},
                            "avg_level": {"$avg": "$level"}
                        }}
                    ]
                    
                    result = list(self.users_collection.aggregate(pipeline))
                    if result:
                        stats.update({
                            "total_coins": result[0].get("total_coins", 0),
                            "total_xp": result[0].get("total_xp", 0),
                            "avg_level": round(result[0].get("avg_level", 1), 2)
                        })
            else:
                with self.memory_lock:
                    stats["users"] = len(self.memory_users)
                    stats["guilds"] = len(self.memory_guilds)
                    
                    # Calculate aggregates from memory
                    if self.memory_users:
                        stats["total_coins"] = sum(user.get("coins", 0) for user in self.memory_users.values())
                        stats["total_xp"] = sum(user.get("xp", 0) for user in self.memory_users.values())
                        stats["avg_level"] = sum(user.get("level", 1) for user in self.memory_users.values()) / len(self.memory_users)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {
                "storage_type": "Error",
                "connection_status": "Error",
                "users": 0,
                "guilds": 0,
                "error": str(e)
            }
    
    # ==================== WORK AND DAILY SYSTEM ====================
    
    def can_work(self, user_id: int) -> bool:
        """Check if user can work with cooldown"""
        try:
            user_data = self.get_user_data(user_id)
            last_work = user_data.get("last_work", 0)
            cooldown = 3600  # 1 hour default
            
            # Check for work energizer boost
            active_purchases = self.get_active_temporary_purchases(user_id)
            if any(p.get("item_type") == "work_energizer" for p in active_purchases):
                cooldown = 0  # No cooldown with boost
            
            return time.time() - last_work >= cooldown
        except Exception as e:
            logger.error(f"Error checking work status for {user_id}: {e}")
            return True
    
    def process_work(self, user_id: int, job_title: str, earnings: int) -> Dict[str, Any]:
        """Process work activity with enhanced tracking"""
        try:
            current_time = time.time()
            user_data = self.get_user_data(user_id)
            
            # Calculate work streak
            last_work = user_data.get("last_work", 0)
            work_streak = user_data.get("work_streak", 0)
            
            if current_time - last_work <= 86400:  # Within 24 hours
                work_streak += 1
            else:
                work_streak = 1
            
            # Update work data
            update_data = {
                "last_work": current_time,
                "work_streak": work_streak,
                "work_count": user_data.get("work_count", 0) + 1
            }
            
            # Add earnings
            if earnings > 0:
                self.add_coins(user_id, earnings)
            
            # Add work XP
            xp_gained = 25
            if work_streak > 7:
                xp_gained += 10  # Bonus XP for long streaks
            
            self.add_xp(user_id, xp_gained)
            
            success = self.update_user_data(user_id, update_data)
            
            return {
                "success": success,
                "earnings": earnings,
                "xp_gained": xp_gained,
                "work_streak": work_streak,
                "work_count": update_data["work_count"]
            }
            
        except Exception as e:
            logger.error(f"Error processing work for {user_id}: {e}")
            return {"success": False}
    
    def claim_daily_bonus(self, user_id: int) -> Dict[str, Any]:
        """Enhanced daily bonus system with comprehensive tracking"""
        try:
            user_data = self.get_user_data(user_id)
            current_time = time.time()
            last_daily = user_data.get("last_daily", 0)
            
            # Check if already claimed today
            if current_time - last_daily < 86400:  # 24 hours
                time_left = 86400 - (current_time - last_daily)
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                return {
                    "success": False,
                    "message": f"Already claimed! Next claim in {hours}h {minutes}m"
                }
            
            # Calculate streak
            streak = user_data.get("daily_streak", 0)
            if current_time - last_daily <= 172800:  # Within 48 hours
                streak += 1
            else:
                streak = 1
            
            # Calculate rewards with enhanced bonuses
            base_coins = 100
            base_xp = 50
            
            # Streak bonuses (progressive)
            streak_multiplier = min(1 + (streak * 0.1), 3.0)  # Max 3x multiplier
            total_coins = int(base_coins * streak_multiplier)
            total_xp = int(base_xp * streak_multiplier)
            
            # Milestone bonuses
            milestone_bonus = 0
            if streak == 7:
                milestone_bonus = 500
            elif streak == 30:
                milestone_bonus = 2000
            elif streak == 100:
                milestone_bonus = 10000
            elif streak == 365:
                milestone_bonus = 50000
            
            total_coins += milestone_bonus
            
            # Apply rewards
            self.add_coins(user_id, total_coins)
            xp_result = self.add_xp(user_id, total_xp)
            
            # Update daily data
            self.update_user_data(user_id, {
                "last_daily": current_time,
                "daily_streak": streak
            })
            
            return {
                "success": True,
                "coins_earned": total_coins,
                "xp_earned": total_xp,
                "streak": streak,
                "milestone_bonus": milestone_bonus,
                "level_up": xp_result.get("leveled_up", False),
                "new_level": xp_result.get("new_level", user_data.get("level", 1))
            }
            
        except Exception as e:
            logger.error(f"Error claiming daily bonus for {user_id}: {e}")
            return {"success": False, "message": "An error occurred"}
    
    def add_temporary_purchase(self, user_id: int, item_type: str, duration: int) -> bool:
        """Add temporary purchase with better stacking"""
        try:
            current_time = time.time()
            expiry_time = current_time + duration
            
            user_data = self.get_user_data(user_id)
            temp_purchases = user_data.get("temporary_purchases", [])
            
            # Check if same item type exists and stack duration
            existing_item = None
            for item in temp_purchases:
                if item.get("item_type") == item_type:
                    existing_item = item
                    break
            
            if existing_item:
                # Stack duration
                existing_item["expires_at"] = max(existing_item.get("expires_at", 0), current_time) + duration
            else:
                # Add new item
                purchase_data = {
                    "item_type": item_type,
                    "expires_at": expiry_time,
                    "purchased_at": current_time
                }
                temp_purchases.append(purchase_data)
            
            return self.update_user_data(user_id, {"temporary_purchases": temp_purchases})
            
        except Exception as e:
            logger.error(f"Error adding temporary purchase: {e}")
            return False
    
    def get_active_temporary_purchases(self, user_id: int) -> List[Dict[str, Any]]:
        """Get active temporary purchases with cleanup"""
        try:
            user_data = self.get_user_data(user_id)
            current_time = time.time()
            all_purchases = user_data.get("temporary_purchases", [])
            
            # Filter active purchases
            active_purchases = [
                purchase for purchase in all_purchases
                if purchase.get("expires_at", 0) > current_time
            ]
            
            # If we filtered out expired items, update the database
            if len(active_purchases) != len(all_purchases):
                self.update_user_data(user_id, {"temporary_purchases": active_purchases})
            
            return active_purchases
            
        except Exception as e:
            logger.error(f"Error getting active purchases for {user_id}: {e}")
            return []


# Create global database instance
db = DatabaseManager()

# ==================== LEGACY COMPATIBILITY FUNCTIONS ====================

def get_user_data(user_id: int) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    return db.get_user_data(user_id)

def update_user_data(user_id: int, data: Dict[str, Any]) -> bool:
    """Legacy function for backward compatibility"""
    return db.update_user_data(user_id, data)

def add_coins(user_id: int, amount: int) -> bool:
    """Legacy function for backward compatibility"""
    return db.add_coins(user_id, amount)

def remove_coins(user_id: int, amount: int) -> bool:
    """Legacy function for backward compatibility"""
    return db.remove_coins(user_id, amount)

def get_database():
    """Get database instance"""
    return db

def cleanup_expired_items():
    """Legacy cleanup function"""
    return db.cleanup_expired_data()

def get_active_temporary_purchases(user_id: int):
    """Legacy function for active temporary purchases"""
    return db.get_active_temporary_purchases(user_id)

def add_xp(user_id: int, amount: int):
    """Legacy function for adding XP"""
    return db.add_xp(user_id, amount)

def claim_daily_bonus(user_id: int):
    """Legacy function for claiming daily bonus"""
    return db.claim_daily_bonus(user_id)

# ==================== PERIODIC TASKS ====================

async def periodic_cleanup():
    """Run periodic cleanup tasks"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            db.cleanup_expired_data()
            
            # Attempt reconnection if disconnected
            if not db.connected_to_mongodb:
                db.reconnect_mongodb()
                
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

async def periodic_health_check():
    """Run periodic health checks"""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            health = db.get_database_health()
            
            if not health.get("mongodb_connected", False) and db.connected_to_mongodb:
                logger.warning("MongoDB connection lost, attempting reconnection...")
                db.reconnect_mongodb()
                
        except Exception as e:
            logger.error(f"Error in periodic health check: {e}")

# Export commonly used functions
__all__ = [
    'DatabaseManager', 'db', 'get_user_data', 'update_user_data', 
    'add_coins', 'remove_coins', 'get_database', 'cleanup_expired_items',
    'get_active_temporary_purchases', 'add_xp',
    'claim_daily_bonus', 'periodic_cleanup', 'periodic_health_check'
]

logger.info("🎯 Enhanced database system initialized successfully!")
logger.info(f"📊 Storage mode: {'MongoDB' if db.connected_to_mongodb else 'Memory'}")
logger.info(f"🔧 Available methods: {len([m for m in dir(db) if not m.startswith('_')])}")

# Schedule periodic tasks if running in async context
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(periodic_cleanup())
        asyncio.create_task(periodic_health_check())
except RuntimeError:
    # Not in async context, tasks will be scheduled when bot starts
    pass
