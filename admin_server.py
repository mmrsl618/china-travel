# -*- coding: utf-8 -*-
"""admin_server.py — 管理后台 v4.1
 - v4.1: 修复 update_guide_listing() tab查找逻辑；预览链接指向线上域名；导航加文章数量；文字"已上线"→"已上站"
 - v4.0: 适配文件夹结构；Git proxy 清掉，靠Windows系统代理

端口 8082 | ThreadingTCPServer

导航栏三栏：
  📫 待审草稿 /admin/draft   — zh_draft/draft → 编辑 + 通过(套壳生成 en.html → en_draft，不 push)
  📪 待上站  /admin/publish — en_draft → 预览 + 编辑(提示撤回) + 上站(git push → online)
  ✅ 已上站  /admin/done     — online → 编辑/重新发布/删除

状态流转：zh_draft → [通过] 套壳 → en_draft → [上站] git push → online
                    ↑ 撤回草稿，改完重新通过
"""
import os, sys, re, json, urllib.parse, urllib.request
import http.server, socketserver
import subprocess
from datetime import datetime, timedelta

os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

SITE_DIR = r'E:\项目库\china-travel-website'
PORT = 8082
GIT_EXE = r'C:\Program Files\Git\bin\git.exe'

ARTICLES_DIR = os.path.join(SITE_DIR, 'articles')
MANIFEST_PATH = os.path.join(SITE_DIR, 'articles', '.manifest.json')

# 新文件夹结构辅助函数
def article_dir(fname):
    """fname = manifest key (文件夹名)"""
    return os.path.join(ARTICLES_DIR, fname)

def source_path(fname):
    """zh.html 路径（历史初稿）"""
    return os.path.join(ARTICLES_DIR, fname, 'zh.html')

def published_path(fname):
    """已发布英文稿路径"""
    return os.path.join(ARTICLES_DIR, fname, 'en.html')

GUIDE_MAP = [
    ('before-you-go', 'Before You Go'),
    ('payment', 'Payment'),
    ('transportation', 'Transportation'),
    ('stay', 'Where to Stay'),
    ('explore', 'Explore China'),
]
GUIDE_SECTIONS = {k: v for k, v in GUIDE_MAP}

# 二级导航（子分类）映射
SUBCAT_MAP = {
    'before-you-go': [
        ('visa', 'Visa Policies'),
        ('arrival', 'Arrival Guide'),
        ('tools', 'Essential Tools'),
    ],
    'payment': [
        ('methods', 'Payment Methods'),
        ('tips', 'Practical Tips'),
    ],
    'transportation': [
        ('trains', 'Trains'),
        ('flights', 'Flights'),
        ('local', 'Local'),
    ],
    'stay': [('accommodations', 'Accommodations')],
    'explore': [
        ('cities', 'City Guides'),
        ('itineraries', 'Itineraries'),
        ('food', 'Food & Dining'),
    ],
}

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
            m = json.load(f)
            # 废弃 zh_approved → zh_draft 自动迁移
            dirty = False
            for fname, info in m.items():
                if info.get('status') == 'zh_approved':
                    info['status'] = 'zh_draft'
                    dirty = True
            if dirty:
                save_manifest(m)
            return m
    except:
        return {}

def save_manifest(manifest):
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

def set_article_manifest(fname, title, section, status, sub_category=''):
    m = get_manifest()
    entry = {'title': title, 'section': section, 'status': status}
    if sub_category:
        entry['sub_category'] = sub_category
    m[fname] = entry
    save_manifest(m)

def remove_article_manifest(fname):
    m = get_manifest()
    m.pop(fname, None)
    save_manifest(m)

# =====================================================================
#  Guide 列表页自动更新
# =====================================================================
def update_guide_listing(section, sub_category, fname, title, remove=False):
    """在 guides/{section}.html 对应子分类 tab 下添加/删除文章链接

    Args:
        section: 板块 key（before-you-go 等）
        sub_category: 子分类 key（visa 等）
        fname: 文件名（xxx.html）
        title: 文章标题
        remove: True=删除链接, False=添加链接
    Returns:
        (ok, err_msg)
    """
    guide_path = f'guides/{section}.html'
    content, err = read_file(guide_path)
    if not content:
        print(f'[update_guide_listing] ❌ 找不到 {guide_path}: {err}')
        return False, f'找不到 {guide_path}: {err}'

    link_html = f'<a href="../articles/{fname}/en.html" class="article-link">{html_escape(title)}</a>'

    if remove:
        # 删除链接（连带前后空白和换行）
        new_content = re.sub(
            r'\s*' + re.escape(link_html) + r'\s*\n?',
            '\n',
            content
        )
        if new_content == content:
            print(f'[update_guide_listing] ❌ 在 {guide_path} 中未找到「{title}」的链接')
            return False, f'在 {guide_path} 中未找到「{title}」的链接'
        # 清理空 article-list
        new_content = re.sub(
            r'<div class="article-list">\s*</div>\n?',
            '',
            new_content
        )
        ok, err = write_file(guide_path, new_content)
        if not ok:
            print(f'[update_guide_listing] ❌ 写入 {guide_path} 失败: {err}')
            return False, f'写入 {guide_path} 失败: {err}'
        return True, None

    # ---- 添加链接 ----
    tab_id = f'tab-{sub_category}'

    # 找 tab-content 的起始位置
    tab_markers = [
        f'<div class="tab-content active" id="{tab_id}">',
        f'<div class="tab-content" id="{tab_id}">',
    ]
    tab_start = -1
    for marker in tab_markers:
        tab_start = content.find(marker)
        if tab_start >= 0:
            break
    if tab_start < 0:
        print(f'[update_guide_listing] ❌ 在 {guide_path} 中未找到 #{tab_id} div')
        return False, f'在 {guide_path} 中未找到 #{tab_id} div'

    # 跳过 opening tag
    tag_end = content.index('>', tab_start) + 1

    # 去重检查
    if f'href="../articles/{fname}/en.html"' in content[tag_end:]:
        return True, None  # 已存在，跳过

    # 找 article-list
    al_marker = '<div class="article-list">'
    al_pos = content.find(al_marker, tag_end)

    if al_pos >= 0:
        # 已有 article-list，在末尾追加新链接
        al_close = content.find('</div>', al_pos)
        if al_close < 0:
            print(f'[update_guide_listing] ❌ 在 {guide_path} 中 article-list 缺少闭合标签')
            return False, f'在 {guide_path} 中 article-list 缺少闭合标签'
        new_content = (content[:al_close] +
                       '\n    ' + link_html +
                       content[al_close:])
    else:
        # 没有 article-list，在 tab-content 内新建
        # 找 tab-content 的闭合 </div>
        tab_close = content.find('</div>', tag_end)
        if tab_close < 0:
            print(f'[update_guide_listing] ❌ 在 {guide_path} 中 #{tab_id} 缺少闭合标签')
            return False, f'在 {guide_path} 中 #{tab_id} 缺少闭合标签'
        new_content = (content[:tab_close] +
                       '\n  <div class="article-list">\n    ' + link_html + '\n  </div>' +
                       content[tab_close:])

    if new_content == content:
        print(f'[update_guide_listing] ❌ 修改 {guide_path} 后无变化')
        return False, f'修改 {guide_path} 后无变化'

    ok, err = write_file(guide_path, new_content)
    if not ok:
        print(f'[update_guide_listing] ❌ 写入 {guide_path} 失败: {err}')
        return False, f'写入 {guide_path} 失败: {err}'
    return True, None

