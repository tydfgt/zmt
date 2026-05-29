"""
平台基类 —— 定义统一的发布接口。
所有平台模块继承此基类，实现 publish() 方法。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..converter import ConvertResult


@dataclass
class PublishResult:
    """发布结果"""
    success: bool
    platform: str
    url: str = ""               # 发布后的文章链接
    message: str = ""           # 成功/失败消息
    draft_id: str = ""          # 草稿 ID（微信等需要审核的平台）


class BasePlatform(ABC):
    """平台基类"""

    name: str = "base"          # 平台标识
    label: str = "未知平台"      # 平台中文名

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("enabled", True)

    @abstractmethod
    def publish(self, result: ConvertResult) -> PublishResult:
        """发布/推送内容到平台"""
        ...

    def validate_config(self) -> list[str]:
        """校验配置是否完整，返回缺失的配置项列表"""
        return []

    def pre_check(self) -> bool:
        """发布前检查（网络连通性、认证有效性等）"""
        return self.enabled
