---
title: GitHub Pages + Jekyll 搭建项目进度管理站点全教程（附踩坑记录）
tags: [GitHub Pages, Jekyll, 项目进度管理, 静态网站, 仪表盘]
categories: [前端, 工具]
---

# GitHub Pages + Jekyll 搭建项目进度管理站点全教程（附踩坑记录）

## 一、前言

在研发团队中，项目进度的透明化管理是提升协作效率的关键一环。无论是向领导汇报，还是团队内部同步，一个直观、专业的进度看板都能大幅降低沟通成本。

本文将手把手教你基于 **GitHub Pages + Jekyll** 搭建一套零成本、易维护的项目进度汇报站点，涵盖以下能力：

- 📊 **仪表盘首页**：关键指标一目了然（阶段进度、完成百分比、待解决问题数）
- 🔄 **研发流程时间线**：多阶段可视化展示，支持状态标记
- 📝 **周报系统**：Markdown 编写，自动归档，历史可查
- 🐛 **问题跟踪**：问题登记、状态管理、解决方案记录
- 🎨 **现代化 UI**：深色科技风主题，滚动动画，响应式布局

> 本文基于实际项目经验撰写，所有代码均可直接复用，并附上开发过程中遇到的典型问题与解决方案。

---

## 二、为什么选择 GitHub Pages + Jekyll？

在开始之前，先聊聊为什么这套方案适合做项目进度管理：

| 对比维度 | GitHub Pages + Jekyll | 传统后端方案（如 Django / Spring） | 在线协作工具（如 Notion / 飞书） |
|----------|----------------------|-----------------------------------|--------------------------------|
| 部署成本 | 免费，无需服务器 | 需要服务器 + 域名 + 运维 | 免费或付费订阅 |
| 学习门槛 | 前端基础 + Markdown 即可 | 需要全栈能力 | 零门槛 |
| 定制程度 | 完全自定义 HTML/CSS | 完全自定义 | 受平台限制 |
| 版本管理 | Git 天然支持，历史可追溯 | 需额外配置 | 平台自带 |
| 数据安全 | 数据在 GitHub，可控 | 自行管理 | 依赖第三方平台 |
| 自动化 | `git push` 即部署 | 需要 CI/CD 配置 | 无需操作 |
| 领导查看 | 浏览器打开链接即可 | 需要部署公网 | 需要账号权限 |

**适用场景**：研发团队内部进度同步、向领导定期汇报、开源项目进度展示。

---

## 三、环境准备

### 3.1 安装 Ruby 与 Jekyll

Jekyll 基于 Ruby，需要先安装 Ruby 环境。

#### macOS

```bash
# macOS 自带 Ruby，但版本较旧，建议通过 Homebrew 安装新版
brew install ruby
echo 'export PATH="/usr/local/opt/ruby/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 安装 Jekyll 和 Bundler
gem install jekyll bundler
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ruby-full build-essential zlib1g-dev

# 配置 gem 安装路径（避免权限问题）
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

gem install jekyll bundler
```

#### Windows

Windows 用户推荐使用 **WSL2（Windows Subsystem for Linux）**，在 WSL 中按上述 Linux 步骤安装。直接使用 Windows 版 Ruby 可能会遇到编码和路径兼容性问题。

### 3.2 验证安装

```bash
ruby -v     # 应输出 Ruby 3.x
jekyll -v   # 应输出 Jekyll 4.x
```

### 3.3 创建 Jekyll 项目

```bash
# 创建新站点
jekyll new my-project-site
cd my-project-site

# 本地启动预览
bundle exec jekyll serve
# 打开浏览器访问 http://localhost:4000
```

此时你会看到一个默认的 Jekyll 博客主题页面。接下来我们将其改造为项目进度管理站点。

### 3.4 初始化 Git 仓库

```bash
git init
git add .
git commit -m "初始化 Jekyll 项目"
```

---

## 四、项目目录结构设计

合理的目录结构是项目可维护性的基础。以下是推荐的结构：

```
.
├── _config.yml              # Jekyll 全局配置（站点信息、集合定义、默认布局）
├── _layouts/                # 页面布局模板
│   ├── default.html         # 基础布局：导航栏 + 内容区 + 页脚
│   ├── post.html            # 周报详情页布局
│   ├── issue.html           # 问题详情页布局
│   └── process.html         # 研发阶段详情页布局
├── _includes/               # 可复用的 HTML 组件
│   ├── nav.html             # 顶部导航栏
│   ├── footer.html          # 底部版权信息
│   └── status-badge.html    # 状态徽章组件（进行中/已完成等）
├── _sass/                   # SCSS 样式源文件目录
│   └── main.scss            # 主样式文件（变量、组件、布局、动画）
├── assets/
│   └── css/
│       └── style.scss       # 样式入口文件（仅包含 front matter + @import）
├── _posts/                  # Jekyll 内置集合：博客/周报文章
│   └── weekly/              # 可选子目录，按周存放
│       ├── 2026-05-23-week01.md
│       └── 2026-05-30-week02.md
├── _issues/                 # 自定义集合：问题跟踪记录
│   ├── ISSUE-001.md
│   └── ISSUE-002.md
├── process/                 # 研发阶段详情页
│   ├── 01-需求分析.md
│   ├── 02-方案设计.md
│   ├── 03-硬件选型.md
│   ├── 04-原型开发.md
│   ├── 05-软件开发.md
│   ├── 06-集成测试.md
│   └── 07-部署交付.md
├── index.md                 # 首页（仪表盘）
├── README.md                # 仓库说明
└── .gitignore               # Git 忽略规则
```

