import csv
import re
import os

def final_cleanup(csv_path):
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    # 1. Filter and clean
    cleaned_data = {}
    for row in rows:
        name = row['term_name']
        desc = row['description'] or ""
        
        if len(desc) < 20: continue
        
        # Deep clean description
        desc = re.sub(r'\s\d+\s', ' ', desc)
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # Keep longest description for each term
        if name not in cleaned_data or len(desc) > len(cleaned_data[name]['description']):
            row['description'] = desc
            cleaned_data[name] = row
            
    # 2. Re-assign IDs and sort
    sorted_terms = sorted(cleaned_data.values(), key=lambda x: int(x['term_id']))
    for i, row in enumerate(sorted_terms):
        row['term_id'] = i + 1
        
    # 3. Write back
    keys = ['term_id', 'term_name', 'category', 'difficulty', 'description', 'example_text']
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(sorted_terms)
    
    print(f"Cleaned CSV. Final count: {len(sorted_terms)}")

if __name__ == "__main__":
    final_cleanup("glossary.csv")
