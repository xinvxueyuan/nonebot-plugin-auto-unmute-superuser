"""插件配置。"""

from __future__ import annotations

from nonebot import get_plugin_config
from pydantic import BaseModel


class Config(BaseModel):
    """超管自动解禁插件配置。

    环境变量 ``SUPERUSER_UNMUTE_GROUPS``：启用自动解禁的群号列表。
    留空（默认）表示所有群生效；配置后仅对列表内的群生效。
    """

    superuser_unmute_groups: list[int] = []


plugin_config: Config = get_plugin_config(Config)

__all__ = ["Config", "plugin_config"]
