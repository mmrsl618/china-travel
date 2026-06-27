# -*- coding: utf-8 -*-
"""regenerate_articles.py — 批量重新套壳所有已上线文章（导航结构调整后）

运行方式：cd E:\项目库\china-travel-website && python regenerate_articles.py
"""

import os, sys, json, re

SITE_DIR = r'E:\项目库\china-travel-website'
ARTICLES_DIR = os.path.join(SITE_DIR, 'articles')
MANIFEST_PATH = os.path.join(ARTICLES_DIR, '.manifest.json')

# section 迁移映射
SECTION_REMAP = {
    'payment': 'before-you-go',
    'transportation': 'getting-around',
    'stay': 'getting-around',
}

def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def read_file(rel_path):
    try:
        with open(os.path.join(SITE_DIR, rel_path), 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None

def write_file(rel_path, content):
    try:
        abspath = os.path.join(SITE_DIR, rel_path)
        with open(abspath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f'  ERROR writing {rel_path}: {e}')
        return False

def apply_master_template(content, title, desc, section='', sub_category=''):
    """从 admin_server.py 复制过来的套壳逻辑（独立版）"""
    tpl_path = os.path.join(SITE_DIR, 'templates', 'article-master.html')
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            tpl = f.read()
    except:
        return content

    GUIDE_SECTIONS = {
        'before-you-go': 'Before You Go',
        'getting-around': 'Getting Around',
        'explore': 'Explore China',
    }

    SUBCAT_MAP = {
        'before-you-go': [],
        'getting-around': [],
        'explore': [
            ('cities', 'City Guides'),
            ('itineraries', 'Itineraries'),
            ('food', 'Food & Dining'),
        ],
    }

    nav_map = [
        ('before-you-go', 'Before You Go', '../../guides/before-you-go.html'),
        ('getting-around', 'Getting Around', '../../guides/getting-around.html'),
        ('explore', 'Explore China', '../../guides/explore.html'),
    ]

    nav_html = ''
    for k, lbl, url in nav_map:
        if k == section:
            nav_html += f'      <span class="crumb current">{lbl}</span>\n'
        else:
            nav_html += f'      <a href="{url}">{lbl}</a>\n'

    section_label = GUIDE_SECTIONS.get(section, section)
    section_url = f'../../guides/{section}.html'

    sub_label = ''
    if sub_category:
        for k, lbl in SUBCAT_MAP.get(section, []):
            if k == sub_category:
                sub_label = lbl
                break

    last_crumb = sub_label if sub_label else title
    breadcrumb = (f'<div class="breadcrumb" style="font-size:0.85rem;color:#666;'
                  f'padding:0 0 1rem;margin:0 0 1rem;border-bottom:1px solid #eee;">\n'
                  f'<a href="../../index.html">Home</a>\n'
                  f'<span class="sep"> › </span>\n'
                  f'<a href="{section_url}">{html_escape(section_label)}</a>\n'
                  f'<span class="sep"> › </span>\n'
                  f'<span>{html_escape(last_crumb)}</span>\n</div>\n')

    content = re.sub(r'(\.\./)+images/', '../../images/', content)
    content = re.sub(r'\s*<div class="breadcrumb".*?</div>\s*', '', content, flags=re.DOTALL)

    tpl = tpl.replace('__CONTENT__', breadcrumb + content)
    tpl = tpl.replace('__TITLE__', title)
    tpl = tpl.replace('__DESCRIPTION__', desc)
    tpl = tpl.replace('__NAV__', nav_html)
    return tpl

def extract_title(content):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    return m.group(1).strip() if m else ''

def strip_title(content):
    return re.sub(r'\s*<h1[^>]*>.*?</h1>\s*', '', content, count=1, flags=re.DOTALL)

def main():
    manifest = json.loads(read_file('articles/.manifest.json'))
    if not manifest:
        print('ERROR: 无法读取 manifest')
        return

    updates = []
    regenerated = 0
    sections_changed = 0

    for fname, info in manifest.items():
        if info.get('status') != 'online':
            continue

        old_section = info.get('section', '')
        new_section = SECTION_REMAP.get(old_section, old_section)
        old_subcategory = info.get('sub_category', '')

        # 非 explore 板块清空 sub_category（因为不再分子分类）
        new_subcategory = old_subcategory if new_section == 'explore' else ''

        zh_path = f'articles/{fname}/zh.html'
        zh_content = read_file(zh_path)
        if not zh_content:
            print(f'  SKIP {fname}: 找不到 zh.html')
            continue

        title = extract_title(zh_content)
        body = strip_title(zh_content)
        desc = info.get('title', title)

        en_content = apply_master_template(body, title, desc, new_section, new_subcategory)

        en_path = f'articles/{fname}/en.html'
        if write_file(en_path, en_content):
            regenerated += 1
            if old_section != new_section or old_subcategory != new_subcategory:
                sections_changed += 1
                info['section'] = new_section
                if new_subcategory != old_subcategory:
                    info['sub_category'] = new_subcategory
                print(f'  OK  {fname}: {old_section} → {new_section}')
            else:
                print(f'  OK  {fname}: {new_section} (no change)')

    # 保存更新后的 manifest
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f'\nDone. Regenerated: {regenerated}, Sections changed: {sections_changed}')

if __name__ == '__main__':
    main()
