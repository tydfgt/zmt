"""
Markdown 转换引擎 —— 将 MD 转换为各平台所需格式。

核心能力：
- MD → 微信公众号 HTML（行间距、字号、配色适配手机阅读）
- MD → 知乎格式（处理知乎不支持的 MD 语法）
- MD → 博客园/开源中国（保留标准 MD + 平台特有 Front Matter）
- MD → 小红书文案（提取要点，生成短文案）
- 代码高亮、图片处理、Front Matter 解析
"""

import re
import html as html_mod
from dataclasses import dataclass, field
from typing import Optional

import markdown
from bs4 import BeautifulSoup, NavigableString, Tag


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ArticleMeta:
    """文章元数据（从 MD Front Matter 提取）"""
    title: str = ""
    tags: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    summary: str = ""
    cover_image: str = ""

    @property
    def tags_str(self) -> str:
        return ", ".join(self.tags) if self.tags else ""

    @property
    def keywords(self) -> str:
        """逗号分隔的关键词，用于 SEO"""
        return ", ".join(self.tags[:5]) if self.tags else ""


@dataclass
class ConvertResult:
    """转换结果"""
    platform: str           # 目标平台名
    title: str              # 文章标题
    content: str            # 转换后的内容（HTML 或 Markdown）
    meta: ArticleMeta       # 元数据
    extra: dict = field(default_factory=dict)  # 平台特有字段


# ============================================================
# Markdown → HTML 核心转换器
# ============================================================

class MarkdownConverter:
    """Markdown 转 HTML，支持代码高亮和扩展语法"""

    def __init__(self, code_theme: str = "monokai"):
        self.code_theme = code_theme
        self._md = markdown.Markdown(extensions=[
            "markdown.extensions.fenced_code",   # ``` 代码块
            "markdown.extensions.codehilite",     # 代码高亮
            "markdown.extensions.tables",         # GFM 表格
            "markdown.extensions.toc",            # 目录
            "markdown.extensions.nl2br",          # 换行转 <br>
            "markdown.extensions.sane_lists",     # 智能列表
            "markdown.extensions.attr_list",      # 属性列表 {: .class }
            "markdown.extensions.def_list",       # 定义列表
            "markdown.extensions.footnotes",      # 脚注
            "markdown.extensions.abbr",           # 缩写
            "markdown.extensions.md_in_html",     # HTML 中的 MD
        ], extension_configs={
            "markdown.extensions.codehilite": {
                "css_class": "highlight",
                "guess_lang": True,
                "use_pygments": True,
            },
        })

    def to_html(self, md_text: str) -> str:
        """Markdown → HTML"""
        self._md.reset()
        return self._md.convert(md_text)

    def to_plain_text(self, md_text: str) -> str:
        """Markdown → 纯文本（去除所有格式标记）"""
        html = self.to_html(md_text)
        soup = BeautifulSoup(html, "lxml")
        # 保留代码块内容
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                pre.replace_with(f"\n```\n{code.get_text()}\n```\n")
        return soup.get_text(separator="\n").strip()


# ============================================================
# 平台专属格式化器
# ============================================================

