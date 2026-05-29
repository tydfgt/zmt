# 🚀 多平台内容分发工具 — 一文多发，省时省力

> 写一篇 Markdown 文章 → 自动推送到 **博客园 · 开源中国 · 微信公众号 · 知乎 · 小红书**  
> 支持 DeepSeek AI 智能优化：同一篇文章，自动改写成各平台喜欢的风格

---

## 📖 这是什么？

如果你在做自媒体或技术博客，你一定遇到过这种痛苦：

> 写好一篇文章 → 打开博客园粘贴 → 打开知乎粘贴 → 打开公众号后台粘贴 → 打开小红书再粘贴……  
> 每个平台的格式还不一样，公众号要 HTML，知乎不支持表格，小红书要短文案+emoji……

**这个工具就是来解决这个问题的。** 你只需要写好一篇 Markdown 文章，一条命令，它就帮你：

- 🔄 **格式转换**：自动把 Markdown 变成公众号 HTML、知乎格式、小红书文案
- 📡 **一键发布**：博客园和开源中国可以直接自动发布，无需打开网页
- 🧠 **AI 优化**：接入 DeepSeek，自动按各平台风格改写文章（公众号要抓人、知乎要严谨、小红书要活泼）

---

## 🎯 效果对比

| 你的工作量 | 不用工具 | 用这个工具 |
|-----------|---------|-----------|
| 写文章 | 1 篇 | 1 篇 |
| 调整格式 × 5 平台 | 30-60 分钟 | **0 分钟（自动）** |
| 手动发布 × 5 平台 | 10-20 分钟 | **1 条命令** |
| 总耗时 | 40-80 分钟 | **写文章的时间 + 1 分钟** |

---

## 🧭 前置准备（小白版）

### 第一步：确认你有 Python

这个工具是用 Python 写的，所以电脑上要有 Python。

**怎么知道有没有？** 打开终端（黑窗口），输入：

```bash
python3 --version
```

如果显示类似 `Python 3.10.x` 或 `Python 3.11.x`，说明已经有了。  
如果显示 `command not found`，需要先安装 Python：

| 系统 | 安装方式 |
|------|---------|
| **macOS** | 终端输入 `brew install python3`（没有 brew 的话先去 https://brew.sh 安装） |
| **Windows** | 去 https://www.python.org/downloads/ 下载安装包，**安装时勾选「Add Python to PATH」** |
| **Linux** | 终端输入 `sudo apt install python3 python3-pip python3-venv -y` |

### 第二步：下载项目

```bash
# 把项目下载到本地
git clone git@github.com:tydfgt/zmt.git
cd zmt/multi-publisher
```

> 如果不会用 git，也可以在 https://github.com/tydfgt/zmt 点绿色「Code」按钮 → Download ZIP → 解压后进入 `multi-publisher` 文件夹。

### 第三步：创建虚拟环境（很重要！）

虚拟环境就是一个「隔离的小房间」，不会搞乱你电脑上其他 Python 项目：

```bash
# 创建虚拟环境（只需要做一次）
python3 -m venv venv
```

### 第四步：激活虚拟环境 + 安装依赖

```bash
# macOS / Linux：
source venv/bin/activate

# Windows：
venv\Scripts\activate

# 安装需要的包（只需要做一次）
pip install -r requirements.txt
```

> 看到 `Successfully installed ...` 就说明装好了。  
> ⚠️ 以后每次打开新终端都要先执行 `source venv/bin/activate`（或 Windows 的激活命令）。

### 第五步：创建你的配置文件

```bash
# 复制配置模板
cp config.yaml.example config.yaml
```

然后用任意文本编辑器（VS Code、记事本、vim 都行）打开 `config.yaml`，填入你的各平台账号信息。

---

## 🔑 各平台配置详解

编辑 `config.yaml` 文件，把下面这些信息填进去。**不要填错了，冒号后面必须有空格。**

### 博客园

```yaml
cnblogs:
  enabled: true
  blog_url: "https://rpc.cnblogs.com/metaweblog/你的博客名"
  username: "你的博客园用户名"
  password: "你的博客园密码"
```

**怎么获取？**

1. 登录 https://www.cnblogs.com
2. 点右上角头像 → 「管理」→ 左侧「设置」
3. 找到「允许 MetaWeblog 博客客户端访问」，勾选 ✅
4. 你的「博客名」就是博客地址里那串英文，比如 `https://www.cnblogs.com/zhangsan/` → 博客名是 `zhangsan`
5. `blog_url` 填 `https://rpc.cnblogs.com/metaweblog/zhangsan`

### 开源中国

