# export_service.py
# Service untuk handle export data

import json
import csv
from io import StringIO
from datetime import datetime

def export_to_json(data):
    """Export data ke format JSON"""
    export_data = []
    for item in data:
        clean_item = {
            "title": item.get("title", ""),
            "year": item.get("year", ""),
            "runtime": item.get("runtime", ""),
            "jwRating": item.get("jwRating", ""),
            "tomatometer": item.get("tomatometer", ""),
            "tomatocertifiedFresh": item.get("tomatocertifiedFresh", False),
            "overview": item.get("overview", ""),
            "poster": item.get("poster", ""),
            "link": item.get("link", ""),
        }
        # Tambah offers jika ada
        offers = item.get("offers", [])
        if offers:
            clean_item["offers"] = offers
        export_data.append(clean_item)
    
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def export_to_csv(data):
    """Export data ke format CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["title", "year", "runtime", "jwRating", "tomatometer", 
                    "tomatocertifiedFresh", "overview", "poster", "link"])
    
    # Data
    for item in data:
        writer.writerow([
            item.get("title", ""),
            item.get("year", ""),
            item.get("runtime", ""),
            item.get("jwRating", ""),
            item.get("tomatometer", ""),
            item.get("tomatocertifiedFresh", False),
            item.get("overview", "")[:100],  # Potong overview biar tidak terlalu panjang
            item.get("poster", ""),
            item.get("link", ""),
        ])
    
    return output.getvalue()

def generate_filename(prefix, query=""):
    """Generate nama file untuk export"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    if query:
        return f"{prefix}_{query}_{timestamp}"
    return f"{prefix}_{timestamp}"