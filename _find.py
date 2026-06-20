with open(r'E:\项目库\china-travel-website\admin_server.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        lower = line.lower()
        if 'publish' in lower or 'local' in lower or '/done' in lower or 'mark_published' in lower or 'get_published' in lower:
            print(f'{i}: {line.rstrip()[:120]}')