class WechatFormatter:
    """
    微信公众号 HTML 格式化器

    微信特点：
    - 不支持 Markdown，需要 HTML
    - 不支持外链样式表，必须内联样式
    - 字号建议 15-16px，行高 1.75-2
    - 段间距 1em，两侧留白 16px
    - 代码块需要用特殊格式
    """

    # 微信内置样式模板
    BASE_STYLE = """
    <style>
      .wx-article { max-width: 100%; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; color: #333; font-size: 15px; line-height: 1.75; word-break: break-all; }
      .wx-article h1 { font-size: 22px; font-weight: 700; margin: 1.4em 0 0.8em; padding-bottom: 0.3em; border-bottom: 2px solid #1aad19; color: #1a1a1a; }
      .wx-article h2 { font-size: 19px; font-weight: 600; margin: 1.3em 0 0.7em; color: #1a1a1a; padding-left: 10px; border-left: 4px solid #1aad19; }
      .wx-article h3 { font-size: 17px; font-weight: 600; margin: 1.1em 0 0.5em; color: #333; }
      .wx-article p { margin: 0 0 0.8em; text-align: justify; }
      .wx-article blockquote { margin: 1em 0; padding: 12px 16px; background: #f6f9f6; border-left: 4px solid #1aad19; color: #555; font-size: 14px; border-radius: 0 4px 4px 0; }
      .wx-article ul, .wx-article ol { margin: 0.8em 0; padding-left: 1.8em; }
      .wx-article li { margin: 0.3em 0; }
      .wx-article a { color: #576b95; text-decoration: none; }
      .wx-article hr { margin: 1.5em 0; border: none; border-top: 1px solid #e0e0e0; }
      .wx-article table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 14px; }
      .wx-article th { background: #f0f9f0; font-weight: 600; padding: 10px 12px; border: 1px solid #e0e0e0; }
      .wx-article td { padding: 8px 12px; border: 1px solid #e0e0e0; }
      .wx-article img { max-width: 100%; height: auto; border-radius: 4px; margin: 0.8em 0; display: block; }
      .wx-article strong { color: #1aad19; font-weight: 600; }

      /* 代码块 */
      .wx-code-block { margin: 1em 0; border-radius: 8px; overflow: hidden; background: #282c34; color: #abb2bf; font-size: 13px; line-height: 1.6; }
      .wx-code-header { padding: 6px 16px; background: #21252b; color: #999; font-size: 12px; display: flex; align-items: center; gap: 8px; }
      .wx-code-header .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
      .wx-code-header .dot.red { background: #ff5f56; }
      .wx-code-header .dot.yellow { background: #ffbd2e; }
      .wx-code-header .dot.green { background: #27c93f; }
      .wx-code-body { padding: 14px 16px; overflow-x: auto; }
      .wx-code-body code { font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace; font-size: 13px; }

      /* 提示框 */
      .wx-tip { margin: 1em 0; padding: 14px 16px; border-radius: 8px; font-size: 14px; line-height: 1.7; }
      .wx-tip.info { background: #e8f4fd; border: 1px solid #b3d9f2; color: #1e6fa0; }
      .wx-tip.warn { background: #fef9e7; border: 1px solid #f9e79f; color: #7d6608; }
      .wx-tip.success { background: #eafaf1; border: 1px solid #a9dfbf; color: #1e8449; }
      .wx-tip.danger { background: #fdedec; border: 1px solid #f5b7b1; color: #922b21; }

      /* 关注引导 */
      .wx-follow { margin: 1.5em 0; padding: 20px; text-align: center; background: linear-gradient(135deg, #f0f9f0, #e8f5e9); border-radius: 12px; font-size: 14px; color: #666; }
      .wx-follow strong { color: #1aad19; font-size: 16px; }
    </style>
    """

    def format(self, md_text: str, meta: ArticleMeta) -> str:
        """将 MD 转换为微信公众号 HTML"""
        conv = MarkdownConverter()
        raw_html = conv.to_html(md_text)
        soup = BeautifulSoup(raw_html, "lxml")

        # 包裹在微信文章容器中
        wrapper = soup.new_tag("div", **{"class": "wx-article"})

        # 处理所有标签：将 class 映射为内联样式不需要额外操作，
        # 因为我们用了 <style> 标签（微信支持）
        wrapper.extend(soup.contents)

        # 处理代码块：从 highlight pre 转为微信代码块样式
        for pre in wrapper.find_all("pre"):
            code_tag = pre.find("code")
            lang = ""
            if code_tag:
                classes = code_tag.get("class", [])
                for c in classes:
                    if c.startswith("language-"):
                        lang = c.replace("language-", "")
                        break
                code_text = code_tag.get_text()

            # 构建微信代码块
            code_block = soup.new_tag("div", **{"class": "wx-code-block"})
            header = soup.new_tag("div", **{"class": "wx-code-header"})
            header.append(BeautifulSoup(
                '<span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>',
                "html.parser"
            ))
            lang_span = soup.new_tag("span")
            lang_span.string = lang or "code"
            header.append(lang_span)
            code_block.append(header)

            body = soup.new_tag("div", **{"class": "wx-code-body"})
            code_el = soup.new_tag("code")
            code_el.string = code_text
            body.append(code_el)
            code_block.append(body)

            pre.replace_with(code_block)

        # 处理图片：添加微信兼容属性
        for img in wrapper.find_all("img"):
            img["style"] = img.get("style", "") + "max-width:100%;height:auto;display:block;"
            if not img.get("alt"):
                img["alt"] = meta.title or "图片"

        # 最终拼装
        full_html = f"""{self.BASE_STYLE}
<div class="wx-article">
{wrapper.decode_contents()}
</div>
"""
        return full_html


