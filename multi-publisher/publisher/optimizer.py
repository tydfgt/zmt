"""
DeepSeek AI 文章优化器 —— 调用 DeepSeek V4 API 按平台风格优化文章。

各平台风格特点：
- 博客园：技术深度、代码详实、逻辑清晰，可长文
- 开源中国：技术社区风，接地气，鼓励讨论
- 微信公众号：碎片化阅读，短段落，强互动感，emoji 点缀
- 知乎：专业严谨，论证充分，有「谢邀」文化
- 小红书：短平快，emoji 密集，话题标签，种草风

API: DeepSeek Chat API (OpenAI 兼容格式)
文档: https://platform.deepseek.com/api-docs
"""

import json
import time
from typing import Optional, Callable

import requests


# ============================================================
# 平台专属 Prompt 模板
# ============================================================

PLATFORM_PROMPTS = {
    "cnblogs": """你是一位资深技术博主，擅长在博客园撰写高质量技术文章。请优化以下文章，使其更适合博客园读者。

【博客园风格要求】
- 保持技术深度和专业性，不简化核心技术细节
- 代码示例要完整、可运行，注释清晰
- 逻辑结构清晰：背景 → 问题 → 方案 → 实现 → 总结
- 可以加入自己的实践经验和踩坑记录
- 语气专业但不生硬，像资深工程师在分享经验
- 适当使用表格、列表增强可读性
- 段落长度适中，不要拆得太碎

【原标题】{title}
【原文】

{content}

请直接输出优化后的完整 Markdown 文章，不要加任何前言或后缀说明。""",

    "oschina": """你是一位活跃在开源中国的技术达人。请优化以下文章，使其更适合开源中国社区。

【开源中国风格要求】
- 保持技术干货，但语气更接地气、有社区感
- 开头可以简短引出话题，快速进入正文
- 鼓励读者在评论区交流讨论
- 可以适当提及相关开源项目或工具链
- 代码示例清晰实用
- 结尾可以抛出讨论话题

【原标题】{title}
【原文】

{content}

请直接输出优化后的完整 Markdown 文章，不要加任何前言或后缀说明。""",

    "wechat": """你是一位微信公众号大 V，擅长写出 10w+ 的技术爆文。请优化以下文章，使其适合微信公众号发布。

【公众号风格要求】
- 开头 3 句话内必须抓住读者注意力（痛点、共鸣、悬念）
- 段落短小精悍，每段不超过 4 行，方便手机阅读
- 适当使用 emoji 点缀（但不过多，2-3 个/段为宜）
- 关键观点用加粗或特殊格式突出
- 每隔几个段落插入引导语（如「看到这里，你可能想问…」）
- 结尾要有总结 + 引导关注
- 代码块保持原样，但可加简短说明
- 全文节奏感强，让读者一口气读完

【原标题】{title}
【原文】

{content}

请直接输出优化后的完整内容（Markdown 格式），不要加任何前言或后缀说明。""",

    "zhihu": """你是一位知乎优秀回答者，拥有 10 万+ 关注者。请优化以下文章，使其适合知乎发布。

【知乎风格要求】
- 开头要有「破题」：一句话点出问题本质
- 逻辑严密，层层递进，论证充分
- 可以引用数据、案例增强说服力
- 语气理性、客观，避免情绪化表达
- 专业术语要解释，让非专业读者也能看懂
- 结构清晰，用小标题引导阅读
- 结尾可以总结核心观点（1-2 句话）
- 可适当使用加粗强调重点

【原标题】{title}
【原文】

{content}

请直接输出优化后的完整内容（Markdown 格式），不要加任何前言或后缀说明。""",

    "xiaohongshu": """你是一位小红书万粉博主，擅长把技术内容转化为小红书爆款笔记。请优化以下文章，使其适合小红书发布。

【小红书风格要求】
- 标题要有爆点：用数字、emoji、悬念、痛点吸引点击（不超过 20 字）
- 正文用短句 + emoji 分点，每句话一行
- 善用「✨💡🔥📌✅」等 emoji 做视觉引导
- 把最核心的干货提炼为 3-5 个要点
- 语气像朋友分享，亲切自然，不说教
- 结尾加上相关话题标签 #tag
- 全文控制在 800 字以内
- 代码块要删掉，改用通俗语言描述

【原标题】{title}
【原文】

{content}

请直接输出优化后的小红书风格内容，格式：
第一行：吸引人的标题
空一行
正文内容（短句 + emoji）
空一行
话题标签

不要加任何其他说明。""",
}


