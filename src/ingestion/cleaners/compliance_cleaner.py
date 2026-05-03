import pandas as pd
from src.utils.text_utils import clean_text

class ComplianceCleaner:
    def clean_finra_rule(self, row):
        """Clean a single FINRA rule"""
        cleaned = {}
        
        cleaned['rule_id'] = str(row.get('rule_id', '')).strip()
        cleaned['rule_text'] = clean_text(row.get('rule_text', ''))
        cleaned['category'] = clean_text(row.get('category', 'Unknown'))
        cleaned['source'] = clean_text(row.get('source', 'FINRA.org'))
        cleaned['scrape_date'] = row.get('scrape_date', '')
        
        return cleaned
    
    def clean_finra_rules(self, df):
        """Clean FINRA rules DataFrame"""
        cleaned_rows = []
        for _, row in df.iterrows():
            cleaned_rows.append(self.clean_finra_rule(row))
        
        return pd.DataFrame(cleaned_rows)