**设计要点**：

- `_posts/` 是 Jekyll 内置集合，天然支持按日期归档，非常适合周报场景
- `_issues/` 是自定义集合（在 `_config.yml` 中声明），用于问题跟踪这类非时间线内容
- `process/` 直接放在项目根目录，利用 Jekyll 的 `site.pages` 变量遍历
- `_sass/` 存放 SCSS 源文件，由 `assets/css/style.scss` 统一引入

---

## 五、核心配置详解：`_config.yml`

`_config.yml` 是 Jekyll 的「控制中心」，所有全局设置都在这里定义：

```yaml
# ===== 站点基本信息 =====
title: 项目进度看板
description: 研发进度实时汇报平台
url: "https://你的用户名.github.io"       # GitHub Pages 域名
baseurl: "/你的仓库名"                    # 仓库名作为子路径（重要！）

# ===== Markdown 渲染引擎 =====
markdown: kramdown
kramdown:
  input: GFM                             # 支持 GitHub Flavored Markdown（表格、任务列表等）

# ===== 自定义集合（Collections） =====
collections:
  issues:                                # 声明名为 "issues" 的集合
    output: true                         # 为每个条目生成独立页面
    permalink: /issues/:name/            # 自定义 URL 格式

# ===== 默认 Front Matter =====
defaults:
  - scope:
      path: ""                           # 作用于所有 _posts 目录下的文件
      type: "posts"
    values:
      layout: "post"                     # 自动使用 post 布局
      category: "weekly"
  - scope:
      path: ""
      type: "issues"                     # 作用于 _issues 集合
    values:
      layout: "issue"                    # 自动使用 issue 布局
  - scope:
      path: "process"                    # 作用于 process/ 目录下的所有文件
    values:
      layout: "process"                  # 自动使用 process 布局

# ===== 插件 =====
plugins:
  - jekyll-seo-tag                       # SEO 优化插件（GitHub Pages 官方支持）
```

**配置详解**：

| 配置项 | 类型 | 说明 | 注意事项 |
|--------|------|------|----------|
| `title` | 字符串 | 站点标题，会出现在浏览器标签页和 SEO 信息中 | 修改后需重启 Jekyll |
| `url` | 字符串 | 站点的完整域名 | 部署到 GitHub Pages 时填写 `https://用户名.github.io` |
| `baseurl` | 字符串 | 子路径，值为仓库名称 | **项目站点必须设置**，否则部署后链接全部 404 |
| `collections` | 对象 | 自定义内容集合，类似 `_posts` 但可自定义行为 | `output: true` 才会生成页面 |
| `defaults` | 数组 | 为特定路径/类型的文件自动设置默认 Front Matter | 减少重复编写，提高效率 |
| `plugins` | 数组 | 启用的 Jekyll 插件 | GitHub Pages 仅支持白名单插件 |

---

## 六、SCSS 样式系统搭建

### 6.1 为什么用 SCSS？

SCSS 是 CSS 的超集，提供了变量、嵌套、混入（Mixin）、继承等功能。对于需要大量自定义样式的仪表盘页面，SCSS 能显著提升开发效率和代码可维护性。

### 6.2 入口文件：`assets/css/style.scss`

这个文件本身不写样式，仅作为「入口」引入 `_sass/` 下的模块：

```scss
---
---
@import "main";
```

> **注意**：两个 `---` 是 Jekyll 的 Front Matter 标记。即使没有实际 YAML 内容，也必须保留，否则 Jekyll 不会处理该文件。

### 6.3 主样式文件结构：`_sass/main.scss`

建议按以下顺序组织样式代码：

