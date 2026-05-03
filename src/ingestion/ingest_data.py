#!/usr/bin/env python3
"""
FinAgentix - Main Ingestion Script (Lab 2)
Processes all datasets, creates chunks, embeds, and indexes in ChromaDB
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.utils.config import config
from src.utils.file_utils import list_files, read_csv, ensure_dir
from src.ingestion.cleaners.market_cleaner import MarketCleaner
from src.ingestion.cleaners.news_cleaner import NewsCleaner
from src.ingestion.cleaners.compliance_cleaner import ComplianceCleaner
from src.ingestion.cleaners.economic_cleaner import EconomicCleaner
from src.ingestion.cleaners.fundamental_cleaner import FundamentalCleaner
from src.ingestion.cleaners.risk_cleaner import RiskCleaner
from src.ingestion.metadata.metadata_enricher import MetadataEnricher
from src.ingestion.chunkers.semantic_chunker import SemanticChunker
from src.vector_store.embeddings.embedding_model import EmbeddingModel
from src.vector_store.chroma_client import ChromaClient

import warnings
warnings.filterwarnings('ignore')


class FinAgentixIngestion:
    def __init__(self):
        print("="*70)
        print("FINAGENTIX - KNOWLEDGE ENGINEERING (LAB 2)")
        print("="*70)
        
        # Load config
        self.config = config
        
        # Initialize all cleaners
        print("\n[Step 1] Initializing Cleaners...")
        self.market_cleaner = MarketCleaner()
        self.news_cleaner = NewsCleaner()
        self.compliance_cleaner = ComplianceCleaner()
        self.economic_cleaner = EconomicCleaner()
        self.fundamental_cleaner = FundamentalCleaner()
        self.risk_cleaner = RiskCleaner()
        print("✅ All cleaners initialized")
        
        # Initialize metadata enricher
        self.metadata_enricher = MetadataEnricher()
        
        # Initialize chunker
        self.chunker = SemanticChunker(self.config)
        
        # Initialize embedding model
        print("\n[Step 2] Initializing Embedding Model...")
        self.embedder = EmbeddingModel(
            model_name=self.config.get('embedding', 'model_name'),
            cache_dir=self.config.get('paths', 'embeddings_cache')
        )
        print(f"✅ Embedding model loaded (dimension: {self.embedder.dimension})")
        
        # Initialize vector database
        print("\n[Step 3] Initializing Vector Database...")
        self.chroma = ChromaClient(
            persist_directory=self.config.get('paths', 'knowledge_base')
        )
        
        # Data directories
        self.raw_dir = Path(self.config.get('paths', 'raw_data'))
        self.processed_dir = Path(self.config.get('paths', 'processed_data'))
        ensure_dir(self.processed_dir)
        
        # Statistics
        self.stats = {
            'total_chunks': 0,
            'collections': {},
            'processing_time': {}
        }
        
        # Collection name mapping
        self.collection_names = self.config.get('chromadb', 'collection_names')
    
    def ingest_market_data(self):
        """Process and ingest market data"""
        print("\n" + "="*70)
        print("[Task 1] Ingesting Market Data")
        print("="*70)
        
        market_files = list_files(self.raw_dir / "01_market_data", extension="csv")
        # Filter out the combined file
        market_files = [f for f in market_files if "all_stocks_combined" not in f.name]
        print(f"Found {len(market_files)} stock files")
        
        all_chunks = []
        
        # Process all stock files
        for i, file in enumerate(market_files):
            ticker = file.stem.replace('_5yr_REAL', '')
            print(f"  Processing {ticker} ({i+1}/{len(market_files)})...")
            
            try:
                # Read and clean
                df = pd.read_csv(file)
                df = self.market_cleaner.clean_stock_data(df, ticker)
                
                # Skip if empty after cleaning
                if len(df) == 0:
                    print(f"    ⚠️ No data after cleaning")
                    continue
                
                # Chunk
                chunks = self.chunker.chunk_stock_data(df, ticker, strategy='by_month')
                
                # Add metadata using enricher
                for chunk in chunks:
                    chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
                
                all_chunks.extend(chunks)
                print(f"    ✅ Created {len(chunks)} chunks")
            except Exception as e:
                print(f"    ❌ Error processing {ticker}: {e}")
        
        print(f"\n  Total chunks created: {len(all_chunks)}")
        
        if not all_chunks:
            print("  ⚠️ No chunks to ingest")
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(all_chunks)
        
        # Add to vector database using specialized handler
        collection_name = self.collection_names['market']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['market'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def ingest_news_data(self):
        """Process and ingest news data"""
        print("\n" + "="*70)
        print("[Task 2] Ingesting News & Sentiment Data")
        print("="*70)
        
        news_folder = self.raw_dir / "02_news_sentiment"
        all_chunks = []
        
        # Process news articles
        news_file = news_folder / "newsapi_articles_REAL.csv"
        if news_file.exists():
            print(f"Processing news articles...")
            df = pd.read_csv(news_file)
            print(f"  Loaded {len(df)} articles")
            
            # Clean
            df = self.news_cleaner.clean_news_dataframe(df)
            
            # Chunk
            chunks = self.chunker.chunk_news_articles(df)
            
            # Add metadata
            for chunk in chunks:
                chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
            
            all_chunks.extend(chunks)
            print(f"  ✅ Created {len(chunks)} news article chunks")
        else:
            print(f"  ⚠️ News file not found: {news_file}")
        
        # Process Financial PhraseBank
        phrase_file = news_folder / "financial_phrasebank_REAL.csv"
        if phrase_file.exists():
            print(f"\nProcessing Financial PhraseBank...")
            df = pd.read_csv(phrase_file)
            print(f"  Loaded {len(df)} phrases")
            
            # Clean
            df = self.news_cleaner.clean_financial_phrasebank(df)
            
            # Create chunks for each phrase
            phrase_chunks = []
            for _, row in df.iterrows():
                phrase_chunks.append({
                    'text': f"Financial Phrase: {row.get('phrase', '')}",
                    'metadata': {
                        'doc_type': 'sentiment_phrase',
                        'sentiment': row.get('sentiment', 'neutral'),
                        'source': 'Financial PhraseBank',
                        'ingestion_date': pd.Timestamp.now().isoformat()
                    }
                })
            
            all_chunks.extend(phrase_chunks)
            print(f"  ✅ Created {len(phrase_chunks)} sentiment phrase chunks")
        else:
            print(f"  ⚠️ PhraseBank file not found: {phrase_file}")
        
        print(f"\n  Total chunks created: {len(all_chunks)}")
        
        if not all_chunks:
            print("  ⚠️ No chunks to ingest")
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(all_chunks)
        
        # Add to vector database
        collection_name = self.collection_names['news']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['news'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def ingest_compliance_data(self):
        """Process and ingest FINRA rules"""
        print("\n" + "="*70)
        print("[Task 3] Ingesting Compliance Data")
        print("="*70)
        
        compliance_folder = self.raw_dir / "04_compliance_data"
        rule_file = compliance_folder / "finra_rules_scraped_REAL.csv"
        
        if not rule_file.exists():
            print(f"  ⚠️ FINRA rules file not found")
            return 0
        
        print(f"Loading FINRA rules...")
        df = pd.read_csv(rule_file)
        print(f"  Loaded {len(df)} rules")
        
        # Clean
        df = self.compliance_cleaner.clean_finra_rules(df)
        
        # Chunk
        chunks = self.chunker.chunk_finra_rules(df)
        
        # Add metadata
        for chunk in chunks:
            chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
        
        print(f"  Created {len(chunks)} FINRA rule chunks")
        
        if not chunks:
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(chunks)
        
        # Add to vector database
        collection_name = self.collection_names['compliance']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['compliance'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def ingest_fundamental_data(self):
        """Process and ingest fundamental data"""
        print("\n" + "="*70)
        print("[Task 4] Ingesting Fundamental Data")
        print("="*70)
        
        fund_folder = self.raw_dir / "06_fundamental_data"
        fund_file = fund_folder / "company_fundamentals_REAL.csv"
        
        if not fund_file.exists():
            print(f"  ⚠️ Fundamentals file not found")
            return 0
        
        print(f"Loading fundamentals...")
        df = pd.read_csv(fund_file)
        print(f"  Loaded {len(df)} companies")
        
        # Clean using fundamental cleaner
        df = self.fundamental_cleaner.clean_fundamentals(df)
        
        # Chunk
        chunks = self.chunker.chunk_company_fundamentals(df)
        
        # Add metadata
        for chunk in chunks:
            chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
        
        print(f"  Created {len(chunks)} company chunks")
        
        if not chunks:
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(chunks)
        
        # Add to vector database
        collection_name = self.collection_names['fundamental']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['fundamental'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def ingest_economic_data(self):
        """Process and ingest economic data"""
        print("\n" + "="*70)
        print("[Task 5] Ingesting Economic Data")
        print("="*70)
        
        eco_folder = self.raw_dir / "05_economic_data"
        eco_files = list_files(eco_folder, extension="csv")
        
        print(f"Found {len(eco_files)} economic indicator files")
        all_chunks = []
        
        # Friendly name mapping
        indicator_names = {
            'GDP': 'Gross Domestic Product',
            'UNRATE': 'Unemployment Rate',
            'CPIAUCSL': 'Consumer Price Index',
            'FEDFUNDS': 'Federal Funds Rate',
            'DGS10': '10-Year Treasury Rate',
            'DGS2': '2-Year Treasury Rate',
            'VIXCLS': 'CBOE Volatility Index',
            'MORTGAGE30US': '30-Year Mortgage Rate',
            'DEXUSEU': 'USD/EUR Exchange Rate',
            'T10Y2Y': '10Y-2Y Treasury Spread',
            'DAAA': 'Moodys Aaa Corporate Bond Yield',
            'DBAA': 'Moodys Baa Corporate Bond Yield',
            'RECPROUSM156N': 'Recession Probabilities',
            'HOUST': 'Housing Starts',
            'UMCSENT': 'Consumer Sentiment'
        }
        
        for file in eco_files:
            series_id = file.stem.replace('fred_', '').replace('_REAL', '')
            indicator_name = indicator_names.get(series_id, series_id)
            
            print(f"  Processing {indicator_name}...")
            
            try:
                # Read and clean using economic cleaner
                df = pd.read_csv(file)
                df = self.economic_cleaner.clean_economic_indicator(df, series_id)
                
                # Chunk
                chunks = self.chunker.chunk_economic_data(df, indicator_name, series_id)
                
                # Add metadata
                for chunk in chunks:
                    chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
                
                all_chunks.extend(chunks)
                print(f"    ✅ Created chunk")
            except Exception as e:
                print(f"    ❌ Error processing {series_id}: {e}")
        
        print(f"\n  Total chunks created: {len(all_chunks)}")
        
        if not all_chunks:
            print("  ⚠️ No chunks to ingest")
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(all_chunks)
        
        # Add to vector database
        collection_name = self.collection_names['economic']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['economic'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def ingest_risk_data(self):
        """Process and ingest risk metrics"""
        print("\n" + "="*70)
        print("[Task 6] Ingesting Risk Metrics")
        print("="*70)
        
        risk_folder = self.raw_dir / "03_risk_data"
        risk_file = risk_folder / "risk_metrics_REAL.csv"
        
        if not risk_file.exists():
            print(f"  ⚠️ Risk metrics file not found")
            return 0
        
        print(f"Loading risk metrics...")
        df = pd.read_csv(risk_file)
        print(f"  Loaded {len(df)} stocks")
        
        # Validate risk metrics
        validation_issues = self.risk_cleaner.validate_risk_metrics(df)
        if validation_issues:
            print(f"  ⚠️ Found {len(validation_issues)} validation issues")
        
        # Clean using risk cleaner
        df = self.risk_cleaner.clean_risk_metrics(df)
        
        # Chunk
        chunks = self.chunker.chunk_risk_metrics(df)
        
        # Add metadata
        for chunk in chunks:
            chunk['metadata']['ingestion_date'] = pd.Timestamp.now().isoformat()
        
        print(f"  Created {len(chunks)} risk metric chunks")
        
        if not chunks:
            return 0
        
        # Generate embeddings
        print(f"  Generating embeddings...")
        chunks_with_embeddings = self.embedder.embed_chunks(chunks)
        
        # Add to vector database
        collection_name = self.collection_names['risk']
        num_added = self.chroma.add_chunks_with_handler(collection_name, chunks_with_embeddings)
        
        self.stats['collections']['risk'] = num_added
        self.stats['total_chunks'] += num_added
        
        return num_added
    
    def run_all(self):
        """Run complete ingestion pipeline"""
        print("\n" + "="*70)
        print("STARTING COMPLETE INGESTION PIPELINE")
        print("="*70)
        
        import time
        start_time = time.time()
        
        # Run all ingestion tasks
        tasks = [
            self.ingest_market_data,
            self.ingest_news_data,
            self.ingest_compliance_data,
            self.ingest_fundamental_data,
            self.ingest_economic_data,
            self.ingest_risk_data
        ]
        
        for task in tasks:
            task_start = time.time()
            task()
            task_end = time.time()
            task_name = task.__name__.replace('ingest_', '')
            self.stats['processing_time'][task_name] = round(task_end - task_start, 2)
        
        total_time = round(time.time() - start_time, 2)
        
        # Get final stats from ChromaDB
        print("\n" + "="*70)
        print("GATHERING FINAL STATISTICS")
        print("="*70)
        
        try:
            db_stats = self.chroma.get_all_stats()
        except:
            print("  Could not retrieve database stats")
        
        # Final summary
        print("\n" + "="*70)
        print("INGESTION COMPLETE! 🎉")
        print("="*70)
        print(f"\n📊 Total chunks ingested: {self.stats['total_chunks']}")
        print(f"⏱️  Total processing time: {total_time} seconds")
        
        print("\n📋 Collection Summary:")
        for collection, count in self.stats['collections'].items():
            print(f"   • {collection}: {count} chunks")
        
        print("\n⏱️  Processing Time by Task:")
        for task, seconds in self.stats['processing_time'].items():
            print(f"   • {task}: {seconds}s")
        
        print(f"\n📁 Knowledge Base: {self.chroma.persist_directory.absolute()}")
        
        # Verify collections
        print("\n🔍 Verifying collections...")
        try:
            self.chroma.list_collections()
        except:
            print("  Could not list collections")
        
        print("\n✅ Ready for retrieval testing!")
        print("="*70)


if __name__ == "__main__":
    ingestion = FinAgentixIngestion()
    ingestion.run_all()