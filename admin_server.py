# -*- coding: utf-8 -*-
"""admin_server.py — 管理后台
端口 8082
左侧导航 + 右侧内容
三界面：中文待审 / 英文待审 / 已上架（细分5板块）
"""
import os, sys, re, shutil, subprocess, urllib.parse, http.server, socketserver

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

SITE_DIR = r'E:\项目库\china-travel-website'
PORT = 8082
GIT_EXE = r'C:\Program Files\Git\bin\git.exe'

def read_file(path):
    try:
        with open(os.path.join(SITE_DIR, path), 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

def write_file(path, content):
    try:
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
    if not os.path.isdir(full): return []
    items = sorted(os.listdir(full), key=lambda x: os.path.getmtime(os.path.join(full, x)), reverse=True)
    return [{'name': f, 'path': os.path.join(rel_dir, f).replace('\\', '/')} for f in items if f.endswith(ext)]

# ===== CSS =====

CSS = '''
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
/* 已上架 - 折叠样式 */
.nav-parent { display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.nav-parent .arrow { font-size: 0.65rem; transition: transform 0.15s; margin-left: auto; opacity: 0.5; }
.nav-parent.open .arrow { transform: rotate(90deg); }
.nav-child { display: none; padding: 0; }
.nav-child.show { display: block; }
.nav-child .nav-item { padding: 0.3rem 1rem 0.3rem 2rem; font-size: 0.76rem; border-left: 3px solid transparent; }
.nav-child .nav-item.active { color: #FFDE00; border-left-color: #FFDE00; background: transparent; }
.nav-child .nav-item:hover { color: #fff; }

/* 右侧内容 */
.content { flex: 1; min-width: 0; padding: 1.5rem 2rem; max-width: 1000px; }
.content-wide { display: flex; flex-direction: column; overflow: hidden; max-height: 100vh; }
.content-wide .card { flex: 1; min-height: 0; }
.card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden; margin-bottom: 1rem; }
.card-title { font-size: 0.88rem; font-weight: 700; color: #1a1a2e; padding: 0.9rem 1.2rem;
              border-bottom: 1px solid #f0f0f0; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 1.2rem;
       border-bottom: 1px solid #f5f5f5; gap: 0.5rem; }
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

/* 编辑页布局 */
.edit-card { display: flex; flex-direction: column; min-height: 0; }
.edit-card > form { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 0 1.2rem 1.2rem; }
.edit-actions { flex-shrink: 0; display: flex; gap: 0.5rem; padding: 0.8rem 0 0; }
.editor-area { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; }
.editor-inner { max-width: 700px; margin: 0 auto; font-size: 18px; line-height: 1.6; }
.editor-inner:focus { outline: none; }

/* 子分类 tab 导航 */
.sub-tabs { display: flex; gap: 0; border-bottom: 1px solid #e0e0e0; background: #fff;
            border-radius: 8px 8px 0 0; overflow-x: auto; }
.sub-tab { padding: 0.5rem 1rem; font-size: 0.8rem; cursor: pointer; border: none;
            background: transparent; color: #888; font-weight: 500; white-space: nowrap;
            border-bottom: 2px solid transparent; transition: all 0.12s; }
.sub-tab:hover { color: #333; background: #fafbfc; }
.sub-tab.active { color: #1a1a2e; border-bottom-color: #DE2910; font-weight: 600; background: #fff; }
.sub-pane { display: none; padding: 0; }
.sub-pane.active { display: block; }
'''

# ===== 页面渲染 =====

def sidebar_nav(current):
    """生成左侧导航 HTML。current: 'zh','en','done-xxx'"""
    html = ''
    html += f'<a class="nav-item {"active" if current=="zh" else ""}" href="/admin/zh">📄 中文待审</a>'
    html += f'<a class="nav-item {"active" if current=="en" else ""}" href="/admin/en">📝 英文待审</a>'
    # 已上架：折叠
    is_done = current.startswith('done')
    guide_sections = [
        ('before-you-go', 'Before You Go'),
        ('payment', 'Payment'),
        ('transportation', 'Transportation'),
        ('stay', 'Where to Stay'),
        ('explore', 'Explore China'),
    ]
    html += f'''<div class="nav-item nav-parent{" open" if is_done else ""}" onclick="toggleDone()">
✅ 已上架 <span class="arrow">▸</span></div>'''
    ch = ''
    for key, label in guide_sections:
        act = 'active' if current == f'done-{key}' else ''
        ch += f'<a class="nav-item {act}" href="/admin/done/{key}">{label}</a>'
    html += f'<div class="nav-child{" show" if is_done else ""}" id="done-child">{ch}</div>'
    return html

def render_page(title, body_html, current='zh', msg=None, wide=False):
    m = f'<div class="msg msg-{msg[0]}">{msg[1]}</div>' if msg else ''
    nav = sidebar_nav(current)
    content_cls = 'content content-wide' if wide else 'content'
    js = '''<script>
function toggleDone(){
  var c=document.getElementById('done-child');
  var p=c.previousElementSibling;
  c.classList.toggle('show');
  p.classList.toggle('open');
}</script>'''
    return f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title><style>{CSS}</style></head><body>
<div class="sidebar"><div class="sidebar-header">📋 管理后台</div><div class="sidebar-nav">{nav}</div></div>
<div class="{content_cls}">{m}{body_html}</div>{js}</body></html>'''

def render_list_page(items, label, icon, has_done=False, done_url='', show_preview=True, base_from='/admin'):
    if not items:
        return f'<div class="card"><div class="card-title">{icon} {label}</div><div class="empty">暂无待审文章</div></div>'
    rows = ''
    for it in items:
        preview = f'http://localhost:8080/{it["path"]}'
        done_btn = ''
        if has_done:
            done_btn = f'<form method="POST" action="{done_url}" style="display:inline" onsubmit="return confirm(\'确认完成？\')"><input type="hidden" name="path" value="{it["path"]}"><button type="submit" class="btn btn-done">✓ 完成</button></form>'
        preview_btn = f'<a class="btn btn-preview" href="{preview}" target="_blank">👁 预览</a>' if show_preview else ''
        rows += f'''<div class="row">
<div class="info"><div class="name">{it["name"]}</div><div class="path">{it["path"]}</div></div>
<div class="actions">
<a class="btn btn-edit" href="/admin/edit?path={it["path"]}&from={base_from}">✎ 编辑</a>
{preview_btn}
{done_btn}
</div></div>'''
    return f'<div class="card"><div class="card-title">{icon} {label}</div>{rows}</div>'

def render_edit_page(path, return_to='/admin', msg=None):
    content, err = read_file(path)
    if err:
        return None, err
    is_md = path.endswith('.md')
    body_html = content if is_md else ''
    if not is_md:
        m = re.search(r'<div class="article-page-inner">(.*?)</div>\s*</div>\s*(?:<footer|<div class="article-page)', content, re.DOTALL)
        body_html = m.group(1) if m else (content[content.find('<body>')+6:content.find('</body>')] if '<body>' in content else content)

    msg_html = f'<div class="msg msg-{msg[0]}">{msg[1]}</div>' if msg else ''
    save_btn_label = '💾 保存'
    btn_style = 'padding:0.4rem 1.5rem;font-size:0.85rem;'

    if is_md:
        editor = f'''<textarea name="raw_content" style="width:100%;flex:1;border:1px solid #e0e0e0;padding:1rem;font-size:0.86rem;font-family:inherit;resize:none;outline:none;border-radius:4px;background:#fafafa;" spellcheck="false">{html_escape(content)}</textarea>'''
        page = f'''<div class="card edit-card">
<div style="padding:0.8rem 1.2rem;border-bottom:1px solid #eee;font-weight:600;font-size:0.85rem;flex-shrink:0;">{path}</div>
<form method="POST" action="/admin/save" style="flex:1;display:flex;flex-direction:column;min-height:0;padding:1.2rem;">
<input type="hidden" name="path" value="{html_escape(path)}">
<input type="hidden" name="return_to" value="{return_to}">
{editor}
<div class="edit-actions">
  <button type="submit" class="btn btn-done" style="{btn_style}">{save_btn_label}</button>
  <a class="btn btn-edit" href="{return_to}" style="padding:0.4rem 1rem;background:#f0f0f0;color:#555;">← 返回</a>
</div>
</form></div>'''
    else:
        editor = f'''<div class="editor-area" style="flex:1;overflow-y:auto;padding:1rem;">
  <div class="editor-inner">
    <div id="editable-content" contenteditable="true" style="outline:none;">{body_html}</div>
  </div>
</div>'''
        page = f'''<div class="card edit-card">
<div style="padding:0.8rem 1.2rem;border-bottom:1px solid #eee;font-weight:600;font-size:0.85rem;flex-shrink:0;">{path}</div>
<form method="POST" action="/admin/save" id="edit-form" style="flex:1;display:flex;flex-direction:column;min-height:0;padding:1.2rem;">
<input type="hidden" name="path" value="{path}">
<input type="hidden" name="content" id="hdn-content">
<input type="hidden" name="return_to" value="{return_to}">
{editor}
<div class="edit-actions">
  <button type="submit" class="btn btn-done" style="{btn_style}">{save_btn_label}</button>
  <a class="btn btn-edit" href="{return_to}" style="padding:0.4rem 1rem;background:#f0f0f0;color:#555;">← 返回</a>
</div>
</form></div>'''

    js = '''<script>
var f=document.getElementById('edit-form');
if(f) f.addEventListener('submit',function(){
  var e=document.getElementById('editable-content');
  if(e) document.getElementById('hdn-content').value=e.innerHTML;});</script>'''

    cur = 'zh'
    if 'articles/en/' in path: cur = 'en'
    elif 'articles/' in path: cur = 'done-before-you-go'
    return render_page('编辑', msg_html + page + js, cur, wide=True), None

def html_escape(s):
    return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

# ===== 已上架：解析网站本地文件 =====

def render_done_page(section_key, sync_msg=None):
    """渲染已上架板块。section_key 必填，只显示该板块内容"""
    sync_html = ''
    if sync_msg:
        sync_html = f'<div class="sync-status">{sync_msg}</div>'
    sync_btn = f'''<form method="POST" action="/admin/sync" style="display:inline" onsubmit="showSyncStatus()">
<button type="submit" class="btn btn-sync" id="sync-btn">🔄 同步到线上</button>
</form>'''
    sync_js = '''<script>
function showSyncStatus(){
  var b=document.getElementById('sync-btn');
  b.textContent='⏳ 同步中...';
  b.disabled=true;
  b.style.opacity='0.6';
}
</script>'''
    guide_map = [
        ('before-you-go', 'Before You Go', 'before-you-go.html'),
        ('payment', 'Payment', 'payment.html'),
        ('transportation', 'Transportation', 'transportation.html'),
        ('stay', 'Where to Stay', 'stay.html'),
        ('explore', 'Explore China', 'explore.html'),
    ]
    match = [g for g in guide_map if g[0] == section_key]
    if not match:
        return '<div class="card"><div class="card-title">📘 未找到</div><div class="empty">未知板块</div></div>'
    key, label, page_file = match[0]
    fpath = os.path.join(SITE_DIR, 'guides', page_file)
    if not os.path.isfile(fpath):
        return f'<div class="card"><div class="card-title">📘 {label}</div><div class="empty">暂无文章</div></div>'
    with open(fpath, 'r', encoding='utf-8') as f:
        html = f.read()
    tabs = []
    for idx, tm in enumerate(re.finditer(r'data-tab="([^"]+)"[^>]*>\s*([^<]+?)\s*<', html)):
        tab_id = tm.group(1)
        tab_name = tm.group(2).strip()
        tc = re.search(r'<div class="tab-content[^"]*"\s+id="tab-' + re.escape(tab_id) + r'">(.*?)(?:</div>\s*<div class="tab-content|\s*</div>\s*</div>|\s*</div>\s*$)', html, re.DOTALL)
        tab_html = tc.group(1) if tc else ''
        articles = []
        for am in re.finditer(r'<a href="\.\./articles/([^"]+)"[^>]*class="article-link"[^>]*>([^<]+)</a>', tab_html):
            articles.append({'title': am.group(2).strip(), 'file': am.group(1)})
        tabs.append({'id': tab_id, 'name': tab_name, 'articles': articles})
    
    if not tabs:
        return f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;"><div></div>{sync_btn}</div>{sync_html}<div class="card"><div class="empty">暂无分类</div></div>{sync_js}'
    
    # 子分类 tab 导航
    tab_bar = '<div class="sub-tabs">'
    for idx, t in enumerate(tabs):
        act = 'active' if idx == 0 else ''
        tab_bar += f'<button class="sub-tab {act}" onclick="switchSubTab({idx},this)">{t["name"]}</button>'
    tab_bar += '</div>'
    
    # tab 内容面板
    panes = ''
    for idx, t in enumerate(tabs):
        act = 'active' if idx == 0 else ''
        panes += f'<div class="sub-pane {act}" id="sub-pane-{idx}">'
        if t['articles']:
            for a in t['articles']:
                online_url = f'https://mmrsl618.github.io/china-travel/articles/{a["file"]}'
                panes += f'''<div class="row">
<div class="info"><div class="name">{a["title"]}</div><div class="path">articles/{a["file"]}</div></div>
<div class="actions">
<a class="btn btn-edit" href="/admin/edit?path=articles/{a["file"]}&from=/admin/done/{section_key}">✎ 编辑</a>
<a class="btn btn-preview" href="{online_url}" target="_blank">👁 预览</a>
</div></div>'''
        else:
            panes += '<div class="empty">暂无文章</div>'
        panes += '</div>'
    
    tab_js = '''<script>
function switchSubTab(idx,btn){
  document.querySelectorAll('.sub-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.sub-pane').forEach(p=>p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('sub-pane-'+idx).classList.add('active');
}</script>'''
    return f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;"><div></div>{sync_btn}</div>{sync_html}<div class="card">{tab_bar}{panes}</div>{tab_js}{sync_js}'

# ===== HTTP Handler =====

class AdminHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        p = parsed.path.rstrip('/')

        if p == '/admin' or p == '/admin/zh':
            items = list_dir('reviews')
            body = render_list_page(items, '中文待审稿', '📄', has_done=True, done_url='/admin/zh/done', show_preview=False, base_from='/admin/zh')
            html = render_page('中文待审', body, 'zh')
        elif p == '/admin/en':
            items = list_dir('articles/en', ('.html',))
            body = render_list_page(items, '英文待审稿', '📝', has_done=True, done_url='/admin/en/done', base_from='/admin/en')
            html = render_page('英文待审', body, 'en')
        elif p == '/admin/done':
            # 跳转到第一个板块
            self.send_response(302)
            self.send_header('Location', '/admin/done/before-you-go')
            self.end_headers()
            return
        elif p.startswith('/admin/done/'):
            section = p.split('/')[-1]
            sync_msg = params.get('sync_msg', [None])[0]
            body = render_done_page(section, sync_msg)
            html = render_page(f'已上架 - {section}', body, f'done-{section}')
        elif p == '/admin/edit':
            path = params.get('path', [None])[0]
            return_to = params.get('from', ['/admin'])[0]
            if not path: self.send_redirect(return_to); return
            safe = os.path.normpath(os.path.join(SITE_DIR, path))
            if not safe.startswith(os.path.normpath(SITE_DIR)): self.send_error(403); return
            html, err = render_edit_page(path, return_to=return_to)
            if err:
                body = f'<div class="msg msg-err">{err}</div><a class="btn btn-edit" href="{return_to}">← 返回</a>'
                html = render_page('错误', body, 'zh')
        else:
            super().do_GET(); return

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == '/admin/sync':
            self.send_html(self._do_sync())
            return

        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)
        path = data.get('path', [None])[0]
        if not path: self.send_redirect('/admin'); return
        safe = os.path.normpath(os.path.join(SITE_DIR, path))
        if not safe.startswith(os.path.normpath(SITE_DIR)): self.send_error(403); return

        if parsed.path == '/admin/save':
            nc = data.get('content', [None])[0]
            rc = data.get('raw_content', [None])[0]
            return_to = data.get('return_to', [None])[0] or '/admin'
            if nc is not None:
                orig, err = read_file(path)
                if err:
                    self.send_redirect(f'{return_to}?sync_msg=读取失败:{err}'); return
                    return
                new_file, count = re.subn(
                    r'(<div class="article-page-inner">)(.*?)(</div>\s*</div>\s*(?:<footer|<div class="article-page"))',
                    lambda m: m.group(1) + '\n' + nc + '\n' + m.group(3), orig, count=1, flags=re.DOTALL)
                write_file(path, new_file if count > 0 else nc)
            elif rc is not None:
                write_file(path, rc)
            self.send_response(302)
            self.send_header('Location', return_to)
            self.end_headers()
            return
        elif parsed.path == '/admin/zh/done':
            ok, err = move_file(path, path.replace('reviews/', 'reviews/_done/'))
            self.send_redirect('/admin/zh')
        elif parsed.path == '/admin/en/done':
            ok, err = move_file(path, path.replace('articles/en/', 'articles/en/_done/'))
            self.send_redirect('/admin/en')
        else:
            self.send_error(404)

    def _do_sync(self):
        """执行 Git 同步"""
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
                if out: lines.append(f'$ {" ".join(cmd[-2:])}\n{out}')
                if err and 'git' not in err.lower(): lines.append(f'⚠ {err}')
                if r.returncode != 0:
                    # commit 无变化不算失败
                    # 自动备份标签推送失败不阻断同步
                    if cmd[1] == 'push' and cmd[2] == 'origin' and cmd[3].startswith('auto-'):
                        lines.append(f'⚠ 备份标签推送失败（不影响同步）')
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

    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_redirect(self, url):
        self.send_response(302); self.send_header('Location', url); self.end_headers()

    def log_message(self, format, *args):
        print(f'[admin] {args[0]} {args[1]} {args[2]}')

if __name__ == '__main__':
    os.makedirs(os.path.join(SITE_DIR, 'reviews', '_done'), exist_ok=True)
    os.makedirs(os.path.join(SITE_DIR, 'articles', 'en', '_done'), exist_ok=True)
    server = socketserver.TCPServer(('0.0.0.0', PORT), AdminHandler)
    print(f'✅ 后台启动: http://localhost:{PORT}/admin')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
