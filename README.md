# nonebot-plugin-auto-unmute-superuser

超级用户（NoneBot 全局 `SUPERUSERS`）在群内被禁言时**自动解禁**的 NoneBot2 插件：群禁言事件即时恢复 + apscheduler 周期轮询兜底，为「操作前白名单拦截」补上**操作后恢复**。

## 功能

- **自动运行、无命令**：插件没有任何用户指令；靠下面两条通道触发解禁。
- **事件驱动（即时）**：监听 `GroupBanNoticeEvent` 的 `ban` 子事件，超管在启用范围内被禁言的瞬间调用 `set_group_ban(duration=0)` 解禁（`block=False`，不拦截事件 —— OCR 插件的会话禁言状态同步等监听不受影响）。
- **周期轮询（兜底）**：apscheduler 定时任务周期性调用 `get_group_member_list`，发现保护对象处于禁言状态即恢复 —— 覆盖事件遗漏、bot 掉线期间被禁言等场景；两条通道对同一禁言各解禁一次是幂等的，无副作用。
- **权限感知**：每次禁言事件落库（标准库 `sqlite3`），解禁前查询最近一次 operator 的角色 —— 禁言者是**群主**则静默跳过（尊重群主决定，bot 通常也无权操作），其他来源（bot 自身 API 如 poke 惩罚、管理员禁言）照常解禁；事件遗漏无记录时按目标角色兜底（目标为 admin/owner 且 bot 非 owner 则跳过）。
- **超管判定**：使用 NoneBot 全局 `SUPERUSERS`（`get_driver().config.superusers`），无插件私有名单；启用范围由 `SUPERUSER_UNMUTE_GROUPS` 控制（留空 = 全部群）。
- **失败只记日志**：解禁调用失败（如 bot 无群管理权限）记异常日志、不抛出，不影响其他处理；事件库每对 (群, 用户) 只保留最近 5 条（轮询时清理）。
- **生产现状**：本插件在 qbot 生产里**已停用**（2026-10-02 起，qbot `pyproject.toml` 的 `plugin_dirs` 中注释掉）—— 超管抽奖后 1 秒就被它解禁，抽奖对超管失效；子模块仍在（钉定版本），恢复 = 取消注释并重启。

## 配置

| 键 | 默认 | 说明 |
|---|---|---|
| `SUPERUSER_UNMUTE_GROUPS` | `[]` | 启用自动解禁的群号列表；**留空 = 所有群生效** |
| `SUPERUSER_UNMUTE_POLL_ENABLED` | `true` | 是否启用周期轮询兜底（默认开启；关闭后只剩事件驱动） |
| `SUPERUSER_UNMUTE_POLL_INTERVAL` | `60` | 轮询间隔（秒）；每轮对每个启用群调用一次 `get_group_member_list` |

```dotenv
# 示例：仅对指定群生效
SUPERUSER_UNMUTE_GROUPS=[1094538078]
# 轮询兜底：每 2 分钟检测一次
SUPERUSER_UNMUTE_POLL_INTERVAL=120
```

超管判定使用 NoneBot 全局 `SUPERUSERS`（`get_driver().config.superusers`），无需额外配置。

## 依赖与安装

- 运行依赖（以 `pyproject.toml` 的 `dependencies` 为准）：`nonebot2 >= 2.5.0`、`nonebot-adapter-onebot >= 2.4.6`（OneBot V11 适配器）、`nonebot-plugin-apscheduler >= 0.5.0`（轮询调度）、`nonebot-plugin-localstore >= 0.7.4`（禁言事件库的数据目录）
- Python：`>= 3.10`
- 安装（宿主以 git 子模块引入）：

```bash
git submodule add -b main https://github.com/xinvxueyuan/nonebot-plugin-auto-unmute-superuser.git \
  vendor/nonebot-plugin-auto-unmute-superuser
git -C vendor/nonebot-plugin-auto-unmute-superuser checkout <钉定 SHA>
```

- 宿主 `[tool.nonebot] plugin_dirs` 加一行 `vendor/nonebot-plugin-auto-unmute-superuser/src/plugins`（仓库实际布局 `src/plugins/nonebot_plugin_auto_unmute_superuser`）
- 也可直接放进 zhenxun（或任意 NoneBot2 项目）的 `plugins/` 目录；本仓自带 `[tool.nonebot] plugin_dirs = ["src/plugins"]` 供独立开发

## 测试与门禁

```bash
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run python scripts/verify_storage.py   # storage 纯逻辑验证（3 个场景）
```

- 本仓暂无 `tests/`；`scripts/verify_storage.py` 覆盖 storage 的记录 / 查询最近 operator /
  `prune_events` 三条纯逻辑：它**按路径直接加载 `storage.py`**（不 import 插件包），
  只 mock 该模块真正用到的 `nonebot.logger` / `require` 与 localstore 数据目录 ——
  2026-10-14 修过一次「包入口加了 `get_bots`，脚本 ImportError 变死文件」。
- ⚠️ 若 `uv run pyright` 只打 `Please install the new version` 而不检查（包装器版本漂移），
  用 `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`（实测 0 errors）。

## 为什么需要它

lingchu-bot 的 `protect_member` 是**操作前白名单拦截**——只挡人工命令（禁言/踢出等）。
但 bot 自身 API 调用（如 poke 戳一戳插件的惩罚逻辑直接 `set_group_ban`）白名单拦不住。
本插件是**操作后恢复**：监听群禁言事件，若被禁言者是超级用户则立即解禁，两者互补。

## 设计来源

从 ocr-fanqie-novel v0.1.1 剥离（commit `8228d36`「剥离超级用户保护，交由外部 bot 处理」），
独立成插件部署。

## 许可

MIT（见 `pyproject.toml` 的 `license` 字段；仓库暂未附 `LICENSE` 文件）。
