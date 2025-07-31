#!/usr/bin/env python3
"""
Moderation and User Tracking System for iHub Bot

This module provides user behavior tracking, content moderation,
IP address logging, and administrative controls.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib
import sqlite3
from dataclasses import dataclass, asdict
from flask import request

@dataclass
class UserSession:
    """Represents a user session with tracking data"""
    ip_address: str
    session_start: str
    messages_sent: int = 0
    flagged_messages: int = 0
    warnings_issued: int = 0
    last_activity: str = ""
    user_agent: str = ""
    is_blocked: bool = False
    block_reason: str = ""
    block_expires: str = ""

class ModerationSystem:
    def __init__(self, db_path='moderation.db'):
        self.db_path = db_path
        self.init_database()
        self.load_bad_words()
        self.load_config()
        
    def init_database(self):
        """Initialize SQLite database for user tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                ip_address TEXT PRIMARY KEY,
                session_start TEXT,
                messages_sent INTEGER DEFAULT 0,
                flagged_messages INTEGER DEFAULT 0,
                warnings_issued INTEGER DEFAULT 0,
                last_activity TEXT,
                user_agent TEXT,
                is_blocked BOOLEAN DEFAULT FALSE,
                block_reason TEXT,
                block_expires TEXT
            )
        ''')
        
        # Message logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                timestamp TEXT,
                message_content TEXT,
                is_flagged BOOLEAN DEFAULT FALSE,
                flag_reasons TEXT,
                user_agent TEXT,
                response_time_ms INTEGER
            )
        ''')
        
        # Moderation actions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS moderation_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                action_type TEXT,
                reason TEXT,
                timestamp TEXT,
                admin_id TEXT,
                expires_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_bad_words(self):
        """Load bad words list from file or use defaults"""
        default_bad_words = [
            # Profanity
            "fuck", "shit", "damn", "bitch", "asshole", "bastard",
            # Hate speech indicators
            "hate", "stupid", "idiot", "retard", "kill yourself",
            # Spam indicators
            "buy now", "click here", "free money", "viagra",
            # Inappropriate requests
            "hack", "break", "destroy", "damage", "illegal"
        ]
        
        try:
            if os.path.exists('bad_words.json'):
                with open('bad_words.json', 'r') as f:
                    data = json.load(f)
                    self.bad_words = data.get('words', default_bad_words)
                    self.bad_patterns = data.get('patterns', [])
            else:
                self.bad_words = default_bad_words
                self.bad_patterns = [
                    r'\b(fuck|shit|damn)\w*\b',  # Variations of bad words
                    r'\b(kill\s+yourself)\b',   # Harmful phrases
                    r'\b(hack\s+into)\b',       # Malicious intent
                    r'(.)\1{4,}',               # Excessive repetition
                ]
                self.save_bad_words()
        except Exception as e:
            print(f"Error loading bad words: {e}")
            self.bad_words = default_bad_words
            self.bad_patterns = []
    
    def save_bad_words(self):
        """Save bad words configuration to file"""
        data = {
            'words': self.bad_words,
            'patterns': self.bad_patterns
        }
        with open('bad_words.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_config(self):
        """Load moderation configuration"""
        default_config = {
            'max_messages_per_hour': 60,
            'max_flagged_messages': 3,
            'auto_block_threshold': 5,
            'rate_limit_window_minutes': 60,
            'warning_threshold': 2,
            'block_duration_hours': 24
        }
        
        try:
            if os.path.exists('moderation_config.json'):
                with open('moderation_config.json', 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = default_config
    
    def save_config(self):
        """Save moderation configuration"""
        with open('moderation_config.json', 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_client_ip(self) -> str:
        """Get client IP address from Flask request"""
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return request.environ['REMOTE_ADDR']
        else:
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
    
    def hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy (optional)"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def check_message_content(self, message: str) -> Tuple[bool, List[str]]:
        """Check message for inappropriate content"""
        flags = []
        message_lower = message.lower()
        
        # Check for bad words
        for word in self.bad_words:
            if word.lower() in message_lower:
                flags.append(f"inappropriate_language:{word}")
        
        # Check for patterns
        for pattern in self.bad_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                flags.append(f"pattern_match:{pattern}")
        
        # Check for excessive caps
        if len(message) > 10 and sum(1 for c in message if c.isupper()) / len(message) > 0.7:
            flags.append("excessive_caps")
        
        # Check for spam indicators
        if len(message) > 500:
            flags.append("message_too_long")
        
        # Check for repeated characters
        if re.search(r'(.)\1{5,}', message):
            flags.append("excessive_repetition")
        
        return len(flags) > 0, flags
    
    def log_message(self, ip: str, message: str, is_flagged: bool, 
                   flag_reasons: List[str], response_time: int = 0):
        """Log user message to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
        
        cursor.execute('''
            INSERT INTO message_logs 
            (ip_address, timestamp, message_content, is_flagged, flag_reasons, user_agent, response_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ip, 
            datetime.now().isoformat(),
            message[:1000],  # Limit message length in DB
            is_flagged,
            json.dumps(flag_reasons),
            user_agent,
            response_time
        ))
        
        conn.commit()
        conn.close()
    
    def update_user_session(self, ip: str) -> UserSession:
        """Update or create user session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get existing session
        cursor.execute('SELECT * FROM user_sessions WHERE ip_address = ?', (ip,))
        row = cursor.fetchone()
        
        user_agent = request.headers.get('User-Agent', '')[:500]
        now = datetime.now().isoformat()
        
        if row:
            # Update existing session
            cursor.execute('''
                UPDATE user_sessions 
                SET messages_sent = messages_sent + 1, last_activity = ?, user_agent = ?
                WHERE ip_address = ?
            ''', (now, user_agent, ip))
            
            # Fetch updated data
            cursor.execute('SELECT * FROM user_sessions WHERE ip_address = ?', (ip,))
            row = cursor.fetchone()
        else:
            # Create new session
            cursor.execute('''
                INSERT INTO user_sessions 
                (ip_address, session_start, messages_sent, last_activity, user_agent)
                VALUES (?, ?, 1, ?, ?)
            ''', (ip, now, now, user_agent))
            
            cursor.execute('SELECT * FROM user_sessions WHERE ip_address = ?', (ip,))
            row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        # Convert to UserSession object
        session = UserSession(
            ip_address=row[0],
            session_start=row[1],
            messages_sent=row[2],
            flagged_messages=row[3],
            warnings_issued=row[4],
            last_activity=row[5],
            user_agent=row[6],
            is_blocked=bool(row[7]),
            block_reason=row[8] or "",
            block_expires=row[9] or ""
        )
        
        return session
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """Check if user is rate limited"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check messages in last hour
        hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM message_logs 
            WHERE ip_address = ? AND timestamp > ?
        ''', (ip, hour_ago))
        
        message_count = cursor.fetchone()[0]
        conn.close()
        
        if message_count >= self.config['max_messages_per_hour']:
            return True, f"Rate limit exceeded: {message_count} messages in last hour"
        
        return False, ""
    
    def flag_user_message(self, ip: str, flag_reasons: List[str]):
        """Flag a user message and update their session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET flagged_messages = flagged_messages + 1
            WHERE ip_address = ?
        ''', (ip,))
        
        # Check if auto-block threshold reached
        cursor.execute('SELECT flagged_messages FROM user_sessions WHERE ip_address = ?', (ip,))
        flagged_count = cursor.fetchone()[0]
        
        if flagged_count >= self.config['auto_block_threshold']:
            self.block_user(ip, f"Auto-blocked after {flagged_count} flagged messages", 
                           self.config['block_duration_hours'])
        
        conn.commit()
        conn.close()
    
    def block_user(self, ip: str, reason: str, duration_hours: int = 24, admin_id: str = "system"):
        """Block a user for specified duration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        
        # Update user session
        cursor.execute('''
            UPDATE user_sessions 
            SET is_blocked = TRUE, block_reason = ?, block_expires = ?
            WHERE ip_address = ?
        ''', (reason, expires_at, ip))
        
        # Log moderation action
        cursor.execute('''
            INSERT INTO moderation_actions 
            (ip_address, action_type, reason, timestamp, admin_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ip, "block", reason, datetime.now().isoformat(), admin_id, expires_at))
        
        conn.commit()
        conn.close()
    
    def unblock_user(self, ip: str, admin_id: str = "system"):
        """Unblock a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_sessions 
            SET is_blocked = FALSE, block_reason = '', block_expires = ''
            WHERE ip_address = ?
        ''', (ip,))
        
        # Log moderation action
        cursor.execute('''
            INSERT INTO moderation_actions 
            (ip_address, action_type, reason, timestamp, admin_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip, "unblock", "Manual unblock", datetime.now().isoformat(), admin_id))
        
        conn.commit()
        conn.close()
    
    def is_user_blocked(self, ip: str) -> Tuple[bool, str]:
        """Check if user is currently blocked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT is_blocked, block_reason, block_expires 
            FROM user_sessions WHERE ip_address = ?
        ''', (ip,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0]:
            return False, ""
        
        # Check if block has expired
        if row[2]:  # block_expires
            expires_at = datetime.fromisoformat(row[2])
            if datetime.now() > expires_at:
                self.unblock_user(ip, "auto_expire")
                return False, ""
        
        return True, row[1]  # block_reason
    
    def get_user_stats(self, ip: str = None) -> Dict:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if ip:
            # Individual user stats
            cursor.execute('SELECT * FROM user_sessions WHERE ip_address = ?', (ip,))
            session = cursor.fetchone()
            
            cursor.execute('''
                SELECT COUNT(*), COUNT(CASE WHEN is_flagged THEN 1 END)
                FROM message_logs WHERE ip_address = ?
            ''', (ip,))
            message_stats = cursor.fetchone()
            
            conn.close()
            
            if session:
                return {
                    'ip_address': session[0],
                    'session_start': session[1],
                    'total_messages': message_stats[0],
                    'flagged_messages': message_stats[1],
                    'warnings_issued': session[4],
                    'is_blocked': bool(session[7]),
                    'block_reason': session[8],
                    'last_activity': session[5]
                }
        else:
            # Overall stats
            cursor.execute('SELECT COUNT(DISTINCT ip_address) FROM user_sessions')
            total_users = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM message_logs')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM message_logs WHERE is_flagged = TRUE')
            flagged_messages = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM user_sessions WHERE is_blocked = TRUE')
            blocked_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'total_messages': total_messages,
                'flagged_messages': flagged_messages,
                'blocked_users': blocked_users,
                'flagged_percentage': (flagged_messages / total_messages * 100) if total_messages > 0 else 0
            }
        
        conn.close()
        return {}
    
    def get_recent_activity(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """Get recent user activity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT ip_address, timestamp, message_content, is_flagged, flag_reasons
            FROM message_logs 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (since, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'ip_address': row[0],
                'timestamp': row[1],
                'message': row[2][:100] + '...' if len(row[2]) > 100 else row[2],
                'is_flagged': bool(row[3]),
                'flag_reasons': json.loads(row[4]) if row[4] else []
            }
            for row in rows
        ]
    
    def moderate_message(self, message: str) -> Dict:
        """Main moderation function - call this for each message"""
        ip = self.get_client_ip()
        
        # Check if user is blocked
        is_blocked, block_reason = self.is_user_blocked(ip)
        if is_blocked:
            return {
                'allowed': False,
                'reason': 'user_blocked',
                'message': f"Your access has been temporarily restricted: {block_reason}",
                'retry_after': None
            }
        
        # Check rate limiting
        rate_limited, rate_message = self.check_rate_limit(ip)
        if rate_limited:
            return {
                'allowed': False,
                'reason': 'rate_limited',
                'message': rate_message,
                'retry_after': 3600  # 1 hour
            }
        
        # Check message content
        is_flagged, flag_reasons = self.check_message_content(message)
        
        # Update user session
        session = self.update_user_session(ip)
        
        # Log message
        self.log_message(ip, message, is_flagged, flag_reasons)
        
        # Handle flagged message
        if is_flagged:
            self.flag_user_message(ip, flag_reasons)
            return {
                'allowed': False,
                'reason': 'content_flagged',
                'message': "Your message contains inappropriate content. Please keep conversations respectful and on-topic.",
                'flags': flag_reasons
            }
        
        return {
            'allowed': True,
            'reason': 'approved',
            'session_info': asdict(session)
        }

# Initialize global moderation system
moderation = ModerationSystem()