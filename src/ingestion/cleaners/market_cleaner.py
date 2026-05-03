import pandas as pd
from src.utils.text_utils import clean_text

class MarketCleaner:
    def clean_stock_data(self, df, ticker):

        """Clean stock price DataFrame"""
        df = df.copy()
        
        # Ensure Date is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Convert price columns to numeric
        price_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in price_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove any rows with missing values
        df = df.dropna(subset=price_cols)
        
        # Sort by date
        if 'Date' in df.columns:
            df = df.sort_values('Date')
        
        # Add ticker column if not present
        if 'Ticker' not in df.columns:
            df['Ticker'] = ticker
        
        return df
    
    def clean_all_stocks(self, stock_files):
        """Clean multiple stock files"""
        cleaned_data = {}
        for file in stock_files:
            ticker = file.stem.replace('_5yr_REAL', '')
            df = pd.read_csv(file)
            cleaned_data[ticker] = self.clean_stock_data(df, ticker)
        return cleaned_data