# 🚀 多平台内容分发工具

> 一文编写，多平台分发 —— Markdown → 知乎 · 博客园 · 小红书 · 微信公众号 · 开源中国

---

## 核心能力

| 平台 | 能力 | 方式 |
|------|------|------|
| 📝 **博客园** | 一键发布（含标题、标签、分类） | MetaWeblog XML-RPC API |
| 🏗️ **开源中国** | 一键发布博客/文章 | Open API (OAuth 2.0) |
| 💬 **微信公众号** | 生成精美 HTML + 自动存草稿 | 微信 API + 格式引擎 |
| 🧠 **知乎** | MD → 知乎兼容格式 | 格式转换 + 剪贴板辅助 |
| 📕 **小红书** | 文案精炼 + 封面图生成 | 内容提取 + 手动发布引导 |

---

## 快速开始

### 1. 安装依赖

```bash
cd multi-publisher
pip install -r requirements.txt
```

### 2. 配置平台密钥

编辑 `config.yaml`：

```yaml
# 博客园（必填）
cnblogs:
  enabled: true
  blog_url: "https://rpc.cnblogs.com/metaweblog/你的博客名"
  username: "你的用户名"
  password: "你的密码"

# 开源中国（必填）
oschina:
  enabled: true
  client_id: "你的client_id"
  client_secret: "你的client_secret"
```

### 3. 检查配置

```bash
python -m publisher.cli check
```

### 4. 模拟发布（预览）

```bash
python -m publisher.cli publish templates/sample_article.md --all --dry-run
```

### 5. 正式发布

```bash
# 发布到所有已启用平台
python -m publisher.cli publish article.md --all

# 发布到指定平台
python -m publisher.cli publish article.md -p cnblogs -p oschina

# 仅转换格式，不发布
python -m publisher.cli convert article.md -p wechat
```

---

## 你的 Markdown 文章格式

```markdown
---
title: 文章标题
tags: [标签1, 标签2, 标签3]
categories: [分类]
summary: 摘要（用于 SEO 和列表展示）
---

## 正文内容

正常写 Markdown 即可，支持表格、代码块、图片等。
```

---

## 项目结构

```
multi-publisher/
├── config.yaml              # 平台配置（API 密钥等）
├── requirements.txt         # Python 依赖
├── publisher/
│   ├── cli.py               # 命令行入口
│   ├── converter.py         # MD 转换引擎
│   └── platforms/
│       ├── base.py          # 平台基类
│       ├── cnblogs.py       # 博客园
│       ├── oschina.py       # 开源中国
│       ├── wechat.py        # 微信公众号
│       ├── zhihu.py         # 知乎
│       └── xiaohongshu.py   # 小红书
├── templates/
│   └── sample_article.md    # 示例文章
└── output/                  # 转换结果输出
```

---

## 常见问题

### Q: 微信公众号怎么自动发布？

微信 API 只允许**已认证**的服务号/订阅号调用。如果你有认证公众号：
1. 在 `config.yaml` 中填写 `appid` 和 `appsecret`
2. 将 `draft_only` 设为 `false`
3. 工具会自动保存到草稿箱

如果只有个人订阅号（未认证），工具会生成 HTML 文件，你手动粘贴即可。

### Q: 小红书和知乎能自动发布吗？

这两个平台没有公开的创作 API，只能半自动：
- 工具帮你做好格式转换和文案优化
- 你手动粘贴发布（约 1 分钟/平台）

### Q: 图片怎么处理？

建议使用图床（如 GitHub + jsDelivr、七牛云、阿里云 OSS），在 Markdown 中用 URL 引用。各平台会自动拉取。
