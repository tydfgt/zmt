"""
开源中国（OSChina）发布模块 - 通过 Open API 发布博客/动弹。

官方 API 文档: https://www.oschina.net/openapi/docs
ApiFox 文档:   https://s.apifox.cn/apidoc/docs-site/1241446/doc-1279573

认证方式: OAuth 2.0 (authorization_code 模式)
- ⚠️ 不支持 client_credentials！必须走 Web 授权流程
- 获取 token 后有效期约为 12 小时
- 过期后可用 refresh_token 刷新

API 列表:
- blog_pub:  POST /action/openapi/blog_pub   (发布博客, JSON body)
- tweet_pub: POST /action/openapi/tweet_pub  (发动弹, JSON body)

前置条件:
1. 登录 https://www.oschina.net → 头像 → 个人中心 → Open API
2. 创建应用，获取 client_id 和 client_secret
3. 设置回调地址（如 https://www.oschina.net）
4. 首次使用时，工具会打开浏览器引导你完成 OAuth 授权
5. 授权后把 refresh_token 保存到 config.yaml，后续无需反复授权
"""

import time
import webbrowser
import requests
from typing import Optional

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class OschinaPlatform(BasePlatform):
    name = "oschina"
    label = "开源中国"

    # ---- API 端点 ----
    AUTH_URL    = "https://www.oschina.net/action/oauth2/authorize"
    TOKEN_URL   = "https://www.oschina.net/action/openapi/token"
    BLOG_PUB    = "https://www.oschina.net/action/openapi/blog_pub"
    TWEET_PUB   = "https://www.oschina.net/action/openapi/tweet_pub"

    # ---- 博客系统分类（classification 参数，必填整数） ----
    BLOG_CLASSIFICATIONS = {
        "编程语言": 428, "移动开发": 429, "前端开发": 430,
        "后端开发": 431, "数据库": 432,   "云计算": 433,
        "AI/机器学习": 434, "开源项目": 435, "操作系统": 436,
        "软件工具": 437, "其他": 438,
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.client_id     = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.redirect_uri  = config.get("redirect_uri", "https://www.oschina.net")
        self.access_token  = config.get("access_token", "")
        self.refresh_token = config.get("refresh_token", "")
        self.pub_type      = config.get("pub_type", "blog")          # blog / tweet
        self.classification = config.get("classification", 428)      # 默认「编程语言」
        self.save_as_draft  = config.get("save_as_draft", 0)         # 0=发布, 1=草稿
        self.privacy        = config.get("privacy", "0")             # "0"=公开

        self._token_expires_at = 0.0

    # ================================================================
    # 配置校验
    # ================================================================

    def validate_config(self) -> list[str]:
        missing = []
        if self.access_token:
            return missing
        if not self.client_id:
            missing.append("oschina.client_id")
        if not self.client_secret:
            missing.append("oschina.client_secret")
        return missing

    def pre_check(self) -> bool:
        """轻量连通性检查（不触发浏览器 OAuth 弹窗）"""
        if not self.enabled:
            return False
        # 有 token 时验证是否过期
        if self.access_token and self._token_expires_at > time.time() + 60:
            return True
        # 有 refresh_token 时尝试静默刷新
        if self.refresh_token:
            try:
                self._refresh_token()
                return True
            except Exception:
                pass
        # 没 token 但配置完整 → 标记为需要授权
        if self.client_id and self.client_secret:
            return True  # 配置完整，但需要首次授权
        return False

    # ================================================================
    # OAuth 2.0 认证（authorization_code 模式）
    # ================================================================

    def _get_token(self) -> str:
        """获取有效的 access_token：缓存 → refresh → 浏览器授权"""
        # 1. token 还没过期
        if self.access_token and self._token_expires_at > time.time() + 60:
            return self.access_token

        # 2. 尝试用 refresh_token 刷新
        if self.refresh_token:
            try:
                return self._refresh_token()
            except Exception:
                pass

        # 3. 打开浏览器重新授权
        return self._web_auth()

    def _web_auth(self) -> str:
        """Web 授权流程：打开浏览器 → 用户点授权 → 复制 code → 换 token"""
        auth_url = (
            f"{self.AUTH_URL}"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
        )

        print(f"\n{'='*60}")
        print(f"🔐 开源中国 OAuth2 授权")
        print(f"{'='*60}")
        print(f"浏览器将打开授权页面，请点击「授权」")
        print(f"授权后会跳转到 {self.redirect_uri}")
        print(f"复制地址栏中 code= 后面的值，粘贴到下面：")
        print(f"{'='*60}\n")

        webbrowser.open(auth_url)
        code = input("请输入 code: ").strip()
        if not code:
            raise Exception("未输入授权码，已取消")

        return self._exchange_code(code)

    def _exchange_code(self, code: str) -> str:
        """用授权码交换 access_token"""
        resp = requests.post(self.TOKEN_URL, json={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
            "dataType": "json",
        }, timeout=15)
        return self._save_token(resp.json())

    def _refresh_token(self) -> str:
        """用 refresh_token 刷新 access_token"""
        resp = requests.post(self.TOKEN_URL, json={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "dataType": "json",
        }, timeout=15)
        return self._save_token(resp.json())

    def _save_token(self, data: dict) -> str:
        """保存并返回 access_token"""
        if "access_token" not in data:
            raise Exception(f"获取 Token 失败: {data}")

        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", "")
        expires_in = data.get("expires_in", 43200)
        self._token_expires_at = time.time() + expires_in - 300

        print(f"✅ Token 就绪（有效期 {expires_in // 3600} 小时）")
        if self.refresh_token:
            print(f"💡 复制下面这行到 config.yaml 的 oschina 段，以后不用重复授权：")
            print(f"   refresh_token: {self.refresh_token}")

        return self.access_token

    # ================================================================
    # 发布
    # ================================================================

    def publish(self, result: ConvertResult) -> PublishResult:
        """发布到开源中国。pub_type: blog（默认）/ tweet"""
        try:
            token = self._get_token()
            if self.pub_type == "tweet":
                return self._publish_tweet(token, result)
            else:
                return self._publish_blog(token, result)
        except requests.RequestException as e:
            return PublishResult(False, self.name, message=f"❌ 网络错误: {e}")
        except Exception as e:
            return PublishResult(False, self.name, message=f"❌ 发布失败: {e}")

    def _publish_blog(self, token: str, result: ConvertResult) -> PublishResult:
        """
        发布博客 (POST /action/openapi/blog_pub)。

        官方要求（务必遵守）:
        - Content-Type: application/json  ← 不是 form-encoded！
        - 必填: access_token, title, content, classification
        - 成功: {"error": 200, "error_description": "操作成功完成"}
        - 失败: {"error": 500, "error_description": "错误原因"}
        """
        # 自动匹配分类 ID
        classification = self.classification
        for cat_name, cat_id in self.BLOG_CLASSIFICATIONS.items():
            if result.meta.categories and cat_name in str(result.meta.categories):
                classification = cat_id
                break

        payload = {
            "access_token": token,
            "title": result.title or "未命名文章",
            "content": result.content,
            "classification": classification,       # 必填！整数
            "save_as_draft": self.save_as_draft,    # 0=发布, 1=草稿
            "abstracts": result.meta.summary or "", # 摘要
            "tags": result.meta.tags_str or "",     # 逗号分隔
            "type": 1,                              # 1=原创, 4=转载
            "privacy": self.privacy,                # "0"=公开
            "deny_comment": "0",                    # "0"=允许评论
            "auto_content": "0",                    # "0"=不自动生成目录
            "as_top": "0",                          # "0"=不置顶
        }

        resp = requests.post(self.BLOG_PUB, json=payload, timeout=30)
        data = resp.json()

        if data.get("error") == 200:
            blog_id = data.get("id", "")
            blog_url = data.get("url", "")
            if not blog_url and blog_id:
                blog_url = f"https://my.oschina.net/u/xxx/blog/{blog_id}"
            return PublishResult(
                success=True, platform=self.name,
                url=blog_url,
                message=f"✅ 博客发布成功！{data.get('error_description', '')}",
                draft_id=str(blog_id),
            )
        else:
            return PublishResult(
                success=False, platform=self.name,
                message=f"❌ 博客发布失败: {data.get('error_description', str(data))}",
            )

    def _publish_tweet(self, token: str, result: ConvertResult) -> PublishResult:
        """
        发动弹 (POST /action/openapi/tweet_pub)。

        动弹是类似微博的短消息，适合发简短动态。
        """
        msg = result.content[:256]

        resp = requests.post(self.TWEET_PUB, json={
            "access_token": token,
            "msg": msg,
        }, timeout=30)
        data = resp.json()

        if data.get("error") == 200:
            return PublishResult(
                success=True, platform=self.name,
                message=f"✅ 动弹发布成功！{data.get('error_description', '')}",
            )
        else:
            return PublishResult(
                success=False, platform=self.name,
                message=f"❌ 动弹发布失败: {data.get('error_description', str(data))}",
            )
