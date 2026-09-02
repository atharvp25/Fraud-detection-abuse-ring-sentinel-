"""
Helper functions for data generation (dates, IDs, etc.)
"""
import random
from datetime import datetime, timedelta

def random_date_past_year(end_date=None, days_back=365):
    """Generate a random date within the past year."""
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back)
    random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
    return start_date + timedelta(seconds=random_seconds)

def random_date_within_window(base_date, min_hours=0, max_hours=24):
    """Generate a date within a short window (used for ring creation bursts)."""
    random_minutes = random.randint(min_hours * 60, max_hours * 60)
    return base_date + timedelta(minutes=random_minutes)

def generate_id(prefix, index):
    """Format an ID cleanly, e.g., C0001, D0125"""
    return f"{prefix}{index:04d}"
