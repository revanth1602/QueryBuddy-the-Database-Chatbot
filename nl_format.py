import re

def format_nl_response(raw_text):
    # Format currency values (e.g., 2000.00 → $2,000.00)
    formatted = re.sub(
        r'\b(\d+\.\d{2})\b',
        lambda m: f"${int(m.group(1).split('.')[0]):,}.{m.group(1).split('.')[1]}",
        raw_text
    )
    
    # Add spaces after punctuation (.,)
    formatted = re.sub(r'([.,])(?=[A-Za-z0-9])', r'\1 ', formatted)
    
    # Split merged words (e.g., "top4customers" → "top 4 customers")
    formatted = re.sub(r'([a-z])([A-Z0-9])', r'\1 \2', formatted)  # Lowercase → Uppercase/Number
    formatted = re.sub(r'([0-9])([A-Za-z])', r'\1 \2', formatted)  # Number → Letter
    
    return formatted