```scss
// ===== 1. 变量定义 =====
$primary: #00e5ff;
$primary-dark: #00b8d4;
$primary-glow: rgba(0, 229, 255, 0.25);
$accent: #ff6b35;
$bg: #050a14;
$bg-card: rgba(12, 22, 42, 0.7);
$border: rgba(0, 229, 255, 0.1);
$text: #e0e6f0;
$text-muted: #6b7fa3;
// ... 更多变量

// ===== 2. 全局 Reset 与基础样式 =====
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: $bg;
  color: $text;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

// ===== 3. 背景装饰 =====
body::before {
  content: '';
  position: fixed; inset: 0; z-index: -2;
  background:
    radial-gradient(ellipse 800px 600px at 20% 20%, rgba(0, 229, 255, 0.04), transparent),
    radial-gradient(ellipse 600px 500px at 80% 80%, rgba(255, 107, 53, 0.03), transparent),
    $bg;
}

// ===== 4. 组件样式 =====
// 4.1 导航栏
.navbar { /* ... */ }

// 4.2 状态卡片
.status-card { /* ... */ }

// 4.3 进度条
.progress-bar { /* ... */ }

// 4.4 时间线
.timeline { /* ... */ }

// 4.5 列表项
.item-row { /* ... */ }

// 4.6 徽章
.badge { /* ... */ }

// ===== 5. 页面布局 =====
.hero { /* ... */ }
.section { /* ... */ }

// ===== 6. 动画 =====
@keyframes shimmer { /* ... */ }
@keyframes activePulse { /* ... */ }

// ===== 7. 滚动动画 =====
.fade-in {
  opacity: 0; transform: translateY(40px);
  transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  &.visible { opacity: 1; transform: translateY(0); }
}

// ===== 8. 响应式 =====
@media (max-width: 768px) { /* ... */ }
@media (max-width: 480px) { /* ... */ }
```

### 6.4 深色科技风配色方案

| 用途 | 色值 | SCSS 变量 | 说明 |
|------|------|-----------|------|
| 主色调 | `#00e5ff` | `$primary` | 青色，用于高亮文字、进度条、边框 |
| 强调色 | `#ff6b35` | `$accent` | 橙色，用于进度条渐变、警示元素 |
| 背景色 | `#050a14` | `$bg` | 深蓝色，营造科技感氛围 |
| 卡片背景 | `rgba(12,22,42,0.7)` | `$bg-card` | 半透明玻璃态效果 |
| 文字色 | `#e0e6f0` | `$text` | 浅灰白，保证可读性 |
| 辅助文字 | `#6b7fa3` | `$text-muted` | 蓝灰色，用于描述性文字 |

### 6.5 核心组件样式示例

#### 状态卡片（毛玻璃效果）

```scss
.status-card {
  position: relative; overflow: hidden;
  background: rgba(8, 16, 32, 0.6);
  backdrop-filter: blur(16px);            // 毛玻璃效果
  border: 1px solid rgba(0, 229, 255, 0.1);
  border-radius: 16px;
  padding: 28px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);

  // 顶部渐变装饰线
  &::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, $primary, transparent);
    opacity: 0; transition: opacity 0.4s;
  }

  &:hover {
    border-color: rgba(0, 229, 255, 0.35);
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4), 0 0 24px $primary-glow;
    &::before { opacity: 1; }
  }
}
```

#### 进度条（带流光动画）

```scss
.progress-bar {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 50px;
  height: 8px;
  overflow: hidden;

  .progress-fill {
    height: 100%; border-radius: 50px;
    background: linear-gradient(90deg, $primary, $accent);
    transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 12px rgba(0, 229, 255, 0.25);

    // 流光效果
    &::after {
      content: ''; position: absolute; inset: 0;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      animation: shimmer 2s infinite;
    }
  }
}

@keyframes shimmer {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
```

---

## 七、布局模板设计

### 7.1 基础布局：`_layouts/default.html`

所有页面都继承这个基础布局，提供导航栏和页脚：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% if page.title %}{{ page.title }} · {% endif %}{{ site.title }}</title>
  <link rel="stylesheet" href="{{ '/assets/css/style.css' | relative_url }}">
  {% seo %}
</head>
<body>
  {% include nav.html %}
  <main style="padding-top: 68px;">
    {{ content }}
  </main>
  {% include footer.html %}

  <script>
    // 滚动淡入动画
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('visible');
      });
    }, { threshold: 0.08 });
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
  </script>
</body>
</html>
```

**关键点说明**：

| 代码 | 作用 |
|------|------|
| `{% if page.title %}` | 如果子页面有标题，显示为 `子标题 · 站点标题`，否则只显示站点标题 |
| `{% seo %}` | `jekyll-seo-tag` 插件提供的标签，自动生成 SEO 元数据 |
| `relative_url` 过滤器 | 自动拼接 `baseurl`，确保部署后路径正确 |
| `{% include nav.html %}` | 引入可复用组件，保持 DRY 原则 |
| `{{ content }}` | Jekyll 占位符，渲染子页面的实际内容 |
| `IntersectionObserver` | 原生 JS API，实现滚动到视口时触发淡入动画 |

### 7.2 导航栏组件：`_includes/nav.html`

```html
<nav class="navbar">
  <div class="navbar-inner">
    <a href="{{ '/' | relative_url }}" class="logo">
      <span class="icon">📊</span> 项目进度看板
    </a>
    <ul class="nav-links">
      <li><a href="{{ '/' | relative_url }}#overview">状态总览</a></li>
      <li><a href="{{ '/' | relative_url }}#process">研发流程</a></li>
      <li><a href="{{ '/' | relative_url }}#weekly">周报</a></li>
      <li><a href="{{ '/' | relative_url }}#issues">问题跟踪</a></li>
    </ul>
  </div>
