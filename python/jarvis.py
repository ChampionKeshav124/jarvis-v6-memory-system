"""
 ═══════════════════════════════════════════════════════════════
  JARVIS V6 — Python Backend Bridge
  BYTEFORGE SYSTEM
 
  V6: Persistent Memory & Dedicated Workspace.
      System commands handled INSTANTLY.
 ═══════════════════════════════════════════════════════════════
"""

import sys
import json
import os
import base64
import requests
import re
from datetime import datetime
from memory import MemoryCore
from google import genai
from google.genai import types

_MEMORY = MemoryCore()

# V6.13: ATOMIC HARDENED FLOOD GATE (Zero-429 Resilience)
def _check_flood_gate():
    """Atomic-ish gate to prevent 429 errors from multiple processes."""
    import time, msvcrt
    gate_file = os.path.join(_MEMORY.memory_dir, "flood_gate.txt")
    now = time.time()
    
    # 7.0 seconds for 'Nuclear' safety on 15-RPM Free Tier
    COOLDOWN = 7.0 

    try:
        # Open in read+write mode to set a lock
        mode = os.O_RDWR | os.O_CREAT
        fd = os.open(gate_file, mode)
        try:
            # 1. Lock the file exclusively (wait for it)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1024)
            
            # 2. Read timestamp
            os.lseek(fd, 0, os.SEEK_SET)
            data = os.read(fd, 1024).decode().strip()
            if data:
                last_call = float(data)
                if now - last_call < COOLDOWN:
                    return True
            
            # 3. Update timestamp
            os.lseek(fd, 0, os.SEEK_SET)
            os.ftruncate(fd, 0)
            os.write(fd, str(now).encode())
            return False
            
        finally:
            os.close(fd)
    except: 
        return False # Fallback to allowing if file system fails

def _store_preference_tool(key: str, value: str) -> str:
    """
    Tool to store or update user preferences, roles, or biographical data.
    This is called automatically by the AI when information is provided.
    """
    try:
        # Assuming update_preferences exists in MemoryCore
        _MEMORY.update_preferences({key: value})
        return f"Successfully updated memory: {key} is now '{value}'."
    except Exception as e:
        return f"Failed to update memory: {str(e)}"

def run_code(code: str) -> str:
    """Executes python code. Required to explicitly disable the default code execution tool."""
    return "Code execution is disabled locally. Please provide the plain text code directly to the user."

