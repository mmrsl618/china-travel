import re, os

src_done = r'E:\项目库\china-travel-website\articles\en\before-you-go\visa\_done\visa-guide.html'
dst_src = r'E:\项目库\china-travel-website\articles\.src\visa-guide.html'

with open(src_done, 'r', encoding='utf-8') as f:
    raw = f.read()

# 提取 body
m = re.search(r'<body>(.*?)</body>', raw, re.DOTALL)
body = m.group(1).strip() if m else raw

# 去掉 header
hi = body.find('</header>')
if hi > 0:
    body = body[hi + len('</header>'):]

# 去掉 footer
fi = body.find('<footer>')
if fi > 0:
    body = body[:fi]

body = body.strip()

# 检查 h1
h1 = re.search(r'<h1[^>]*>(.*?)</h1>', body, re.DOTALL)
print(f'H1 found: {"YES -> " + h1.group(1).strip() if h1 else "NO"}')

# 保存
with open(dst_src, 'w', encoding='utf-8') as f:
    f.write(body)
print(f'Saved {len(body)} bytes to .src/visa-guide.html')