# =====================================================================
#  模板套壳
# =====================================================================
def apply_master_template(content, title, desc, section='', sub_category=''):
    tpl_path = os.path.join(SITE_DIR, 'templates', 'article-master.html')
    try:
        with open(tpl_path, 'r', encoding='utf-8') as f:
            tpl = f.read()
    except:
        return content
    nav_map = [
        ('before-you-go', 'Before You Go', '../../guides/before-you-go.html'),
        ('payment', 'Payment', '../../guides/payment.html'),
        ('transportation', 'Transportation', '../../guides/transportation.html'),
        ('stay', 'Where to Stay', '../../guides/stay.html'),
        ('explore', 'Explore China', '../../guides/explore.html'),
    ]
    nav_html = ''
    for k, lbl, url in nav_map:
        if k == section:
            nav_html += f'      <span class="crumb current">{lbl}</span>\n'
        else:
            nav_html += f'      <a href="{url}">{lbl}</a>\n'

    # 面包屑：Home › 板块名 › 子分类名
    # 如果有子分类，显示子分类名；否则显示文章标题
    section_label = GUIDE_SECTIONS.get(section, section)
    section_url = f'../../guides/{section}.html'
    sub_label = ''
    if sub_category:
        for subs in SUBCAT_MAP.get(section, []):
            for k, lbl in subs:
                if k == sub_category:
                    sub_label = lbl
                    break
            if sub_label:
                break
    last_crumb = sub_label if sub_label else title
    breadcrumb = (f'<div class="breadcrumb" style="font-size:0.85rem;color:#666;'
                  f'padding:0 0 1rem;margin:0 0 1rem;border-bottom:1px solid #eee;">\n'
                  f'<a href="../../index.html">Home</a>\n'
                  f'<span class="sep"> › </span>\n'
                  f'<a href="{section_url}">{html_escape(section_label)}</a>\n'
                  f'<span class="sep"> › </span>\n'
                  f'<span>{html_escape(last_crumb)}</span>\n</div>\n')

    # 修正图片路径：统一为 images/ 相对路径
    content = re.sub(r'(\.\./)+images/', '../../images/', content)

    # 替换/剥离现有面包屑（可能是旧的），统一用新的
    content = re.sub(r'\s*<div class="breadcrumb".*?</div>\s*', '', content, flags=re.DOTALL)

    tpl = tpl.replace('__CONTENT__', breadcrumb + content)
    tpl = tpl.replace('__TITLE__', title)
    tpl = tpl.replace('__DESCRIPTION__', desc)
    tpl = tpl.replace('__NAV__', nav_html)
    return tpl

# =====================================================================
#  标题处理
# =====================================================================
def extract_title(content):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.DOTALL)
    return m.group(1).strip() if m else ''

def strip_title(content):
    return re.sub(r'\s*<h1[^>]*>.*?</h1>\s*', '', content, count=1, flags=re.DOTALL)

# =====================================================================
#  Git 同步
# =====================================================================
def git_push():
    """git add + commit + push，不写死代理，由系统 git 自行读取用户配置"""
    if not os.path.isdir(os.path.join(SITE_DIR, '.git')):
        return False, '不是 git 仓库'
    try:
        # add
        r_add = subprocess.run([GIT_EXE, 'add', '-A'], cwd=SITE_DIR, capture_output=True, timeout=10)
        if r_add.returncode != 0:
            return False, f'git add 失败: {r_add.stderr.decode("utf-8", errors="replace")[:200]}'

        # commit（nothing to commit 不算失败）
        r_commit = subprocess.run([GIT_EXE, 'commit', '-m', 'admin: publish'], cwd=SITE_DIR, capture_output=True, timeout=10)
        if r_commit.returncode != 0:
            commit_msg = r_commit.stderr.decode('utf-8', errors='replace')
            if 'nothing to commit' not in commit_msg and 'nothing added to commit' not in commit_msg:
                return False, f'git commit 失败: {commit_msg[:200]}'

        # push
        r_push = subprocess.run([GIT_EXE, 'push'], cwd=SITE_DIR, capture_output=True, timeout=60)
        if r_push.returncode != 0:
            err_text = r_push.stderr.decode('utf-8', errors='replace') + r_push.stdout.decode('utf-8', errors='replace')
            network_keywords = [
                'Could not resolve host', 'Failed to connect',
                'Connection refused', 'Connection timed out',
                'timeout', 'timed out', 'Name or service not known',
                'Network is unreachable',
            ]
            if any(kw in err_text for kw in network_keywords):
                return False, 'GitHub 连接失败，请检查网络后重试\n（如已配代理请确认代理软件已开启）'
            return False, err_text[:300]
        return True, None
    except subprocess.TimeoutExpired:
        return False, 'Git push 超时，请检查网络后重试\n（如已配代理请确认代理软件已开启）'
    except Exception as e:
        return False, str(e)[:200]