```yaml
oschina:
  enabled: true
  client_id: "你的client_id"
  client_secret: "你的client_secret"
  pub_type: "article"
```

**怎么获取？**

1. 登录 https://www.oschina.net
2. 点右上角头像 →「个人中心」→ 左侧「Open API」
3. 创建一个应用，获取 `client_id` 和 `client_secret`
4. `pub_type` 填 `article`（文章）或 `blog`（博客），推荐 `article`

### 微信公众号（可选，需要认证公众号）

```yaml
wechat:
  enabled: false          # 没有认证公众号就保持 false
  appid: "你的AppID"
  appsecret: "你的AppSecret"
  draft_only: true        # true = 只存草稿；false = 直接发布
```

**如果你没有认证的公众号**（大多数个人用户），保持 `enabled: false`，工具会生成 HTML 文件，你手动复制粘贴到公众号后台即可，效果一样好。

### 知乎（不需要 API Key）

```yaml
zhihu:
  enabled: true
  auto_copy: false
```

这个不需要任何密钥。`auto_copy: true` 会自动把转换后的内容复制到剪贴板，方便粘贴。

### 小红书（不需要 API Key）

```yaml
xiaohongshu:
  enabled: true
  cover:
    width: 1080
    height: 1440
    bg_color: "#1a1a2e"
```

也不需要密钥。工具会自动生成封面图和精炼后的文案。

### DeepSeek AI 优化（强烈推荐！）

```yaml
deepseek:
  enabled: true
  api_key: "sk-xxxxxxxx"        # 改这里！
  model: "deepseek-chat"
  max_tokens: 8192
  temperature: 0.7
```

**怎么获取 API Key？**

1. 打开 https://platform.deepseek.com
2. 注册账号（用手机号就行）
3. 点左侧「API Keys」→「创建新的 API Key」→ 复制那串 `sk-` 开头的密钥
4. 粘贴到 `config.yaml` 的 `api_key` 位置

> 💰 DeepSeek 非常便宜，优化一篇文章大概花 **1 分钱**。充值 10 块钱够用一年。

---

## ✍️ 怎么写文章？

在 `multi-publisher/` 目录下（或任意位置），创建一个 `.md` 文件，格式如下：

```markdown
---
title: 你的文章标题
tags: [Python, 自动化, 效率]
categories: [技术, 编程]
summary: 一句话描述这篇文章讲什么
---

## 第一个小标题

正文内容……支持所有标准 Markdown 语法。

## 第二个小标题

- 列表项 1
- 列表项 2

```python
# 代码块也支持（带语法高亮）
print("Hello, World!")
```

| 表格 | 也 | 支持 |
|------|----|------|
| 数据 | 数据 | 数据 |

> 引用也支持

![图片](https://你的图片地址.png)
```

> ⚠️ **图片要用网络地址**（URL），不能用本地路径。推荐用 GitHub、七牛云、阿里云 OSS 等图床。

---

## 🎮 命令大全

> ⚠️ 每次运行命令前，确保已激活虚拟环境：`source venv/bin/activate`

### 1. 检查配置是否正确

```bash
python -m publisher.cli check
```

会显示每个平台的配置状态，如果有问题会告诉你是哪个配置项缺失。

### 2. 试运行（强烈推荐第一次用！）

```bash
python -m publisher.cli publish 你的文章.md --all --dry-run
```

`--dry-run` 意思是「假装发布」，只显示会发布到哪里、内容有多少字，**不会真的发出去**。放心测试。

### 3. 正式发布

```bash
# 发到所有已启用的平台
python -m publisher.cli publish 你的文章.md --all

# 只发到博客园 + 开源中国
python -m publisher.cli publish 你的文章.md -p cnblogs -p oschina

# 发布时开启 AI 优化（需要先配好 DeepSeek API Key）
python -m publisher.cli publish 你的文章.md --all --optimize
```

### 4. 只转换格式，不发布

```bash
# 生成公众号 HTML 文件（在 output/ 目录下）
python -m publisher.cli convert 你的文章.md -p wechat

# 加 AI 优化
python -m publisher.cli convert 你的文章.md -p wechat --optimize
```

转换后的文件在 `output/` 文件夹里，打开复制内容即可。

---

## 🤖 AI 优化效果示例

原始文章 → 发给 DeepSeek → 各平台得到不同风格的版本：

| 平台 | AI 会怎么改 |
|------|------------|
| **博客园** | 保持技术深度，增加实践心得和踩坑记录 |
| **开源中国** | 语气更接地气，引导读者在评论区讨论 |
| **微信公众号** | 碎片化段落、吸引人的开头、emoji 点缀、结尾引导关注 |
| **知乎** | 严谨论证、层层递进、专业术语解释到位 |
| **小红书** | 提炼 3-5 个要点、短句 + emoji、话题标签 |