</nav>
```

> 锚点链接（`#overview` 等）配合首页对应区域的 `id` 属性实现页内跳转。

### 7.3 状态徽章组件：`_includes/status-badge.html`

```html
{% if include.status == "open" %}
  <span class="badge badge-danger">● 未解决</span>
{% elsif include.status == "closed" %}
  <span class="badge badge-success">● 已解决</span>
{% elsif include.status == "进行中" %}
  <span class="badge badge-info">● 进行中</span>
{% elsif include.status == "已完成" %}
  <span class="badge badge-success">● 已完成</span>
{% else %}
  <span class="badge badge-muted">● {{ include.status }}</span>
{% endif %}
```

使用方式：

```liquid
{% include status-badge.html status=issue.status %}
```

通过 `include.status` 接收传入的状态值，根据值渲染不同颜色的徽章。

---

## 八、功能模块详细实现

### 8.1 首页仪表盘

首页是站点的核心，需要汇总所有关键信息。推荐使用 `index.md`（而非 `index.html`），这样既能享受 Markdown 的简洁，又能嵌入 Liquid 模板和 HTML：

```markdown
---
layout: default
title: 项目进度总览
---

<!-- Hero 区域 -->
<section class="hero">
  <div class="hero-content">
    <span class="hero-badge">R&D PROGRESS DASHBOARD</span>
    <h1 class="hero-title">项目进度看板</h1>
    <p class="hero-desc">实时掌握研发动态，数据驱动项目管理</p>
    
    <!-- 关键指标 -->
    <div class="hero-stats">
      {% assign active_phase = site.pages | where: 'status', '进行中' | first %}
      <div class="stat-item">
        <div class="stat-value">{{ active_phase.phase | default: "—" }}/7</div>
        <div class="stat-label">当前阶段</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{% assign completed = site.pages | where: 'status', '已完成' | size %}{{ completed | times: 100 | divided_by: 7 }}%</div>
        <div class="stat-label">整体进度</div>
      </div>
      <div class="stat-item">
        {% assign open_issues = site.issues | where: 'status', 'open' %}
        <div class="stat-value">{{ open_issues.size }}</div>
        <div class="stat-label">待解决问题</div>
      </div>
    </div>
  </div>
</section>
```

**Liquid 技巧解析**：

| 代码 | 说明 |
|------|------|
| `{% assign active_phase = site.pages \| where: 'status', '进行中' \| first %}` | 从所有页面中找出状态为「进行中」的第一个，赋值给变量 |
| `{% assign completed = site.pages \| where: 'status', '已完成' \| size %}` | 统计已完成页面数量 |
| `{{ completed \| times: 100 \| divided_by: 7 }}` | Liquid 数学运算：计算完成百分比 |
| `{% assign open_issues = site.issues \| where: 'status', 'open' %}` | 从自定义集合中筛选未解决问题 |

### 8.2 状态卡片网格

用四张卡片展示项目的核心 KPI：

```html
<div class="status-cards fade-in">
  <!-- 当前阶段 -->
  <div class="status-card">
    <div class="card-label">当前阶段</div>
    <div class="card-value" style="font-size: 1.4rem;">
      {% assign current = site.pages | where: 'status', '进行中' | first %}
      {{ current.title | default: "未开始" }}
    </div>
    <div class="card-sub">阶段 {{ current.phase | default: "—" }}/7</div>
  </div>

  <!-- 整体进度 -->
  <div class="status-card">
    <div class="card-label">整体进度</div>
    <div class="card-value">
      {% assign done = site.pages | where: 'status', '已完成' | size %}
      {{ done | times: 100 | divided_by: 7 }}%
    </div>
    <div class="progress-bar" style="margin-top: 12px;">
      <div class="progress-fill" style="width: {{ done | times: 100 | divided_by: 7 }}%;"></div>
    </div>
  </div>

  <!-- 待解决问题 -->
  <div class="status-card">
    <div class="card-label">待解决问题</div>
    <div class="card-value">{{ open_issues.size }}</div>
    <div class="card-sub">{{ site.issues.size }} 个问题总计</div>
  </div>

  <!-- 周报数量 -->
  <div class="status-card">
    <div class="card-label">周报数量</div>
    <div class="card-value">{{ site.posts.size }}</div>
    <div class="card-sub">持续更新中</div>
  </div>
</div>
```

