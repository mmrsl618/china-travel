# Footer 位置问题 — 血泪经验总结

最后更新：2026-06-20

## 背景

文章详情页的 footer 位置问题前后出现 20+ 次，每次修复 30 分钟到数小时不等。根因每次不同，但都跟同一套 CSS/HTML 结构有关。本文记录所有已知的坑、原理和预防方案。

## 根本原因链

### 1. 文章内容非常长（9000+px）
- 长文章自然把 footer 推到页面末尾
- 用户滚动到文章底部才能看到 footer
- 要求：**页面本身不滚动，footer 始终在底部可见，只有中间内容区独立滚动**

### 2. 多层嵌套导致布局互相影响
文章页面的 HTML 结构经过多次迭代：

```
版本A（初始）: body > .article-page > header + .article-page-inner + footer
版本B（去外层）: body > header + .article-page-inner + footer
版本C（加body类）: body.article-page > header + .article-page-inner + footer
```

每次改结构，CSS 选择器也跟着变，漏一个就崩。

### 3. Flexbox 的隐藏规则
Flexbox 有多条影响元素尺寸的规则，不同组合结果不同：

| 规则 | 效果 | 坑点 |
|------|------|------|
| `flex: 1` | 弹性增长 | 父容器如果也在增长，它会跟着长 |
| `min-height: auto` | flex 项默认不能小于内容高度 | 加了 `overflow-y: auto` 也不生效，必须显式设 `min-height: 0` |
| `min-height: 100vh` vs `height: 100vh` | 前者允许撑大，后者固定 | 前者是「至少 100vh」，内容长时 body 继续撑大 |
| `margin-top: auto` | 推到底部 | 和 `flex-grow: 1` 同时存在时可能被覆盖 |

### 4. 提取函数带入了旧结构标签
- `extract_article_content()` 从 `</header>` 取到 `<footer>`
- 旧文章的结构标签（`<div class="article-page-inner">`、`</div><!-- /article-page -->` 等）也被提取
- 塞进新模板后造成**双重嵌套**，布局全乱

### 5. 多文件维护
页面的最终渲染效果由 3 个文件共同决定：
- `templates/article-master.html` — HTML 结构
- `style.css` — 所有样式
- `admin_server.py` — 提取+套壳逻辑

改了一个没改另外两个就出问题。

## Footer 正确配置（最终定版）

### HTML 结构（`templates/article-master.html`）
```html
<body class="article-page">
  <header>...</header>
  <div class="article-page-inner">
    <div class="article">__CONTENT__</div>
  </div>
  <footer>...</footer>
  <nav class="bottom-nav">...</nav>
  <script src="../js/main.js"></script>
</body>
```

**要点：** footer 是 body 的直接子元素，和 `article-page-inner` 平级。不要让 footer 嵌在任何容器里。

### CSS（`style.css`）
```css
/* ===== body 高度锁死为视口高度 ===== */
body.article-page {
  height: 100vh;            /* 锁死，别用 min-height（允许撑大就没用了） */
  background: #fff;
}

/* ===== 内容区独立滚动 ===== */
.article-page-inner {
  flex: 1;                  /* 撑满剩余空间 */
  min-height: 0;            /* ⚠️ 必须！覆盖 flex 默认 min-height: auto */
  overflow-y: auto;         /* 内容太长时独立滚动 */
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
}

/* ===== footer ===== */
footer {
  flex-shrink: 0;           /* 防止 footer 被挤压 */
  background: var(--dark);
  color: #888;
  text-align: center;
  padding: 1.25rem 2rem;
  font-size: 0.85rem;
}

/* ===== 移动端隐藏 footer ===== */
@media (max-width: 768px) {
  footer { display: none; }           /* 手机端用 bottom-nav 代替 */
  body { padding-bottom: 50px; }      /* 给 bottom-nav 让位 */
}
```

