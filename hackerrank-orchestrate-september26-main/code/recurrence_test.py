import pandas as pd
import numpy as np
import datetime
import math
import re
import sys

# Image OCR mapping
IMAGE_AMOUNTS = {
    'event_253': 4365000.0,
    'event_1442': 100000.0,
    'event_1545': 41272.0,
    'event_1700': 2854.0,
    'event_1786': 704.05,
    'event_3051': 1995.0,
    'event_3231': 8528.0,
    'event_4535': 15339.0,
    'event_5170': 723.0,
    'event_6033': 79679.26,
    'event_6859': 3650.0,
    'event_7307': 33.50,
    'event_7941': 2298.0,
    'event_9421': 4543.0,
    'event_9806': 9968.0,
    'event_10521': 393.22,
}

def parse_date(d_str):
    if not isinstance(d_str, str) or not d_str or str(d_str) == 'nan':
        return None
    try:
        return datetime.datetime.strptime(str(d_str)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

def format_date(d):
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")

# Load datasets
profiles = pd.read_csv("dataset/financial_profiles.csv")
events = pd.read_csv("dataset/financial_events.csv")
exchange_rates = pd.read_csv("dataset/exchange_rates.csv")
sample_requests = pd.read_csv("dataset/sample_requests.csv")
messages = pd.read_csv("dataset/messages.csv")
payment_options = pd.read_csv("dataset/request_payment_options.csv")

print("Recurrence test loaded successfully.")
