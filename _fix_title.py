import json, os
mf = r'E:\项目库\china-travel-website\articles\.manifest.json'
if os.path.isfile(mf):
    with open(mf, 'r', encoding='utf-8') as f:
        m = json.load(f)
    if 'visa-guide.html' in m:
        m['visa-guide.html']['title'] = 'China Tourist Visa (L-Visa)'
    with open(mf, 'w', encoding='utf-8') as f:
        json.dump(m, f, ensure_ascii=False, indent=2)
    print('Fixed manifest title')
else:
    print('No manifest yet')
