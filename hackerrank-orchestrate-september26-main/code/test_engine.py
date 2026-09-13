import pandas as pd
import numpy as np
import datetime
import math
import re

# 1. Image OCR Dictionary (Exact amounts extracted from 16 images)
IMAGE_AMOUNTS = {
    'event_253': 4365000.0,   # image_01: Payslip Net Pay IDR
    'event_1442': 100000.0,   # image_02: Rent balance due INR
    'event_1545': 41272.0,    # image_03: Riddhi Siddhi bill INR
    'event_1700': 2854.0,     # image_04: Groceries bill INR
    'event_1786': 704.05,     # image_05: Airtel bill INR
    'event_3051': 1995.0,     # image_06: Blink invoice INR
    'event_3231': 8528.0,     # image_07: Nagarjuna tax invoice INR
    'event_4535': 15339.0,    # image_08: Property maintenance INR
    'event_5170': 723.0,      # image_09: Water bill INR
    'event_6033': 79679.26,   # image_10: Grocery invoice INR
    'event_6859': 3650.0,     # image_11: Hospital bill INR
    'event_7307': 33.50,      # image_12: Taxi fare USD
    'event_7941': 2298.0,     # image_13: Tote bag order INR
    'event_9421': 4543.0,     # image_14: Pharmacy bill INR
    'event_9806': 9968.0,     # image_15: IndiGo flight INR
    'event_10521': 393.22,    # image_16: EV charge invoice INR
}

def parse_date(d_str):
    if not isinstance(d_str, str) or not d_str or d_str == 'nan':
        return None
    return datetime.datetime.strptime(d_str[:10], "%Y-%m-%d").date()

def format_date(d):
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")

print("Test engine helper loaded.")
