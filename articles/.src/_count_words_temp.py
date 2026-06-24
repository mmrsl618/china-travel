import re, sys, os

files = [
    "regional-chinese-cuisines-guide.html",
    "classic-china-beijing-xian-shanghai.html",
    "shanghai-hangzhou-week-itinerary.html"
]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract body text between <h1> and references separator
    body = html.split('<h1>', 1)[1] if '<h1>' in html else html
    body = body.split('<hr class="ref-separator">')[0] if '<hr class="ref-separator">' in body else body
    
    # Strip HTML tags
    text = re.sub(r'<[^>]+>', '', body)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    words = text.split()
    
    # Count h2s
    h2_count = html.count('<h2>')
    
    # Count images
    img_count = len(re.findall(r'<img[^>]+>', body))
    
    print(f"{fname}: {len(words)} words, {h2_count} x ## H2, {img_count} images")