**一句话总结**：同一个内容，AI 帮你写 5 个不同版本，适配 5 个平台的用户口味。

---

## 📁 项目文件说明

```
zmt/
│
├── README.md                        ← 你正在看的就是这个
├── .gitignore                       ← 告诉 git 哪些文件不要上传（保护密钥！）
├── CSDN_GitHubPages_Jekyll教程.md    ← 一篇 GitHub Pages 搭建教程
│
└── multi-publisher/                 ← 多平台分发工具
    │
    ├── config.yaml                  ← 你的配置文件（含密钥，不要上传！）
    ├── config.yaml.example          ← 配置文件模板（安全，可以上传）
    ├── requirements.txt             ← Python 依赖包列表
    │
    ├── publisher/                   ← 核心代码
    │   ├── cli.py                   ← 命令行入口（publish / convert / check 命令）
    │   ├── converter.py             ← Markdown → 各平台格式转换引擎
    │   ├── optimizer.py             ← DeepSeek AI 优化器
    │   └── platforms/               ← 各平台对接模块
    │       ├── base.py              ← 平台基类
    │       ├── cnblogs.py           ← 博客园（MetaWeblog API）
    │       ├── oschina.py           ← 开源中国（Open API）
    │       ├── wechat.py            ← 微信公众号（HTML 生成 + 草稿箱）
    │       ├── zhihu.py             ← 知乎（格式转换）
    │       └── xiaohongshu.py       ← 小红书（文案 + 封面图）
    │
    ├── templates/
    │   └── sample_article.md        ← 示例文章（可以拿来测试）
    │
    ├── tests/                       ← 测试代码
    └── output/                      ← 转换结果输出（不上传）
        ├── wechat/
        ├── zhihu/
        └── xiaohongshu/
```

---

## 🐛 常见问题

### Q: 运行命令报 `No module named 'xxx'`

说明依赖没装好，重新执行：

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Q: `config.yaml` 改了没生效？

Jekyll 类似的工具需要重启，但这个工具每次运行都会重新读取 `config.yaml`，改完直接生效，不需要重启。

### Q: 博客园发布失败？

检查三点：
1. 博客园后台是否勾选了「允许 MetaWeblog 访问」
2. `blog_url` 里的博客名是否正确
3. 用户名密码是否正确

可以运行 `python -m publisher.cli check` 看具体报错。

### Q: 图片显示不出来？

所有平台的图片都需要是**网络地址**（以 `http://` 或 `https://` 开头）。本地路径（如 `./images/xxx.png`）上传后别人看不到。

推荐免费图床：
- **GitHub + jsDelivr**：把图片放到 GitHub 仓库，通过 jsDelivr CDN 访问（免费、稳定）
- **路过图床**：https://imgse.com （免费，无需注册）

### Q: 我的 `config.yaml` 会被上传到 GitHub 吗？

**不会。** 项目根目录的 `.gitignore` 已经写了 `config.yaml`，git 会自动忽略它。  
仓库里只有 `config.yaml.example`（模板文件），不包含任何真实密钥。

### Q: DeepSeek API 怎么充值？

打开 https://platform.deepseek.com → 点左侧「充值」→ 支付宝/微信扫码。最低充 10 元，优化一篇文章约 0.01 元，够用很久。

### Q: 我没有博客园/开源中国的账号，能用吗？

可以。只需在 `config.yaml` 中把对应平台的 `enabled: true` 改成 `enabled: false`，工具会自动跳过。

### Q: 能加更多平台吗？

可以。每个平台只需要写一个继承 `BasePlatform` 的类，放在 `publisher/platforms/` 目录下即可。欢迎提 Pull Request！

---

## 🔄 日常使用流程（TL;DR）

```bash
# 1. 激活环境（每次打开终端都要做）
cd zmt/multi-publisher
source venv/bin/activate

# 2. 写文章（用 VS Code / Typora / Obsidian 等）
vim my_article.md

# 3. 试运行检查
python -m publisher.cli publish my_article.md --all --dry-run

# 4. 确认无误，正式发布（加 AI 优化）
python -m publisher.cli publish my_article.md --all --optimize

# 5. 对于微信/知乎/小红书：去 output/ 文件夹找到转换后的文件，手动粘贴发布
```

---

> **作者**：屈雪松  
> **技术栈**：Python · Markdown · DeepSeek API · MetaWeblog · OAuth 2.0  
> **仓库**：https://github.com/tydfgt/zmt
