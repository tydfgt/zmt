"""
微信公众号模块 - 生成公众号 HTML + 草稿箱 + 一键发布。

微信公众平台 API (订阅号):
- 文档: https://developers.weixin.qq.com/doc/subscription/api/
- 获取 Token:    GET  /cgi-bin/token
- 新增草稿:      POST /cgi-bin/draft/add
- 发布草稿:      POST /cgi-bin/freepublish/submit

前置条件:
1. 微信订阅号/服务号（需已认证才能用部分接口）
2. 在 MP 后台「开发 → 基本配置」添加 IP 白名单
3. 获取 AppID 和 AppSecret
"""

import os
import time
import requests
from pathlib import Path
from typing import Optional

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class WechatPlatform(BasePlatform):
    name = "wechat"
    label = "微信公众号"

    TOKEN_URL              = "https://api.weixin.qq.com/cgi-bin/token"
    DRAFT_ADD_URL          = "https://api.weixin.qq.com/cgi-bin/draft/add"
    FREEPUBLISH_SUBMIT_URL = "https://api.weixin.qq.com/cgi-bin/freepublish/submit"
    MATERIAL_ADD_URL       = "https://api.weixin.qq.com/cgi-bin/material/add_material"

    def __init__(self, config: dict):
        super().__init__(config)
        self.appid = config.get("appid", "")
        self.appsecret = config.get("appsecret", "")
        self.draft_only = config.get("draft_only", True)
        self._access_token: Optional[str] = None
        self._token_expires = 0

    def validate_config(self) -> list[str]:
        missing = []
        if not self.appid:
            missing.append("wechat.appid")
        if not self.appsecret:
            missing.append("wechat.appsecret")
        return missing

    def _get_access_token(self) -> str:
        """获取微信公众号 access_token"""
        if self._access_token and time.time() < self._token_expires:
            return self._access_token

        resp = requests.get(self.TOKEN_URL, params={
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.appsecret,
        }, timeout=15)
        data = resp.json()
        if "access_token" in data:
            self._access_token = data["access_token"]
            self._token_expires = time.time() + data.get("expires_in", 7200) - 300
            return self._access_token
        raise Exception(f"获取 access_token 失败: {data}")

    def publish(self, result: ConvertResult) -> PublishResult:
        """
        发布流程:
        1. 将转换后的 HTML 保存到本地 output/ 目录
        2. 上传到微信草稿箱
        3. 如果 draft_only=false，自动提交发布
        """
        # 1. 保存 HTML 文件（始终执行，方便手动粘贴）
        output_dir = Path("output/wechat")
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._safe_filename(result.title or "article")
        filepath = output_dir / f"{safe_name}.html"
        filepath.write_text(result.content, encoding="utf-8")

        message = f"📄 HTML 已保存至: {filepath}"

        # 如果没有 API 凭据，仅生成 HTML
        if not self.appid or not self.appsecret:
            message += "\n👉 下一步：打开微信公众号后台 → 新建图文 → 复制 HTML 粘贴"
            return PublishResult(success=True, platform=self.name,
                                 url=f"file://{filepath.absolute()}", message=message)

        # 2. 获取 token → 上传封面图 → 添加草稿
        try:
            token = self._get_access_token()

            # 2a. 上传默认封面图（必填！）
            thumb_media_id = self._upload_default_cover(token)

            # 2b. 添加草稿
            draft_data = self._add_draft(token, result, thumb_media_id)

            if "media_id" not in draft_data:
                raise Exception(f"添加草稿失败: {draft_data}")

            media_id = draft_data["media_id"]
            message += f"\n✅ 已保存到草稿箱 (media_id: {media_id})"

            # 3. 发布草稿
            if not self.draft_only:
                pub_data = self._publish_draft(token, media_id)
                if pub_data.get("errcode") == 0:
                    publish_id = pub_data.get("publish_id", "")
                    message += f"\n🚀 已提交发布！(publish_id: {publish_id})"
                    article_url = self._get_published_url(token, publish_id)
                    if article_url:
                        message += f"\n🔗 {article_url}"
                elif pub_data.get("errcode") == 48001:
                    message += "\n💡 订阅号不支持 API 发布，请在后台手动点「发布」"
                else:
                    message += f"\n⚠️ 发布提交失败: {pub_data.get('errmsg', pub_data)}"

        except Exception as e:
            message += f"\n⚠️ API 调用失败: {e}"
            message += "\n👉 备选方案：打开微信公众号后台 → 新建图文 → 复制 HTML 粘贴"

        return PublishResult(
            success=True,
            platform=self.name,
            url=f"file://{filepath.absolute()}",
            message=message,
        )

    def _upload_default_cover(self, token: str) -> str:
        """上传默认封面图，返回 media_id（thumb_media_id 是草稿必填字段）"""
        try:
            from PIL import Image
            import io

            # 生成 900x383 纯色封面图（微信推荐尺寸）
            img = Image.new("RGB", (900, 383), color=(26, 26, 46))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)

            resp = requests.post(
                f"{self.MATERIAL_ADD_URL}?access_token={token}&type=image",
                files={"media": ("cover.png", buf, "image/png")},
                timeout=20,
            )
            data = resp.json()
            if "media_id" in data:
                return data["media_id"]
            raise Exception(f"上传封面失败: {data}")
        except ImportError:
            raise Exception("需要 Pillow 库生成封面图: pip install Pillow")

    def _add_draft(self, token: str, result: ConvertResult, thumb_media_id: str) -> dict:
        """将文章保存到微信草稿箱"""
        title = (result.title or "未命名")
        # 微信订阅号草稿标题限制约 30 字节（实测值）
        title_bytes = title.encode("utf-8")[:30]
        while title_bytes:
            try:
                title = title_bytes.decode("utf-8")
                break
            except UnicodeDecodeError:
                title_bytes = title_bytes[:-1]
        if not title_bytes:
            title = "未命名"
        articles = [{
            "title": title,
            "content": result.content,
            "thumb_media_id": thumb_media_id,       # 必填！
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
        resp = requests.post(
            f"{self.DRAFT_ADD_URL}?access_token={token}",
            json={"articles": articles},
            timeout=20,
        )
        return resp.json()

    def _publish_draft(self, token: str, media_id: str) -> dict:
        """将草稿提交发布"""
        resp = requests.post(
            f"{self.FREEPUBLISH_SUBMIT_URL}?access_token={token}",
            json={"media_id": media_id},
            timeout=20,
        )
        return resp.json()

    def _get_published_url(self, token: str, publish_id: str) -> str:
        """发布后查询文章链接"""
        try:
            resp = requests.post(
                "https://api.weixin.qq.com/cgi-bin/freepublish/getarticle",
                params={"access_token": token},
                json={"publish_id": publish_id},
                timeout=10,
            )
            data = resp.json()
            # 返回结构中有 news_item 包含 url
            news_items = data.get("news_item", [])
            if news_items:
                return news_items[0].get("url", "")
        except Exception:
            pass
        return ""

    @staticmethod
    def _safe_filename(name: str) -> str:
        """生成安全的文件名"""
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        return safe.strip()[:50] or "article"
