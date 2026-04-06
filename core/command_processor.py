from modules import system_control
from modules.ai_chat import AIChat

class CommandProcessor:
    def __init__(self, api_key: str):
        """
        Initializes the command processor with AI chat capabilities.
        """
        self.ai_chat = AIChat(api_key=api_key)

    def process(self, command: str) -> str:
        """
        Processes a raw input string from the user.
        Routes it to a system command or to the AI.
        """
        command = command.strip()
        lower_command = command.lower()

        if not command:
            return ""

        # Basic system commands
        if lower_command == "open chrome":
            system_control.open_chrome()
            return "" # open_chrome prints its own message as per example
            
        elif lower_command.startswith("search google "):
            query = command[14:].strip()
            if query:
                system_control.search_google(query)
                return ""
            else:
                return "What would you like me to search for?"
                
        elif lower_command == "time":
            return system_control.get_time()
            
        elif lower_command == "help":
            return system_control.print_help()
            
        elif lower_command in ["exit", "quit", "stop"]:
            return "Shutting down systems. Goodbye."

        # If it's not a recognized system command, send to Gemini
        return self.ai_chat.get_response(command)
