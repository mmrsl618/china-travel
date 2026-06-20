# -*- coding: utf-8 -*-
"""admin_server.py — 管理后台 v2（精简版）

端口 8082 | ThreadingTCPServer

工作流：
  编辑 → 保存 → 发布上线（套壳 + git push）
  已上线文章 → 编辑 → 保存 → 重新发布上线

导航：
  📂 文章列表 | 🚀 全部同步
"""
import os, sys, re, json, shutil, urllib.parse
import http.server, socketserver
import subprocess

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

SITE_DIR = r'E:\项目库\china-travel-website'
PORT = 8082
GIT_EXE = r'C:\Program Files\Git\bin\git.exe'

SRC_DIR = os.path.join(SITE_DIR, 'articles', '.src')
ARTICLES_DIR = os.path.join(SITE_DIR, 'articles')
MANIFEST_PATH = os.path.join(SITE_DIR, 'articles', '.manifest.json')

GUIDE_MAP = [
    ('before-you-go', 'Before You Go'),
    ('payment', 'Payment'),
    ('transportation', 'Transportation'),
    ('stay', 'Where to Stay'),
    ('explore', 'Explore China'),
]
GUIDE_SECTIONS = {k: v for k, v in GUIDE_MAP}

# =====================================================================
#  文件操作
# =====================================================================
def read_file(rel_path):
    try:
        with open(os.path.join(SITE_DIR, rel_path), 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

def write_file(rel_path, content):
    try:
        abspath = os.path.join(SITE_DIR, rel_path)
        os.makedirs(os.path.dirname(abspath), exist_ok=True)
        with open(abspath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except Exception as e:
        return False, str(e)

def delete_file(rel_path):
    try:
        os.remove(os.path.join(SITE_DIR, rel_path))
        return True, None
    except Exception as e:
        return False, str(e)

def html_escape(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# =====================================================================
#  Manifest 管理
# =====================================================================
def get_manifest():
    if not os.path.isfile(MANIFEST_PATH):
        return {}
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def set_article_status(fname, title, section, status):
    m = get_manifest()
    m[fname] = {'title': title, 'section': section, 'status': status}
    save_manifest(m)

def remove_article(fname):
    m = get_manifest()
    m.pop(fname, None)
    save_manifest(m)

# =====================================================================
#  初始化（创建目录 + 迁移旧数据）
# =====================================================================
def ensure_dirs():
    os.makedirs(SRC_DIR, exist_ok=True)

def migrate_existing():
    """将已有的 articles/xxx.html 迁移到新系统"""
    manifest = get_manifest()
    changed = False
    for f in os.listdir(ARTICLES_DIR):
        if not f.endswith('.html') or f.startswith('.') or f in ('.src',):
            continue
        if f in manifest:
            continue  # 已在 manifest 中
        # 从文件名推断 section
        section = 'before-you-go'  # 默认
        # 尝试从文件内容提取标题
        content, _ = read_file(f'articles/{f}')
        title = f.replace('.html', '').replace('-', ' ').title()
        if content:
            tm = re.search(r'<title>(.*?)</title>', content, re.DOTALL)
            title = tm.group(1).strip() if tm else title
        manifest[f] = {'title': title, 'section': section, 'status': 'online'}
        changed = True
    if changed:
        save_manifest(manifest)
        print(f'[迁移] 已导入 {changed} 篇文章')

# =====================================================================
#  模板套壳（从当前代码提取，不变）
# =====================================================================
def apply_master_template(content, title, desc, section=''):
    tpl_path = os.path.join(SITE_DIR, 'templates', 'article-master.html')
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            tpl = f.read()
    except:
        return content
    nav_map = [
        ('before-you-go', 'Before You Go', '../guides/before-you-go.html'),
        ('payment', 'Payment', '../guides/payment.html'),
        ('transportation', 'Transportation', '../guides/transportation.html'),
        ('stay', 'Where to Stay', '../guides/stay.html'),
        ('explore', 'Explore China', '../guides/explore.html'),
    ]
    nav_html = ''
    for k, lbl, url in nav_map:
        if k == section:
            nav_html += f'      <span class="crumb current">{lbl}</span>\n'
        else:
            nav_html += f'      <a href="{url}">{lbl}</a>\n'
    tpl = tpl.replace('__TITLE__', title)
    tpl = tpl.replace('__DESCRIPTION__', desc)
    tpl = tpl.replace('__CONTENT__', content)
    tpl = tpl.replace('__NAV__', nav_html)
    return tpl

# =====================================================================
#  标题处理
# =====================================================================
def extract_title(content):
    """从 HTML 内容中提取第一个 <h1> 作为标题"""
    m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    if m:
        return m.group(1).strip()
    return ''

def strip_title(content):
    """去掉第一个 <h1> 及其前后空白"""
    return re.sub(r'\s*<h1[^>]*>.*?</h1>\s*', '', content, count=1, flags=re.DOTALL)

# =====================================================================
#  渲染
# =====================================================================
ADMIN_CSS = '''
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       background: #eef0f5; color: #222; min-height: 100vh; display: flex; }
.sidebar { width: 180px; background: #1a1a2e; color: #fff; display: flex; flex-direction: column;
           flex-shrink: 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.sidebar-header { padding: 1rem 1rem 0.6rem; font-size: 0.85rem; font-weight: 700;
                  letter-spacing: 0.3px; border-bottom: 1px solid rgba(255,255,255,0.06); }
.sidebar-nav { padding: 0.4rem 0; flex: 1; }
.nav-item { display: block; padding: 0.4rem 1rem; font-size: 0.8rem; color: rgba(255,255,255,0.45);
            text-decoration: none; transition: all 0.12s; border-left: 3px solid transparent; }
.nav-item:hover { color: #fff; background: rgba(255,255,255,0.04); }
.nav-item.active { color: #FFDE00; background: rgba(255,222,0,0.06); border-left-color: #FFDE00; font-weight: 600; }
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
.badge { display: inline-block; font-size: 0.68rem; padding: 0.08rem 0.4rem; border-radius: 3px; font-weight: 600; margin-left: 0.4rem; }
.status-badge { display: inline-block; font-size: 0.72rem; padding: 0.1rem 0.5rem; border-radius: 4px; font-weight: 600; margin-left: 0.4rem; }
.status-online { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status-draft { background: #fff3cd; color: #856404; border: 1px solid #ffeeba; }
.actions { display: flex; gap: 0.3rem; flex-shrink: 0; flex-wrap: wrap; }
.btn { display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.28rem 0.6rem;
       border-radius: 4px; font-size: 0.76rem; text-decoration: none; border: none;
       cursor: pointer; font-weight: 500; transition: all 0.12s; line-height: 1.3; }
.btn:hover { opacity: 0.85; }
.btn-edit { background: #1a1a2e; color: #fff; }
.btn-preview { background: #DE2910; color: #fff; }
.btn-done { background: #28a745; color: #fff; }
.btn-delete { background: #dc3545; color: #fff; }
.btn-sync { background: #007bff; color: #fff; padding: 0.4rem 1rem; }
.empty { text-align: center; padding: 3rem 1rem; font-size: 0.85rem; color: #aaa; }
.msg { padding: 0.5rem 1rem; font-size: 0.8rem; border-radius: 4px; margin: 0.5rem 0; }
.msg-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.msg-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.edit-card { display: flex; flex-direction: column; min-height: 0; }
.edit-card > form { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 0 1.2rem 1.2rem; }
.editor-area { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; flex: 1; overflow-y: auto; min-height: 0; }
.editor-inner { max-width: 700px; margin: 0 auto; font-size: 18px; line-height: 1.6; }
.editor-inner:focus { outline: none; }
.edit-actions { flex-shrink: 0; display: flex; gap: 0.5rem; padding: 0.8rem 0 0; align-items: center; }
.edit-meta { flex-shrink: 0; display: flex; gap: 1rem; padding: 0.6rem 0 0; font-size: 0.8rem; align-items: center; }
.edit-meta select { padding: 0.2rem 0.4rem; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 0.8rem; }
'''

def render_page(title, body_html):
    return f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title><style>{ADMIN_CSS}</style></head><body>
<div class="sidebar"><div class="sidebar-header">📋 管理后台</div>
<div class="sidebar-nav">
<a class="nav-item active" href="/admin">📂 文章管理</a>
<a class="nav-item" href="/admin/sync">🔄 同步到线上</a>
</div></div>
<div class="content">{body_html}</div></body></html>'''

def render_list_page(msg=None):
    manifest = get_manifest()
    rows = ''
    for fname in sorted(manifest.keys(), key=lambda x: manifest[x].get('title', x)):
        info = manifest[fname]
        title = info.get('title', fname)
        section = info.get('section', '')
        status = info.get('status', 'draft')
        section_label = GUIDE_SECTIONS.get(section, section)
        if status == 'online':
            status_html = '<span class="status-badge status-online">✅ 已上线</span>'
        else:
            status_html = '<span class="status-badge status-draft">📝 草稿</span>'
        preview_url = f'/articles/{fname}'
        edit_url = f'/admin/edit?path={fname}'
        rows += f'''<div class="row">
<div class="info">
<div class="name">{html_escape(title)} {status_html}</div>
<div class="path">文件名：{fname} · 所属板块：{section_label}</div>
</div>
<div class="actions">
<a class="btn btn-edit" href="{edit_url}">✏️ 修改内容</a>
<a class="btn btn-preview" href="{preview_url}" target="_blank">👁 预览效果</a>
<form method="POST" action="/admin/publish" style="display:inline"
      onsubmit="return confirm('确定要发布这篇文章吗？\n\n发布流程：\n1. 自动套用网站模板\n2. \u4fdd\u5b58到 articles/ 目录\n3. 同步到 GitHub Pages 线上网站')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn btn-done">🚀 发布到线上</button></form>
<form method="POST" action="/admin/delete" style="display:inline"
      onsubmit="return confirm('确定要删除这篇文章吗？\n\n删除后本地文件和线上网站都会同步移除，不可恢复。')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn btn-delete">🗑 删除</button></form>
</div></div>'''
    if not rows:
        rows = '<div class="empty">还没有文章，点下方按钮新建一篇</div>'

    # 提示消息
    msg_html = ''
    if msg:
        if msg.startswith('ok:'):
            msg_html = f'<div class="msg msg-success">✅ {msg[3:]}</div>'
        elif msg.startswith('err:'):
            msg_html = f'<div class="msg msg-error">❌ {msg[3:]}</div>'
        else:
            msg_html = f'<div class="msg msg-success">{msg}</div>'

    return f'''<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">
<h2 style="font-size:1rem;font-weight:700;color:#1a1a2e;">📂 文章管理</h2>
<a class="btn btn-edit" href="/admin/edit" style="padding:0.35rem 0.8rem;font-size:0.8rem;">＋ 新建文章</a>
</div>
{msg_html}
<div class="card">
<div class="card-title">文章列表（共 {len(manifest)} 篇）</div>
{rows}
</div>
<div style="font-size:0.75rem;color:#999;padding:0.5rem 0;text-align:center;">
💡 操作说明：修改内容 → 保存 → 发布到线上（自动套模板+同步网站）
</div>'''

def render_edit_page(fname='', msg=None):
    """render edit page for a given filename"""
    manifest = get_manifest()
    is_new = not fname or fname not in manifest
    content = ''
    section = 'before-you-go'
    title = ''

    if not is_new:
        info = manifest[fname]
        section = info.get('section', 'before-you-go')
        title = info.get('title', '')
        # 读 .src/ 源文件
        src_content, err = read_file(f'articles/.src/{fname}')
        if src_content:
            content = src_content
        else:
            # fallback: 从已发布文章还原
            pub_content, _ = read_file(f'articles/{fname}')
            if pub_content:
                # 去掉模板，提取内容区
                m = re.search(r'<div class="article">(.*?)</div>\s*</div>\s*<footer', pub_content, re.DOTALL)
                body = m.group(1).strip() if m else pub_content
                content = f'<h1>{html_escape(title)}</h1>\n{body}' if title else body
        if not content and title:
            content = f'<h1>{html_escape(title)}</h1>'

    msg_html = ''
    if msg:
        cls = 'msg-success' if msg[0] == 'ok' else 'msg-error'
        icon = '✅' if msg[0] == 'ok' else '❌'
        msg_html = f'<div class="{cls}">{icon} {msg[1]}</div>'

    section_opts = ''.join(f'<option value="{k}"{" selected" if k==section else ""}>{v}</option>'
                           for k, v in GUIDE_MAP)

    body_html = content

    js = '''<script>
var ed=document.getElementById('editable');
var hdn=document.getElementById('hdn-content');
document.querySelector('form').addEventListener('submit',function(e){hdn.value=ed.innerHTML;});
</script>'''

    path_hidden = f'<input type="hidden" name="path" value="{fname}">' if fname else ''

    page_title = '新建文章' if is_new else f'编辑文章：{fname}'
    return render_page(
        page_title,
        f'''<div class="card edit-card">
<div class="card-title">{"📝 新建文章" if is_new else f"✏️ 编辑文章：{fname}"}</div>
<form method="POST" action="/admin/save">
{path_hidden}
<input type="hidden" name="content" id="hdn-content" value="">
<div class="edit-meta">
<label>所属板块：
<select name="section">{section_opts}</select></label>
<label>文件名：
<input type="text" name="filename" value="{fname}" style="padding:0.2rem 0.4rem;border:1px solid #e0e0e0;border-radius:4px;font-size:0.8rem;width:200px;"{" readonly" if not is_new else ""}></label>
<div style="font-size:0.76rem;color:#999;">💡 提示：在编辑器中用 &lt;h1&gt; 写标题，发布时自动提取标题到列表，正文不会重复显示标题。</div>
</div>
{msg_html}
<div class="editor-area"><div class="editor-inner" id="editable" contenteditable="true" style="padding:1rem;">{body_html}</div></div>
<div class="edit-actions">
<button type="submit" class="btn btn-done" style="padding:0.4rem 1rem;font-size:0.85rem;">💾 保存内容</button>
<a class="btn btn-edit" href="/admin" style="padding:0.4rem 1rem;">← 返回文章列表</a>
</div>
</form>
{js}</div>''')

# =====================================================================
#  Git 同步
# =====================================================================
def git_push():
    if not os.path.isdir(os.path.join(SITE_DIR, '.git')):
        return False, '不是 git 仓库'
    try:
        subprocess.run([GIT_EXE, 'add', '-A'], cwd=SITE_DIR, capture_output=True, timeout=10)
        subprocess.run([GIT_EXE, 'commit', '-m', 'admin: publish'], cwd=SITE_DIR, capture_output=True, timeout=10)
        r = subprocess.run([GIT_EXE, 'push'], cwd=SITE_DIR, capture_output=True, timeout=30)
        if r.returncode != 0:
            return False, r.stderr.decode('utf-8', errors='replace')[:200]
        return True, None
    except subprocess.TimeoutExpired:
        return False, '超时'
    except Exception as e:
        return False, str(e)

# =====================================================================
#  Server
# =====================================================================
class AdminHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SITE_DIR, **kwargs)

    def send_html(self, html):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(html.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_redirect(self, loc):
        self.send_response(302)
        self.send_header('Location', loc)
        self.end_headers()

    # ---- GET ----
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)
        msg = qs.get('msg', [None])[0]

        if path == '/admin/sync':
            ok, err = git_push()
            text = err or '✅ 所有文章已同步到 GitHub Pages 线上网站'
            status_cls = 'msg-success' if ok else 'msg-error'
            icon = '✅' if ok else '❌'
            self.send_html(render_page('同步结果',
                f'<div class="card"><div class="card-title">🔄 同步结果</div>'
                f'<div class="msg {status_cls}">{icon} {text}</div>'
                f'<div style="padding:0.8rem 1.2rem;"><a class="btn btn-edit" href="/admin">← 返回文章列表</a></div></div>'))
            return

        if path == '/admin':
            msg = qs.get('msg', [None])[0]
            self.send_html(render_list_page(msg))
            return

        if path == '/admin/edit':
            fname = qs.get('path', [None])[0] or ''
            msg_data = qs.get('msg', [None])[0]
            msg_tuple = None
            if msg_data:
                parts = msg_data.split(':', 1)
                msg_tuple = (parts[0], parts[1]) if len(parts) > 1 else ('ok', msg_data)
            self.send_html(render_edit_page(fname, msg_tuple))
            return

        # 静态文件交给 SimpleHTTPRequestHandler
        return super().do_GET()

    # ---- POST ----
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)

        if path == '/admin/save':
            content = data.get('content', [None])[0] or ''
            section = data.get('section', ['before-you-go'])[0]
            fname = data.get('filename', [None])[0] or data.get('path', [None])[0]

            if not fname:
                self.send_redirect('/admin?msg=err:文件名不能为空')
                return
            if not fname.endswith('.html'):
                fname += '.html'

            # 提取标题
            title = extract_title(content)

            # 保存源文件（带标题）
            ok, err = write_file(f'articles/.src/{fname}', content)
            if not ok:
                self.send_redirect(f'/admin?msg=err:保存失败:{err}')
                return

            # 更新 manifest
            set_article_status(fname, title or fname.replace('.html', '').replace('-', ' ').title(),
                               section, 'draft')

            self.send_redirect(f'/admin?msg=ok:文章已保存，可以继续修改或发布到线上')
            return

        if path == '/admin/publish':
            fname = data.get('path', [None])[0]
            if not fname:
                self.send_redirect('/admin?msg=err:参数错误，请重试')
                return

            manifest = get_manifest()
            info = manifest.get(fname, {})
            section = info.get('section', 'before-you-go')
            title = info.get('title', '')

            # 读源文件
            src_content, err = read_file(f'articles/.src/{fname}')
            if not src_content:
                # 没有源文件，从已发布文章取内容
                pub_content, err = read_file(f'articles/{fname}')
                if not pub_content:
                    self.send_redirect(f'/admin?msg=err:找不到文章文件:{err}')
                    return
                m = re.search(r'<div class="article">(.*?)</div>\s*</div>\s*<footer', pub_content, re.DOTALL)
                body = m.group(1).strip() if m else pub_content
                content = body
            else:
                content = src_content
                # 从源文件重新提取标题
                t = extract_title(content)
                if t:
                    title = t
                # 去掉标题
                content = strip_title(content)

            # 套模板
            final_html = apply_master_template(content, title, '', section)

            # 保存到 articles/
            ok, err = write_file(f'articles/{fname}', final_html)
            if not ok:
                self.send_redirect(f'/admin?msg=err:套壳保存失败:{err}')
                return

            # git push
            git_ok, git_err = git_push()

            # 更新状态
            set_article_status(fname, title, section, 'online')

            if git_ok:
                self.send_redirect(f'/admin?msg=ok:文章「{title}」已发布到线上网站')
            else:
                self.send_redirect(f'/admin?msg=err:文章已保存但同步线上失败:{git_err}')
            return

        if path == '/admin/delete':
            fname = data.get('path', [None])[0]
            if not fname:
                self.send_redirect('/admin?msg=err:参数错误')
                return

            # 取标题用于提示
            manifest = get_manifest()
            title = manifest.get(fname, {}).get('title', fname)

            # 删源文件
            delete_file(f'articles/.src/{fname}')
            # 删已发布文件
            delete_file(f'articles/{fname}')
            # 删 manifest 记录
            remove_article(fname)
            # git push
            git_ok, git_err = git_push()

            if git_ok:
                self.send_redirect(f'/admin?msg=ok:文章「{title}」已删除，线上网站已同步移除')
            else:
                self.send_redirect(f'/admin?msg=err:文章已删除但同步线上失败:{git_err}')
            return

        self.send_redirect('/admin')

# =====================================================================
#  启动
# =====================================================================
if __name__ == '__main__':
    print(f'管理后台 v2 — http://localhost:{PORT}/admin')
    print(f'  文章源文件: articles/.src/')
    print(f'  成品: articles/')
    ensure_dirs()
    migrate_existing()
    with socketserver.ThreadingTCPServer(('', PORT), AdminHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