### 8.3 研发流程时间线

7 个研发阶段以横向时间线展示，按状态渲染不同样式：

```html
<div class="timeline fade-in">
  {% assign phases = site.pages | where_exp: "item", "item.phase" | sort: "phase" %}
  {% for p in phases %}
    {% if p.status == "已完成" %}
      {% assign step_class = "completed" %}
    {% elsif p.status == "进行中" %}
      {% assign step_class = "active" %}
    {% else %}
      {% assign step_class = "" %}
    {% endif %}

    <a href="{{ p.url | relative_url }}" class="timeline-step {{ step_class }}">
      <div class="step-dot">{{ p.icon }}</div>
      <div class="step-label">{{ p.title }}</div>
    </a>
  {% endfor %}
</div>
```

**实现要点**：

- `where_exp` 过滤器筛选出 front matter 中包含 `phase` 字段的页面
- `sort: "phase"` 按阶段编号排序
- 根据 `status` 字段动态设置 CSS class（`completed` / `active`）
- 使用 `<a>` 标签包裹每个阶段，实现点击跳转到详情页

### 8.4 周报列表

```html
<ul class="item-list fade-in">
  {% for post in site.posts limit: 5 %}
    <a href="{{ post.url | relative_url }}" class="item-row">
      <span class="item-date">{{ post.date | date: "%m-%d" }}</span>
      <span class="item-title">{{ post.title }}</span>
      <span class="item-meta">{{ post.progress }}%</span>
    </a>
  {% endfor %}
</ul>
```

`limit: 5` 限制只显示最近 5 篇，避免列表过长。

### 8.5 问题跟踪列表

```html
<ul class="item-list fade-in">
  {% for issue in site.issues %}
    <a href="{{ issue.url | relative_url }}" class="item-row">
      <span class="item-date">{{ issue.date | date: "%m-%d" }}</span>
      <span class="item-title">{{ issue.title }}</span>
      {% include status-badge.html status=issue.status %}
    </a>
  {% endfor %}
</ul>
```

### 8.6 功能模块展示

对于产品型项目，可以用卡片网格展示各功能模块的技术路线：

```html
<div class="features-grid fade-in">
  {% for module in page.modules %}
    <div class="feature-card">
      <span class="card-icon">{{ module.icon }}</span>
      <h3>{{ module.name }}</h3>
      <p class="sub-features">{{ module.features }}</p>
      <span class="tech-tag">{{ module.tech }}</span>
    </div>
  {% endfor %}
</div>
```

模块数据可以在 `index.md` 的 Front Matter 中集中定义：

```yaml
modules:
  - icon: "📡"
    name: "模块A"
    features: "功能描述1 · 功能描述2"
    tech: "核心技术"
  - icon: "🔋"
    name: "模块B"
    features: "功能描述1 · 功能描述2"
    tech: "核心技术"
```

---

## 九、Collections 自定义集合详解

### 9.1 为什么需要自定义集合？

Jekyll 内置的 `_posts` 集合天然与时间绑定，适合周报这种按时序排列的内容。但对于问题跟踪这类「非时间线」内容，自定义集合更为灵活。

### 9.2 集合配置

在 `_config.yml` 中声明：

```yaml
collections:
  issues:
    output: true             # 是否生成独立页面
    permalink: /issues/:name/ # 自定义 URL 模式
```

### 9.3 集合文件结构

集合文件存放在 `_issues/` 目录下，命名格式自由（不同于 `_posts` 必须包含日期）：

```
_issues/
├── ISSUE-001.md
├── ISSUE-002.md
└── ISSUE-003.md
```

每个文件的 Front Matter：

```yaml
---
title: 问题标题（简要描述）
status: open           # open / closed
severity: 高           # 高 / 中 / 低
date: 2026-05-23
resolution_date: 2026-06-01    # 解决后填写
resolution: 具体的解决方案描述   # 解决后填写
---

## 问题描述

详细说明问题的现象、复现步骤等。

## 影响范围

说明该问题对项目的影响。

## 解决思路

记录排查过程和最终采用的方案。
```

### 9.4 集合详情页布局：`_layouts/issue.html`

```html
---
layout: default
---

<div class="container">
  <div class="section">
    <a href="{{ '/' | relative_url }}#issues" class="page-back">&larr; 返回问题列表</a>

    <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 1rem;">
      <h1 class="page-title" style="margin-bottom: 0;">{{ page.title }}</h1>
      {% include status-badge.html status=page.status %}
    </div>

    <div class="page-meta">
      <div class="meta-item">
        <div class="meta-label">严重程度</div>
        <div class="meta-value">{{ page.severity }}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">发现日期</div>
        <div class="meta-value">{{ page.date | date: "%Y-%m-%d" }}</div>
      </div>
      {% if page.resolution_date %}
      <div class="meta-item">
        <div class="meta-label">解决日期</div>
        <div class="meta-value">{{ page.resolution_date | date: "%Y-%m-%d" }}</div>
      </div>
      {% endif %}
    </div>

    <div class="post-content">
      {{ content }}
    </div>

    {% if page.resolution %}
    <div class="info-panel panel-success" style="margin-top: 2rem;">
      <h3>✅ 解决方案</h3>
      <p>{{ page.resolution }}</p>
    </div>
    {% endif %}
  </div>
</div>
```