**关键配合（缺一不可）：**
- `body.article-page { height: 100vh }` + `body { display: flex; flex-direction: column }` → body 高度锁死为视口高度，子项垂直排列，页面整体不滚动
- `.article-page-inner { flex: 1; min-height: 0; overflow-y: auto }` → 内容区撑满剩余空间，文章太长时在内容区内部独立滚动

### 提取函数（`admin_server.py`）
```python
# 提取正文后必须清理旧结构标签
content = re.sub(r'\s*<div\s+class="article-page">\s*', '', content)
content = re.sub(r'\s*<div\s+class="article-page-inner">\s*', '', content)
content = re.sub(r'\s*</div>\s*<!--\s*/article-page-inner\s*-->\s*', '', content)
content = re.sub(r'\s*</div>\s*<!--\s*/article-page\s*-->\s*', '', content)
```

## 经验总结

### ⚠️ 核心原则：不动 footer 相关代码

**不要猜测，直接用验证过的方案。** Footer 问题是经典「容易改坏」场景。

### ❌ 绝对别做的事

| 操作 | 后果 |
|------|------|
| 改模板的 HTML 结构层次（移 wrapper、改嵌套） | 所有 CSS 选择器可能失效 |
| 在模板里加内联 `<style>` | 和 style.css 冲突，搜索框/ footer 全跑偏 |
| 改 body 的 height 策略（min-height ↔ height 之间切换） | 整页布局都变 |
| 动 footer 的 flex 属性（删 flex-shrink、改 position） | 位置错乱 |
| 改提取函数的切割范围（从不同位置切 content） | 可能带进残留标签 |
| 修改 `.article-page-inner` 的 overflow 策略 | 滚动行为改变 |

### ✅ 排查顺序

发现 footer 异常后，**别急着改代码**，按这个顺序查：

```
□ 1. 浏览器打开页面，打开 DevTools
□ 2. 检查 body 的实际高度（document.body.scrollHeight）
     → 如果 > viewport 高度，说明 body 被撑大了
     → 修复：body.article-page 必须是 height: 100vh（不是 min-height）
□ 3. 检查 .article-page-inner 的 computed style
     → flex: 1 1 0% ?  min-height: 0px ?  overflow-y: auto ?
     → 如果 scrollHeight == clientHeight → overflow 没生效，检查 min-height
□ 4. 检查 footer 的 computed style
     → display: block ? position: static ?
     → 如果是 display: none → 检查是否在 ≤768px media query 下
□ 5. 检查页面 HTML 里有没有结构嵌套
     → 看 <div class="article-page-inner"> 是否重复出现
     → 看有没有 <!-- /article-page --> 等残留注释
□ 6. 检查模板 CSS 链接版本号
     → style.css?v=3（每改一次 CSS 加 1）
□ 7. 检查提取逻辑
     → extract_article_content 是否清理了旧结构标签
```

### 症状 → 根因速查

| 症状 | 最可能的根因 |
|------|-------------|
| Footer 在视口底部但看不见（需要滑到底） | body 被内容撑大 → `height` vs `min-height` |
| Footer 显示正常但文章内容不会独立滚动 | `.article-page-inner` 缺 `min-height: 0` |
| Footer 完全不存在 HTML 里 | 提取时 footer 被截掉了 |
| Footer 在 HTML 里但看不见（桌面端） | 检查 `<footer>` 标签是否完整 |
| Footer 在 HTML 里但看不见（手机端） | ≤768px media query 中 `footer { display: none }`，正常设计 |
| 搜索框在导航栏最右侧 | 模板有内联 CSS 覆盖了 style.css |
| 页面布局全乱，结构异常 | 提取时带入了旧结构标签，造成双重嵌套 |

## 维护规则

以下 3 个文件必须一起维护，改了一个要检查另外两个：

```
templates/article-master.html  ← 页面骨架（body class 不能丢）
style.css                      ← 三个关键规则（body height / article-page-inner / footer）
admin_server.py                ← 提取函数要清理结构标签
```

**修改任何文件前，先看本文档。**
