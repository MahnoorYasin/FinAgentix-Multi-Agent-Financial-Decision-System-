# download_with_sentence_transformers.py
from sentence_transformers import SentenceTransformer
import os

print("="*60)
print("DOWNLOADING MODEL VIA SENTENCE-TRANSFORMERS")
print("="*60)

# This will download and cache the model automatically
print("Downloading all-MiniLM-L6-v2 (this may take a few minutes)...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Test it
sentences = ["This is a test sentence", "This is another one"]
embeddings = model.encode(sentences)

print(f"✅ Model loaded successfully!")
print(f"✅ Embedding dimension: {embeddings.shape[1]}")
print(f"\nModel cached at: {os.path.expanduser('~')}\\.cache\\huggingface\\hub")