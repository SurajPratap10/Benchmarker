"""
User database management for Benchmarker
"""
import sqlite3
import hashlib
import os
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

class UserDatabase:
    """Manages user accounts and authentication"""
    
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a new user
        Returns (success, message)
        """
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Hash password
        password_hash = self._hash_password(password)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO users (username, password_hash, email)
                VALUES (?, ?, ?)
            """, (username.lower(), password_hash, email))
            
            conn.commit()
            conn.close()
            
            return True, "Account created successfully"
        
        except sqlite3.IntegrityError:
            return False, "Username already exists"
        except Exception as e:
            return False, f"Error creating account: {str(e)}"
    
    def verify_user(self, username: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verify user credentials
        Returns (success, user_data or None)
        """
        password_hash = self._hash_password(password)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at, is_active
            FROM users
            WHERE username = ? AND password_hash = ?
        """, (username.lower(), password_hash))
        
        result = cursor.fetchone()
        
        if result:
            user_data = {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": result[3],
                "is_active": result[4]
            }
            
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now().isoformat(), user_data["id"]))
            
            conn.commit()
            conn.close()
            
            if not user_data["is_active"]:
                return False, None
            
            return True, user_data
        
        conn.close()
        return False, None
    
    def user_exists(self, username: str) -> bool:
        """Check if username exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.lower(),))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": result[3]
            }
        
        return None
    
    def get_total_users(self) -> int:
        """Get total number of users"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count

# Global user database instance
user_db = UserDatabase()

