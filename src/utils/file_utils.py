import os
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

def ensure_dir(path):
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

def list_files(directory, extension=None):
    """List files in directory with optional extension filter"""
    path = Path(directory)
    if extension:
        return list(path.glob(f"*.{extension}"))
    return list(path.glob("*"))

def read_csv(file_path):
    """Read CSV file"""
    return pd.read_csv(file_path)

def read_json(file_path):
    """Read JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_processed_chunk(data, folder, filename):
    """Save processed chunk to processed folder"""
    path = Path(f"./data/processed/{folder}")
    ensure_dir(path)
    if isinstance(data, pd.DataFrame):
        data.to_csv(path / filename, index=False)
    elif isinstance(data, dict):
        with open(path / filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)