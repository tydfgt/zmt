"""
小红书模块 - 文案生成 + 封面图制作 + 手动发布引导。

小红书没有公开 API，需要完全手动发布：
1. 生成吸引眼球的标题和文案（≤1000字）
2. 可选：用 Pillow 生成封面图
3. 保存为文本文件供手动复制
"""

from pathlib import Path

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class XiaohongshuPlatform(BasePlatform):
    name = "xiaohongshu"
    label = "小红书"

    def __init__(self, config: dict):
        super().__init__(config)
        self.cover_cfg = config.get("cover", {})

    def publish(self, result: ConvertResult) -> PublishResult:
        """小红书 = 文案保存 + 封面试生成 + 手动引导"""

        extra = result.extra

        # 1. 保存文案
        output_dir = Path("output/xiaohongshu")
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{self._safe_name(result.title)}.txt"
        filepath.write_text(extra.get("content", result.content), encoding="utf-8")

        # 2. 尝试生成封面图
        cover_msg = ""
        cover_path = output_dir / f"{self._safe_name(result.title)}_cover.png"
        try:
            self._generate_cover(extra.get("cover_text", result.title), str(cover_path))
            cover_msg = f"\n🎨 封面图已生成: {cover_path}"
        except Exception as e:
            cover_msg = f"\n⚠️ 封面图生成失败: {e}（请用 Canva/醒图 自行制作）"

        hashtags = extra.get("tags_str", "")

        message = (
            f"📄 小红书文案已保存至: {filepath}{cover_msg}\n"
            f"🏷️ 建议标签: {hashtags}\n"
            f"👉 下一步操作：\n"
            f"   1. 打开小红书 App → 底部 + → 上传封面图\n"
            f"   2. 粘贴文案（已保存为 txt 文件）\n"
            f"   3. 添加话题标签 → 发布\n"
            f"\n💡 提示：小红书标题限 20 字，正文限 1000 字"
        )

        return PublishResult(
            success=True,
            platform=self.name,
            url=f"file://{filepath.absolute()}",
            message=message,
        )

    def _generate_cover(self, text: str, output_path: str):
        """
        用 Pillow 生成简易封面图。
        如果要更精美的封面，建议用 Canva / 醒图。
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise Exception("需要安装 Pillow: pip install Pillow")

        w = self.cover_cfg.get("width", 1080)
        h = self.cover_cfg.get("height", 1440)
        title_size = self.cover_cfg.get("title_font_size", 48)

        # 创建背景
        bg_color = self.cover_cfg.get("bg_color", "#1a1a2e")
        img = Image.new("RGB", (w, h), bg_color)
        draw = ImageDraw.Draw(img)

        # 尝试加载中文字体，否则回退到默认
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", title_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", title_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

        # 绘制标题文字（居中）
        lines = self._wrap_text(text, font, draw, w - 120)
        total_text_h = len(lines) * (title_size + 10)
        y_start = (h - total_text_h) // 2

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (w - text_w) // 2
            y = y_start + i * (title_size + 10)
            draw.text((x, y), line, fill="#00e5ff", font=font)

        img.save(output_path, "PNG")

    @staticmethod
    def _wrap_text(text: str, font, draw, max_width: int) -> list:
        """简单的中文换行"""
        lines = []
        current = ""
        for char in text:
            test = current + char
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > max_width and current:
                lines.append(current)
                current = char
            else:
                current = test
        if current:
            lines.append(current)
        return lines or [text]

    @staticmethod
    def _safe_name(name: str) -> str:
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        return safe.strip()[:50] or "xhs_note"
