"""
Utility functions for JARVIS V1.
Contains placeholder functions for future expansions like voice input/output.
"""

def listen() -> str:
    """
    Placeholder for voice input (Speech-to-Text).
    Currently just falls back to text input if called, or raises NotImplementedError.
    """
    print("[SYSTEM] Microphone listening not implemented yet in V1.")
    return ""

def speak(text: str):
    """
    Placeholder for voice output (Text-to-Speech).
    Currently just prints to terminal.
    """
    # For V1, we just print the text, but in the future this will speak it aloud.
    print(text)

def memory_save(key: str, value: any):
    """
    Placeholder for saving user data to long-term memory.
    """
    pass

def memory_load(key: str) -> any:
    """
    Placeholder for loading user data from long-term memory.
    """
    return None
