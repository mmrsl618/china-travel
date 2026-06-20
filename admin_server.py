# -*- coding: utf-8 -*-
"""admin_server.py — 管理后台 v1.1

端口 8082 | ThreadingTCPServer（多线程防阻塞）

工作流：
  中文待审 → 英文待审 → ✓完成套壳 → 已发布（本地预览）→ 🚀上线 → 已上线（GitHub Pages）

导航：
  📄 中文待审 | 📝 英文待审 | 📦 已发布（5板块） | ✅ 已上线（5板块）
"""
import os, sys, re, json, shutil
import subprocess, urllib.parse
import http.server, socketserver

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

# =====================================================================
#  配置
# =====================================================================
SITE_DIR = r'E:\项目库\china-travel-website'
PORT = 8082
GIT_EXE = r'C:\Program Files\Git\bin\git.exe'

GUIDE_MAP = [              # (key, label)
    ('before-you-go',  'Before You Go'),
    ('payment',        'Payment'),
    ('transportation', 'Transportation'),
    ('stay',           'Where to Stay'),
    ('explore',        'Explore China'),
]

GUIDE_FILES = {           # key → guides/ filename
    'before-you-go': 'before-you-go.html',
    'payment': 'payment.html',
    'transportation': 'transportation.html',
    'stay': 'stay.html',
    'explore': 'explore.html',
}

PUBLISH_STATE = os.path.join(SITE_DIR, 'articles', '.publish-state.json')