class ZhihuFormatter:
    """
    知乎回答/文章格式转换器

    知乎特点：
    - 支持部分 Markdown（标题、加粗、列表、代码块、引用、链接）
    - 不支持表格、流程图等复杂语法
    - 代码块用 ``` 即可
    - 图片需要先上传到知乎图床
    - 单段不宜过长（建议每段不超过 3-4 行）
    """

    def format(self, md_text: str, meta: ArticleMeta) -> str:
        """转换为知乎兼容格式（本质还是 MD，但去掉不兼容语法）"""
        content = md_text

        # 1. 表格 → 列表形式（知乎不支持表格）
        content = self._table_to_list(content)

        # 2. HTML 标签 → 对应的 MD 或移除
        content = self._strip_html_tags(content)

        # 3. 脚注 → 行内括号
        content = self._footnote_to_inline(content)

        # 4. 定义列表 → 普通列表
        content = self._deflist_to_list(content)

        return content

    def _table_to_list(self, text: str) -> str:
        """将 GFM 表格转为层级列表（知乎不支持表格）"""
        lines = text.split("\n")
        result = []
        in_table = False
        table_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                table_lines.append(stripped)
            else:
                if in_table and table_lines:
                    result.append(self._render_table_as_list(table_lines))
                    table_lines = []
                    in_table = False
                result.append(line)

        if in_table and table_lines:
            result.append(self._render_table_as_list(table_lines))

        return "\n".join(result)

    def _render_table_as_list(self, table_lines: list) -> str:
        """把表格行渲染为列表"""
        if len(table_lines) < 1:
            return ""

        # 解析表头
        def parse_row(row: str) -> list:
            cells = [c.strip() for c in row.strip("|").split("|")]
            return [c for c in cells if c and c != "---" and not all(ch == '-' for ch in c)]

        rows = [parse_row(line) for line in table_lines]
        rows = [r for r in rows if r]

        if len(rows) < 2:
            return "\n".join([f"- {cell}" for row in rows for cell in row])

        headers = rows[0]
        data_rows = rows[2:] if len(rows) > 2 and all(
            all(c in "-: " for c in "".join(rows[1]))
            for _ in [1]
        ) else rows[1:]

        # 如果只有一行表头匹配上了分隔行，就从第2行开始
        # 实际上上面的判断可能不够准确，做个简单处理
        if len(rows) >= 2:
            # 检查第二行是否是分隔行
            second_row_str = "".join(rows[1]) if len(rows) > 1 else ""
            if all(c in "-: |" for c in second_row_str):
                headers = rows[0]
                data_rows = rows[2:]
            else:
                headers = []
                data_rows = rows

        output = []
        for i, data in enumerate(data_rows):
            if headers and len(headers) == len(data):
                item = f"- **{headers[0]}**: {data[0]}"
                for h, d in zip(headers[1:], data[1:]):
                    item += f" | **{h}**: {d}"
                output.append(item)
            else:
                output.append(f"- {' · '.join(data)}")

        return "\n".join(output)

    def _strip_html_tags(self, text: str) -> str:
        """移除或替换不兼容的 HTML 标签"""
        # 保留 <br> → 换行
        text = re.sub(r"<br\s*/?>", "\n", text)
        # <img> 保留
        # 其他 HTML 标签去除标签保留内容
        text = re.sub(r"<(?!img\b|br\b)[^>]+>", "", text)
        return text

    def _footnote_to_inline(self, text: str) -> str:
        """脚注 → 行内括号"""
        # 简单处理：移除 [^id] 引用
        text = re.sub(r"\[\^(\d+)\]", r"(注\1)", text)
        text = re.sub(r"\[\^(.*?)\]", r"(注：\1)", text)
        # 移除脚注定义行
        text = re.sub(r"^\[\^.*?\]:\s*.*$", "", text, flags=re.MULTILINE)
        return text

    def _deflist_to_list(self, text: str) -> str:
        """定义列表 → 普通列表"""
        lines = text.split("\n")
        result = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(": "):
                result.append(f"  - {stripped[2:]}")
            else:
                result.append(line)
        return "\n".join(result)


