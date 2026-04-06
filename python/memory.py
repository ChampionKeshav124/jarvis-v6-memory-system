import sqlite3
import os
import json
from datetime import datetime
import re

class MemoryCore:
    def __init__(self, db_path=None):
        # V6.2: Universal root resolution
        current_file = os.path.abspath(__file__)
        self.root_dir = os.path.dirname(os.path.dirname(current_file))
        self.memory_dir = os.path.join(self.root_dir, "memory")
        
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        if db_path is None:
            self.db_path = os.path.join(self.memory_dir, "jarvis_memory.db")
        else:
            self.db_path = db_path
            
        # Migration: Check if old DB exists in python folder and move it
        old_db = os.path.join(os.path.dirname(__file__), "jarvis_memory.db")
        if os.path.exists(old_db) and not os.path.exists(self.db_path):
            try:
                os.rename(old_db, self.db_path)
            except: pass
            
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database with the required V6 schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                labels TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_user_info_from_file(self):
        """Parses the user_info.txt file if it exists and returns a dict."""
        info = {}
        info_file = os.path.join(self.memory_dir, "user_info.txt")
        if not os.path.exists(info_file):
            return info
            
        try:
            with open(info_file, "r") as f:
                for line in f:
                    if ":" in line and not line.startswith("#"):
                        key, val = line.split(":", 1)
                        val = val.strip()
                        # Check for placeholders
                        if val and not val.startswith("[ENTER_") and val != "[ANY_OTHER_INFO]":
                            info[key.strip().lower()] = val
        except: pass
        return info

    def get_preferences(self):
        """Retrieves all user preferences, prioritizing the user_info.txt file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM preferences")
        db_raw = {row[0].lower().replace("user_", ""): row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Merge with file info (file info takes precedence)
        file_info = self.get_user_info_from_file()
        
        # Standardize keys from file
        standard_file_info = {k.replace("user_", ""): v for k, v in file_info.items()}
        
        # Combine: file overrides DB
        final_prefs = db_raw.copy()
        final_prefs.update(standard_file_info)
        
        # Add a flag if the user is completely unknown
        if not standard_file_info and "name" not in final_prefs:
            final_prefs["__is_unknown__"] = "true"
            
        return final_prefs

    def store_preference(self, key, value):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        conn.close()
        
        # V6.7: Bi-directional Sync for Core Identity
        core_keys = ["name", "occupation", "interests"]
        check_key = key.lower().replace("user_", "")
        if check_key in core_keys:
            self.sync_to_user_info_file(check_key.capitalize(), value)
            
        return f"Stored: {key} = {value}"

    def sync_to_user_info_file(self, key, value):
        """Updates or appends a key-value pair in the user_info.txt file."""
        info_file = os.path.join(self.memory_dir, "user_info.txt")
        lines = []
        
        # Ensure directory exists
        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)
            
        if os.path.exists(info_file):
            with open(info_file, "r") as f:
                lines = f.readlines()
        
        updated = False
        new_lines = []
        for line in lines:
            if line.strip().lower().startswith(key.lower() + ":"):
                new_lines.append(f"{key}: {value}\n")
                updated = True
            else:
                new_lines.append(line)
        
        if not updated:
            # If [USER_INFO] tag exists, append after it. Otherwise append to end.
            inserted = False
            for i, line in enumerate(new_lines):
                if "[USER_INFO]" in line:
                    new_lines.insert(i+1, f"{key}: {value}\n")
                    inserted = True
                    break
            if not inserted:
                if not new_lines:
                    new_lines.append("[USER_INFO]\n")
                new_lines.append(f"{key}: {value}\n")
                
        with open(info_file, "w") as f:
            f.writelines(new_lines)

    def start_conversation(self, title="New Conversation", labels=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (title, labels) VALUES (?, ?)", (title, labels))
        conv_id = cursor.lastrowid
        conn.commit()
        conn.close()
        self.export_conversation_to_file(conv_id) # Initial export
        return conv_id

    def add_message(self, conversation_id, role, content):
        if conversation_id is None:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)", 
                       (conversation_id, role, content))
        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (conversation_id,))
        conn.commit()
        conn.close()
        
        # V6.10: Real-time Append to Chat Log (High Visibility)
        self.append_to_chat_log(conversation_id, role, content)

    def get_history(self, conversation_id, limit=15):
        if conversation_id is None:
            return []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT role, content FROM (
                SELECT role, content, timestamp FROM messages 
                WHERE conversation_id = ? 
                ORDER BY timestamp DESC LIMIT ?
            ) sub ORDER BY timestamp ASC
        """, (conversation_id, limit))
        history = [{"role": row[0], "parts": [{"text": row[1]}]} for row in cursor.fetchall()]
        conn.close()
        return history

    def _get_conversation_path(self, conversation_id, title):
        """Standardized naming for conversation files: Conversation_[ID]_[Title].md"""
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
        if not safe_title: safe_title = "Untitled"
        filename = f"Conversation_{conversation_id}_{safe_title}.md"
        return os.path.join(self.memory_dir, filename)

    def append_to_chat_log(self, conversation_id, role, content):
        """Appends a single message to the conversation's Markdown file in real-time."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row: return
            title = row[0]
            filepath = self._get_conversation_path(conversation_id, title)
            
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            name = "USER" if role == "user" else "JARVIS"
            
            # Start file if it doesn't exist
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n")
                    f.write(f"**ID:** {conversation_id}\n")
                    f.write(f"**Started:** {ts}\n\n---\n\n")
            
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(f"### {name} ({ts})\n{content}\n\n")
                f.flush()
                os.fsync(f.fileno())
        except: pass

    def rename_conversation(self, conversation_id, new_title):
        if conversation_id is None:
            return
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))
        conn.commit()
        conn.close()
        self.export_conversation_to_file(conversation_id)
        return f"Conversation {conversation_id} renamed to '{new_title}'"

    def export_conversation_to_file(self, conversation_id):
        """Exports a conversation thread to a readable Markdown file in the memory folder."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT title, labels FROM conversations WHERE id = ?", (conversation_id,))
            row = cursor.fetchone()
            if not row: return
            title, labels = row
            
            cursor.execute("SELECT role, content, timestamp FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
            messages = cursor.fetchall()
            conn.close()
            
            # Sanitize title for 'normal' filename
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
            if not safe_title: safe_title = f"Conv_{conversation_id}"
            
            filename = self._get_conversation_path(conversation_id, title)
            filepath = filename # (already absolute from the helper)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n")
                if labels:
                    f.write(f"**Labels:** {labels}\n")
                f.write(f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                for role, content, ts in messages:
                    name = "USER" if role == "user" else "JARVIS"
                    f.write(f"### {name} ({ts})\n{content}\n\n")
        except: pass

    def search_conversations(self, query):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT c.id, c.title, c.updated_at
            FROM conversations c 
            JOIN messages m ON c.id = m.conversation_id 
            WHERE c.title LIKE ? OR m.content LIKE ?
            ORDER BY c.updated_at DESC
        ''', (f"%{query}%", f"%{query}%"))
        results = [f"ID: {row[0]} | Title: {row[1]} | Last Activity: {row[2]}" for row in cursor.fetchall()]
        conn.close()
        return "\n".join(results) if results else "No matching conversations found."

    def get_conversation_title(self, conversation_id):
        if conversation_id is None: return "Untitled"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "Untitled"

    def get_last_conversation_id(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM conversations ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
