from datetime import datetime

class MetadataEnricher:
    def enrich_stock_chunk(self, chunk, ticker, start_date, end_date):
        """Add metadata to stock price chunk"""
        metadata = {
            "doc_type": "stock_price",
            "ticker": ticker,
            "date_range_start": start_date,
            "date_range_end": end_date,
            "chunk_type": "time_series",
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata
    
    def enrich_news_article(self, article):
        """Add metadata to news article"""
        metadata = {
            "doc_type": "news_article",
            "source": article.get('source', 'Unknown'),
            "published_date": article.get('published_at', '')[:10] if article.get('published_at') else '',
            "query_used": article.get('query_used', ''),
            "has_content": 1 if len(article.get('content', '')) > 100 else 0,
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata
    
    def enrich_finra_rule(self, rule):
        """Add metadata to FINRA rule"""
        metadata = {
            "doc_type": "finra_rule",
            "rule_id": rule.get('rule_id', ''),
            "category": rule.get('category', 'Unknown'),
            "source": rule.get('source', 'FINRA.org'),
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata
    
    def enrich_company_fundamental(self, company):
        """Add metadata to company fundamental"""
        metadata = {
            "doc_type": "fundamental_data",
            "ticker": company.get('ticker', ''),
            "sector": company.get('sector', 'Unknown'),
            "industry": company.get('industry', 'Unknown'),
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata
    
    def enrich_economic_indicator(self, indicator_name, series_id):
        """Add metadata to economic indicator"""
        metadata = {
            "doc_type": "economic_indicator",
            "indicator_name": indicator_name,
            "series_id": series_id,
            "source": "FRED",
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata
    
    def enrich_risk_metric(self, ticker, sector):
        """Add metadata to risk metric"""
        metadata = {
            "doc_type": "risk_metrics",
            "ticker": ticker,
            "sector": sector,
            "ingestion_date": datetime.now().isoformat()
        }
        return metadata