class XiaohongshuFormatter:
    """
    小红书文案格式化器

    小红书特点：
    - 笔记以图片为主（封面图 + 多张配图）
    - 文字说明最多 1000 字
    - 要点用 emoji + 短句
    - 标签用 # 话题形式
    - 需要吸引眼球的标题
    - 不支持代码块、表格等复杂格式
    """

    def format(self, md_text: str, meta: ArticleMeta) -> dict:
        """
        返回小红书发布所需数据
        Returns:
            {
                "title": "吸引眼球的标题",
                "content": "精简后的文案（≤1000字）",
                "hashtags": ["#标签1", "#标签2"],
                "cover_text": "封面图上的大字",
            }
        """
        conv = MarkdownConverter()
        plain = conv.to_plain_text(md_text)

        # 提取核心要点（取前 800 字）
        content = plain[:800]
        if len(plain) > 800:
            content += "\n\n...（全文请查看主页链接）"

        # 生成话题标签
        hashtags = [f"#{t}" for t in meta.tags[:5]] if meta.tags else ["#技术分享", "#程序员"]

        # 构造小红书风文案
        xhs_content = self._build_xhs_content(meta.title, content, hashtags)

        return {
            "title": self._make_clickbait_title(meta.title),
            "content": xhs_content,
            "hashtags": hashtags,
            "cover_text": meta.title[:20],
            "tags_str": " ".join(hashtags),
        }

    def _make_clickbait_title(self, title: str) -> str:
        """生成小红书风格的标题"""
        prefixes = ["🔥", "💡", "干货", "建议收藏", "手把手"]
        suffixes = ["！速看", "，建议收藏", "✨", "🔥", "（附教程）"]
        if title:
            return f"{prefixes[0]} {title}{suffixes[0]}"
        return f"{prefixes[2]} 分享{suffixes[2]}"

    def _build_xhs_content(self, title: str, body: str, hashtags: list) -> str:
        """构建小红书正文（emoji + 短段落）"""
        lines = [
            f"✨ {title}",
            "",
            "📌 今天给大家分享一个超实用的内容 👇",
            "",
        ]

        # 将正文切为短段，每段加点 emoji
        paragraphs = [p.strip() for p in body.split("\n") if p.strip()]
        emojis = ["🔹", "✅", "📊", "💻", "🎯", "🔧", "📝", "🚀", "⭐", "💪"]
        for i, para in enumerate(paragraphs[:10]):
            emoji = emojis[i % len(emojis)]
            if len(para) > 200:
                para = para[:200] + "..."
            lines.append(f"{emoji} {para}")
            lines.append("")

        lines.append("—" * 10)
        lines.append(" ".join(hashtags))

        return "\n".join(lines)


# ============================================================
# 统一的转换入口
# ============================================================

