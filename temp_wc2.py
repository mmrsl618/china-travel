import re
with open(r'E:\项目库\china-travel-website\articles\.src\vpn-china.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove everything before <h1> and after <hr class="ref-separator">
# (to exclude reference section)
html = html.split('<hr class="ref-separator">')[0] if '<hr class="ref-separator">' in html else html

text = re.sub(r'<[^>]+>', ' ', html)
# Remove image alt tags
text = re.sub(r'\[比例:16:9\]', '', text)
# Remove alt text inside img tags
text = re.sub(r'alt="[^"]*"', '', text)
# Remove h1/h2 heading text (count separately)
# Actually, let me just count all body text including headings
words = text.split()
print(f'Total words (body + sources): {len(words)}')