---

## 十、周报系统设计

### 10.1 周报文件命名

`_posts/` 目录下文件必须遵循 `YYYY-MM-DD-title.md` 格式。建议使用子目录组织：

```
_posts/weekly/
├── 2026-05-23-week01.md
├── 2026-05-30-week02.md
└── 2026-06-06-week03.md
```

### 10.2 Front Matter 模板

```yaml
---
title: 第N周 · 本周主题
date: 2026-06-06
progress: 35              # 本周完成后的整体进度（0-100）
issues:
  - 遇到的问题描述 1
  - 遇到的问题描述 2
next_plan:
  - 下周计划事项 1
  - 下周计划事项 2
---

## 本周完成

- [x] 完成事项 1
- [x] 完成事项 2
- [ ] 未完成事项（迁移到下周）

## 详细进展

### 模块A

具体进展描述...

### 模块B

具体进展描述...

## 风险与应对

如有潜在风险，在此记录。
```

### 10.3 在首页展示周报进度

```liquid
{% assign latest = site.posts | first %}
{% if latest %}
  <div class="status-card">
    <div class="card-label">最新周报</div>
    <div class="card-value">{{ latest.title }}</div>
    <div class="progress-bar" style="margin-top: 12px;">
      <div class="progress-fill" style="width: {{ latest.progress }}%;"></div>
    </div>
  </div>
{% endif %}
```

---

## 十一、部署上线流程

### 11.1 推送代码到 GitHub

首先在 GitHub 上创建一个新仓库（建议命名与本地项目一致），然后关联推送：

```bash
# 关联远程仓库（使用 SSH）
git remote add origin git@github.com:<用户名>/<仓库名>.git

# 添加并提交所有文件
git add .
git commit -m "初始化项目进度管理站点"

# 推送到 GitHub
git push -u origin master
```

### 11.2 启用 GitHub Pages

1. 打开仓库页面，点击顶部 **Settings** 选项卡
2. 左侧导航栏找到 **Pages**（在 "Code and automation" 分组下）
3. **Source** 下拉选择 `Deploy from a branch`
4. **Branch** 选择 `master`（或 `main`），目录保持 `/ (root)`
5. 点击 **Save** 按钮

### 11.3 等待构建

保存后 GitHub 会自动触发 Jekyll 构建。你可以：

- 前往仓库 **Actions** 标签页查看 `pages-build-deployment` 工作流的实时日志
- 构建成功后，页面顶部会显示部署地址：`https://<用户名>.github.io/<仓库名>/`
- 首次构建通常需要 **30 秒到 2 分钟**

### 11.4 日常更新流程

每次更新内容后，只需三步：

```bash
git add .
git commit -m "更新第X周周报 / 关闭 ISSUE-00X / 更新XX阶段进度"
git push
```

推送后 GitHub Pages 自动重新构建部署，无需任何额外操作。

---

## 十二、踩坑记录（重点收藏）

### 🕳️ 坑 1：SCSS 引用路径错误 —— 样式完全丢失

**严重程度**：⭐⭐⭐⭐⭐（必踩）

**现象**：部署后打开页面，所有文字挤在左上角，没有任何样式，就像纯文本 HTML。

**根因分析**：

Jekyll 处理 SCSS 的流程是：
1. 读取 `assets/css/style.scss`（源码）
2. 通过 `@import "main"` 找到 `_sass/main.scss`
3. 编译为标准 CSS
4. 输出到 `_site/assets/css/style.css`（构建产物）

但如果你在 HTML 模板中引用的是 `.scss` 路径：

```html
<!-- ❌ 错误：引用源码路径 -->
<link rel="stylesheet" href="{{ '/assets/css/style.scss' | relative_url }}">
```

浏览器会去请求 `style.scss` 文件，而 GitHub Pages 不会将 `.scss` 源文件作为静态资源提供（404），导致样式完全丢失。

**正确做法**：

```html
<!-- ✅ 正确：引用构建产物路径 -->
<link rel="stylesheet" href="{{ '/assets/css/style.css' | relative_url }}">
```

**关键原则**：**模板中永远引用构建后的 `.css` 路径，而非源码 `.scss` 路径。**

---

### 🕳️ 坑 2：`baseurl` 配置错误导致全站链接 404

