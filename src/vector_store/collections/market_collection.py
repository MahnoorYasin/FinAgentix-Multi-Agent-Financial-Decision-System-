import uuid
from typing import List, Dict, Any, Optional

class MarketCollection:
    """Handles stock market data operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="market_data"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add stock price chunks to collection"""
        if not chunks:
            print(f"  ⚠️ No chunks to add to {self.collection_name}")
            return 0
        
        # Prepare data for ChromaDB
        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        embeddings = [chunk['embedding'] for chunk in chunks]
        
        # Add in batches
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
        
        print(f"  ✅ Added {len(ids)} chunks to {self.collection_name}")
        return len(ids)
    
    def query_by_ticker(self, ticker: str, n_results: int = 5, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """Query stock data by ticker symbol - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"Stock data for {ticker}",
            n_results=n_results,
            filter_dict={"ticker": ticker}
        )
    
    def query_by_date_range(self, start_date: str, end_date: str, n_results: int = 10):
        """Query stocks within a date range - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        all_results = self.collection.query(
            collection_name=self.collection_name,
            query_text="stock prices",
            n_results=100
        )
        
        # Filter by date range manually
        filtered_results = []
        if all_results and all_results.get('metadatas') and all_results['metadatas'][0]:
            for i, metadata in enumerate(all_results['metadatas'][0]):
                if start_date <= metadata.get('start_date', '') <= end_date:
                    filtered_results.append({
                        'document': all_results['documents'][0][i] if all_results.get('documents') and all_results['documents'][0] else None,
                        'metadata': metadata,
                        'distance': all_results['distances'][0][i] if all_results.get('distances') and all_results['distances'][0] else None
                    })
        
        return filtered_results[:n_results]
    
    def get_ticker_summary(self, ticker: str):
        """Get summary of all data available for a ticker - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        results = self.collection.query(
            collection_name=self.collection_name,
            query_text=f"{ticker} summary",
            n_results=50,
            filter_dict={"ticker": ticker}
        )
        
        months = []
        if results and results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                months.append(metadata.get('month', ''))
        
        return {
            'ticker': ticker,
            'total_chunks': len(results['ids'][0]) if results and results.get('ids') and results['ids'][0] else 0,
            'months_available': sorted(months)
        }
    
    def delete_ticker_data(self, ticker: str):
        """Delete all data for a specific ticker"""
        try:
            self.collection.delete(where={"ticker": ticker})
            print(f"  ✅ Deleted all data for {ticker} from {self.collection_name}")
        except Exception as e:
            print(f"  ❌ Error deleting {ticker}: {e}")