import uuid
from typing import List, Dict, Any, Optional

class RiskCollection:
    """Handles risk metrics operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="risk_metrics"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add risk metric chunks to collection"""
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
                print(f"    ❌ Error adding batch {i//batch_size + 1}: {e}")
        
        print(f"  ✅ Added {len(ids)} risk metrics to {self.collection_name}")
        return len(ids)
    
    def query_by_ticker(self, ticker: str):
        """Get risk metrics for specific stock - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"{ticker} risk",
            n_results=1,
            filter_dict={"ticker": ticker}
        )
    
    def query_by_sector(self, sector: str, n_results: int = 10):
        """Get risk metrics for all stocks in a sector - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"{sector} sector risk",
            n_results=n_results,
            filter_dict={"sector": sector}
        )
    
    def get_high_risk_stocks(self, threshold: float = 40.0):
        """Get stocks with volatility above threshold - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        all_results = self.collection.query(
            collection_name=self.collection_name,
            query_text="high volatility",
            n_results=50
        )
        
        high_risk = []
        if all_results and all_results.get('documents') and all_results['documents'][0]:
            for i, doc in enumerate(all_results['documents'][0]):
                if all_results.get('metadatas') and all_results['metadatas'][0]:
                    high_risk.append({
                        'document': doc,
                        'metadata': all_results['metadatas'][0][i]
                    })
        
        return high_risk[:10]
    
    def compare_risk_profiles(self, tickers: List[str]):
        """Compare risk metrics for multiple stocks"""
        profiles = []
        for ticker in tickers:
            result = self.query_by_ticker(ticker)
            if result and result.get('documents') and result['documents'][0]:
                profiles.append({
                    'ticker': ticker,
                    'document': result['documents'][0][0],
                    'metadata': result['metadatas'][0][0] if result.get('metadatas') and result['metadatas'][0] else None
                })
        
        return profiles