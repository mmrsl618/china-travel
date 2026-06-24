import re, os, sys
from collections import Counter

files = [
    "regional-chinese-cuisines-guide.html",
    "classic-china-beijing-xian-shanghai.html",
    "shanghai-hangzhou-week-itinerary.html"
]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for fname in files:
    with open(fname, 'r', encoding='utf-8') as f:
        html = f.read()
    
    body = html.split('<h1>', 1)[1] if '<h1>' in html else html
    body = body.split('<hr class="ref-separator">')[0] if '<hr class="ref-separator">' in body else body
    
    paragraphs = re.findall(r'<p>(.*?)</p>', body, re.DOTALL)
    para_texts = [re.sub(r'<[^>]+>', '', p).strip() for p in paragraphs]
    para_texts = [t for t in para_texts if len(t) > 20]
    
    dupes = [item for item, count in Counter(para_texts).items() if count > 1]
    
    if dupes:
        print(f"\n=== {fname}: FOUND {len(dupes)} DUPLICATE PARAGRAPHS ===")
        for d in dupes:
            print(f"  -> \"{d[:80]}...\"")
    else:
        print(f"{fname}: No duplicate paragraphs [OK]")
    
    all_text = ' '.join(para_texts)
    sentences = re.split(r'(?<=[.!?])\s+', all_text)
    sent_dupes = [item for item, count in Counter(sentences).items() if count > 1 and len(item) > 30]
    if sent_dupes:
        print(f"  Found {len(sent_dupes)} duplicate sentences:")
        for d in sent_dupes[:3]:
            print(f"  -> \"{d[:60]}...\"")