def update_kv_url_map():
    """调用 gen_url_map.py 重新生成 URL 映射并上传 Cloudflare KV"""
    script = os.path.join(SITE_DIR, 'gen_url_map.py')
    if not os.path.exists(script):
        return False, 'gen_url_map.py 不存在'
    try:
        r = subprocess.run(['python', script], cwd=SITE_DIR, capture_output=True, timeout=30)
        if r.returncode != 0:
            return False, r.stderr.decode('utf-8', errors='replace')[:300]
        return True, None
    except subprocess.TimeoutExpired:
        return False, 'URL 映射更新超时'
    except Exception as e:
        return False, str(e)[:200]

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
.nav-item.active { background: rgba(255,222,0,0.06); border-left-color: #FFDE00; }
.nav-parent { display: flex; align-items: center; justify-content: space-between; cursor: pointer; }
.nav-parent .arrow { font-size: 0.65rem; transition: transform 0.15s; margin-left: auto; opacity: 0.5; }
.nav-parent.open .arrow { transform: rotate(90deg); }
.nav-child { display: none; padding: 0; }
.nav-child.show { display: block; }
.nav-sub-parent { display: flex; align-items: center; cursor: pointer; padding: 0.3rem 1rem 0.3rem 2rem; font-size: 0.76rem; color: rgba(255,255,255,0.45); border-left: 3px solid transparent; transition: all 0.12s; }
.nav-sub-parent:hover { color: #fff; background: rgba(255,255,255,0.04); }
.nav-sub-parent.active { background: rgba(255,222,0,0.06); border-left-color: #FFDE00; }
/* 无子分类的板块链接，跟 nav-sub-parent 保持一致 */
.nav-section-link { display: flex; align-items: center; padding: 0.3rem 1rem 0.3rem 2rem; font-size: 0.76rem; color: rgba(255,255,255,0.45); border-left: 3px solid transparent; text-decoration: none; transition: all 0.12s; }
.nav-section-link:hover { color: #fff; background: rgba(255,255,255,0.04); }
.nav-section-link.active { background: rgba(255,222,0,0.06); border-left-color: #FFDE00; }
.nav-section-link .arrow-sub { visibility: hidden; display: inline-block; width: 0.55rem; margin-right: 0.4rem; }
.nav-sub-parent .arrow-sub { font-size: 0.55rem; transition: transform 0.15s; margin-right: 0.4rem; opacity: 0.5; display: inline-block; }
.nav-sub-parent.open .arrow-sub { transform: rotate(90deg); }
.nav-sub-child { display: none; }
.nav-sub-child.show { display: block; }
.nav-sub-child .nav-item.sub { padding: 0.25rem 1rem 0.25rem 3.5rem; font-size: 0.72rem; border-left: 3px solid transparent; color: rgba(255,255,255,0.35); text-decoration: none; display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* 子分类更靠右，视觉层次更清晰 */
.nav-sub-child .nav-item.sub:hover { color: #fff; background: rgba(255,255,255,0.03); }
.nav-sub-child .nav-item.sub.active { color: #FFDE00; border-left-color: #FFDE00; background: transparent; font-weight: 500; }
.content { flex: 1; min-width: 0; padding: 1.5rem 2rem; max-width: 1000px; }
.content-wide { display: flex; flex-direction: column; overflow: hidden; max-height: 100vh; max-width: none; }
.content-wide .card { flex: 1; min-height: 0; }
.card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); overflow: hidden; margin-bottom: 1rem; }
.card-title { font-size: 0.88rem; font-weight: 700; color: #1a1a2e; padding: 0.9rem 1.2rem; border-bottom: 1px solid #f0f0f0; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 1.2rem; border-bottom: 1px solid #f5f5f5; gap: 0.5rem; }
.row:last-child { border-bottom: none; }
.row:hover { background: #fafbfc; }
.info { flex: 1; min-width: 0; }
.name { font-size: 0.86rem; color: #222; font-weight: 500; }
.path { font-size: 0.7rem; color: #aaa; margin-top: 0.06rem; }
.actions { display: flex; gap: 0.3rem; flex-shrink: 0; flex-wrap: wrap; }
.btn { display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.28rem 0.6rem;
       border-radius: 4px; font-size: 0.76rem; text-decoration: none; border: none;
       cursor: pointer; font-weight: 500; transition: all 0.12s; line-height: 1.3; }
.btn:hover { opacity: 0.85; }
.btn-edit { background: #1a1a2e; color: #fff; }
.btn-preview { background: #DE2910; color: #fff; }
.btn-done { background: #28a745; color: #fff; }
.btn-delete { background: #dc3545; color: #fff; }
.empty { text-align: center; padding: 3rem 1rem; font-size: 0.85rem; color: #aaa; }
.msg { padding: 0.5rem 1rem; font-size: 0.8rem; border-radius: 4px; margin: 0.5rem 0; }
.msg-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.msg-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.edit-card { display: flex; flex-direction: column; min-height: 0; }
.edit-card > form { flex: 1; display: flex; flex-direction: column; min-height: 0; padding: 0 1.2rem 1.2rem; }
.editor-area { background: #fafafa; border: 1px solid #e0e0e0; border-radius: 4px; flex: 1; overflow-y: auto; min-height: 0; }
.editor-inner { max-width: 900px; margin: 0 auto; font-size: 18px; line-height: 1.6; padding: 1rem; min-height: 300px; }
.editor-inner:focus { outline: none; }
.edit-actions { flex-shrink: 0; display: flex; gap: 0.5rem; padding: 0.8rem 0 0; align-items: center; }
.edit-meta { flex-shrink: 0; display: flex; gap: 1rem; padding: 0.6rem 0 0; font-size: 0.8rem; align-items: center; }
.edit-meta select, .edit-meta input { padding: 0.2rem 0.4rem; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 0.8rem; }
'''

def _section_nav_html(section_key, section_label, current_page):
    """生成一个板块的导航HTML（含二级子分类折叠）"""
    subs = SUBCAT_MAP.get(section_key, [])
    page = f'done-{section_key}'
    active = ' active' if current_page.startswith(page) else ''
    # 从 current_page 解析子分类（格式：done-{section}-{sub}）
    sub_active = ''
    if current_page.startswith(page + '-'):
        sub_active = current_page[len(page)+1:]

    if not subs:
        # 无子分类，直接链接到板块页（加一个隐藏的箭头占位符，保证文字对齐）
        return f'<a class="nav-section-link{active}" href="/admin/done/{section_key}"><span class="arrow-sub" aria-hidden="true"></span>{section_label}</a>\n'

    # 有子分类 → 可折叠的二级导航
    is_open = bool(active)
    sec_indent = '    '
    html = f'{sec_indent}<div class="nav-item nav-sub-parent{active}{" open" if is_open else ""}" onclick="toggleSubcat(\'{section_key}\')">'
    html += f'<span class="arrow-sub">\u25b8</span> {section_label}</div>\n'
    html += f'{sec_indent}<div class="nav-sub-child{" show" if is_open else ""}" id="sub-{section_key}">\n'
    for k, lbl in subs:
        sub_active_cls = ' active' if sub_active == k else ''
        html += f'{sec_indent}  <a class="nav-item sub{sub_active_cls}" href="/admin/done/{section_key}?sub={k}">{lbl}</a>\n'
    html += f'{sec_indent}</div>\n'
    return html

def _count_articles(manifest, status_filter):
    try:
        return sum(1 for info in manifest.values() if status_filter(info.get('status', '')))
    except:
        return '?'

def sidebar_nav(current_page):
    """生成左侧导航 — v4.0 三栏"""
    manifest = get_manifest()
    draft_cnt = _count_articles(manifest, lambda s: s in ('zh_draft', 'draft'))
    pub_cnt   = _count_articles(manifest, lambda s: s == 'en_draft')
    done_cnt  = _count_articles(manifest, lambda s: s == 'online')
    draft_active = ' active' if current_page == 'draft' else ''
    publish_active = ' active' if current_page == 'publish' else ''
    html = f'<a class="nav-item{draft_active}" href="/admin/draft">📫 待审草稿({draft_cnt})</a>'
    html += f'<a class="nav-item{publish_active}" href="/admin/publish">📪 待上站({pub_cnt})</a>'
    # 已上站（汉堡式导航，5个板块）
    is_online = current_page.startswith('done')
    html += f'''<div class="nav-item nav-parent{" open" if is_online else ""}" onclick="toggleDone()">
✅ 已上站({done_cnt}) <span class="arrow">▸</span></div>'''
    ch = ''.join(
        _section_nav_html(k, v, current_page)
        for k, v in GUIDE_MAP)
    html += f'<div class="nav-child{" show" if is_online else ""}" id="done-child">{ch}</div>'
    # JavaScript 控制折叠（两层折叠）
    js = '''<script>
function toggleDone(){
  var c=document.getElementById('done-child');
  c.previousElementSibling.classList.toggle('open');
  c.classList.toggle('show');
}
function toggleSubcat(id){
  var c=document.getElementById('sub-'+id);
  if(!c)return;
  c.previousElementSibling.classList.toggle('open');
  c.classList.toggle('show');
}
</script>'''
    stats_active = ' active' if current_page == 'stats' else ''
    html += f'<a class="nav-item{stats_active}" href="/admin/stats">📊 流量统计</a>'
    return html + js

def render_page(title, body_html, current_page='draft', wide=False):
    nav = sidebar_nav(current_page)
    content_cls = 'content content-wide' if wide else 'content'
    return f'''<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title><style>{ADMIN_CSS}</style></head><body>
<div class="sidebar"><div class="sidebar-header">📋 管理后台</div>
<div class="sidebar-nav">{nav}</div></div>
<div class="{content_cls}">{body_html}</div></body></html>'''

def _msg_html(msg):
    """渲染消息提示"""
    if not msg:
        return ''
    if msg.startswith('ok:'):
        return f'<div class="msg msg-success">✅ {msg[3:]}</div>'
    elif msg.startswith('err:'):
        return f'<div class="msg msg-error">❌ {msg[3:]}</div>'
    return ''

def _search_bar(input_id):
    """客户端实时搜索框 — 按 data-keyword 过滤 .row"""
    return f'''<div style="padding:0.5rem 1.2rem;">
<input type="text" id="{input_id}" placeholder="🔍 搜索文章标题或文件夹名…"
       style="width:100%; padding:0.4rem 0.6rem; border:1px solid #e0e0e0; border-radius:4px; font-size:0.8rem;"
       oninput="var q=this.value.toLowerCase();var rows=this.parentElement.parentElement.querySelectorAll('.row');
rows.forEach(function(r){{r.style.display=(!q||r.getAttribute('data-keyword')||'').indexOf(q)>=0?'':'none'}});">
</div>'''

# =====================================================================
#  配置（admin_config.json，不提交到 git）
# =====================================================================
def _load_config():
    """从 admin_config.json 读取凭据，文件不存在时返回 None"""
    cfg_path = os.path.join(os.path.dirname(__file__), 'admin_config.json')
    try:
        with open(cfg_path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

CFG = _load_config()

# =====================================================================
#  流量统计
# =====================================================================
def _fetch_cloudflare_stats():
    """请求 Cloudflare GraphQL API，返回每日数据列表或 None"""
    if not CFG:
        return None
    url = 'https://api.cloudflare.com/client/v4/graphql'
    token = CFG.get('cloudflare_api_token', '')
    zone_id = CFG.get('cloudflare_zone_id', '')
    if not token or not zone_id:
        return None
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
    }
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')
    query = '''query {
  viewer {
    zones(filter: { zoneTag: "''' + zone_id + '''" }) {
      httpRequests1dGroups(limit: 7, filter: { date_gt: "''' + seven_days_ago + '''" }, orderBy: [date_DESC]) {
        dimensions { date }
        sum { requests pageViews bytes }
      }
    }
  }
}'''
    payload = json.dumps({'query': query}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            zones = data.get('data', {}).get('viewer', {}).get('zones', [])
            if not zones:
                return None
            return zones[0].get('httpRequests1dGroups', [])
    except Exception as e:
        print(f'[stats] Cloudflare API 请求失败: {e}')
        return None

def render_stats_page():
    """流量统计页"""
    daily_data = _fetch_cloudflare_stats()

    if not daily_data:
        body = '''<div class="card">
<div class="card-title">📊 流量统计</div>
<div class="empty" style="padding:3rem 1rem;">
  <p style="font-size:1.2rem;margin-bottom:0.5rem;">暂无数据</p>
  <p style="font-size:0.85rem;color:#aaa;">Cloudflare API 请求失败或返回为空，请稍后重试</p>
</div></div>'''
        return render_page('流量统计', body, 'stats')

    # 今日数据
    today = daily_data[0]
    today_pageviews = today['sum']['pageViews']
    today_bytes = today['sum']['bytes']
    today_mb = round(today_bytes / 1048576, 2)

    # 今日概览卡片
    cards = f'''<div style="display:flex;gap:1rem;margin-bottom:1rem;">
<div class="card" style="flex:1;text-align:center;padding:1.2rem;">
  <div style="font-size:0.8rem;color:#999;">今日页面浏览</div>
  <div style="font-size:2rem;font-weight:700;color:#1a1a2e;">{today_pageviews:,}</div>
</div>
<div class="card" style="flex:1;text-align:center;padding:1.2rem;">
  <div style="font-size:0.8rem;color:#999;">今日带宽</div>
  <div style="font-size:2rem;font-weight:700;color:#1a1a2e;">{today_mb} MB</div>
</div>
</div>'''

    # 折线图数据
    chart_dates_json = json.dumps([d['dimensions']['date'] for d in reversed(daily_data)])
    chart_pv_json = json.dumps([d['sum']['pageViews'] for d in reversed(daily_data)])

    # 每日明细表
    rows = ''
    for day in daily_data:
        date = day['dimensions']['date']
        pvs = day['sum']['pageViews']
        mb = round(day['sum']['bytes'] / 1048576, 2)
        rows += f'''<tr>
<td>{date}</td>
<td style="text-align:right;">{pvs:,}</td>
<td style="text-align:right;">{mb} MB</td>
</tr>'''

    table = f'''<div class="card">
<div class="card-title">📋 每日明细</div>
<div style="overflow-x:auto;padding:0 1.2rem 1.2rem;">
<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
<thead><tr style="border-bottom:2px solid #1a1a2e;">
<th style="text-align:left;padding:0.5rem;">日期</th>
<th style="text-align:right;padding:0.5rem;">页面浏览</th>
<th style="text-align:right;padding:0.5rem;">带宽</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
</div></div>'''

    # 折线图
    chart_card = f'''<div class="card">
<div class="card-title">📈 近7天趋势</div>
<div style="padding:0.5rem 1.2rem 1.2rem;">
<canvas id="statsChart" height="220" style="width:100%;max-height:260px;"></canvas>
</div></div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script>
var ctx = document.getElementById('statsChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {chart_dates_json},
    datasets: [{{
      label: '页面浏览',
      data: {chart_pv_json},
      borderColor: '#DE2910',
      backgroundColor: 'rgba(222,41,16,0.06)',
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointBackgroundColor: '#DE2910',
    }}]
  }},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }}
    }},
    scales: {{
      x: {{ grid: {{ display: false }} }},
      y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }} }}
    }}
  }}
}});
</script>'''

    top_articles = '''<div class="card" style="margin-top:1rem;">
<div class="card-title">🔥 热门文章排行（近7天）</div>
<div id="top-articles" style="padding:0.5rem 1.2rem 1.2rem;color:#999;">加载中...</div>
</div>
<script>
fetch("https://visitchinatips.com/api/top-pages")
  .then(function(r){return r.json();})
  .then(function(data){
    var el=document.getElementById("top-articles");
    if(!data||!data.length){el.innerHTML='<p style="color:#aaa;">暂无数据，等文章有浏览量后自动显示</p>';return;}
    var rows="";
    data.forEach(function(item,i){
      var path=item.path;
      var name=item.title||path.replace("/articles/","").replace("/en.html","").replace(/-/g," ");
      var rank=i==0?"🥇":i==1?"🥈":i==2?"🥉":(i+1)+".";
      var href=item.guide_url||path.replace("/articles/","guides/").replace("/en.html",".html");
      rows+='<tr style="border-bottom:1px solid #eee;">'+
        '<td style="padding:0.5rem;width:2.5rem;">'+rank+'</td>'+
        '<td style="padding:0.5rem;text-transform:capitalize;"><a href="'+href+'" target="_blank">'+name+'</a></td>'+
        '<td style="padding:0.5rem;text-align:right;color:#1a1a2e;font-weight:600;">'+item.count+'</td></tr>';
    });
    el.innerHTML='<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'+rows+'</table>';
  })
  .catch(function(e){
    document.getElementById("top-articles").innerHTML='<p style="color:#aaa;">Worker API 请求失败，请检查 Worker 是否在线</p>';
  });
</script>'''
    body = cards + table + chart_card + top_articles
    return render_page('流量统计', body, 'stats')

# =====================================================================
#  页面渲染函数
# =====================================================================
def render_draft_page(msg=None):
    """待审草稿页 — 显示 status=zh_draft 或 draft 的文章
    按钮：【编辑】→ 编辑 zh.html；【通过】→ 套壳生成 en.html → en_draft（不 push）
    """
    manifest = get_manifest()
    rows = ''
    count = 0
    for fname in sorted(manifest.keys(), key=lambda x: manifest[x].get('title', x)):
        info = manifest[fname]
        status = info.get('status', 'draft')
        if status not in ('draft', 'zh_draft'):
            continue

        count += 1
        title = info.get('title', fname)
        sp = source_path(fname)
        src_content, _ = read_file(os.path.relpath(sp, SITE_DIR).replace('\\', '/'))
        if src_content:
            src_title = extract_title(src_content)
            if src_title:
                title = src_title
        section = info.get('section', '')
        section_label = GUIDE_SECTIONS.get(section, section)

        action_btns = f'''
<a class="btn btn-edit" href="/admin/edit?path={fname}&from=draft">✏️ 编辑</a>
<form method="POST" action="/admin/pass" style="display:inline"
      onsubmit="return confirm('确认通过？将套壳发布（不推送上线）')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn btn-done">✅ 通过</button></form>'''

        rows += f'''<div class="row" data-keyword="{html_escape(title).lower()} {fname.lower()}">
<div class="info">
<div class="name">{html_escape(title)}</div>
<div class="path">{fname} · {section_label} · {status}</div>
</div>
<div class="actions">{action_btns}
</div></div>'''

    if count == 0:
        rows = '<div class="empty">暂无待审草稿</div>'
    msg_html = _msg_html(msg)

    search_html = _search_bar('draft-search')
    return render_page('待审草稿',
        f'''<div class="card">
<div class="card-title">📫 待审草稿（共 {count} 篇）</div>
{search_html}
{msg_html}
<div id="draft-list">{rows}</div>
</div>''', 'draft')

def render_publish_page(msg=None):
    """待上站页 — 显示 status=en_draft 的文章
    按钮：【预览】→ 打开 en.html；【编辑】→ 提示撤回；【上站】→ git push → online
    """
    manifest = get_manifest()
    rows = ''
    count = 0
    for fname in sorted(manifest.keys(), key=lambda x: manifest[x].get('title', x)):
        info = manifest[fname]
        status = info.get('status', 'en_draft')
        if status != 'en_draft':
            continue

        count += 1
        title = info.get('title', fname)
        # 尝试从 en.html 提取标题
        pp = published_path(fname)
        pub_content, _ = read_file(os.path.relpath(pp, SITE_DIR).replace('\\', '/'))
        if pub_content:
            pub_title = extract_title(pub_content)
            if pub_title:
                title = pub_title
        else:
            sp = source_path(fname)
            src_content, _ = read_file(os.path.relpath(sp, SITE_DIR).replace('\\', '/'))
            if src_content:
                src_title = extract_title(src_content)
                if src_title:
                    title = src_title
        section = info.get('section', '')
        section_label = GUIDE_SECTIONS.get(section, section)

        preview_url = f'http://localhost:8080/articles/{fname}/en.html'
        action_btns = f'''
<a class="btn btn-preview" href="javascript:void(0)" onclick="window.open('{preview_url}','_blank')">👁 预览</a>
<a class="btn btn-edit" href="javascript:void(0)" onclick="alert('此文章已套壳，如需修改请先撤回草稿，改完重新通过')">✏️ 编辑</a>
<form method="POST" action="/admin/withdraw" style="display:inline"
      onsubmit="return confirm('确认撤回草稿？manifest 将回到 zh_draft')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn" style="background:#6c757d;color:#fff;">↩ 撤回</button></form>
<form method="POST" action="/admin/go-live" style="display:inline"
      onsubmit="return confirm('确认上站？将 git push 到线上')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn btn-done" style="background:#DE2910;">🚀 上站</button></form>'''

        rows += f'''<div class="row" data-keyword="{html_escape(title).lower()} {fname.lower()}">
<div class="info">
<div class="name">{html_escape(title)}</div>
<div class="path">{fname} · {section_label} · {status}</div>
</div>
<div class="actions">{action_btns}
</div></div>'''

    if count == 0:
        rows = '<div class="empty">暂无待上站文章</div>'
    msg_html = _msg_html(msg)

    search_html = _search_bar('publish-search')
    return render_page('待上站',
        f'''<div class="card">
<div class="card-title">📪 待上站（共 {count} 篇）</div>
{search_html}
{msg_html}
<div id="publish-list">{rows}</div>
</div>''', 'publish')

def render_done_page(section_key, sub='', msg=None):
    """已上站：按板块列出已发布的文章，可选按子分类过滤"""
    manifest = get_manifest()
    label = GUIDE_SECTIONS.get(section_key, section_key)
    rows = ''
    count = 0
    # 如果有子分类过滤，显示子分类名
    sub_label = ''
    if sub:
        for k, lbl in SUBCAT_MAP.get(section_key, []):
            if k == sub:
                sub_label = lbl
                break
    for fname in sorted(manifest.keys(), key=lambda x: manifest[x].get('title', x)):
        info = manifest[fname]
        if info.get('status') != 'online' or info.get('section') != section_key:
            continue
        if sub and info.get('sub_category', '') != sub:
            continue
        count += 1
        title = info.get('title', fname)
        preview_url = f'https://visitchinatips.com/articles/{fname}/en.html'
        edit_from = f'done-{section_key}-{sub}' if sub else f'done-{section_key}'
        edit_url = f'/admin/edit?path={fname}&from={edit_from}'
        rows += f'''<div class="row">
<div class="info">
<div class="name">{html_escape(title)}</div>
<div class="path">{fname}</div>
</div>
<div class="actions">
<a class="btn btn-edit" href="{edit_url}">✏️ 编辑</a>
<a class="btn btn-preview" href="{preview_url}" target="_blank">👁 预览</a>
<form method="POST" action="/admin/republish" style="display:inline"
      onsubmit="return confirm('确定要重新发布吗？将重新套壳并同步到线上。')">
<input type="hidden" name="path" value="{fname}">
<input type="hidden" name="section" value="{section_key}">
<button type="submit" class="btn btn-done">🚀 重新发布</button></form>
<form method="POST" action="/admin/delete" style="display:inline"
      onsubmit="return confirm('确定要删除吗？将删除本地文件并同步到线上移除。')">
<input type="hidden" name="path" value="{fname}">
<button type="submit" class="btn btn-delete">🗑 删除</button></form>
</div></div>'''
    if count == 0:
        rows = '<div class="empty">该板块暂无已发布的文章</div>'
    msg_html = ''
    if msg:
        if msg.startswith('ok:'):
            msg_html = f'<div class="msg msg-success">✅ {msg[3:]}</div>'
        elif msg.startswith('err:'):
            msg_html = f'<div class="msg msg-error">❌ {msg[3:]}</div>'
    title_parts = ['已上站', label]
    if sub_label:
        title_parts.append(sub_label)
    page_title = ' · '.join(title_parts)
    current_page = f'done-{section_key}-{sub}' if sub else f'done-{section_key}'

    return render_page(page_title,
        f'''<div class="card">
<div class="card-title">✅ 已上站 · {label}{" > " + sub_label if sub_label else ""}（共 {count} 篇）</div>
{msg_html}
{rows}
</div>''', current_page)

def render_edit_page(fname, return_to='draft', msg=None):
    """编辑页，和原来一样——contenteditable + 滚动 + 底部按钮"""
    manifest = get_manifest()
    info = manifest.get(fname, {})
    is_new = not info
    content = ''
    section = info.get('section', 'before-you-go')
    title = info.get('title', '')
    sub_category = info.get('sub_category', '')

    if not is_new:
        # 优先读 zh.html 源文件（用户的工作副本）
        sp = source_path(fname)
        src_content, _ = read_file(os.path.relpath(sp, SITE_DIR).replace('\\', '/'))
        if src_content:
            content = src_content
            # 剥掉 <head>/<body>/<header>/<footer>，防止外部样式/导航/版权信息污染管理后台和套壳
            m_body = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL)
            if m_body:
                content = m_body.group(1).strip()
            else:
                content = re.sub(r'<head>.*?</head>', '', content, flags=re.DOTALL)
                content = re.sub(r'</?html[^>]*>|<!DOCTYPE[^>]*>', '', content, flags=re.DOTALL)
            content = re.sub(r'<header>.*?</header>', '', content, flags=re.DOTALL)
            content = re.sub(r'<footer>.*?</footer>', '', content, flags=re.DOTALL)
            # 剥掉可能从之前发布带回来的面包屑
            content = re.sub(r'\s*<div class="breadcrumb".*?</div>\s*', '', content, flags=re.DOTALL)
            content = content.strip()

        # 如果 zh.html 为空，尝试从已发布文章（en.html）恢复
        if not content:
            pp = published_path(fname)
            pub_content, _ = read_file(os.path.relpath(pp, SITE_DIR).replace('\\', '/'))
            if pub_content:
                m = re.search(r'<div class="article">(.*?)</div>\s*</div>\s*<footer', pub_content, re.DOTALL)
                body = m.group(1).strip() if m else pub_content
                # 剥离 en.html 中已有的 <h1>（避免和合成的标题重复）
                body = re.sub(r'\s*<h1[^>]*>.*?</h1>\s*', '', body, count=1, flags=re.DOTALL)
                # 剥离面包屑
                body = re.sub(r'\s*<div class="breadcrumb".*?</div>\s*', '', body, flags=re.DOTALL)
                body = body.strip()
                content = f'<h1>{html_escape(title)}</h1>\n{body}' if title else body

        if not content and title:
            content = f'<h1>{html_escape(title)}</h1>'

    msg_html = ''
    if msg:
        cls = 'msg-success' if msg[0] == 'ok' else 'msg-error'
        msg_html = f'<div class="{cls}">{"✅" if msg[0]=="ok" else "❌"} {msg[1]}</div>'

    section_opts = ''.join(f'<option value="{k}"{" selected" if k==section else ""}>{v}</option>'
                           for k, v in GUIDE_MAP)

    subcat_list = SUBCAT_MAP.get(section, [])
    subcat_opts = ''.join(f'<option value="{k}"{" selected" if k==sub_category else ""}>{v}</option>'
                          for k, v in subcat_list)

    js = '''<script>
var ed=document.getElementById('editable');
var hdn=document.getElementById('hdn-content');
document.querySelector('form').addEventListener('submit',function(e){hdn.value=ed.innerHTML;});
// 动态更新子分类下拉
var secSel=document.getElementById('sel-section');
var subSel=document.getElementById('sel-subcat');
var subMap=''' + json.dumps(SUBCAT_MAP, ensure_ascii=False) + ''';
secSel.addEventListener('change',function(){
  var k=this.value;
  var subs=subMap[k]||[];
  subSel.innerHTML=subs.length?subs.map(function(s){return '<option value="'+s[0]+'">'+s[1]+'</option>';}).join(''):'<option value="">（无）</option>';
});
</script>'''

    # 解析 return_to 确定返回链接
    if return_to.startswith('done'):
        rest = return_to[5:]  # 去掉 "done-"
        # 匹配已知的板块key（有些key自带连字符如 before-you-go）
        section_from = rest
        sub_from = ''
        for sk in GUIDE_SECTIONS:
            if rest == sk or rest.startswith(sk + '-'):
                section_from = sk
                sub_from = rest[len(sk)+1:]
                break
        back_url = f'/admin/done/{section_from}'
        if sub_from:
            back_url += f'?sub={sub_from}'
        back_label = '返回已上站'
    else:
        back_url = '/admin/draft'
        back_label = '返回草稿管理'
        if return_to == 'publish':
            back_url = '/admin/publish'
            back_label = '返回待上站'
    path_readonly = ' readonly' if not is_new else ''

    # 修正编辑页图片路径：相对路径 → 绝对路径（浏览器在 /admin/ 下解析不到）
    content = re.sub(r'(src=")(?!http|/)(.*?images/)', lambda m: m.group(1) + '/articles/' + fname + '/' + m.group(2), content)

    return render_page(
        f'编辑文章：{fname}',
        f'''<div class="card edit-card">
<div class="card-title">✏️ 编辑文章：{fname}</div>
<form method="POST" action="/admin/save">
<input type="hidden" name="path" value="{fname}">
<input type="hidden" name="return_to" value="{return_to}">
<input type="hidden" name="content" id="hdn-content" value="">
<div class="edit-meta">
<label>所属板块：<select name="section" id="sel-section">{section_opts}</select></label>
<label>子分类：<select name="sub_category" id="sel-subcat">{subcat_opts or '<option value="">（无）</option>'}</select></label>
<label>文件名：<input type="text" name="filename" value="{fname}"{path_readonly}></label>
</div>
<div style="font-size:0.76rem;color:#999;">💡 在编辑器中用 &lt;h1&gt; 写标题，发布时标题自动提取到列表，正文不重复显示。</div>
{msg_html}
<div class="editor-area"><div class="editor-inner" id="editable" contenteditable="true" style="padding:1rem;">{content}</div></div>
<div class="edit-actions">
<button type="submit" class="btn btn-done" style="padding:0.4rem 1rem;font-size:0.85rem;">💾 保存内容</button>
<a class="btn btn-edit" href="{back_url}" style="padding:0.4rem 1rem;">← {back_label}</a>
</div>
</form>
{js}</div>''', return_to if return_to.startswith('done') else 'draft', wide=True)

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

    def redirect_msg(self, base_url, msg_type, msg_text):
        """安全地构建带消息的重定向URL（自动URL编码）"""
        params = urllib.parse.urlencode({'msg': f'{msg_type}:{msg_text}'})
        sep = '&' if '?' in base_url else '?'
        self.send_redirect(f'{base_url}{sep}{params}')

    # ---- GET ----
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # 根路径重定向到待审草稿
        if path in ('/admin', '/admin/'):
            self.send_redirect('/admin/draft')
            return

        # 旧路由 /admin/draft/zh 和 /admin/draft/en → 重定向到 /admin/draft
        if path in ('/admin/draft/zh', '/admin/draft/en'):
            self.send_redirect('/admin/draft')
            return

        # 待审草稿（新统一页）
        if path == '/admin/draft':
            msg = qs.get('msg', [None])[0]
            self.send_html(render_draft_page(msg))
            return

        # 待上站
        if path == '/admin/publish':
            msg = qs.get('msg', [None])[0]
            self.send_html(render_publish_page(msg))
            return

        # 已上站板块
        m = re.match(r'/admin/done/([\w-]+)/?$', path)
        if m:
            section = m.group(1)
            if section not in GUIDE_SECTIONS:
                self.send_redirect('/admin/draft')
                return
            sub = qs.get('sub', [None])[0] or ''
            msg = qs.get('msg', [None])[0]
            self.send_html(render_done_page(section, sub, msg))
            return

        # 编辑页
        if path == '/admin/edit':
            fname = qs.get('path', [None])[0] or ''
            return_to = qs.get('from', ['draft'])[0]
            msg_data = qs.get('msg', [None])[0]
            msg_tuple = None
            if msg_data:
                parts = msg_data.split(':', 1)
                msg_tuple = (parts[0], parts[1]) if len(parts) > 1 else ('ok', msg_data)
            if not fname:
                self.send_redirect('/admin/draft')
                return
            self.send_html(render_edit_page(fname, return_to, msg_tuple))
            return

        # 流量统计
        if path == '/admin/stats':
            self.send_html(render_stats_page())
            return

        # 静态文件
        return super().do_GET()

    # ---- POST ----
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        data = urllib.parse.parse_qs(body)

        # ---- 保存文章 ----
        if path == '/admin/save':
            content = data.get('content', [None])[0] or ''
            section = data.get('section', ['before-you-go'])[0]
            fname = data.get('filename', [None])[0] or data.get('path', [None])[0]
            return_to = data.get('return_to', ['draft'])[0]
            sub_category = data.get('sub_category', [''])[0] or ''

            if not fname:
                self.redirect_msg('/admin/draft', 'err', '文件名不能为空')
                return
            # fname 现在是文件夹名（如 mobile-payment-in-china），不需要 .html 后缀
            title = extract_title(content)
            # 编辑器中的绝对图片路径 → 相对路径（存到源文件）
            content = re.sub(r'/articles/' + re.escape(fname) + r'/images/', 'images/', content)
            ok, err = write_file(os.path.relpath(source_path(fname), SITE_DIR).replace('\\', '/'), content)
            if not ok:
                self.redirect_msg(f'/admin/edit?path={urllib.parse.quote(fname)}&from={return_to}', 'err', f'保存失败:{err}')
                return
            # 更新 manifest（新建草稿默认 zh_draft，已有文章保持原状态）
            manifest = get_manifest()
            old_status = manifest.get(fname, {}).get('status', 'zh_draft')
            # 废弃 zh_approved → 改为 zh_draft
            if old_status == 'zh_approved':
                old_status = 'zh_draft'
            set_article_manifest(fname, title or fname, section, old_status, sub_category)
            self.redirect_msg(f'/admin/edit?path={urllib.parse.quote(fname)}&from={return_to}', 'ok', '已保存成功')
            return

        # ---- 通过（待审草稿 → 套壳生成 en.html → en_draft，不 push） ----
        if path == '/admin/pass':
            fname = data.get('path', [None])[0]
            if not fname:
                self.redirect_msg('/admin/draft', 'err', '参数错误')
                return
            manifest = get_manifest()
            info = manifest.get(fname, {})
            section = info.get('section', 'before-you-go')
            title = info.get('title', '')
            sub_category = info.get('sub_category', '')

            # 读源文件
            sp = source_path(fname)
            src_content, err = read_file(os.path.relpath(sp, SITE_DIR).replace('\\', '/'))
            if not src_content:
                self.redirect_msg('/admin/draft', 'err', f'找不到源文件: {err}')
                return

            t = extract_title(src_content)
            if t:
                title = t
            body_content = strip_title(src_content)

            # 套模板（含面包屑），生成 en.html
            final_html = apply_master_template(body_content, title, '', section, sub_category)
            pp = published_path(fname)
            ok, err = write_file(os.path.relpath(pp, SITE_DIR).replace('\\', '/'), final_html)
            if not ok:
                self.redirect_msg('/admin/draft', 'err', f'套壳失败: {err}')
                return

            # manifest 改为 en_draft（不 push）
            set_article_manifest(fname, title, section, 'en_draft', sub_category)
            self.redirect_msg('/admin/draft', 'ok', f'「{title}」已通过，英文版已生成，请到待上站列表检查')
            return

        # ---- 上站（待上站 → git push → online） ----
        if path == '/admin/go-live':
            fname = data.get('path', [None])[0]
            if not fname:
                self.redirect_msg('/admin/publish', 'err', '参数错误')
                return
            manifest = get_manifest()
            info = manifest.get(fname, {})
            title = info.get('title', fname)
            section = info.get('section', 'before-you-go')
            sub_category = info.get('sub_category', '')

            # git push
            git_ok, git_err = git_push()

            if git_ok:
                set_article_manifest(fname, title, section, 'online', sub_category)
                # 自动更新 guide 列表页
                if sub_category:
                    ok_gl, err_gl = update_guide_listing(section, sub_category, fname, title)
                    if not ok_gl:
                        print(f'[complete] ⚠️ guide 列表更新失败: {err_gl}')
                # 更新 Cloudflare KV URL 映射（供 Worker API 使用）
                ok_map, err_map = update_kv_url_map()
                if not ok_map:
                    print(f'[kv] ⚠️ URL 映射更新失败: {err_map}')
                self.redirect_msg('/admin/publish', 'ok', f'「{title}」已上站，成功上线到网站')
            else:
                # push 失败，manifest 不动（保持 en_draft），文章不消失
                self.redirect_msg('/admin/publish', 'err', f'上站失败: {git_err}')
            return

        # ---- 撤回草稿（en_draft → zh_draft） ----
        if path == '/admin/withdraw':
            fname = data.get('path', [None])[0]
            if not fname:
                self.redirect_msg('/admin/publish', 'err', '参数错误')
                return
            manifest = get_manifest()
            info = manifest.get(fname, {})
            title = info.get('title', fname)
            section = info.get('section', 'before-you-go')
            sub_category = info.get('sub_category', '')

            info['status'] = 'zh_draft'
            manifest[fname] = info
            save_manifest(manifest)
            self.redirect_msg('/admin/draft', 'ok', f'「{title}」已撤回草稿，可重新编辑')
            return

        # ---- 重新发布（已上站文章） ----
        if path == '/admin/republish':
            fname = data.get('path', [None])[0]
            section = data.get('section', [None])[0] or 'before-you-go'
            if not fname:
                self.redirect_msg(f'/admin/done/{section}', 'err', '参数错误')
                return
            manifest = get_manifest()
            info = manifest.get(fname, {})
            title = info.get('title', '')
            sub_category = info.get('sub_category', '')

            sp = source_path(fname)
            src_content, err = read_file(os.path.relpath(sp, SITE_DIR).replace('\\', '/'))
            if not src_content:
                pp = published_path(fname)
                pub_content, err = read_file(os.path.relpath(pp, SITE_DIR).replace('\\', '/'))
                if not pub_content:
                    self.redirect_msg(f'/admin/done/{section}', 'err', f'找不到文件:{err}')
                    return
                m = re.search(r'<div class="article">(.*?)</div>\s*</div>\s*<footer', pub_content, re.DOTALL)
                body = m.group(1).strip() if m else pub_content
                body_content = body
            else:
                t = extract_title(src_content)
                if t:
                    title = t
                body_content = strip_title(src_content)

            final_html = apply_master_template(body_content, title, '', section, sub_category)
            pp = published_path(fname)
            write_file(os.path.relpath(pp, SITE_DIR).replace('\\', '/'), final_html)
            git_ok, git_err = git_push()
            set_article_manifest(fname, title, section, 'online', sub_category)

            # 自动更新 guide 列表页（确保链接存在）
            if sub_category:
                ok_gl, err_gl = update_guide_listing(section, sub_category, fname, title)
                if not ok_gl:
                    print(f'[republish] ⚠️ guide 列表更新失败: {err_gl}')

            if git_ok:
                self.redirect_msg(f'/admin/done/{section}', 'ok', f'「{title}」已重新发布到线上')
            else:
                self.redirect_msg(f'/admin/done/{section}', 'err', f'重新发布失败:{git_err}')
            return

        # ---- 删除 ----
        if path == '/admin/delete':
            fname = data.get('path', [None])[0]
            if not fname:
                self.redirect_msg('/admin/draft', 'err', '参数错误')
                return
            manifest = get_manifest()
            info = manifest.get(fname, {})
            title = info.get('title', fname)
            section = info.get('section', 'before-you-go')
            sub_category = info.get('sub_category', '')
            title = info.get('title', fname)

            # 先从 guide 列表页移除链接
            if sub_category:
                ok_gl, err_gl = update_guide_listing(section, sub_category, fname, title, remove=True)
                if not ok_gl:
                    print(f'[delete] ⚠️ guide 列表移除链接失败: {err_gl}')

            # 删除整个文章文件夹
            import shutil
            ad = article_dir(fname)
            if os.path.exists(ad):
                shutil.rmtree(ad)
            remove_article_manifest(fname)
            git_ok, git_err = git_push()

            if git_ok:
                self.redirect_msg(f'/admin/done/{section}', 'ok', f'「{title}」已删除')
            else:
                self.redirect_msg(f'/admin/done/{section}', 'err', f'删除但同步失败:{git_err}')
            return

        self.send_redirect('/admin/draft')

# =====================================================================
#  启动
# =====================================================================
if __name__ == '__main__':
    print(f'管理后台 v4.0 — http://localhost:{PORT}/admin')
    with socketserver.ThreadingTCPServer(('', PORT), AdminHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n已停止')
