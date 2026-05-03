import pandas as pd
from src.utils.text_utils import clean_text

class FundamentalCleaner:
    def clean_fundamentals(self, df):
        """Clean company fundamentals DataFrame"""
        df = df.copy()
        
        # Standardize column names
        column_mapping = {
            'ticker': 'ticker',
            'company_name': 'company_name',
            'sector': 'sector',
            'industry': 'industry',
            'market_cap': 'market_cap',
            'pe_ratio': 'pe_ratio',
            'forward_pe': 'forward_pe',
            'peg_ratio': 'peg_ratio',
            'price_to_book': 'price_to_book',
            'debt_to_equity': 'debt_to_equity',
            'profit_margin': 'profit_margin',
            'operating_margin': 'operating_margin',
            'return_on_equity': 'return_on_equity',
            'dividend_yield': 'dividend_yield',
            'beta': 'beta',
            'fifty_two_week_high': 'fifty_two_week_high',
            'fifty_two_week_low': 'fifty_two_week_low',
            'average_volume': 'average_volume'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and old_col != new_col:
                df[new_col] = df[old_col]
        
        # Clean text fields
        text_fields = ['company_name', 'sector', 'industry']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].apply(lambda x: clean_text(str(x)) if pd.notna(x) else 'Unknown')
        
        # Convert market cap to billions for readability
        if 'market_cap' in df.columns:
            # Check if market cap is already in billions
            if df['market_cap'].max() > 1e10:  # If values are > 10 billion
                df['market_cap_billions'] = df['market_cap'] / 1e9
            else:
                df['market_cap_billions'] = df['market_cap']
        
        # Convert ratios to percentages where appropriate
        ratio_cols = ['profit_margin', 'operating_margin', 'return_on_equity', 'dividend_yield']
        for col in ratio_cols:
            if col in df.columns:
                # If values are between 0 and 1, convert to percentage
                if df[col].max() < 1 and df[col].max() > -1:
                    df[f'{col}_pct'] = df[col] * 100
                else:
                    df[f'{col}_pct'] = df[col]
        
        # Handle missing values
        df = df.fillna({
            'pe_ratio': 0,
            'forward_pe': 0,
            'peg_ratio': 0,
            'price_to_book': 0,
            'debt_to_equity': 0,
            'profit_margin': 0,
            'operating_margin': 0,
            'return_on_equity': 0,
            'dividend_yield': 0,
            'beta': 1.0,
            'fifty_two_week_high': 0,
            'fifty_two_week_low': 0,
            'average_volume': 0
        })
        
        # Add metadata
        df['source'] = 'Yahoo Finance'
        df['download_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        return df
    
    def extract_company_summary(self, row):
        """Create a human-readable summary from fundamentals"""
        ticker = row.get('ticker', 'Unknown')
        name = row.get('company_name', ticker)
        sector = row.get('sector', 'Unknown')
        
        summary = f"{name} ({ticker}) is in the {sector} sector. "
        
        if pd.notna(row.get('market_cap_billions')):
            summary += f"Market capitalization: ${row['market_cap_billions']:.2f}B. "
        
        if pd.notna(row.get('pe_ratio')) and row['pe_ratio'] > 0:
            summary += f"P/E ratio: {row['pe_ratio']:.2f}. "
        
        if pd.notna(row.get('profit_margin_pct')):
            summary += f"Profit margin: {row['profit_margin_pct']:.2f}%. "
        
        if pd.notna(row.get('beta')):
            risk = "high" if row['beta'] > 1.5 else "moderate" if row['beta'] > 1 else "low"
            summary += f"Beta: {row['beta']:.2f} ({risk} volatility)."
        
        return summary