from google import genai
import os
import sys

# Add current dir to path to import config
sys.path.append(os.path.join(os.getcwd(), 'python'))
try:
    import config
    api_key = config.GEMINI_API_KEY
except:
    api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
print("Listing models...")
try:
    for m in client.models.list():
        # Using supported_actions as suggested by the error
        print(f"Model ID: {m.name}, Actions: {m.supported_actions}")
except Exception as e:
    print(f"Error listing: {e}")
