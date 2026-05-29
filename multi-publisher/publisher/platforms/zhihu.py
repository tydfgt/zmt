"""
知乎模块 - 格式转换 + 剪贴板辅助 + 手工发布引导。

知乎没有公开的创作 API，只能半自动：
1. 将 MD 转为知乎兼容格式
2. 复制到剪贴板（可选）
3. 保存为 .md 文件供手动粘贴
"""

from pathlib import Path

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class ZhihuPlatform(BasePlatform):
    name = "zhihu"
    label = "知乎"

    def __init__(self, config: dict):
        super().__init__(config)
        self.auto_copy = config.get("auto_copy", False)

    def publish(self, result: ConvertResult) -> PublishResult:
        """知乎「发布」= 格式转换 + 保存 + 引导手动操作"""

        # 1. 保存转换后的 MD 文件
        output_dir = Path("output/zhihu")
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{self._safe_name(result.title)}.md"
        filepath.write_text(result.content, encoding="utf-8")

        # 2. 尝试复制到剪贴板
        copy_msg = ""
        if self.auto_copy and HAS_PYPERCLIP:
            try:
                pyperclip.copy(result.content)
                copy_msg = "\n📋 已复制到剪贴板，直接粘贴即可"
            except Exception:
                copy_msg = "\n⚠️ 剪贴板复制失败，请手动打开文件复制"

        message = (
            f"📄 知乎格式已保存至: {filepath}\n"
            f"👉 下一步操作：\n"
            f"   1. 打开知乎 → 写文章/写回答\n"
            f"   2. 粘贴转换后的内容{copy_msg}\n"
            f"   3. 检查格式（特别是表格已转为列表）\n"
            f"   4. 上传图片 → 发布"
        )

        return PublishResult(
            success=True,
            platform=self.name,
            url=f"file://{filepath.absolute()}",
            message=message,
        )

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        return safe.strip()[:50] or "zhihu_article"
