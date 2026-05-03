import pandas as pd
from src.utils.text_utils import clean_text

class EconomicCleaner:
    def clean_economic_indicator(self, df, series_id):
        """Clean FRED economic indicator DataFrame"""
        df = df.copy()
        
        # Standardize date column
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'])
        elif 'date' in df.columns:
            df['DATE'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        
        # Rename value column to standard name
        if series_id in df.columns:
            df['value'] = df[series_id]
            df = df.drop(series_id, axis=1)
        elif 'value' not in df.columns:
            # Try to find the numeric column
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if len(numeric_cols) > 0:
                df['value'] = df[numeric_cols[0]]
        
        # Remove rows with missing values
        df = df.dropna(subset=['value'])
        
        # Sort by date
        if 'DATE' in df.columns:
            df = df.sort_values('DATE')
        
        # Add metadata columns
        df['series_id'] = series_id
        df['source'] = 'FRED'
        
        return df
    
    def clean_all_economic(self, economic_files):
        """Clean multiple economic indicator files"""
        cleaned_data = {}
        for file in economic_files:
            series_id = file.stem.replace('fred_', '').replace('_REAL', '')
            df = pd.read_csv(file)
            cleaned_data[series_id] = self.clean_economic_indicator(df, series_id)
        return cleaned_data