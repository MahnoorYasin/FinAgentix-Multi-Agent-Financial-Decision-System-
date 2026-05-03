import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# Test simple completion
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="Say hello in one word"
)
print(f"Response: {response.text}")
print("✅ Gemini is working!")