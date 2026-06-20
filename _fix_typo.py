import sys
path = r'E:\项目库\china-travel-website\admin_server.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('artricles', 'articles')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed all artricles → articles')
