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

```dotenv
# 示例：仅对指定群生效
SUPERUSER_UNMUTE_GROUPS=[1094538078]
```

超管判定使用 NoneBot 全局 `SUPERUSERS`（`get_driver().config.superusers`），
无需额外配置。

## 行为说明

- 仅处理 `GroupBanNoticeEvent` 的 `ban` 子事件；`lift_ban` 不处理（解禁由本插件完成）。
- 解禁调用 `set_group_ban(duration=0)`，与原 OCR 插件剥离前的实现一致。
- `block=False`：不拦截事件，OCR 插件的会话禁言状态同步等监听不受影响。
- 解禁失败（如 bot 无群管理权限）会记录异常日志，不会抛错影响其他处理。

## 设计来源

从 ocr-fanqie-novel v0.1.1 剥离（commit `8228d36`「剥离超级用户保护，交由外部 bot 处理」），
独立成插件部署。
