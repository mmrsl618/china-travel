"""发布文章后，从 manifest.json 生成 URL 映射并上传到 Cloudflare KV。
运行方式: python gen_url_map.py
"""
import json, subprocess, sys, os

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
KV_NS_ID = 'abbf3a722fd34e4d9f38c1c59042abd2'

# wrangler full path (may be .cmd on Windows)
WRANGLER = r'D:\Qwenpaw\nodejs\wrangler.cmd'

SECTION_TO_GUIDE = {
    'before-you-go': 'before-you-go',
    'payment': 'payment',
    'transportation': 'transportation',
    'stay': 'stay',
    'explore': 'explore',
}

def main():
    with open(f'{SITE_DIR}/articles/.manifest.json', encoding='utf-8') as f:
        manifest = json.load(f)

    url_map = {}
    for key, info in manifest.items():
        if info.get('status') != 'online':
            continue
        section = info.get('section', 'before-you-go')
        guide_file = SECTION_TO_GUIDE.get(section, 'before-you-go')
        url_map[key] = {
            'guide_url': f'guides/{guide_file}.html#tab-{key}',
            'title': info.get('title', key.replace('-', ' ').title())
        }

    # Write local file
    output = f'{SITE_DIR}/url_map.json'
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(url_map, f, indent=2, ensure_ascii=False)

    print(f'OK: {len(url_map)} articles mapped')

    # Upload to KV
    result = subprocess.run([
        WRANGLER, 'kv', 'key', 'put',
        '--namespace-id', KV_NS_ID,
        'url_map',
        '--path', output,
        '--remote'
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')

    if result.returncode == 0:
        print('OK: uploaded to KV')
    else:
        print('ERR: KV upload failed:', result.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
