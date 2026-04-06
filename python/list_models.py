from google import genai
import os
import sys

api_key = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GEMINI_API_KEY")
if not api_key:
    print("No API key provided.")
    sys.exit(1)

client = genai.Client(api_key=api_key)
print("Listing available models...")
try:
    for m in client.models.list():
        print(f"Model Name: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
