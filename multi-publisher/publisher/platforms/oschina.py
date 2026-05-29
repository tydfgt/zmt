"""
开源中国（OSChina）发布模块 - 通过 Open API 发布文章。

开源中国 Open API:
- 文档: https://www.oschina.net/openapi
- 认证: OAuth 2.0 (Client Credentials)
- 端点: https://www.oschina.net/action/openapi/

前置条件:
1. 登录开源中国 → 个人设置 → Open API → 创建应用
2. 获取 client_id 和 client_secret
3. 通过 client_credentials 模式获取 access_token
"""

import time
import requests
from typing import Optional

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class OschinaPlatform(BasePlatform):
    name = "oschina"
    label = "开源中国"

    API_BASE = "https://www.oschina.net/action/openapi"
    TOKEN_URL = f"{API_BASE}/token"
    PUB_ARTICLE_URL = f"{API_BASE}/article_pub"      # 发布文章
    PUB_BLOG_URL = f"{API_BASE}/blog_pub"             # 发布博客
    PUB_TWEET_URL = f"{API_BASE}/tweet_pub"           # 发动弹

    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.access_token = config.get("access_token", "")
        self.pub_type = config.get("pub_type", "article")
        self._token_expires_at = 0

    def validate_config(self) -> list[str]:
        missing = []
        # 如果有 access_token 就不需要 client_id/secret
        if not self.access_token:
            if not self.client_id:
                missing.append("oschina.client_id")
            if not self.client_secret:
                missing.append("oschina.client_secret")
        return missing

    def pre_check(self) -> bool:
        """检查 token 是否有效"""
        if not self.enabled:
            return False
        try:
            token = self._get_token()
            return bool(token)
        except Exception:
            return False

    def _get_token(self) -> str:
        """获取或刷新 access_token"""
        # 如果手动配置了长期 token
        if self.access_token and self._token_expires_at > time.time():
            return self.access_token

        resp = requests.post(self.TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        })
        data = resp.json()
        if data.get("access_token"):
            self.access_token = data["access_token"]
            expires_in = data.get("expires_in", 7200)
            self._token_expires_at = time.time() + expires_in - 300  # 提前 5 分钟刷新
            return self.access_token
        raise Exception(f"获取 Token 失败: {data}")

    def publish(self, result: ConvertResult) -> PublishResult:
        """
        发布到开源中国。

        支持类型:
        - article: 普通文章（技术问答类）
        - blog: 博客
        - tweet: 动弹（短消息，≤256字）
        """
        try:
            token = self._get_token()

            # 构建请求
            if self.pub_type == "blog":
                url = self.PUB_BLOG_URL
                params = {
                    "access_token": token,
                    "title": result.title or "未命名",
                    "content": result.content,
                    "tags": result.meta.tags_str or "",
                    "privacy": "0",       # 0=公开, 1=好友可见, 2=私有
                    "deny_comment": "0",  # 0=允许评论
                    "as_top": "0",        # 0=不置顶
                }
            else:
                url = self.PUB_ARTICLE_URL
                params = {
                    "access_token": token,
                    "title": result.title or "未命名",
                    "content": result.content,
                    "tags": result.meta.tags_str or "",
                    "catalog": result.meta.categories[0] if result.meta.categories else "综合",
                    "origin_url": "",     # 原文链接（如为转载）
                }

            resp = requests.post(url, data=params, timeout=30)
            data = resp.json()

            if data.get("code") == 200 or str(data.get("code")) == "1":
                article_id = data.get("id") or data.get("result", {}).get("id", "")
                article_url = data.get("url") or f"https://www.oschina.net/p/{article_id}"
                return PublishResult(
                    success=True,
                    platform=self.name,
                    url=article_url,
                    message=f"✅ 发布成功！文章 ID: {article_id}",
                    draft_id=str(article_id),
                )
            else:
                error_msg = data.get("msg") or data.get("message") or str(data)
                return PublishResult(
                    success=False,
                    platform=self.name,
                    message=f"❌ API 错误: {error_msg}",
                )

        except requests.RequestException as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"❌ 网络错误: {str(e)}",
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"❌ 发布失败: {str(e)}",
            )