**严重程度**：⭐⭐⭐⭐⭐

**现象**：本地 `jekyll serve` 预览一切正常，部署到 GitHub Pages 后所有内部链接（导航、CSS、页面跳转）全部指向错误路径。

**根因**：GitHub Pages 上的项目站点 URL 结构是 `https://<用户名>.github.io/<仓库名>/`，而非根路径 `/`。如果 `_config.yml` 中 `baseurl` 未正确设置，所有链接都会丢失仓库名这一级路径。

**示例**：

```yaml
# ❌ 错误
baseurl: ""

# 生成的链接：/assets/css/style.css
# 实际需要：  /仓库名/assets/css/style.css
```

```yaml
# ✅ 正确
baseurl: "/你的仓库名"

# 生成的链接：/你的仓库名/assets/css/style.css ✅
```

**配套使用 `relative_url` 过滤器**：

```liquid
<!-- 所有内部路径统一使用 relative_url -->
<link href="{{ '/assets/css/style.css' | relative_url }}">
<a href="{{ '/' | relative_url }}">
<a href="{{ '/process/01-需求分析.html' | relative_url }}">
```

`relative_url` 会自动在路径前拼接 `baseurl`，避免手动拼接出错。

---

### 🕳️ 坑 3：Liquid 变量未定义导致页面崩溃

**严重程度**：⭐⭐⭐⭐

**现象**：本地正常，部署后页面部分区域空白或显示 `Liquid error`。

**常见场景**：

1. **遍历空集合时访问属性**：
   ```liquid
   <!-- ❌ 当 site.posts 为空时，latest.title 报错 -->
   {% assign latest = site.posts | first %}
   {{ latest.title }}
   ```

2. **数学运算中除以零**：
   ```liquid
   <!-- ❌ 当 total 为 0 时报错 -->
   {{ completed | divided_by: total }}
   ```

**解决方案**：始终添加默认值或条件判断：

```liquid
<!-- ✅ 使用 default 过滤器 -->
{{ latest.title | default: "暂无数据" }}

<!-- ✅ 条件判断 -->
{% if site.posts.size > 0 %}
  {% assign latest = site.posts | first %}
  {{ latest.title }}
{% else %}
  暂无周报
{% endif %}

<!-- ✅ 避免除零 -->
{% assign total = site.pages | where_exp: "item", "item.phase" | size %}
{% if total > 0 %}
  {{ completed | times: 100 | divided_by: total }}%
{% else %}
  0%
{% endif %}
```

---

### 🕳️ 坑 4：GitHub Pages 构建成功但页面未更新

**严重程度**：⭐⭐⭐

**现象**：Actions 显示构建成功（绿色勾），但浏览器中看到的仍是旧版页面。

**原因与对策**：

| 可能原因 | 对策 |
|----------|------|
| 浏览器缓存 | **强制刷新**：`Ctrl + Shift + R`（Windows）或 `Cmd + Shift + R`（Mac） |
| CDN 缓存延迟 | GitHub Pages 使用全球 CDN，部分地区可能需要 3-5 分钟才能生效，耐心等待即可 |
| 构建的是旧提交 | 检查 Actions 日志中的 commit SHA，确认构建的是最新提交 |
| 移动端缓存 | 在移动端浏览器中清除缓存或使用隐私模式打开 |

---

### 🕳️ 坑 5：Jekyll 插件兼容性限制

**严重程度**：⭐⭐⭐

**现象**：在本地 `Gemfile` 中添加了某个 Jekyll 插件（如 `jekyll-admin`、`jekyll-paginate-v2`），本地运行正常，但 GitHub Pages 构建直接失败。