def _call_gemini_api(model: str, contents: list, config: dict = None, tools: list = None) -> str:
    """Centralized, throttled gateway for all Gemini API calls (V6.12)."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY" or len(GEMINI_API_KEY) < 15:
        return "Please put your API keys in the config.py program file to establish a neural link."

    if _check_flood_gate():
        return "Neural sync in progress. Throttled locally to protect quota."
    
    # Ensure tools are correctly injected into the configuration
    if tools:
        config = config or {}
        config['tools'] = tools

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config
        )
        # Safely extract text — avoid KeyError when model returns function-call parts
        text_parts = []
        try:
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
        except Exception:
            pass
        if text_parts:
            return "\n".join(text_parts)
        # Last resort fallback
        try:
            if response.text:
                return response.text
        except Exception:
            pass
        return "I processed your request but couldn't format a response. Please try again."
    except Exception as e:
        return f"API ERROR: {repr(e)}"

# ── API Keys & Config ─────────────────────────────────────────
def _load_config(key_name, default_val):
    try:
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        sys.path.insert(0, parent_dir)
        import config
        return getattr(config, key_name, default_val)
    except Exception:
        return os.environ.get(key_name, default_val)

GEMINI_API_KEY    = _load_config("GEMINI_API_KEY",    "YOUR_API_KEY")
ELEVENLABS_API_KEY  = _load_config("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = _load_config("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJcg")

# ── System Control Integration ───────────────────────────────
try:
    from system_tools import tools
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from system_tools import tools

# ── Local Intent Patterns (no API needed) ────────────────────
# These patterns are matched INSTANTLY without any network call.
_OPEN_APP_PATTERN  = re.compile(
    r'^(?:please\s+)?(?:open|launch|start|run|execute|play)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|program|software))?\s*$',
    re.IGNORECASE
)
_CLOSE_APP_PATTERN = re.compile(
    r'^(?:please\s+)?(?:close|quit|kill|terminate|exit|stop)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|program|software))?\s*$',
    re.IGNORECASE
)
_OPEN_URL_PATTERN  = re.compile(
    r'^(?:please\s+)?(?:open|go\s+to|navigate\s+to|visit|browse\s+to|show\s+me)\s+(?:the\s+)?(?:website\s+)?(?:https?://)?(.+?)\s*$',
    re.IGNORECASE
)
_SEARCH_SYSTEM_PATTERN = re.compile(
    r'^(?:please\s+)?search\s+(?:the|my)?\s*(?:system|computer|pc|files)\s+(?:for\s+)?(.+?)\s*$',
    re.IGNORECASE
)
_SEARCH_GOOGLE_PATTERN = re.compile(
    r'^(?:please\s+)?(?:search\s+(?:in\s+)?google|google)\s+(?:for\s?|the\s?)?(.+?)(?:\s+online|\s+on\s+the\s+web)?\s*$',
    re.IGNORECASE
)
_IDLE_MODE_PATTERN = re.compile(
    r'^(?:please\s+)?(?:enter|go\s+to|put\s+in|switch\s+to)\s+(?:idle|sleep|quiet|waiting)\s+mode\s*$',
    re.IGNORECASE
)
_SHOW_LOGS_PATTERN = re.compile(
    r'^(?:please\s+)?(?:show|display|access|read)\s+(?:the\s+)?(?:logs|history|chat logs|conversation history)\s*$',
    re.IGNORECASE
)

# --- TITAN PATTERNS ---
_GAME_INSTALL_PATTERN = re.compile(
    r'^(?:please\s+)?(?:install|setup|download|play)\s+(.+?)(?:\s+(?:on|from|in)\s+(steam|epic|epic\s+games))?\s*$',
    re.IGNORECASE
)
_WHATSAPP_PATTERN = re.compile(
    r'^(?:please\s+)?(?:send\s+(?:a\s+)?whatsapp|whatsapp)\s+(?:to\s+)?(\d+)\s+(?:saying|message|texting)\s+(.+?)\s*$',
    re.IGNORECASE
)
_SCOUT_PATTERN = re.compile(
    r'^(?:please\s+)?(?:search|scout|look\s+up)\s+(amazon|github|reddit|youtube)\s+(?:for\s+)?(.+?)\s*$',
    re.IGNORECASE
)
_TYPE_PATTERN = re.compile(
    r'^(?:please\s+)?(?:type|write|dictate)\s+(.+?)\s*$',
    re.IGNORECASE
)
_YOUTUBE_PATTERN = re.compile(
    r'^(?:please\s+)?(?:play|find)\s+(.+?)\s+on\s+youtube\s*$',
    re.IGNORECASE
)
_UPDATE_PATTERN = re.compile(
    r'^(?:please\s+)?(?:update|upgrade)\s+(?:my\s+)?(?:pc|computer|system|software|games)(?:\s+now)?\s*$',
    re.IGNORECASE
)
# Vision-Atomic Patterns (Titan-Vision Upgrade)
_CLICK_PATTERN  = re.compile(r"(?i)^(?:please\s+)?(?:click|tap|double click|right click)\s*(?:on|at)?\s*(.*)$")
_FIND_PATTERN   = re.compile(r"(?i)^(?:please\s+)?(?:find|locate|where is)\s+(.*)$")
_SCROLL_PATTERN = re.compile(r"(?i)^(?:please\s+)?scroll\s+(up|down|left|right)?(?:\s+(.*))?$")
_HOTKEY_PATTERN = re.compile(r"(?i)^(?:please\s+)?(?:press|hotkey)\s+(.*)$")
# ----------------------

_SEARCH_PATTERN = re.compile(
    r'^(?:please\s+)?(?:search|find|look\s+for|locate)\s+(?:for\s+)?(.+?)\s*$',
    re.IGNORECASE
)

# Popular AppID Mapping for Zero-Lag (Steam)
_COMMON_STEAM_IDS = {
    "csgo": "730", "counter strike": "730", "cs2": "730",
    "dota": "570", "dota 2": "570",
    "pubg": "578080", "elden ring": "1245620",
    "cyberpunk": "1091500", "gta": "271590", "stardew valley": "413150"
}
# JARVIS STATE (Context for Aegis Protocol)
def load_state():
    try:
        with open(os.path.join(os.path.dirname(__file__), "state.json"), "r") as f:
            return json.load(f)
    except Exception:
        return {"last_scout": None}

def save_state(state):
    try:
        with open(os.path.join(os.path.dirname(__file__), "state.json"), "w") as f:
            json.dump(state, f)
    except Exception:
        pass

_JARVIS_STATE = load_state()

def _local_intent(command: str):
    """
    Tries to match command against local patterns instantly.
    Returns (action_fn, arg) or None if no match.
    """
    cmd = command.strip().lower()

    # 1. Aegis Confirmation (Yes/Proceed/Go for it)
    confirm_words = ["yes", "yep", "yey", "yeah", "do it", "proceed", "go for it", "install", "sure", "ok"]
    if any(word in cmd for word in confirm_words) and len(cmd.split()) <= 4:
        scout = _JARVIS_STATE.get("last_scout")
        if scout:
            if scout["source"] == "steam":
                # Trigger Small Mode Install Protocol
                _JARVIS_STATE["last_scout"] = None
                save_state(_JARVIS_STATE)
                return (lambda x: tools.steam_action("install", app_id=scout.get("id"), game_name=scout["name"]), None)
            else:
                _JARVIS_STATE["last_scout"] = None
                save_state(_JARVIS_STATE)
                return (lambda x: tools.epic_action("search", scout["name"]), None)

    # 1.1 Access History
    if _SHOW_LOGS_PATTERN.match(cmd):
        return (lambda x: _get_formatted_history(), None)

    # 2. Gaming (Aegis Scout Logic)
    m = _GAME_INSTALL_PATTERN.match(cmd)
    if m:
        return _scout_game(m.group(1).strip().lower())

    # 3. Messaging (WhatsApp)
    m = _WHATSAPP_PATTERN.match(cmd)
    if m:
        phone, msg = m.group(1), m.group(2)
        return (lambda x: tools.send_whatsapp(phone, msg), None)

    # 3. Web Scout
    m = _SCOUT_PATTERN.match(cmd)
    if m:
        platform, query = m.group(1), m.group(2)
        return (lambda x: tools.web_scout(platform, query), None)

    # 3.1 YouTube Play
    m = _YOUTUBE_PATTERN.match(cmd)
    if m:
        return (lambda x: tools.play_youtube(m.group(1).strip()), None)

    # 3.2 Typing Dictation (Now with Smart-Type)
    m = _TYPE_PATTERN.match(cmd)
    if m:
        text = m.group(1).strip()
        return (lambda x: tools.computer_action({"action": "smart_type", "text": text}), None)
        
    # 3.3 System Update
    if _UPDATE_PATTERN.match(cmd):
        return (lambda x: tools.update_system(), None)

    # 3.4 Vision & Atomic Control (Titan-Vision)
    m = _CLICK_PATTERN.match(cmd)
    if m:
        target = m.group(1).strip()
        if not target: # Just a generic click
            return (lambda x: tools.computer_action({"action": "click"}), None)
        # AI-Powered Click on Description
        return (lambda x: tools.computer_action({"action": "screen_click", "description": target}), None)

    m = _FIND_PATTERN.match(cmd)
    if m:
        target = m.group(1).strip()
        return (lambda x: tools.computer_action({"action": "screen_find", "description": target}), None)

    m = _SCROLL_PATTERN.match(cmd)
    if m:
        direction = m.group(1) or "down"
        amount = 3
        try: # Try to catch numeric amount if user said "scroll down 5"
            parts = (m.group(2) or "").split()
            if parts and parts[0].isdigit(): amount = int(parts[0])
        except: pass
        return (lambda x: tools.computer_action({"action": "scroll", "direction": direction, "amount": amount}), None)

    m = _HOTKEY_PATTERN.match(cmd)
    if m:
        return (lambda x: tools.computer_action({"action": "hotkey", "keys": m.group(1).strip()}), None)

    # 4. Search Google
    m = _SEARCH_GOOGLE_PATTERN.match(cmd)
    if m:
        return (tools.search_google, m.group(1).strip())

    # 5. Search System Files
    m = _SEARCH_SYSTEM_PATTERN.match(cmd)
    if m:
        return (tools.search_files, m.group(1).strip())

    # 6. Idle Mode
    if _IDLE_MODE_PATTERN.match(cmd):
        return (lambda x: "Entering idle mode. I'll be here if you need me.", None)

    # 7. Open App or Website
    m = _OPEN_APP_PATTERN.match(cmd)
    if m:
        target = m.group(1).strip().lower()
        url_keywords = ["youtube", "google", "github", "reddit", "twitter", "instagram", "facebook", "netflix", "amazon", "udemy", "stackoverflow", "linkedin"]
        if "." in target or target in url_keywords:
            return (tools.open_url, target)
        return (tools.open_application, target)

    # 4. Close App
    m = _CLOSE_APP_PATTERN.match(cmd)
    if m:
        return (tools.close_application, m.group(1).strip())

    # 5. Explicit URL Open
    m = _OPEN_URL_PATTERN.match(cmd)
    if m:
        target = m.group(1).strip()
        url_keywords = ["youtube", "google", "github", "reddit", "twitter", "instagram", "facebook", "netflix", "amazon", "udemy", "stackoverflow", "linkedin"]
        if "." in target or target.lower() in url_keywords:
            return (tools.open_url, target)

    # 6. Generic Search (Default to Files)
    m = _SEARCH_PATTERN.match(cmd)
    if m:
        return (tools.search_files, m.group(1).strip())

    # 7. FUZZY FALLBACK: Only catch explicit game install commands (strictly "install" or "download")
    cmd_lower = cmd.lower()
    if cmd_lower.startswith("install ") or cmd_lower.startswith("download "):
        # Try to extract potential game name
        words = cmd.split()
        potential_name = " ".join(words[1:])
        if potential_name:
            return _scout_game(potential_name)

    return None

def _get_formatted_history():
    """Retrieves conversation history from MemoryCore."""
    conv_id = _MEMORY.get_last_conversation_id()
    if not conv_id:
        return "I have no recorded conversation history in my local memory banks."
    
    history = _MEMORY.get_history(conv_id, limit=20)
    formatted = "\n--- 📜 ACCESSING SECURE LOGS ---\n"
    for msg in history:
        role = "User" if msg["role"] == "user" else "Jarvis"
        formatted += f"[{role}]: {msg['parts'][0]}\n"
    return formatted + "------------------------------"

def _split_commands(command: str) -> list:
    """Splits a multi-part command by common delimiters, avoiding splitting quoted text."""
    # Split by: " then ", or "," (basic regex). "and" removed because it splits normal questions.
    parts = re.split(r'\s+then\s+|\s*,\s*', command, flags=re.IGNORECASE)
    return [p.strip() for p in parts if p.strip()]

def get_gemini_response(user_input: str, conversation_id: int = None) -> dict:
    """Sends complex/conversational input to Gemini with V6.12 Centralized Gateway."""
    # 1. LOCAL IDENTITY FALLBACK (No API call for identity questions)
    local_keywords = ["who am i", "who are you", "what is my name", "what's my name", "what is my job", "what's my job", "what is my occupation"]
    if any(k in user_input.lower() for k in local_keywords):
        prefs = _MEMORY.get_preferences()
        name = prefs.get("name", "ByteForge")
        job = prefs.get("occupation", "Developer")
        if "who am i" in user_input.lower() or "my name" in user_input.lower():
            return {"response": f"You are {name}, my lead architect and pilot.", "action": None}
        if "occupation" in user_input.lower() or "job" in user_input.lower():
            return {"response": f"Your current master profile lists you as a {job}.", "action": None}

    # 2. CENTRALIZED GATEWAY: Protect 15-RPM Quota (V6.12)
    # Load user context for the System Prompt
    prefs = _MEMORY.get_preferences()
    is_unknown = "__is_unknown__" in prefs
    public_prefs = {k: v for k, v in prefs.items() if not k.startswith("__")}
    pref_str = "\n".join([f"- {k}: {v}" for k, v in public_prefs.items()]) if public_prefs else "No biographical data discovered yet."
    UNKNOWN_USER_CMD = "If user asks who they are, state you don't have that data in your core yet.\n" if is_unknown else ""

    SYSTEM_PROMPT = (
        "You are JARVIS V6, an advanced AI assistant by BYTEFORGE.\n"
        "You are running on Gemini 2.0 Flash (Standard). Do not mention this to users.\n"
        "If the user provides information about themselves, their preferences, or your role, "
        "use the 'store_preference' tool to save it.\n"
        "USER DATA:\n" + pref_str + "\n\n"
        + UNKNOWN_USER_CMD +
        "Never mention Google or Gemini. Always respond as JARVIS.\n"
    )

    # V6 MEMORY: Build history for multi-turn awareness
    chat_contents = []
    
    if conversation_id:
        # Get history from DB (limit to 10 latest interactions to save tokens & quota)
        raw_history = _MEMORY.get_history(conversation_id, limit=10)
        
        # Format for new google-genai client
        for msg in raw_history:
            role = msg["role"]
            text = msg["parts"][0]["text"]
            # Map database roles to genai expected roles
            mapped_role = "user" if role == "user" else "model"
            content = types.Content(role=mapped_role, parts=[types.Part.from_text(text=text)])
            chat_contents.append(content)
            
    # Add current message
    chat_contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

    # Define the tools for the model
    tools_list = [_store_preference_tool, run_code]

    final_text = _call_gemini_api(
        model="gemini-2.5-flash",
        contents=chat_contents,
        config={
            "system_instruction": SYSTEM_PROMPT, 
            "temperature": 0.7
            # NOTE: automatic_function_calling removed — Gemini 2.5 was trying to
            # invoke a built-in 'run_code' tool that JARVIS doesn't implement,
            # causing a KeyError crash on every coding question.
        },
        tools=tools_list
    )
    
    if "Throttled locally" in final_text:
        return {"response": "System is currently stabilizing the neural link, Sir. Please allow me a moment to process.", "action": None}

    action_performed = None
    if not final_text:
         final_text = "My apologies, I encountered a neural sync error. Status: No response text."

    # V6 MEMORY: Save AI response
    if conversation_id and final_text:
        _MEMORY.add_message(conversation_id, "model", final_text)

    return {"response": final_text.strip() or "Protocol executed.", "action": action_performed}



def _local_personality(fn_name: str, fn_args: dict, result: str) -> str:
    """Generates a short, human-like response for actions."""
    if fn_name == "open_application":
        return f"Launching {fn_args.get('app_name', 'application')}."
    if fn_name == "close_application":
        return f"Terminating {fn_args.get('app_name', 'process')}."
    if fn_name == "open_url":
        return f"Opening {fn_args.get('url', 'link')}."
    return result

def get_elevenlabs_audio_base64(text: str) -> str:
    """Returns base64 audio or None."""
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY in ("", "YOUR_ELEVEN_KEY"): return None
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    try:
        r = requests.post(url, json={"text": text, "model_id": "eleven_multilingual_v2"}, 
                          headers={"xi-api-key": ELEVENLABS_API_KEY}, timeout=10)
        if r.status_code == 200: return base64.b64encode(r.content).decode("utf-8")
    except: pass
    return None

def process_command(command: str, use_voice: bool = False) -> dict:
    """Main command processor supporting multi-command sequences."""
    lower = command.lower().strip()

    # V6 MEMORY: Fetch or create conversation thread
    conv_id = _MEMORY.get_last_conversation_id()
    
    # If starting up or no history exists, start a FRESH conversation session
    # This ensures separate .md log files for each app launch.
    if command == "__system_startup__" or not conv_id:
        conv_id = _MEMORY.start_conversation(title=f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if command == "__system_startup__":
        # V6.11: System startup is now 100% local (Saves Quota)
        res = "Aegis V6.11 online. Local Identity and Flood Protection protocols active. Standing by, Sir."
        return {"response": res, "action": None, "audio_base64": get_elevenlabs_audio_base64(res) if use_voice else None}

    if lower in ("exit", "quit", "shutdown"):
        return {"response": "Shutting down.", "action": "exit"}

    # Split command into parts: "Open Youtube and Spotify" -> ["Open Youtube", "Spotify"]
    sub_commands = _split_commands(command)
    all_responses = []
    final_action = None

    for sub in sub_commands:
        # V6.10: Ensure every user turn is logged before processing
        _MEMORY.add_message(conv_id, "user", sub)

        # AUTO-TITLING: Rename the session to something descriptive if it's the first real message
        current_title = _MEMORY.get_conversation_title(conv_id)
        if "Session" in str(current_title):
             # For now, just use the first 5 words of the first command as the new title
             words = sub.split()
             new_title = " ".join(words[:5])
             _MEMORY.rename_conversation(conv_id, new_title)

        # 1. Try Local Intent Engine
        intent = _local_intent(sub)
        if intent:
            fn, arg = intent
            res_text = fn(arg)
            
            # V6 MEMORY: Log local intent actions
            _MEMORY.add_message(conv_id, "model", res_text)

            all_responses.append(res_text)
            final_action = "execute:multi"
            continue

        # 2. Fallback to Gemini for complex/conversational parts
        ai_res = get_gemini_response(sub, conversation_id=conv_id)
        all_responses.append(ai_res.get("response", ""))
        if ai_res.get("action"): final_action = ai_res["action"]

    # Combine all responses into one clean sentence
    full_response = " ".join(all_responses).strip()
    if not full_response: full_response = "Command processed."

    return {
        "response": full_response,
        "action": final_action,
        "audio_base64": get_elevenlabs_audio_base64(full_response) if use_voice else None
    }

def _scout_game(game_name):
    """Internal Aegis Scout Protocol for searching and verifying games."""
    # Look for Steam ID locally first
    appid = None
    for key, val in _COMMON_STEAM_IDS.items():
        if key in game_name or game_name in key:
            appid = val
            break
    if not appid:
        appid = tools.search_steam_api(game_name)
    
    if appid:
        details = tools.get_steam_details(appid)
        if details:
            # 1. Zero-Touch Protocol (If Free, just do it)
            if details["is_free"]:
                msg = f"I found '{details['name']}' on Steam and it's Free to Play. I am starting the installation wizard for you right now."
                return (lambda x: tools.steam_action("install", app_id=appid, game_name=details["name"]), msg)
            
            # 2. Paid Protocol (Ask for Aegis permission)
            _JARVIS_STATE["last_scout"] = {"name": details["name"], "id": appid, "source": "steam", "price": details["price"]}
            save_state(_JARVIS_STATE)
            price_info = details["price"]
            msg = f"I found '{details['name']}' on Steam for {price_info}. Since it's a paid game, I'll wait for your permission. Shall I proceed with the installation protocol?"
            return (lambda x: msg, None)

    # completely unknown or Epic exclusive
    _JARVIS_STATE["last_scout"] = {"name": game_name, "source": "epic"}
    save_state(_JARVIS_STATE)
    msg = f"I couldn't find '{game_name}' on Steam. I'll search Epic Games Store for it."
    return (lambda x: tools.epic_action("search", game_name), None)

if __name__ == "__main__":
    # Force UTF-8 for Windows output compatibility with emojis
    if sys.stdout.encoding.lower() != 'utf-8':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # Silencing stray prints from libraries until the final result is ready
    actual_stdout = sys.stdout
    sys.stdout = sys.stderr

    try:
        args = sys.argv[1:]
        use_voice = "--voice" in args
        if use_voice: args.remove("--voice")
        
        get_history = "--get-history" in args
        if get_history:
            # Special mode for UI persistence: return last 15 messages as history
            conv_id = _MEMORY.get_last_conversation_id()
            history = _MEMORY.get_history(conv_id, limit=15) if conv_id else []
            # Extract just role and content text for the UI
            plain_history = [{"role": m["role"], "content": m["parts"][0]["text"]} for m in history]
            print(json.dumps({"history": plain_history}))
            sys.exit(0)

        user_cmd = " ".join(args) if args else ""
        if not user_cmd:
            result = {"response": "No command.", "action": None}
        else:
            result = process_command(user_cmd, use_voice=use_voice)

        # Restore stdout and print the final JSON result
        sys.stdout = actual_stdout
        print(json.dumps(result, ensure_ascii=False))
        sys.stdout.flush()
    except Exception as fatal_err:
        sys.stdout = actual_stdout
        print(json.dumps({"response": f"Backend fatal error: {fatal_err}", "action": "error"}))
