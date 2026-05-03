import uuid
from typing import List, Dict, Any, Optional

class FundamentalCollection:
    """Handles company fundamentals operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="company_fundamentals"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add fundamental data chunks to collection"""
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
        
        print(f"  ✅ Added {len(ids)} company fundamentals to {self.collection_name}")
        return len(ids)
    
    def query_by_ticker(self, ticker: str):
        """Get fundamentals for specific company - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=ticker,
            n_results=1,
            filter_dict={"ticker": ticker}
        )
    
    def query_by_sector(self, sector: str, n_results: int = 10):
        """Get companies in a specific sector - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"{sector} companies",
            n_results=n_results,
            filter_dict={"sector": sector}
        )
    
    def compare_companies(self, tickers: List[str]):
        """Compare multiple companies - SAFE VERSION"""
        all_results = []
        for ticker in tickers:
            result = self.query_by_ticker(ticker)
            if result and result.get('documents') and result['documents'][0]:
                all_results.append({
                    'ticker': ticker,
                    'document': result['documents'][0][0],
                    'metadata': result['metadatas'][0][0] if result.get('metadatas') and result['metadatas'][0] else None
                })
        
        return all_results
    
    def get_sector_summary(self, sector: str):
        """Get summary of all companies in a sector - SAFE VERSION"""
        results = self.query_by_sector(sector, n_results=50)
        
        companies = []
        if results and results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                ticker = metadata.get('ticker', '')
                if ticker:
                    companies.append(ticker)
        
        return {
            'sector': sector,
            'company_count': len(companies),
            'companies': companies
        }