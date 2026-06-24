import re
with open(r'E:\项目库\china-travel-website\articles\.src\vpn-china.html', 'r', encoding='utf-8') as f:
    html = f.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\[比例:16:9\]', '', text)
words = text.split()
print(f'Word count (EN): {len(words)}')