# =====================================================================
#  文件操作
# =====================================================================
def read_file(path):
    try:
        with open(os.path.join(SITE_DIR, path), 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

def write_file(path, content):
    try:
        os.makedirs(os.path.dirname(os.path.join(SITE_DIR, path)), exist_ok=True)
        with open(os.path.join(SITE_DIR, path), 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except Exception as e:
        return False, str(e)

def move_file(src_rel, dst_rel):
    src = os.path.join(SITE_DIR, src_rel)
    dst = os.path.join(SITE_DIR, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        shutil.move(src, dst)
        return True, None
    except Exception as e:
        return False, str(e)

def list_dir(rel_dir, ext=('.html', '.md')):
    full = os.path.join(SITE_DIR, rel_dir)
    if not os.path.isdir(full):
        return []
    items = sorted(os.listdir(full),
                   key=lambda x: os.path.getmtime(os.path.join(full, x)), reverse=True)
    return [{'name': f, 'path': os.path.join(rel_dir, f).replace(chr(92), '/')}
            for f in items if f.endswith(ext)]

def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# =====================================================================
#  发布状态管理 (.publish-state.json)
# =====================================================================
def get_published_set():
    if not os.path.isfile(PUBLISH_STATE):
        write_file('articles/.publish-state.json', '{"published":[]}')
        return set()
    try:
        with open(PUBLISH_STATE, 'r', encoding='utf-8') as f:
            return set(json.load(f).get('published', []))
    except:
        return set()

def mark_published(fname):
    s = get_published_set()
    s.add(fname)
    with open(PUBLISH_STATE, 'w', encoding='utf-8') as f:
        json.dump({'published': sorted(s)}, f, ensure_ascii=False)

# =====================================================================
#  英文审稿 — 按 guide 分组扫描
# =====================================================================
def list_en_reviews():
    result = {}
    for key, label in GUIDE_MAP:
        d = os.path.join(SITE_DIR, 'articles', 'en', key)
        os.makedirs(d, exist_ok=True)
        items = []
        for f in os.listdir(d):
            if f.endswith('.html') or f.endswith('.md'):
                fp = os.path.join(d, f)
                items.append({
                    'name': f,
                    'path': f'articles/en/{key}/{f}',
                    'mtime': os.path.getmtime(fp),
                })
        items.sort(key=lambda x: x['mtime'], reverse=True)
        result[key] = {'label': label, 'items': items}
    return result

# =====================================================================
#  文章处理（提取 + 套模板）
# =====================================================================
def extract_article_content(full_html):
    """从英文审稿完整 HTML 提取 title / description / 正文（不含 back-link）"""
    title = ''
    desc = ''
    tm = re.search(r'<title>(.*?)</title>', full_html, re.DOTALL)
    if tm:
        title = tm.group(1).strip()
    dm = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', full_html, re.DOTALL)
    if dm:
        desc = dm.group(1).strip()
    body_start = full_html.find('</header>')
    if body_start == -1:
        body_start = full_html.find('<body>')
    if body_start != -1:
        body_start += len('</header>')
        rest = full_html[body_start:]
        footer_pos = rest.find('<footer>')
        content = rest[:footer_pos].strip() if footer_pos != -1 else rest.strip()
    else:
        content = full_html
    # 移除返回链接
    content = re.sub(r'<a\s+[^>]*class="back-link"[^>]*>.*?</a>', '', content, flags=re.DOTALL)
    # 剥离残留旧结构标签
    for tag in ['<div\s+class="article-page">', '<div\s+class="article-page-inner">',
                '</div>\s*<!--\s*/article-page-inner\s*-->', '</div>\s*<!--\s*/article-page\s*-->']:
        content = re.sub(r'\s*' + tag + r'\s*', '', content)
    return title.strip(), desc.strip(), content.strip()

def apply_master_template(content, title, desc):
    tpl_path = os.path.join(SITE_DIR, 'templates', 'article-master.html')
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            tpl = f.read()
    except:
        return content
    return (tpl
            .replace('__TITLE__', title)
            .replace('__DESCRIPTION__', desc)
            .replace('__CONTENT__', content))

# =====================================================================
#  管理后台 CSS（内嵌，单文件免依赖）
# =====================================================================
ADMIN_CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: #eef0f5; color: #222; min-height: 100vh; display: flex; }

/* 左侧导航 */
.sidebar { width: 180px; background: #1a1a2e; color: #fff; display: flex; flex-direction: column;
           flex-shrink: 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.sidebar-header { padding: 1rem 1rem 0.6rem; font-size: 0.85rem; font-weight: 700;
                  letter-spacing: 0.3px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sidebar-nav { padding: 0.4rem 0; flex: 1; }
.nav-item { display: block; padding: 0.4rem 1rem; font-size: 0.8rem; color: rgba(255,255,255,0.45);
            text-decoration: none; transition: all 0.12s; border-left: 3px solid transparent; }
.nav-item:hover { color: #fff; background: rgba(255,255,255,0.04); }
.nav-item.active { color: #FFDE00; background: rgba(255,222,0,0.06); border-left-color: #FFDE00; font-weight: 600; }
.nav-parent { display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.nav-parent .arrow { font-size: 0.65rem; transition: transform 0.15s; margin-left: auto; opacity: 0.5; }
.nav-parent.open .arrow { transform: rotate(90deg); }
.nav-child { display: none; padding: 0; }
.nav-child.show { display: block; }
.nav-child .nav-item { padding: 0.3rem 1rem 0.3rem 2rem; font-size: 0.76rem; border-left: 3px solid transparent; }
.nav-child .nav-item.active { color: #FFDE00; border-left-color: #FFDE00; background: transparent; }
.nav-child .nav-item:hover { color: #fff; }

/* 右侧内容区 */
.content { flex: 1; min-width: 0; padding: 1.5rem 2rem; max-width: 1000px; }
.content-wide { display: flex; flex-direction: column; overflow: hidden; max-height: 100vh; }
.content-wide .card { flex: 1; min-height: 0; }
.card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden; margin-bottom: 1rem; }
.card-title { font-size: 0.88rem; font-weight: 700; color: #1a1a2e; padding: 0.9rem 1.2rem; border-bottom: 1px solid #f0f0f0; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 1.2rem; border-bottom: 1px solid #f5f5f5; gap: 0.5rem; }
.row:last-child { border-bottom: none; }
.row:hover { background: #fafbfc; }
.info { flex: 1; min-width: 0; }
.name { font-size: 0.86rem; color: #222; font-weight: 500; }
.path { font-size: 0.7rem; color: #aaa; margin-top: 0.06rem; }
.actions { display: flex; gap: 0.3rem; flex-shrink: 0; }
.btn { display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.28rem 0.6rem;
       border-radius: 4px; font-size: 0.76rem; text-decoration: none; border: none;
       cursor: pointer; font-weight: 500; transition: all 0.12s; line-height: 1.3; }
.btn-edit { background: #1a1a2e; color: #fff; }
.btn-edit:hover { background: #2a2a4e; }
.btn-preview { background: #DE2910; color: #fff; }
.btn-preview:hover { background: #b8200c; }
.btn-done { background: #16a34a; color: #fff; }
.btn-done:hover { background: #15803d; }
.btn-sync { background: #0366d6; color: #fff; }
.btn-sync:hover { background: #0256b9; }
.sync-status { font-size: 0.78rem; color: #555; padding: 0.4rem 1rem; background: #f6f8fa; border-radius: 4px; margin-top: 0.5rem; white-space: pre-wrap; }
.msg { padding: 0.5rem 1rem; border-radius: 5px; margin-bottom: 0.8rem; font-size: 0.8rem; }
.msg-ok { background: #e6f7ed; color: #1a7a3a; border: 1px solid #b8e6cc; }
.msg-err { background: #fde8e8; color: #b22222; border: 1px solid #f5c6cb; }
.empty { padding: 2rem; text-align: center; color: #bbb; font-size: 0.83rem; }
.sub-tabs { display: flex; gap: 0; border-bottom: 1px solid #e0e0e0; background: #fff; border-radius: 8px 8px 0 0; overflow-x: auto; }
.sub-tab { padding: 0.5rem 1rem; font-size: 0.8rem; cursor: pointer; border: none;
           background: transparent; color: #888; font-weight: 500; white-space: nowrap;
           border-bottom: 2px solid transparent; transition: all 0.12s; }
.sub-tab:hover { color: #333; background: #fafbfc; }
.sub-tab.active { color: #1a1a2e; border-bottom-color: #DE2910; font-weight: 600; background: #fff; }
.sub-pane { display: none; padding: 0; }
.sub-pane.active { display: block; }

/* 编辑页 */
.edit-card { display: flex; flex-direction: column; min-height: 0; }
.edit-card > form { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 0 1.2rem 1.2rem; }
.edit-actions { flex-shrink: 0; display: flex; gap: 0.5rem; padding: 0.8rem 0 0; }
.editor-area { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; }
.editor-inner { max-width: 700px; margin: 0 auto; font-size: 18px; line-height: 1.6; }
.editor-inner:focus { outline: none; }
'''

# =====================================================================
#  HTML 渲染
# =====================================================================
def sidebar_nav(current):
    html = ''
    # 一级导航
    for cur, url, label in [
        ('zh', '/admin/zh', '📄 中文待审'),
        ('en', '/admin/en', '📝 英文待审'),
    ]:
        html += f'<a class="nav-item {"active" if current==cur else ""}" href="{url}">{label}</a>'

    # 已发布（本地预览）
    is_local = current.startswith('local')
    html += f'''<div class="nav-item nav-parent{" open" if is_local else ""}" onclick="toggleLocal()">
📦 已发布 <span class="arrow">▸</span></div>'''
    lch = ''.join(
        f'<a class="nav-item {"active" if current==f"local-{k}" else ""}" href="/admin/local/{k}">{l}</a>'
        for k, l in GUIDE_MAP)
    html += f'<div class="nav-child{" show" if is_local else ""}" id="local-child">{lch}</div>'

    # 已上线（GitHub Pages）
    is_done = current.startswith('done')
    html += f'''<div class="nav-item nav-parent{" open" if is_done else ""}" onclick="toggleDone()">
✅ 已上线 <span class="arrow">▸</span></div>'''
    ch = ''.join(
        f'<a class="nav-item {"active" if current==f"done-{k}" else ""}" href="/admin/done/{k}">{l}</a>'
        for k, l in GUIDE_MAP)
    html += f'<div class="nav-child{" show" if is_done else ""}" id="done-child">{ch}</div>'
    return html

def render_page(title, body_html, current='zh', msg=None, wide=False):
    nav = sidebar_nav(current)
    content_cls = 'content content-wide' if wide else 'content'
    msg_html = ''
    if msg:
        msg_html = f'<div class="msg msg-{msg[0]}">{msg[1]}</div>'
    js = '''<script>
function toggleDone(){
  var c=document.getElementById('done-child');
  c.previousElementSibling.classList.toggle('open');
  c.classList.toggle('show');
}
function toggleLocal(){
  var c=document.getElementById('local-child');
  c.previousElementSibling.classList.toggle('open');
  c.classList.toggle('show');
}</script>'''
    return f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title><style>{ADMIN_CSS}</style></head><body>
<div class="sidebar"><div class="sidebar-header">📋 管理后台</div><div class="sidebar-nav">{nav}</div></div>
<div class="{content_cls}">{msg_html}{body_html}</div>{js}</body></html>'''

def render_list_page(items, label, icon, has_done=False, done_url='', show_preview=True, base_from='/admin'):
    if not items:
        return f'<div class="card"><div class="card-title">{icon} {label}</div><div class="empty">暂无待审文章</div></div>'
    rows = ''
    for it in items:
        preview = f'http://localhost:8080/{it["path"]}'
        done_btn = ''
        if has_done:
            done_btn = (
                f'<form method="POST" action="{done_url}" style="display:inline" '
                f'onsubmit="return confirm(\'确认完成？\')">'
                f'<input type="hidden" name="path" value="{it["path"]}">'
                f'<button type="submit" class="btn btn-done">✓ 完成</button></form>')
        preview_btn = (f'<a class="btn btn-preview" href="{preview}" target="_blank">👁 预览</a>'
                       if show_preview else '')
        rows += f'''<div class="row">
<div class="info"><div class="name">{it["name"]}</div><div class="path">{it["path"]}</div></div>
<div class="actions">
<a class="btn btn-edit" href="/admin/edit?path={it["path"]}&from={base_from}">✎ 编辑</a>
{preview_btn}{done_btn}</div></div>'''
    return f'<div class="card"><div class="card-title">{icon} {label}</div>{rows}</div>'

def render_en_list_page(groups):
    sections = ''
    for key, label in GUIDE_MAP:
        items = groups.get(key, {}).get('items', [])
        if not items:
            rows = '<div class="empty">暂无待审文章</div>'
        else:
            rows = ''
            for it in items:
                preview = f'http://localhost:8080/{it["path"]}'
                rows += f'''<div class="row">
<div class="info"><div class="name">{it["name"]}</div><div class="path">{it["path"]}</div></div>
<div class="actions">
<a class="btn btn-edit" href="/admin/edit?path={it["path"]}&from=/admin/en">✎ 编辑</a>
<a class="btn btn-preview" href="{preview}" target="_blank">👁 预览</a>
<form method="POST" action="/admin/en/done" style="display:inline" onsubmit="return confirm(\'确认完成？将套模板生成正式文章。\')">
<input type="hidden" name="path" value="{it["path"]}">
<button type="submit" class="btn btn-done">✓ 完成</button></form>
</div></div>'''
        sections += (
            f'<div style="padding:0.5rem 1.2rem 0.3rem;font-size:0.78rem;font-weight:600;'
            f'color:#666;background:#f8f9fa;border-bottom:1px solid #eee;">📂 {label}</div>'
            f'{rows}')
    return f'<div class="card"><div class="card-title">📝 英文待审稿</div>{sections}</div>'

# -------------------------------------------------------------------
#  已发布 / 已上线 页面（从 guides/ 解析 + .publish-state 过滤）
# -------------------------------------------------------------------
def render_done_page(section_key, sync_msg=None, mode='online'):
    """已发布（local）或已上线（online）板块。从 guides/*.html 解析文章列表"""
    sync_html = ''
    if sync_msg:
        sync_html = f'<div class="sync-status">{sync_msg}</div>'

    sync_btn = ''
    sync_js = ''
    if mode == 'online':
        sync_btn = '''<form method="POST" action="/admin/sync" style="display:inline" onsubmit="showSyncStatus()">
<button type="submit" class="btn btn-sync" id="sync-btn">🔄 同步到线上</button></form>'''
        sync_js = '''<script>
function showSyncStatus(){
  var b=document.getElementById('sync-btn');
  b.textContent='⏳ 同步中...';
  b.disabled=true; b.style.opacity='0.6';
}</script>'''

    label_map = {k: lbl for k, lbl in GUIDE_MAP}
    if section_key not in label_map:
        return '<div class="card"><div class="card-title">📘 未找到</div><div class="empty">未知板块</div></div>'
    label = label_map[section_key]
    page_file = GUIDE_FILES.get(section_key, f'{section_key}.html')
    fpath = os.path.join(SITE_DIR, 'guides', page_file)
    if not os.path.isfile(fpath):
        return f'<div class="card"><div class="card-title">📘 {label}</div><div class="empty">暂无文章</div></div>'

    with open(fpath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 解析 tab 分类
    tabs = []
    for tm in re.finditer(r'data-tab="([^"]+)"[^>]*>\s*([^<]+?)\s*<', html):
        tab_id = tm.group(1)
        tab_name = tm.group(2).strip()
        tc = re.search(
            r'<div class="tab-content[^"]*"\s+id="tab-' + re.escape(tab_id) + r'">'
            r'(.*?)(?:</div>\s*<div class="tab-content|\s*</div>\s*</div>|\s*</div>\s*$)',
            html, re.DOTALL)
        tab_html = tc.group(1) if tc else ''
        articles = []
        for am in re.finditer(
                r'<a href="\.\./articles/([^"]+)"[^>]*class="article-link"[^>]*>([^<]+)</a>',
                tab_html):
            articles.append({'title': am.group(2).strip(), 'file': am.group(1)})
        tabs.append({'id': tab_id, 'name': tab_name, 'articles': articles})

    if not tabs:
        return (f'<div style="display:flex;align-items:center;justify-content:space-between;'
                f'margin-bottom:0.5rem;"><div></div>{sync_btn}</div>{sync_html}'
                f'<div class="card"><div class="empty">暂无分类</div></div>{sync_js}')

    # tab 导航
    tab_bar = '<div class="sub-tabs">'
    for idx, t in enumerate(tabs):
        act = 'active' if idx == 0 else ''
        tab_bar += f'<button class="sub-tab {act}" onclick="switchSubTab({idx},this)">{t["name"]}</button>'
    tab_bar += '</div>'

    published = get_published_set() if mode in ('local', 'online') else set()
    panes = ''
    for idx, t in enumerate(tabs):
        act = 'active' if idx == 0 else ''
        panes += f'<div class="sub-pane {act}" id="sub-pane-{idx}">'
        filtered = [a for a in t['articles']
                    if (mode == 'local' and a['file'] not in published)
                    or (mode == 'online' and a['file'] in published)
                    or mode not in ('local', 'online')]
        if not filtered:
            panes += '<div class="empty">暂无文章</div>'
        else:
            for a in filtered:
                if mode == 'local':
                    preview_url = f'/articles/{a["file"]}'
                    edit_from = f'/admin/local/{section_key}'
                    publish_btn = (
                        f'<form method="POST" action="/admin/publish" style="display:inline" '
                        f'onsubmit="return confirm(\'确认上线？将 git push 此文章到 GitHub Pages。\')">'
                        f'<input type="hidden" name="file" value="{a["file"]}">'
                        f'<input type="hidden" name="section_key" value="{section_key}">'
                        f'<button type="submit" class="btn btn-done" style="background:#2563eb;">🚀 上线</button></form>')
                    delete_btn = ''
                else:
                    preview_url = f'https://mmrsl618.github.io/china-travel/articles/{a["file"]}'
                    edit_from = f'/admin/done/{section_key}'
                    publish_btn = ''
                    delete_btn = (
                        f'<form method="POST" action="/admin/delete" style="display:inline" '
                        f'onsubmit="return confirm(\'确认彻底删除？将删除本地和线上的文章文件。\')">'
                        f'<input type="hidden" name="file" value="{a["file"]}">'
                        f'<input type="hidden" name="section_key" value="{section_key}">'
                        f'<input type="hidden" name="title" value="{html_escape(a["title"])}">'
                        f'<button type="submit" class="btn btn-edit" style="background:#dc2626;">❌ 删除</button></form>')
                panes += f'''<div class="row">
<div class="info"><div class="name">{a["title"]}</div><div class="path">articles/{a["file"]}</div></div>
<div class="actions">
{publish_btn}{delete_btn}
<a class="btn btn-edit" href="/admin/edit?path=articles/{a["file"]}&from={edit_from}">✎ 编辑</a>
<a class="btn btn-preview" href="{preview_url}" target="_blank">👁 预览</a>
</div></div>'''
        panes += '</div>'

    tab_js = '''<script>
function switchSubTab(idx,btn){
  document.querySelectorAll('.sub-tab').forEach(function(t){t.classList.remove('active');});
  document.querySelectorAll('.sub-pane').forEach(function(p){p.classList.remove('active');});
  btn.classList.add('active');
  document.getElementById('sub-pane-'+idx).classList.add('active');
}</script>'''
    return (f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'margin-bottom:0.5rem;"><div></div>{sync_btn}</div>{sync_html}'
            f'<div class="card">{tab_bar}{panes}</div>{tab_js}{sync_js}')

# -------------------------------------------------------------------
#  编辑页
# -------------------------------------------------------------------
def render_edit_page(path, return_to='/admin', msg=None):
    content, err = read_file(path)
    if err:
        return f'<div class="card"><div class="card-title">✎ 编辑</div><div class="empty">读取失败: {err}</div></div>'
    is_md = path.endswith('.md')
    body_html = content if is_md else ''
    if not is_md:
        m = re.search(r'<div class="article-page-inner">(.*?)</div>\s*</div>(?:\s*<footer|\s*<div class="article-page")',
                      content, re.DOTALL)
        body_html = m.group(1) if m else (
            content[content.find('<body>')+6:content.find('</body>')]
            if '<body>' in content else content)
    msg_html = f'<div class="msg msg-{msg[0]}">{msg[1]}</div>' if msg else ''
    # 判断当前所在的导航位置（为了左侧导航高亮正确）
    if 'articles/en/' in path:
        cur = 'en'
    elif 'articles/' in path:
        # 从路径推断分类
        cur = 'done-before-you-go'
    else:
        cur = 'zh'
    html_content = body_html.replace('<', '&lt;').replace('>', '&gt;')
    md_marker = ' checked' if is_md else ''
    edit_js = '''<script>
var ed=document.getElementById('editable');
var hdn=document.getElementById('hdn-content');
document.querySelector('form').addEventListener('submit',function(e){hdn.value=ed.innerHTML;});
function toggleRaw(){if(this.checked){ed.innerHTML=ed.textContent;}else{ed.textContent=ed.innerHTML;}}
</script>'''
    return render_page(
        '编辑 - 管理后台', f'''<div class="card edit-card"><div class="card-title">✎ 编辑: {path}</div>
<form method="POST" action="/admin/save">
<input type="hidden" name="path" value="{path}">
<input type="hidden" name="return_to" value="{return_to}">
<input type="hidden" name="hdn-content" id="hdn-content" value="">
{msg_html}
<div class="editor-area"><div class="editor-inner" id="editable" contenteditable="true" style="padding:1rem;">{html_content}</div></div>
<label style="font-size:0.76rem;display:flex;align-items:center;gap:0.3rem;margin-top:0.5rem;">
<input type="checkbox" name="raw_content"{md_marker} value="1" onchange="toggleRaw()"> 纯文本（Markdown / 无格式 HTML）</label>
<div class="edit-actions">
<button type="submit" class="btn btn-done">💾 保存</button>
<a class="btn btn-edit" href="{return_to}">← 返回</a>
</div></form></div>
{edit_js}''', cur, wide=True)


# =====================================================================
#  AdminHandler — HTTP 请求处理
# =====================================================================
class AdminHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # 让 SimpleHTTPRequestHandler 以 SITE_DIR 为根目录提供静态文件
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    # ---- GET ----
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 管理后台页面
        if path in ('/admin', '/admin/'):
            body = render_list_page([], '中文待审', '📄', base_from='/admin')
            self.send_html(render_page('管理后台', body))
            return
        if path == '/admin/zh':
            items = list_dir('reviews')
            items = [it for it in items if not it['name'].startswith('_') and not it['path'].startswith('reviews/_done/')]
            body = render_list_page(items, '中文待审稿', '📄', has_done=True,
                                    done_url='/admin/zh/done', base_from='/admin/zh')
            self.send_html(render_page('中文待审', body, 'zh'))
            return
        if path == '/admin/en':
            groups = list_en_reviews()
            body = render_en_list_page(groups)
            self.send_html(render_page('英文待审', body, 'en'))
            return

        # 已上线 / 已发布 板块
        m = re.match(r'/admin/(done|local)/([\w-]+)/?$', path)
        if m:
            mode = 'online' if m.group(1) == 'done' else 'local'
            section = m.group(2)
            qs = urllib.parse.parse_qs(parsed.query)
            sync_msg = qs.get('sync_msg', [None])[0]
            body = render_done_page(section, sync_msg, mode)
            nav_current = f'{m.group(1)}-{section}'
            title = '已上线' if mode == 'online' else '已发布'
            self.send_html(render_page(f'{title} - {section}', body, nav_current))
            return

        # 编辑页
        if path.startswith('/admin/edit'):
            qs = urllib.parse.parse_qs(parsed.query)
            ep = qs.get('path', [None])[0]
            return_to = qs.get('from', ['/admin'])[0]
            if not ep:
                self.send_redirect('/admin')
                return
            body = render_edit_page(ep, return_to)
            self.send_html(body)
            return

        # 非 admin 路径 → 静态文件（交给 SimpleHTTPRequestHandler）
        return super().do_GET()

    # ---- POST ----
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 先解析 body（所有 POST 都需要 data）
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)

        if path == '/admin/publish':
            fname = data.get('file', [None])[0]
            section_key = data.get('section_key', [None])[0]
            if not fname or not section_key:
                self.send_redirect(f'/admin/local/{section_key or "before-you-go"}?msg=参数错误')
                return
            safe_fname = os.path.basename(fname)
            article_rel = f'articles/{safe_fname}'
            article_abs = os.path.join(SITE_DIR, article_rel)
            if not os.path.isfile(article_abs):
                self.send_redirect(f'/admin/local/{section_key}?msg=文件不存在:{safe_fname}')
                return
            ok, err = self._do_publish(article_rel, safe_fname, section_key)
            if not ok:
                self.send_redirect(f'/admin/local/{section_key}?sync_msg=上线失败:{err}')
                return
            mark_published(safe_fname)
            self.send_redirect(f'/admin/local/{section_key}?sync_msg=上线成功:{safe_fname}')
            return

        if path == '/admin/delete':
            fname = data.get('file', [None])[0]
            section_key = data.get('section_key', [None])[0]
            if not fname or not section_key:
                self.send_redirect('/admin/done/before-you-go?sync_msg=参数错误')
                return
            safe_fname = os.path.basename(fname)
            ok, err = self._do_delete(safe_fname, section_key)
            if not ok:
                self.send_redirect(f'/admin/done/{section_key}?sync_msg=删除失败:{err}')
                return
            self.send_redirect(f'/admin/done/{section_key}?sync_msg=已删除:{safe_fname}')
            return

        if path == '/admin/sync':
            self.send_html(self._do_sync())
            return

        # 以下路由需要 path 参数
        ep = data.get('path', [None])[0]
        if not ep:
            self.send_redirect('/admin')
            return
        safe = os.path.normpath(os.path.join(SITE_DIR, ep))
        if not safe.startswith(os.path.normpath(SITE_DIR)):
            self.send_error(403)
            return

        if path == '/admin/save':
            nc = data.get('content', [None])[0]
            rc = data.get('raw_content', [None])[0]
            return_to = data.get('return_to', [None])[0] or '/admin'
            if nc is not None:
                orig, err = read_file(ep)
                if err:
                    self.send_redirect(f'{return_to}?sync_msg=读取失败:{err}')
                    return
                new_file, count = re.subn(
                    r'(<div class="article-page-inner">)(.*?)(</div>\s*</div>\s*(?:<footer|<div class="article-page"))',
                    lambda m: m.group(1) + '\n' + nc + '\n' + m.group(3),
                    orig, count=1, flags=re.DOTALL)
                write_file(ep, new_file if count > 0 else nc)
            elif rc is not None:
                write_file(ep, rc)
            self.send_response(302)
            self.send_header('Location', return_to)
            self.end_headers()
            return

        if path == '/admin/zh/done':
            ok, err = move_file(ep, ep.replace('reviews/', 'reviews/_done/'))
            self.send_redirect('/admin/zh')
            return

        if path == '/admin/en/done':
            content, err = read_file(ep)
            if err:
                self.send_redirect('/admin/en?sync_msg=读取失败:' + err)
                return
            # 提取内容
            title, desc, body_content = extract_article_content(content)
            if not title:
                title = 'China Travel Guide'
            # 套母版
            final_html = apply_master_template(body_content, title, desc)
            # 保存到 articles/ （文件名取自源文件名，去掉新旧前缀和审核后缀）
            fname = os.path.basename(ep)
            for prefix in ['en-', 'zh-']:
                if fname.startswith(prefix):
                    fname = fname[len(prefix):]
                    break
            # 去掉审核后缀
            fname = re.sub(r'(-review|-审核|-审稿|_review|_审核)\.(html|md)$', r'.\2', fname)
            dest = f'articles/{fname}'
            ok, err = write_file(dest, final_html)
            # 移动源文件到 _done/
            done_path = ep.replace('articles/en/', 'articles/en/').rsplit('/', 1)
            if len(done_path) > 1:
                guide_dir = done_path[0]
                done_dir = os.path.join(guide_dir, '_done')
                dst = os.path.join(SITE_DIR, done_dir, done_path[1])
                os.makedirs(done_dir, exist_ok=True)
                try:
                    shutil.move(os.path.join(SITE_DIR, ep), dst)
                except:
                    pass
            self.send_redirect(f'/admin/en?sync_msg={fname} 完成，已存入 articles/')
            return

        self.send_redirect('/admin')

    # ---- 内部方法 ----
    def _do_sync(self):
        now = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M")
        tag_name = f"auto-{now}"
        cmds = [
            [GIT_EXE, 'tag', '-f', tag_name, '-m', f'Auto backup before admin sync at {now}'],
            [GIT_EXE, 'push', 'origin', tag_name],
            [GIT_EXE, 'add', 'articles/', 'guides/', 'images/', 'reviews/', 'admin_server.py'],
            [GIT_EXE, 'commit', '-m', f'admin: sync {now}'],
            [GIT_EXE, 'pull', '--rebase', 'origin', 'main'],
            [GIT_EXE, 'push', 'origin', 'main'],
        ]
        lines = []
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=SITE_DIR)
                out = (r.stdout or '').strip()
                err = (r.stderr or '').strip()
                if out:
                    lines.append(f'$ {" ".join(cmd[-2:])}\n{out}')
                if err and 'git' not in err.lower():
                    lines.append(f'⚠ {err}')
                if r.returncode != 0:
                    if cmd[1] == 'push' and cmd[2] == 'origin' and cmd[3].startswith('auto-'):
                        lines.append('⚠ 备份标签推送失败（不影响同步）')
                    elif 'nothing to commit' in (r.stdout or '') or 'nothing to commit' in (r.stderr or ''):
                        lines.append('→ 无新改动，跳过')
                    elif 'Already up to date' in (r.stdout or '') or 'Already up to date' in (r.stderr or ''):
                        lines.append('→ 已是最新')
                    else:
                        lines.append(f'❌ 失败 (code {r.returncode})')
                        break
            except subprocess.TimeoutExpired:
                lines.append('⏰ 超时')
                break
            except Exception as e:
                lines.append(f'❌ 错误: {e}')
                break
        msg = '\n'.join(lines)
        section = self.path.split('/')[-1] if self.path.startswith('/admin/done/') else 'before-you-go'
        body = render_done_page(section, msg)
        return render_page('已上架 - 同步结果', body, f'done-{section}')

    def _do_publish(self, article_rel, article_name, section_key=''):
        """git push 单篇文章 + 对应 guides 列表页到 GitHub Pages"""
        guide_file = GUIDE_FILES.get(section_key, '')
        cmds = [
            [GIT_EXE, 'add', article_rel],
        ]
        if guide_file:
            cmds[0].append('guides/' + guide_file)
        cmds.extend([
            [GIT_EXE, 'commit', '-m', f'publish: {article_name}'],
            [GIT_EXE, 'pull', '--rebase', 'origin', 'main'],
            [GIT_EXE, 'push', 'origin', 'main'],
        ])
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=SITE_DIR)
                if r.returncode != 0:
                    stderr = (r.stderr or '').strip()
                    stdout = (r.stdout or '').strip()
                    if 'nothing to commit' in stdout or 'nothing to commit' in stderr:
                        return True, '无新改动'
                    if 'Already up to date' in stdout or 'Already up to date' in stderr:
                        continue
                    return False, f'git 失败 (code {r.returncode}): {stderr or stdout}'
            except subprocess.TimeoutExpired:
                return False, '超时'
            except Exception as e:
                return False, str(e)
        return True, ''

    def _do_delete(self, fname, section_key):
        """删除文章：本地 git rm + 线上 git push + 去链接 + 取消标记"""
        guide_file = GUIDE_FILES.get(section_key, '')
        # 1. 从 guides 页面移除链接
        if guide_file:
            gpath = os.path.join(SITE_DIR, 'guides', guide_file)
            if os.path.isfile(gpath):
                with open(gpath, 'r', encoding='utf-8') as f:
                    ghtml = f.read()
                new_html = re.sub(
                    r'\s*<a\s+href="\.\./articles/' + re.escape(fname) + r'"[^>]*class="article-link"[^>]*>.*?</a>\s*',
                    '', ghtml, flags=re.DOTALL)
                if new_html != ghtml:
                    with open(gpath, 'w', encoding='utf-8') as f:
                        f.write(new_html)

        # 2. git rm 文章 + git add guides
        cmds = [
            [GIT_EXE, 'rm', f'articles/{fname}'],
        ]
        if guide_file:
            cmds.append([GIT_EXE, 'add', f'guides/{guide_file}'])
        cmds.extend([
            [GIT_EXE, 'commit', '-m', f'delete: {fname}'],
            [GIT_EXE, 'pull', '--rebase', 'origin', 'main'],
            [GIT_EXE, 'push', 'origin', 'main'],
        ])
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=SITE_DIR)
                if r.returncode != 0:
                    stderr = (r.stderr or '').strip()
                    stdout = (r.stdout or '').strip()
                    if 'nothing to commit' in stdout or 'nothing to commit' in stderr:
                        return True, '无新改动'
                    if 'Already up to date' in stdout or 'Already up to date' in stderr:
                        continue
                    return False, f'git 失败 (code {r.returncode}): {stderr or stdout}'
            except subprocess.TimeoutExpired:
                return False, '超时'
            except Exception as e:
                return False, str(e)

        # 3. 撤销上线标记
        s = get_published_set()
        s.discard(fname)
        with open(PUBLISH_STATE, 'w', encoding='utf-8') as f:
            json.dump({'published': sorted(s)}, f, ensure_ascii=False)
        return True, ''

    # ---- HTTP 工具方法 ----
    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_redirect(self, url):
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 安静模式，不打印请求日志


# =====================================================================
#  启动入口（仅在直接运行时生效）
# =====================================================================
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--generate':
        # 生成模式：输出 admin_server.py
        output_path = os.path.join(os.path.dirname(__file__), 'admin_server.py')
        # 读取自身源码
        with open(__file__, 'r', encoding='utf-8') as f:
            src = f.read()
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(src)
        print(f'✅ 已生成: {output_path}')
        sys.exit(0)

    # 正常启动服务器
    os.makedirs(os.path.join(SITE_DIR, 'reviews', '_done'), exist_ok=True)
    for key, label in GUIDE_MAP:
        os.makedirs(os.path.join(SITE_DIR, 'articles', 'en', key, '_done'), exist_ok=True)

    if not os.path.isfile(PUBLISH_STATE):
        mark_published('visa-guide.html')

    server = socketserver.ThreadingTCPServer(('0.0.0.0', PORT), AdminHandler)
    server.allow_reuse_address = True
    print(f'✅ 后台启动: http://localhost:{PORT}/admin')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


