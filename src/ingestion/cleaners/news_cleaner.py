import pandas as pd
from src.utils.text_utils import clean_text

class NewsCleaner:
    def clean_news_article(self, row):
        """Clean a single news article"""
        cleaned = {}
        
        # Clean title
        cleaned['title'] = clean_text(row.get('title', ''))
        
        # Clean description
        cleaned['description'] = clean_text(row.get('description', ''))
        
        # Clean content
        content = row.get('content', '')
        if isinstance(content, str) and len(content) > 10:
            cleaned['content'] = clean_text(content)
        else:
            cleaned['content'] = cleaned['description']
        
        # Keep metadata
        cleaned['source'] = clean_text(row.get('source', ''))
        cleaned['author'] = clean_text(row.get('author', ''))
        cleaned['published_at'] = row.get('published_at', '')
        cleaned['url'] = row.get('url', '')
        cleaned['query_used'] = row.get('query_used', '')
        
        return cleaned
    
    def clean_news_dataframe(self, df):
        """Clean entire news DataFrame"""
        cleaned_rows = []
        for _, row in df.iterrows():
            cleaned_rows.append(self.clean_news_article(row))
        
        return pd.DataFrame(cleaned_rows)
    
    def clean_financial_phrasebank(self, df):
        """Clean Financial PhraseBank data"""
        df = df.copy()
        if 'phrase' in df.columns:
            df['phrase'] = df['phrase'].apply(clean_text)
        return df