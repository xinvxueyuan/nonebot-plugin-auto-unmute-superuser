"""超管自动解禁插件主模块。

监听 OneBot V11 群禁言事件：当 NoneBot 全局 ``SUPERUSERS`` 中的用户在
启用范围内被禁言时，自动调用 ``set_group_ban(duration=0)`` 解禁。

设计动机（操作后恢复保护）：
    lingchu-bot 的 protect_member 是**操作前白名单拦截**，只挡人工命令；
    bot 自身 API 调用（如 poke 戳一戳插件的惩罚逻辑）直接
    ``set_group_ban``，白名单拦不住。本插件是**操作后恢复**，两者互补。

注意：
    - ``block=False``：OCR 插件的 ``on_group_ban`` 同样监听本事件用于
      验证会话禁言状态同步，不能被拦截。
    - 超管判定使用 NoneBot 全局 ``SUPERUSERS``（非任何插件私有配置）。
"""

from __future__ import annotations

from nonebot import get_driver, logger, on_notice
from nonebot.adapters.onebot.v11 import Bot, GroupBanNoticeEvent
from nonebot.plugin import PluginMetadata

from .config import plugin_config

__plugin_meta__ = PluginMetadata(
    name="超管自动解禁",
    description="超级用户在群内被禁言时自动解禁（操作后恢复保护）",
    usage="自动运行，无需指令。被禁言的超级用户会自动解除禁言。",
    type="application",
    homepage="",
    supported_adapters={"nonebot.adapters.onebot.v11"},
    extra={
        "author": "xinvxueyuan",
        "priority": 1,
        "startup": False,
        "shutdown": False,
    },
)

driver = get_driver()

ban_notice = on_notice(priority=1, block=False)


@ban_notice.handle()
async def auto_unmute_superuser(
    bot: Bot,
    event: GroupBanNoticeEvent,
) -> None:
    """超级用户在启用范围内被禁言时自动解禁。"""
    if event.sub_type != "ban":
        return
    user_id = str(event.user_id)
    if user_id not in driver.config.superusers:
        return
    groups = plugin_config.superuser_unmute_groups
    if groups and event.group_id not in groups:
        return
    try:
        await bot.set_group_ban(
            group_id=event.group_id,
            user_id=event.user_id,
            duration=0,
        )
    except Exception:
        logger.exception(
            "自动解禁超级用户失败 group=%s user=%s",
            event.group_id,
            event.user_id,
        )
        return
    logger.info(
        "超级用户 %s 在群 %s 被禁言，已自动解禁",
        user_id,
        event.group_id,
    )


__all__ = ["__plugin_meta__", "plugin_config"]
