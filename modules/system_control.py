import webbrowser
import datetime

def open_chrome():
    """
    Opens the default web browser (which is usually Chrome if set to default).
    """
    print("Opening Chrome.")
    webbrowser.open("http://www.google.com")
    return True

def search_google(query: str):
    """
    Performs a Google search using the web browser.
    """
    print(f"Here is what I found for '{query}'.")
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return True

def get_time() -> str:
    """
    Returns the current time formatted nicely.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    return f"The current time is {time_str}."

def print_help() -> str:
    """
    Returns a help message listing basic commands.
    """
    return (
        "Here are the core system commands I currently support:\n"
        "- 'open chrome': Launches the web browser.\n"
        "- 'search google <query>': Searches Google for your query.\n"
        "- 'time': Tells you the current time.\n"
        "- 'help': Displays this help message.\n"
        "- 'exit' or 'quit': Shuts down the JARVIS system.\n"
        "Any other input will be processed by my AI core."
    )
