# src/vector_store/embeddings/embedding_model.py
from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path

class EmbeddingModel:
    def __init__(self, model_name="all-MiniLM-L6-v2", cache_dir="./data/embeddings_cache"):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading embedding model: {model_name}...")
        # This will use the cached model from C:\Users\Mahnoor\.cache\huggingface\hub\
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded from cache. Embedding dimension: {self.dimension}")
    
    def embed_text(self, text):
        """Generate embedding for a single text"""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts, batch_size=32):
        """Generate embeddings for a batch of texts"""
        return self.model.encode(texts, batch_size=batch_size).tolist()
    
    def embed_chunks(self, chunks):
        """Add embeddings to chunks"""
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embed_batch(texts)
        
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i]
        
        return chunks