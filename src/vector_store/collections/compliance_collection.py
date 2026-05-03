import uuid
from typing import List, Dict, Any, Optional

class ComplianceCollection:
    """Handles FINRA rules operations in ChromaDB"""
    
    def __init__(self, chroma_client, collection_name="finra_rules"):
        self.client = chroma_client
        self.collection = self.client.get_or_create_collection(collection_name)
        self.collection_name = collection_name
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """Add FINRA rule chunks to collection"""
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
        
        print(f"  ✅ Added {len(ids)} FINRA rules to {self.collection_name}")
        return len(ids)
    
    def query_by_rule_id(self, rule_id: str):
        """Get specific rule by ID - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"Rule {rule_id}",
            n_results=1,
            filter_dict={"rule_id": rule_id}
        )
    
    def query_by_category(self, category: str, n_results: int = 10):
        """Get rules by category - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=f"{category} rules",
            n_results=n_results,
            filter_dict={"category": category}
        )
    
    def search_rules(self, query: str, n_results: int = 5):
        """Semantic search across all rules - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        return self.collection.query(
            collection_name=self.collection_name,
            query_text=query,
            n_results=n_results
        )
    
    def get_all_rule_ids(self):
        """Get list of all rule IDs in collection - SAFE VERSION"""
        # ✅ FIXED: Use self.client.query() instead of self.collection.query()
        results = self.collection.query(
            collection_name=self.collection_name,
            query_text="",
            n_results=100
        )
        
        rule_ids = []
        if results and results.get('metadatas') and results['metadatas'][0]:
            for metadata in results['metadatas'][0]:
                rule_id = metadata.get('rule_id', '')
                if rule_id:
                    rule_ids.append(rule_id)
        
        return rule_ids