class ArticleProcessor:
    """文章处理器：读取 MD → 解析元数据 → AI 优化(可选) → 按平台转换"""

    def __init__(self, config: dict):
        self.config = config
        converter_cfg = config.get("converter", {})
        self.md_converter = MarkdownConverter(
            code_theme=converter_cfg.get("code_theme", "monokai")
        )
        self.wechat_fmt = WechatFormatter()
        self.zhihu_fmt = ZhihuFormatter()
        self.xhs_fmt = XiaohongshuFormatter()
        self._optimizer = None  # 延迟初始化

    def parse_meta(self, md_text: str) -> tuple:
        """解析 Markdown 文件，返回 (meta, body_md)"""
        try:
            import frontmatter
            post = frontmatter.loads(md_text)
            # post.metadata 是 dict，post.content 是正文
            fm = post.metadata if hasattr(post, 'metadata') else {}
            meta = ArticleMeta(
                title=fm.get("title", ""),
                tags=fm.get("tags", []),
                categories=fm.get("categories", []),
                summary=fm.get("summary", fm.get("description", "")),
                cover_image=fm.get("cover", fm.get("cover_image", "")),
            )
            return meta, post.content
        except ImportError:
            # 无 frontmatter 库时，手动解析
            return self._manual_parse(md_text)

    def _manual_parse(self, md_text: str) -> tuple:
        """手动解析 Front Matter"""
        meta = ArticleMeta()
        body = md_text
        if md_text.startswith("---"):
            parts = md_text.split("---", 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    fm = yaml.safe_load(parts[1])
                    if fm:
                        meta = ArticleMeta(
                            title=fm.get("title", ""),
                            tags=fm.get("tags", []),
                            categories=fm.get("categories", []),
                            summary=fm.get("summary", fm.get("description", "")),
                            cover_image=fm.get("cover", fm.get("cover_image", "")),
                        )
                except Exception:
                    pass
                body = parts[2]
        return meta, body

    def convert(self, md_text: str, platform: str, optimize: bool = False) -> ConvertResult:
        """将 MD 转换为指定平台的格式。

        Args:
            md_text: 原始 Markdown 文本
            platform: 目标平台
            optimize: 是否使用 DeepSeek AI 优化内容
        """
        meta, body = self.parse_meta(md_text)

        # ---- AI 优化（在格式转换之前） ----
        if optimize:
            body = self._ai_optimize(body, platform, meta.title)

        if platform == "wechat":
            content = self.wechat_fmt.format(body, meta)
        elif platform == "zhihu":
            content = self.zhihu_fmt.format(body, meta)
        elif platform == "xiaohongshu":
            result = self.xhs_fmt.format(body, meta)
            # 小红书也尝试优化标题
            if optimize:
                opt_title = self._ai_optimize_title(result["title"], platform)
                if opt_title:
                    result["title"] = opt_title
            return ConvertResult(
                platform=platform,
                title=result["title"],
                content=result["content"],
                meta=meta,
                extra=result,
            )
        elif platform in ("cnblogs", "oschina"):
            content = body
        else:
            content = body

        # 优化标题
        final_title = meta.title
        if optimize and final_title:
            opt_title = self._ai_optimize_title(final_title, platform)
            if opt_title:
                final_title = opt_title

        return ConvertResult(
            platform=platform,
            title=final_title,
            content=content,
            meta=meta,
        )

    def _get_optimizer(self):
        """延迟初始化优化器"""
        if self._optimizer is None:
            from .optimizer import create_optimizer
            self._optimizer = create_optimizer(self.config)
        return self._optimizer

    def _ai_optimize(self, content: str, platform: str, title: str = "") -> str:
        """调用 AI 优化内容，优化器未配置时返回原文"""
        opt = self._get_optimizer()
        if opt is None:
            return content
        try:
            return opt.optimize(content, platform, title)
        except Exception:
            return content  # 失败静默回退

    def _ai_optimize_title(self, title: str, platform: str) -> str:
        """调用 AI 优化标题"""
        opt = self._get_optimizer()
        if opt is None:
            return ""
        try:
            return opt.optimize_title(title, platform)
        except Exception:
            return ""
