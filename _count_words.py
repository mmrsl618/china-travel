import re

with open(r'articles\.src\high-speed-trains.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Extract body text: get all text between <p>...</p> and headings
# Remove all HTML tags
text = re.sub(r'<[^>]+>', ' ', html)
# Remove alt text markers like [比例:16:9]
text = re.sub(r'\[[^\]]*\]', '', text)
# Remove references section
parts = text.split('References')
body = parts[0] if len(parts) > 1 else text
# Remove policy note
body = re.sub(r'This article is based on.*$', '', body)
# Normalize whitespace
body = re.sub(r'\s+', ' ', body).strip()

words = body.split()
print(f'Body word count: {len(words)}')
