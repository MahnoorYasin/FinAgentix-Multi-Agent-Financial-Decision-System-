#!/usr/bin/env python3
"""
Test retrieval from the knowledge base
FIXED: Config access issue resolved
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.vector_store.chroma_client import ChromaClient
from src.vector_store.embeddings.embedding_model import EmbeddingModel
from src.utils.config import config

def test_retrieval():
    """Test retrieval with sample queries"""
    print("="*70)
    print("TESTING RETRIEVAL FROM KNOWLEDGE BASE")
    print("="*70)
    
    # Get paths from config correctly
    knowledge_base_path = config.get('paths', 'knowledge_base')
    # If it returns a dict, extract the value
    if isinstance(knowledge_base_path, dict):
        knowledge_base_path = knowledge_base_path.get('knowledge_base', './knowledge_base/chroma_data')
    
    embeddings_cache = config.get('paths', 'embeddings_cache')
    if isinstance(embeddings_cache, dict):
        embeddings_cache = embeddings_cache.get('embeddings_cache', './data/embeddings_cache')
    
    model_name = config.get('embedding', 'model_name')
    if isinstance(model_name, dict):
        model_name = model_name.get('model_name', 'all-MiniLM-L6-v2')
    
    # Initialize Chroma client
    chroma = ChromaClient(persist_directory=knowledge_base_path)
    
    # Initialize embedding model for queries
    print("\n[Step 1] Loading embedding model for queries...")
    embedder = EmbeddingModel(
        model_name=model_name,
        cache_dir=embeddings_cache
    )
    
    # Test queries
    test_cases = [
        {
            "name": "Test 1: Basic Semantic Search",
            "collection": "market_data",
            "query": "What was Apple's stock performance in 2024?",
            "filter": None
        },
        {
            "name": "Test 2: Metadata Filtering",
            "collection": "news_articles",
            "query": "What are the latest news about Tesla?",
            "filter": {"source": "CNBC"}
        },
        {
            "name": "Test 3: Hybrid Search",
            "collection": "finra_rules",
            "query": "What are the rules about customer suitability?",
            "filter": {"doc_type": "finra_rule"}
        },
        {
            "name": "Test 4: Economic Data",
            "collection": "economic_indicators",
            "query": "What is the current GDP growth rate?",
            "filter": {"indicator_name": "Gross Domestic Product"}
        },
        {
            "name": "Test 5: Risk Metrics",
            "collection": "risk_metrics",
            "query": "What is the risk profile for NVDA?",
            "filter": {"ticker": "NVDA"}
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{test['name']}")
        print("-" * 40)
        print(f"Query: {test['query']}")
        if test['filter']:
            print(f"Filter: {test['filter']}")
        
        try:
            # Generate embedding for the query using your model
            print("  Generating query embedding...")
            query_embedding = embedder.embed_text(test['query'])
            
            # Query using the embedding
            response = chroma.query_with_embedding(
                collection_name=test['collection'],
                query_embedding=query_embedding,
                n_results=3,
                filter_dict=test['filter']
            )
            
            if response and response.get('documents') and len(response['documents'][0]) > 0:
                print(f"✅ Found {len(response['documents'][0])} results")
                
                for i, (doc, metadata, distance) in enumerate(zip(
                    response['documents'][0],
                    response['metadatas'][0],
                    response['distances'][0]
                )):
                    print(f"\n  Result {i+1} (distance: {distance:.4f}):")
                    print(f"  Metadata: {metadata}")
                    # Truncate long documents
                    preview = doc[:200] + "..." if len(doc) > 200 else doc
                    print(f"  Preview: {preview}")
                
                results.append({
                    "test": test['name'],
                    "status": "PASS",
                    "results_found": len(response['documents'][0])
                })
            else:
                print("❌ No results found")
                results.append({
                    "test": test['name'],
                    "status": "FAIL",
                    "results_found": 0
                })
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "test": test['name'],
                "status": "ERROR",
                "error": str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Your knowledge base is working perfectly!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the errors above.")
    
    return results


def interactive_query():
    """Interactive mode - ask your own questions"""
    print("\n" + "="*70)
    print("INTERACTIVE RETRIEVAL MODE")
    print("="*70)
    print("Ask questions about your financial data")
    print("Type 'quit' to exit\n")
    
    # Initialize once
    knowledge_base_path = config.get('paths', 'knowledge_base')
    if isinstance(knowledge_base_path, dict):
        knowledge_base_path = knowledge_base_path.get('knowledge_base', './knowledge_base/chroma_data')
    
    embeddings_cache = config.get('paths', 'embeddings_cache')
    if isinstance(embeddings_cache, dict):
        embeddings_cache = embeddings_cache.get('embeddings_cache', './data/embeddings_cache')
    
    model_name = config.get('embedding', 'model_name')
    if isinstance(model_name, dict):
        model_name = model_name.get('model_name', 'all-MiniLM-L6-v2')
    
    chroma = ChromaClient(persist_directory=knowledge_base_path)
    embedder = EmbeddingModel(model_name=model_name, cache_dir=embeddings_cache)
    
    collections = ['market_data', 'news_articles', 'finra_rules', 'economic_indicators', 'company_fundamentals', 'risk_metrics']
    
    while True:
        print("\n" + "-" * 50)
        query = input("Your question: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        print(f"\n🔍 Searching for: '{query}'")
        
        # Ask which collection to search
        print("\nAvailable collections:")
        for i, col in enumerate(collections, 1):
            print(f"  {i}. {col}")
        print(f"  {len(collections)+1}. All collections")
        
        try:
            choice = input(f"\nChoose collection (1-{len(collections)+1}) [default=all]: ").strip()
            
            if choice and choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(collections):
                    collection = collections[choice_num - 1]
                    collections_to_search = [collection]
                else:
                    collections_to_search = collections
            else:
                collections_to_search = collections
            
            # Generate embedding
            query_embedding = embedder.embed_text(query)
            
            all_results = {}
            
            for collection in collections_to_search:
                print(f"\n  Searching {collection}...")
                response = chroma.query_with_embedding(
                    collection_name=collection,
                    query_embedding=query_embedding,
                    n_results=3,
                    filter_dict=None
                )
                
                if response and response.get('documents') and len(response['documents'][0]) > 0:
                    all_results[collection] = response
            
            if all_results:
                print("\n✅ Results found:")
                for collection, response in all_results.items():
                    print(f"\n  📁 {collection}:")
                    for i, (doc, metadata, distance) in enumerate(zip(
                        response['documents'][0],
                        response['metadatas'][0],
                        response['distances'][0]
                    )):
                        print(f"    Result {i+1} (distance: {distance:.4f}):")
                        print(f"    Metadata: {metadata}")
                        preview = doc[:100] + "..." if len(doc) > 100 else doc
                        print(f"    Preview: {preview}")
                        print()
            else:
                print("\n❌ No results found in any collection")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\nChoose mode:")
    print("1. Run predefined tests")
    print("2. Interactive query mode")
    print("3. Both (tests first, then interactive)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_retrieval()
    elif choice == "2":
        interactive_query()
    elif choice == "3":
        test_retrieval()
        interactive_query()
    else:
        print("Invalid choice. Running tests...")
        test_retrieval()