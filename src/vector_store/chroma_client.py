# src/vector_store/chroma_client.py
import chromadb
from chromadb.config import Settings
from pathlib import Path
import uuid
import os
from typing import List, Dict, Any, Optional

# Import all collection handlers
from .collections import (
    MarketCollection, NewsCollection, ComplianceCollection,
    EconomicCollection, FundamentalCollection, RiskCollection
)

class ChromaClient:
    def __init__(self, persist_directory="./knowledge_base/chroma_data"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        # Disable ChromaDB telemetry and auto-download
        os.environ["CHROMA_DISABLE_TELEMETRY"] = "1"
        os.environ["CHROMA_DISABLE_ONNX"] = "1"
        
        print(f"Initializing ChromaDB at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Dictionary to store raw collections
        self.collections = {}
        
        # Initialize specialized collection handlers
        print("\nInitializing collection handlers...")
        self.market = MarketCollection(self)
        self.news = NewsCollection(self)
        self.compliance = ComplianceCollection(self)
        self.economic = EconomicCollection(self)
        self.fundamental = FundamentalCollection(self)
        self.risk = RiskCollection(self)
        
        # Map for easy access by data type
        self.handlers = {
            'market_data': self.market,
            'news_articles': self.news,
            'finra_rules': self.compliance,
            'economic_indicators': self.economic,
            'company_fundamentals': self.fundamental,
            'risk_metrics': self.risk
        }
        
        print("✅ Collection handlers initialized")
        print("✅ ChromaDB configured to use pre-computed embeddings only")
    
    def get_or_create_collection(self, name):
        """Get existing collection or create new one (without embedding function)"""
        if name in self.collections:
            return self.collections[name]
        
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name)
            print(f"  Found existing collection: {name}")
        except:
            # Create new collection WITHOUT embedding function
            # This forces ChromaDB to use pre-computed embeddings only
            collection = self.client.create_collection(
                name=name,
                metadata={"description": f"FinAgentix {name} collection"},
                embedding_function=None  # CRITICAL: Disable internal embeddings
            )
            print(f"  Created new collection: {name}")
        
        self.collections[name] = collection
        return collection
    
    def add_chunks(self, collection_name, chunks):
        """Add chunks to collection using pre-computed embeddings only"""
        collection = self.get_or_create_collection(collection_name)
        
        if not chunks:
            print(f"  ⚠️ No chunks to add to {collection_name}")
            return 0
        
        # Verify embeddings exist
        if 'embedding' not in chunks[0]:
            print(f"  ❌ Error: No pre-computed embeddings found in chunks!")
            print(f"  Please run embed_chunks() before adding to database.")
            return 0
        
        # Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [chunk['text'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        
        print(f"  Adding {len(ids)} chunks with pre-computed embeddings...")
        
        # Add in batches to avoid memory issues
        batch_size = 100
        total_batches = (len(ids) - 1) // batch_size + 1
        
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            try:
                collection.add(
                    ids=ids[i:batch_end],
                    documents=documents[i:batch_end],
                    embeddings=embeddings[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )
                print(f"    Added batch {i//batch_size + 1}/{total_batches}")
            except Exception as e:
                print(f"    ❌ Error adding batch {i//batch_size + 1}: {e}")
        
        print(f"  ✅ Added {len(ids)} chunks to {collection_name}")
        return len(ids)
    
    def query(self, collection_name, query_text, n_results=5, filter_dict=None):
        """Query a collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_dict
            )
            return results
        except Exception as e:
            print(f"❌ Error querying {collection_name}: {e}")
            return None
    
    def query_with_embedding(self, collection_name, query_embedding, n_results=5, filter_dict=None):
        """Query using pre-computed query embedding"""
        try:
            collection = self.get_or_create_collection(collection_name)
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_dict
            )
            
            return results
        except Exception as e:
            print(f"❌ Error querying {collection_name}: {e}")
            return None
    
    def get_handler(self, data_type):
        """Get specialized handler for a data type"""
        return self.handlers.get(data_type)
    
    def add_chunks_with_handler(self, data_type, chunks):
        """Add chunks using specialized handler"""
        handler = self.get_handler(data_type)
        if handler:
            return handler.add_chunks(chunks)
        else:
            print(f"⚠️ No handler found for data type: {data_type}")
            return 0
    
    def list_collections(self):
        """List all collections"""
        try:
            collections = self.client.list_collections()
            print("\n📋 Available collections:")
            for col in collections:
                count = col.count()
                print(f"  • {col.name}: {count} chunks")
            return collections
        except Exception as e:
            print(f"❌ Error listing collections: {e}")
            return []
    
    def delete_collection(self, name):
        """Delete a collection"""
        try:
            self.client.delete_collection(name)
            if name in self.collections:
                del self.collections[name]
            print(f"✅ Deleted collection: {name}")
            return True
        except Exception as e:
            print(f"❌ Error deleting collection {name}: {e}")
            return False
    
    def get_collection_stats(self, name):
        """Get statistics about a collection"""
        try:
            collection = self.get_or_create_collection(name)
            
            return {
                'name': name,
                'count': collection.count(),
                'exists': True
            }
        except Exception as e:
            return {
                'name': name,
                'count': 0,
                'error': str(e),
                'exists': False
            }
    
    def get_all_stats(self):
        """Get statistics for all collections"""
        stats = {}
        collection_names = [
            'market_data', 'news_articles', 'finra_rules',
            'economic_indicators', 'company_fundamentals', 'risk_metrics'
        ]
        
        for name in collection_names:
            stats[name] = self.get_collection_stats(name)
        
        return stats
    
    def reset(self):
        """Reset the database (delete all collections)"""
        try:
            collections = self.client.list_collections()
            for collection in collections:
                self.delete_collection(collection.name)
            self.collections = {}
            print("✅ Database reset complete")
            return True
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False


# Optional: Create a convenience function to get a pre-configured client
def get_chroma_client(config=None):
    """Get a configured ChromaClient instance"""
    if config and hasattr(config, 'get'):
        persist_dir = config.get('paths', 'knowledge_base')
    else:
        persist_dir = "./knowledge_base/chroma_data"
    
    return ChromaClient(persist_directory=persist_dir)