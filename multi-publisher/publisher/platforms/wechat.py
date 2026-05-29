"""
微信公众号模块 - 生成公众号 HTML + 可选自动保存草稿。

微信公众平台 API:
- 文档: https://developers.weixin.qq.com/doc/offiaccount/
- 草稿箱: https://api.weixin.qq.com/cgi-bin/draft/add
- 素材管理: https://api.weixin.qq.com/cgi-bin/material/

前置条件:
1. 已认证的微信服务号/订阅号
2. 在 MP 后台配置 IP 白名单
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

    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
    DRAFT_LIST_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget"

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
            "grant_type": "client_credentials",
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
        2. 如果启用了 API 且不是 draft_only，则自动保存到草稿箱
        """
        # 1. 保存 HTML 文件（始终执行，方便手动粘贴）
        output_dir = Path("output/wechat")
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self._safe_filename(result.title or "article")
        filepath = output_dir / f"{safe_name}.html"
        filepath.write_text(result.content, encoding="utf-8")

        message = f"📄 HTML 已保存至: {filepath}\n"
        message += "👉 下一步：打开微信公众号后台 → 新建图文 → 复制 HTML 粘贴"

        # 2. 尝试自动保存到草稿箱
        if not self.draft_only and self.appid and self.appsecret:
            try:
                token = self._get_access_token()
                draft_result = self._add_draft(token, result)
                if draft_result.get("media_id"):
                    message += f"\n✅ 已自动保存到微信草稿箱 (media_id: {draft_result['media_id']})"
            except Exception as e:
                message += f"\n⚠️ 自动保存草稿失败: {e}"

        return PublishResult(
            success=True,
            platform=self.name,
            url=f"file://{filepath.absolute()}",
            message=message,
        )

    def _add_draft(self, token: str, result: ConvertResult) -> dict:
        """将文章保存到微信草稿箱"""
        articles = [{
            "title": result.title or "未命名",
            "content": result.content,
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

    @staticmethod
    def _safe_filename(name: str) -> str:
        """生成安全的文件名"""
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
        return safe.strip()[:50] or "article"
