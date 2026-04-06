import sys
from core.command_processor import CommandProcessor
from core.utils import speak

class JarvisAssistant:
    def __init__(self, api_key: str):
        self.processor = CommandProcessor(api_key)
        self.running = False

    def start(self):
        """
        Starts the main interaction loop.
        """
        self.running = True
        print("\n--- JARVIS V1 INITIALIZED ---")
        speak("Good evening. How can I assist you?")
        
        while self.running:
            try:
                user_input = input("\n> ")
                if not user_input.strip():
                    continue

                # Process the command
                response = self.processor.process(user_input)
                
                if response:
                    speak(response)

                if user_input.lower().strip() in ["exit", "quit", "stop"]:
                    self.running = False
                    
            except KeyboardInterrupt:
                speak("\nForce quit detected. Shutting down.")
                self.running = False
            except Exception as e:
                print(f"\n[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
                speak("I encountered an internal error.")
