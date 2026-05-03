import re
import html

def clean_text(text):
    """Clean text by removing extra whitespace, HTML tags, etc."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)]', '', text)
    
    return text.strip()

def normalize_text(text):
    """Normalize text for consistent processing"""
    text = clean_text(text)
    text = text.lower()
    return text