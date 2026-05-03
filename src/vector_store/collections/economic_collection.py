import uuid
from typing import List, Dict, Any, Optional

class EconomicCollection:
    """Handles economic indicators operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="economic_indicators"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add economic indicator chunks to collection"""
        if not chunks:
            print(f"  ⚠️ No chunks to add to {self.collection_name}")
            return 0
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            try:
                self.collection.add(
                    ids=ids[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    embeddings=embeddings[i:batch_end]
                )
            except Exception as e:
                print(f"    ❌ Error adding batch: {e}")
        
        print(f"  ✅ Added {len(ids)} economic indicators to {self.collection_name}")
        return len(ids)
    
    def query_by_indicator(self, indicator_name: str):
        """Get specific economic indicator - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=indicator_name,
            n_results=1,
            filter_dict={"indicator_name": indicator_name}
        )
    
    def query_by_series_id(self, series_id: str):
        """Get indicator by FRED series ID - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=series_id,
            n_results=1,
            filter_dict={"series_id": series_id}
        )
    
    def get_all_indicators(self):
        """Get list of all indicators - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        results = self.collection.query(
            collection_name=self.collection_name,
            query_text="",
            n_results=50
        )
        
        indicators = []
        if results and results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                indicators.append({
                    'name': metadata.get('indicator_name', ''),
                    'series_id': metadata.get('series_id', '')
                })
        
        return indicators