**根因**：GitHub Pages 运行在安全沙箱中，仅允许使用[官方白名单内的插件](https://pages.github.com/versions/)。任何未在白名单中的插件都会导致构建失败。

**白名单中常用的插件**：

| 插件 | 用途 |
|------|------|
| `jekyll-seo-tag` | SEO 元数据标签 |
| `jekyll-feed` | RSS Feed 生成 |
| `jekyll-sitemap` | 站点地图 |
| `jekyll-remote-theme` | 远程主题 |
| `jekyll-redirect-from` | 页面重定向 |

**如果需要额外插件**，可以使用 GitHub Actions 自定义构建流程替代默认的 Pages 构建：

```yaml
# .github/workflows/jekyll.yml
name: Deploy Jekyll site
on:
  push:
    branches: [master]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
      - run: bundle install
      - run: bundle exec jekyll build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./_site
```

---

### 🕳️ 坑 6：YAML Front Matter 格式陷阱

**严重程度**：⭐⭐⭐

**现象**：Front Matter 看似写了，但 Jekyll 没有正确读取，字段值总是空的。

**常见错误**：

```yaml
# ❌ 错误 1：冒号后没有空格
title:我的标题

# ✅ 正确
title: 我的标题
```

```yaml
# ❌ 错误 2：布尔值用了引号（变成字符串）
status: "open"

# ✅ 正确
status: open
```

```yaml
# ❌ 错误 3：数组缩进不一致
issues:
  - 问题1
 - 问题2     # 缩进少了一个空格

# ✅ 正确
issues:
  - 问题1
  - 问题2
```

```yaml
# ❌ 错误 4：包含特殊字符但未用引号包裹
title: 项目进度: 50%   # 冒号会被解析为 YAML 分隔符

# ✅ 正确
title: "项目进度: 50%"
```

**建议**：使用在线 YAML 校验工具（如 YAML Lint）检查格式，或在 VS Code 中安装 YAML 扩展获得语法高亮和错误提示。

---

### 🕳️ 坑 7：DNS 解析与网络连通性问题

**严重程度**：⭐⭐

**现象**：`git push` 成功但 GitHub Pages 无法访问，浏览器提示无法连接。

**原因与对策**：

| 原因 | 说明 | 对策 |
|------|------|------|
| DNS 解析 | 部分网络环境下 `github.io` 域名解析可能不稳定 | 切换 DNS 为公共 DNS |
| HTTPS 访问 | GitHub Pages 强制 HTTPS，某些环境可能阻止 443 端口 | 确保网络环境允许 HTTPS 流量 |
| 本地 DNS 缓存 | 本地 DNS 缓存了旧的解析结果 | 刷新 DNS 缓存 |

---

## 十三、高级技巧与优化

### 13.1 响应式布局

确保仪表盘在手机、平板、桌面端都有良好体验：

```scss
// 平板及以下
@media (max-width: 768px) {
  .status-cards { grid-template-columns: 1fr 1fr; }  // 两列
  .features-grid { grid-template-columns: 1fr; }      // 单列
  .timeline { flex-direction: column; }               // 纵向排列
  .navbar .nav-links { display: none; }               // 隐藏导航链接
  .hero .hero-title { font-size: 2.4rem; }            // 缩小标题
}

// 手机
@media (max-width: 480px) {
  .status-cards { grid-template-columns: 1fr; }       // 单列
  .hero .hero-title { font-size: 2rem; }
}
```

### 13.2 SEO 优化

利用 `jekyll-seo-tag` 插件，只需在 `_config.yml` 中填写站点信息，插件会自动为每个页面生成：

- `<title>` 标签
- `<meta name="description">` 描述
- Open Graph 标签（用于社交分享）
- Twitter Card 标签
- JSON-LD 结构化数据

无需在每个页面手动编写 SEO 标签。

### 13.3 本地开发效率技巧

```bash
# 启动本地服务器，支持自动刷新（修改文件后浏览器自动重载）
bundle exec jekyll serve --livereload

# 仅构建，不启动服务器（用于调试构建错误）
bundle exec jekyll build --verbose

# 构建草稿（_drafts 目录下的文件也会被渲染）
bundle exec jekyll serve --drafts
```

### 13.4 自定义 404 页面

在根目录创建 `404.md` 或 `404.html`，GitHub Pages 会自动将其作为 404 错误页面：

```html
---
layout: default
permalink: /404.html
---

<div style="text-align: center; padding: 100px 2rem;">
  <h1 style="font-size: 4rem; color: var(--primary);">404</h1>
  <p>页面未找到，请检查链接是否正确。</p>
  <a href="{{ '/' | relative_url }}">返回首页</a>
</div>
```

---

## 十四、总结

GitHub Pages + Jekyll 是一套低成本、高效率的项目进度管理方案。回顾本文的核心内容：

| 模块 | 关键技术点 |
|------|-----------|
| 环境搭建 | Ruby + Jekyll + Bundler 安装 |
| 样式系统 | SCSS 变量体系 + 深色科技风 + 毛玻璃效果 + 流光动画 |
| 布局模板 | default 基础布局 + Liquid 组件化 + 状态徽章复用 |
| 数据驱动 | Collections 自定义集合 + Front Matter 元数据 + Liquid 动态渲染 |
| 部署运维 | `git push` 自动部署 + GitHub Actions 监控 + CDN 缓存处理 |
| 踩坑避险 | SCSS 路径 → `.css` / `baseurl` 必填 / Liquid 加默认值 / 插件白名单 |

**适用场景延伸**：这套架构不仅适用于项目进度管理，稍作修改即可用于：

- 个人博客 / 技术周报
- 产品文档站点
- 团队 Wiki 知识库
- 开源项目主页

希望本文能帮助你快速搭建自己的进度管理站点。如有疑问或更好的实践方案，欢迎在评论区交流。

---

> **作者**：屈雪松  
> **技术栈**：GitHub Pages · Jekyll · SCSS · Liquid · Markdown