# ============================================================
# DeepSeek API 客户端
# ============================================================

class DeepSeekOptimizer:
    """DeepSeek V4 文章优化器"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL = "deepseek-chat"  # DeepSeek V4

    def __init__(self, api_key: str, model: Optional[str] = None,
                 max_tokens: int = 8192, temperature: float = 0.7,
                 on_progress: Optional[Callable[[str], None]] = None):
        """
        Args:
            api_key: DeepSeek API Key
            model: 模型名称，默认 deepseek-chat（V4）
            max_tokens: 最大输出 token
            temperature: 创意度 0-1
            on_progress: 进度回调，接收状态描述文本
        """
        self.api_key = api_key
        self.model = model or self.MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.on_progress = on_progress

    def optimize(self, content: str, platform: str, title: str = "") -> str:
        """
        按平台风格优化文章内容。

        Args:
            content: 原始 Markdown 内容
            platform: 目标平台 (cnblogs/oschina/wechat/zhihu/xiaohongshu)
            title: 文章标题

        Returns:
            优化后的内容
        """
        prompt_template = PLATFORM_PROMPTS.get(platform)
        if not prompt_template:
            raise ValueError(f"不支持的平台: {platform}，可选: {list(PLATFORM_PROMPTS.keys())}")

        prompt = prompt_template.format(title=title, content=content)

        self._notify(f"🤖 DeepSeek 正在为「{self._platform_label(platform)}」优化文章...")

        try:
            result = self._call_api(prompt)
            self._notify(f"✅ 优化完成 ({len(result)} 字符)")
            return result
        except Exception as e:
            self._notify(f"⚠️ DeepSeek 优化失败: {e}，使用原文")
            return content

    def optimize_title(self, title: str, platform: str) -> str:
        """仅为标题做平台化优化（轻量调用）"""
        prompt = f"""请为「{self._platform_label(platform)}」优化以下文章标题，使其更吸引该平台读者。
只输出优化后的标题，不要加任何说明或标点符号。

原标题：{title}"""

        try:
            result = self._call_api(prompt, max_tokens=100, temperature=0.8)
            # 清理输出（去掉可能的引号和换行）
            result = result.strip().strip('"').strip("'").strip("《").strip("》")
            return result[:100]  # 限制长度
        except Exception:
            return title

    def _call_api(self, prompt: str, max_tokens: Optional[int] = None,
                  temperature: Optional[float] = None) -> str:
        """调用 DeepSeek Chat API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一个专业的内容优化助手，擅长根据不同平台的风格优化文章。你的输出直接就是优化后的内容，不加任何多余的解释。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": False,
        }

        start_time = time.time()
        resp = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=120,  # 优化可能需要较长时间
        )
        elapsed = time.time() - start_time

        if resp.status_code != 200:
            error_info = resp.text[:300]
            raise Exception(f"API 返回 {resp.status_code}: {error_info}")

        data = resp.json()
        usage = data.get("usage", {})
        tokens = usage.get("total_tokens", "?")
        self._notify(f"   ⏱ {elapsed:.1f}s · {tokens} tokens")

        # 提取回复内容
        choices = data.get("choices", [])
        if not choices:
            raise Exception("API 返回为空")

        message = choices[0].get("message", {})
        result = message.get("content", "")

        if not result:
            raise Exception("API 返回内容为空")

        return result

    def _notify(self, msg: str):
        """进度通知"""
        if self.on_progress:
            self.on_progress(msg)

    @staticmethod
    def _platform_label(platform: str) -> str:
        labels = {
            "cnblogs": "博客园",
            "oschina": "开源中国",
            "wechat": "微信公众号",
            "zhihu": "知乎",
            "xiaohongshu": "小红书",
        }
        return labels.get(platform, platform)


# ============================================================
# 便捷工厂函数
# ============================================================

def create_optimizer(config: dict, on_progress: Optional[Callable] = None) -> Optional[DeepSeekOptimizer]:
    """从配置创建优化器实例，未配置 API Key 时返回 None"""
    ds_cfg = config.get("deepseek", {})
    api_key = ds_cfg.get("api_key", "")
    if not api_key or api_key == "你的DeepSeek_API_Key":
        return None

    return DeepSeekOptimizer(
        api_key=api_key,
        model=ds_cfg.get("model"),
        max_tokens=ds_cfg.get("max_tokens", 8192),
        temperature=ds_cfg.get("temperature", 0.7),
        on_progress=on_progress,
    )
