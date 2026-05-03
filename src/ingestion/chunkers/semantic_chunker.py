import pandas as pd
import numpy as np
from datetime import timedelta

class SemanticChunker:
    def __init__(self, config):
        self.config = config
    
    def chunk_stock_data(self, df, ticker, strategy='by_month'):
        """Chunk stock data by month"""
        chunks = []
        
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Group by year-month
            df['year_month'] = df['Date'].dt.to_period('M')
            
            for month, group in df.groupby('year_month'):
                # Create text representation
                text = f"{ticker} stock data for {month}:\n"
                for _, row in group.iterrows():
                    # Convert to float safely
                    try:
                        open_val = float(row['Open'])
                        high_val = float(row['High'])
                        low_val = float(row['Low'])
                        close_val = float(row['Close'])
                        volume_val = int(float(row['Volume'])) if pd.notna(row['Volume']) else 0
                        
                        text += f"Date: {row['Date'].strftime('%Y-%m-%d')}, "
                        text += f"Open: ${open_val:.2f}, High: ${high_val:.2f}, "
                        text += f"Low: ${low_val:.2f}, Close: ${close_val:.2f}, "
                        text += f"Volume: {volume_val}\n"
                    except (ValueError, TypeError) as e:
                        # Skip problematic rows
                        continue
                
                chunks.append({
                    'text': text,
                    'metadata': {
                        'doc_type': 'stock_price',
                        'ticker': ticker,
                        'month': str(month),
                        'start_date': group['Date'].min().strftime('%Y-%m-%d'),
                        'end_date': group['Date'].max().strftime('%Y-%m-%d'),
                        'num_days': len(group)
                    }
                })
        
        return chunks
    
    def chunk_news_articles(self, df, strategy='by_article'):
        """Chunk news articles - each article as one chunk"""
        chunks = []
        
        for _, row in df.iterrows():
            # Combine title and description/content
            text = f"Title: {row.get('title', '')}\n"
            text += f"Description: {row.get('description', '')}\n"
            if row.get('content') and len(str(row.get('content', ''))) > 50:
                text += f"Content: {row.get('content', '')}"
            
            chunks.append({
                'text': text,
                'metadata': {
                    'doc_type': 'news_article',
                    'source': row.get('source', 'Unknown'),
                    'published_date': row.get('published_at', '')[:10] if row.get('published_at') else '',
                    'query_used': row.get('query_used', '')
                }
            })
        
        return chunks
    
    def chunk_finra_rules(self, df, strategy='by_rule'):
        """Chunk FINRA rules - each rule as one chunk"""
        chunks = []
        
        for _, row in df.iterrows():
            text = f"FINRA Rule {row.get('rule_id', '')}:\n"
            text += row.get('rule_text', '')
            
            chunks.append({
                'text': text,
                'metadata': {
                    'doc_type': 'finra_rule',
                    'rule_id': row.get('rule_id', ''),
                    'category': row.get('category', 'Unknown')
                }
            })
        
        return chunks
    
    def chunk_company_fundamentals(self, df, strategy='by_company'):
        """Chunk company fundamentals - each company as one chunk"""
        chunks = []
        
        for _, row in df.iterrows():
            text = f"Company: {row.get('company_name', '')} ({row.get('ticker', '')})\n"
            text += f"Sector: {row.get('sector', '')}, Industry: {row.get('industry', '')}\n"
            text += f"Market Cap: ${row.get('market_cap', 0):,.0f}\n"
            text += f"P/E Ratio: {row.get('pe_ratio', 0):.2f}\n"
            text += f"Forward P/E: {row.get('forward_pe', 0):.2f}\n"
            text += f"Profit Margin: {row.get('profit_margin', 0):.2%}\n"
            text += f"Beta: {row.get('beta', 0):.2f}"
            
            chunks.append({
                'text': text,
                'metadata': {
                    'doc_type': 'fundamental_data',
                    'ticker': row.get('ticker', ''),
                    'sector': row.get('sector', 'Unknown'),
                    'industry': row.get('industry', 'Unknown')
                }
            })
        
        return chunks
    
    def chunk_economic_data(self, df, indicator_name, series_id, strategy='by_indicator'):
        """Chunk economic data - entire indicator as one chunk"""
        # Convert to text
        text = f"Economic Indicator: {indicator_name} ({series_id})\n"
        text += f"Source: FRED (Federal Reserve)\n\n"
        
        # Add recent data points (last 20)
        recent = df.tail(20)
        for _, row in recent.iterrows():
            date = row.get('DATE', '')
            value = row.get(series_id, '')
            if pd.notna(value):
                text += f"{date}: {value}\n"
        
        chunks = [{
            'text': text,
            'metadata': {
                'doc_type': 'economic_indicator',
                'indicator_name': indicator_name,
                'series_id': series_id,
                'source': 'FRED',
                'num_observations': len(df)
            }
        }]
        
        return chunks
    
    def chunk_risk_metrics(self, df, strategy='by_stock'):
        """Chunk risk metrics - each stock as one chunk"""
        chunks = []
        
        for _, row in df.iterrows():
            text = f"Risk Metrics for {row.get('ticker', '')} ({row.get('sector', '')}):\n\n"
            text += f"Annual Volatility: {row.get('volatility_annual', 0):.2f}%\n"
            text += f"Value at Risk (95%): {row.get('var_95_daily', 0):.2f}%\n"
            text += f"Value at Risk (99%): {row.get('var_99_daily', 0):.2f}%\n"
            text += f"Conditional VaR (95%): {row.get('cvar_95_daily', 0):.2f}%\n"
            text += f"Conditional VaR (99%): {row.get('cvar_99_daily', 0):.2f}%\n"
            text += f"Sharpe Ratio: {row.get('sharpe_ratio', 0):.3f}\n"
            text += f"Sortino Ratio: {row.get('sortino_ratio', 0):.3f}\n"
            text += f"Max Drawdown: {row.get('max_drawdown', 0):.2f}%\n"
            text += f"Skewness: {row.get('skewness', 0):.3f}\n"
            text += f"Kurtosis: {row.get('kurtosis', 0):.3f}"
            
            chunks.append({
                'text': text,
                'metadata': {
                    'doc_type': 'risk_metrics',
                    'ticker': row.get('ticker', ''),
                    'sector': row.get('sector', 'Unknown')
                }
            })
        
        return chunks