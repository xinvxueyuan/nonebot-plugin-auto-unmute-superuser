# auto-unmute-superuser

NoneBot2 插件：超级用户（NoneBot 全局 `SUPERUSERS`）在群内被禁言时**自动解禁**。

## 为什么需要它

lingchu-bot 的 `protect_member` 是**操作前白名单拦截**——只挡人工命令（禁言/踢出等）。
但 bot 自身 API 调用（如 poke 戳一戳插件的惩罚逻辑直接 `set_group_ban`）白名单拦不住。
本插件是**操作后恢复**：监听群禁言事件，若被禁言者是超级用户则立即解禁，两者互补。

## 安装

将 `src/plugins/nonebot_plugin_auto_unmute_superuser` 放入 zhenxun（或任意 NoneBot2
项目）的 `plugins/` 目录即可。无第三方依赖（仅 nonebot2 + onebot v11 适配器）。

## 配置

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `SUPERUSER_UNMUTE_GROUPS` | `[]` | 启用自动解禁的群号列表；**留空 = 所有群生效** |
| `SUPERUSER_UNMUTE_POLL_ENABLED` | `true` | 是否启用周期轮询兜底（默认开启） |
| `SUPERUSER_UNMUTE_POLL_INTERVAL` | `60` | 轮询间隔（秒）；每轮对每个启用群调用一次 `get_group_member_list` |

```dotenv
# 示例：仅对指定群生效
SUPERUSER_UNMUTE_GROUPS=[1094538078]
# 轮询兜底：每 2 分钟检测一次
SUPERUSER_UNMUTE_POLL_INTERVAL=120
```

超管判定使用 NoneBot 全局 `SUPERUSERS`（`get_driver().config.superusers`），
无需额外配置。

## 行为说明

- **事件驱动（即时）**：监听 `GroupBanNoticeEvent` 的 `ban` 子事件，
  禁言发生瞬间解禁（`set_group_ban(duration=0)`）。
- **周期轮询（兜底）**：apscheduler 定时任务周期性请求平台 API
  （`get_group_member_list`），发现保护对象处于禁言状态即恢复——覆盖
  事件遗漏、bot 掉线期间被禁言等场景。两种通道对同一禁言各解禁一次
  是幂等的，无副作用。
- `block=False`：不拦截事件，OCR 插件的会话禁言状态同步等监听不受影响。
- 解禁失败（如 bot 无群管理权限）会记录异常日志，不会抛错影响其他处理。
- 轮询依赖 `nonebot-plugin-apscheduler`（zhenxun 环境已内置）。

## 设计来源

从 ocr-fanqie-novel v0.1.1 剥离（commit `8228d36`「剥离超级用户保护，交由外部 bot 处理」），
独立成插件部署。
