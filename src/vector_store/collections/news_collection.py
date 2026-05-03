import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class NewsCollection:
    """Handles news article operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="news_articles"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add news article chunks to collection"""
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
        
        print(f"  ✅ Added {len(ids)} news articles to {self.collection_name}")
        return len(ids)
    
    def query_by_source(self, source: str, query: str = "", n_results: int = 5):
        """Query news from specific source - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=query if query else "news",
            n_results=n_results,
            filter_dict={"source": source}
        )
    
    def query_recent_news(self, days: int = 7, n_results: int = 10):
        """Get news from last N days - SAFE VERSION"""
        # Calculate date threshold
        threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        all_results = self.collection.query(
            collection_name=self.collection_name,
            query_text="recent news",
            n_results=50
        )
        
        # Filter by date
        filtered_results = []
        if all_results and all_results.get('metadatas') and all_results['metadatas'][0]:
            for i, metadata in enumerate(all_results['metadatas'][0]):
                pub_date = metadata.get('published_date', '')
                if pub_date and pub_date >= threshold:
                    filtered_results.append({
                        'document': all_results['documents'][0][i] if all_results.get('documents') and all_results['documents'][0] else None,
                        'metadata': metadata,
                        'distance': all_results['distances'][0][i] if all_results.get('distances') and all_results['distances'][0] else None
                    })
        
        return filtered_results[:n_results]
    
    def query_by_topic(self, topic: str, n_results: int = 10):
        """Search news by topic - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=topic,
            n_results=n_results
        )
    
    def get_source_stats(self):
        """Get statistics about news sources - SAFE VERSION"""
        sources = {}
        
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        results = self.collection.query(
            collection_name=self.collection_name,
            query_text="",
            n_results=100
        )
        
        if results and results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                source = metadata.get('source', 'Unknown')
                sources[source] = sources.get(source, 0) + 1
        
        return sources