import pandas as pd
from src.utils.text_utils import clean_text

class RiskCleaner:
    def clean_risk_metrics(self, df):
        """Clean risk metrics DataFrame"""
        df = df.copy()
        
        # Standardize column names
        column_mapping = {
            'ticker': 'ticker',
            'volatility_annual': 'volatility_annual',
            'var_95_daily': 'var_95_daily',
            'var_99_daily': 'var_99_daily',
            'cvar_95_daily': 'cvar_95_daily',
            'cvar_99_daily': 'cvar_99_daily',
            'sharpe_ratio': 'sharpe_ratio',
            'sortino_ratio': 'sortino_ratio',
            'max_drawdown': 'max_drawdown',
            'skewness': 'skewness',
            'kurtosis': 'kurtosis',
            'sector': 'sector'
        }
        
        # Rename columns if they exist
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns and old_col != new_col:
                df[new_col] = df[old_col]
        
        # Keep only needed columns
        keep_cols = [col for col in column_mapping.values() if col in df.columns]
        df = df[keep_cols]
        
        # Convert percentage strings to floats if needed
        for col in ['volatility_annual', 'var_95_daily', 'var_99_daily', 
                    'cvar_95_daily', 'cvar_99_daily', 'max_drawdown']:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = df[col].str.replace('%', '').astype(float)
        
        # Round numeric columns to 4 decimal places
        numeric_cols = df.select_dtypes(include=['float64']).columns
        df[numeric_cols] = df[numeric_cols].round(4)
        
        # Add metadata
        df['source'] = 'Calculated from Yahoo Finance'
        df['calculation_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
        
        return df
    
    def validate_risk_metrics(self, df):
        """Validate risk metrics are within reasonable ranges"""
        validations = []
        
        for _, row in df.iterrows():
            ticker = row.get('ticker', 'Unknown')
            issues = []
            
            # Check volatility (should be between 0 and 100)
            if 'volatility_annual' in row and (row['volatility_annual'] < 0 or row['volatility_annual'] > 100):
                issues.append(f"volatility {row['volatility_annual']:.2f}% out of range")
            
            # Check VaR (should be between 0 and 30)
            if 'var_95_daily' in row and (row['var_95_daily'] < 0 or row['var_95_daily'] > 30):
                issues.append(f"VaR 95% {row['var_95_daily']:.2f}% out of range")
            
            # Check Sharpe ratio (typically between -2 and 5)
            if 'sharpe_ratio' in row and (row['sharpe_ratio'] < -2 or row['sharpe_ratio'] > 5):
                issues.append(f"Sharpe {row['sharpe_ratio']:.2f} out of range")
            
            if issues:
                validations.append({
                    'ticker': ticker,
                    'issues': issues
                })
        
        return validations