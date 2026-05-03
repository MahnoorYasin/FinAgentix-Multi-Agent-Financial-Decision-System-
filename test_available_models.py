# test_available_models.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print("🔍 Models AVAILABLE to your API key:")
print("=" * 50)

for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        print(f"✅ {model.name}")