import sys
import os

# Ensure the jarvis directory is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import GEMINI_API_KEY
from core.assistant import JarvisAssistant

def main():
    try:
        assistant = JarvisAssistant(api_key=GEMINI_API_KEY)
        assistant.start()
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
