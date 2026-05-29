"""
博客园发布模块 - 通过 MetaWeblog XML-RPC API 发布文章。

博客园 MetaWeblog API:
- 端点: https://rpc.cnblogs.com/metaweblog/{blogName}
- 方法: metaWeblog.newPost / metaWeblog.editPost / blogger.getUsersBlogs
- 认证: Basic Auth (用户名 + 密码/Token)

前置条件:
1. 登录博客园 → 管理 → 设置 → 勾选「允许 MetaWeblog 博客客户端访问」
2. 记录博客名称（博客地址中的 {blogName} 部分）
"""

import xmlrpc.client
import re
from typing import Optional

from .base import BasePlatform, PublishResult
from ..converter import ConvertResult


class CnblogsPlatform(BasePlatform):
    name = "cnblogs"
    label = "博客园"

    def __init__(self, config: dict):
        super().__init__(config)
        self.blog_url = config.get("blog_url", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self._client: Optional[xmlrpc.client.ServerProxy] = None

    def validate_config(self) -> list[str]:
        missing = []
        if not self.blog_url:
            missing.append("cnblogs.blog_url")
        if not self.username:
            missing.append("cnblogs.username")
        if not self.password:
            missing.append("cnblogs.password")
        return missing

    def _get_client(self) -> xmlrpc.client.ServerProxy:
        if self._client is None:
            self._client = xmlrpc.client.ServerProxy(self.blog_url)
        return self._client

    def publish(self, result: ConvertResult) -> PublishResult:
        """
        发布到博客园。

        metaWeblog.newPost 参数:
        - blogid: 一般为 "1"（默认博客）
        - username
        - password
        - struct: { title, description (内容-HTML), categories, mt_keywords }
        - publish: True 立即发布 / False 保存为草稿
        """
        try:
            client = self._get_client()

            # 将 Markdown 转为简单 HTML（博客园有自己的 MD 渲染，也可直接传 MD）
            # 注意：博客园 API 的 description 字段支持 Markdown
            post = {
                "title": result.title or "未命名文章",
                "description": result.content,  # 直接传 Markdown
                "categories": result.meta.categories or ["默认分类"],
                "mt_keywords": result.meta.keywords or "",
            }

            post_id = client.metaWeblog.newPost(
                "1",                   # blogid
                self.username,
                self.password,
                post,
                True,                  # publish = True
            )

            # 构建文章链接
            # 格式: https://www.cnblogs.com/{blogName}/p/{postId}.html
            blog_name = self._extract_blog_name()
            url = f"https://www.cnblogs.com/{blog_name}/p/{post_id}.html"

            return PublishResult(
                success=True,
                platform=self.name,
                url=url,
                message=f"✅ 发布成功！文章 ID: {post_id}",
                draft_id=post_id,
            )

        except xmlrpc.client.Fault as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"❌ XML-RPC 错误: {e.faultString}",
            )
        except Exception as e:
            return PublishResult(
                success=False,
                platform=self.name,
                message=f"❌ 发布失败: {str(e)}",
            )

    def _extract_blog_name(self) -> str:
        """从 blog_url 中提取博客名称"""
        # https://rpc.cnblogs.com/metaweblog/myblog → myblog
        match = re.search(r"/metaweblog/(\w+)", self.blog_url)
        return match.group(1) if match else ""

    def list_blogs(self) -> list:
        """获取用户的所有博客（可用于确认配置正确）"""
        try:
            client = self._get_client()
            blogs = client.blogger.getUsersBlogs("", self.username, self.password)
            return blogs
        except Exception as e:
            return [{"error": str(e)}]
