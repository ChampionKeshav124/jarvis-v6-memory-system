from google import genai
import sys

class AIChat:
    def __init__(self, api_key: str):
        if not api_key or api_key == "YOUR_API_KEY":
            print("[WARNING] Invalid or missing GEMINI_API_KEY. AI responses will not work until this is set in config.py.", file=sys.stderr)
            self.client = None
            return

        try:
            self.client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[ERROR] Failed to initialize Gemini API: {e}", file=sys.stderr)
            self.client = None
            
        self.system_prompt = (
            "You are JARVIS, a highly advanced AI assistant. "
            "Your personality is that of a professional butler AI. "
            "You must keep your responses short, confident, calm, and slightly formal. "
            "Do not use overly complex formatting unless necessary. "
            "Keep the assistance highly practical and direct."
        )

    def get_response(self, user_input: str) -> str:
        """
        Sends the user input to the Gemini model via the throttled V6.13 gateway.
        """
        import os, sys
        python_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "python")
        if python_dir not in sys.path: sys.path.append(python_dir)
        import jarvis
        
        # Build prompt
        prompt = f"{self.system_prompt}\n\nUser: {user_input}"
        
        # Route to Centralized Gateway
        text = jarvis._call_gemini_api(
            model="gemini-1.5-flash",
            contents=[prompt],
            config={"temperature": 0.7}
        )
        
        if "Throttled locally" in text:
            return "System is currently stabilizing the neural link, Sir. Please allow me a moment to process."
        return text or "I apologize, but I could not formulate a response."
