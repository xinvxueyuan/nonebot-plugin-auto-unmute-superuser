"""storage 模块纯逻辑验证（mock localstore，不依赖 NoneBot 运行时）。

⚠️ 为什么要**按路径直接加载 `storage.py`**、而不是 `import` 插件包：
包 `__init__.py` 里是插件级 import（`nonebot.adapters` / `apscheduler` / `on_notice`
等），mock 一个 `nonebot` 根本不够用 —— 2026-10-14 实测：包入口后来加了
`get_bots`，本脚本就 `ImportError` 变成了死文件。这里只验证 storage 的纯逻辑，
所以只 mock 它真正 import 的两个东西（`nonebot.logger` / `require`、localstore 目录）。

用法（仓库根目录）：

    env -u UV_PYTHON ... uv run python scripts/verify_storage.py
"""

# ruff: noqa: T201  # 这是命令行脚本：print 就是它的输出通道

from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import sys
import tempfile
import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

_tmp = Path(tempfile.mkdtemp(prefix="aus_test_"))


def _noop(*_args: object, **_kwargs: object) -> None:
    """吃掉任意参数的占位实现（`logger.xxx` / `require` 只要求「存在且可调用」）。"""


class _FakeLocalstore(types.ModuleType):
    """假 localstore：只提供 `get_plugin_data_dir`。"""

    get_plugin_data_dir: Callable[[], Path]


fake_localstore = _FakeLocalstore("nonebot_plugin_localstore")
fake_localstore.get_plugin_data_dir = lambda: _tmp / "data"
sys.modules["nonebot_plugin_localstore"] = fake_localstore


class _FakeNonebot(types.ModuleType):
    """假 nonebot：`logger` 与 `require`（storage.py 只用到这两个）。"""

    logger: types.SimpleNamespace
    require: Callable[..., None]


fake_nonebot = _FakeNonebot("nonebot")
fake_nonebot.logger = types.SimpleNamespace(
    debug=_noop, info=_noop, exception=_noop, warning=_noop
)
fake_nonebot.require = _noop
sys.modules["nonebot"] = fake_nonebot

_STORAGE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "plugins"
    / "nonebot_plugin_auto_unmute_superuser"
    / "storage.py"
)
_spec = importlib.util.spec_from_file_location("aus_storage", _STORAGE)
assert _spec is not None and _spec.loader is not None, f"加载失败：{_STORAGE}"
storage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(storage)

# 场景 1: 记录 + 查询最近 operator
storage.record_ban_event(
    group_id=1094538078,
    user_id=2846018938,
    operator_id=2351911045,  # 群主
    duration=86400,
    banned_at=1_000_000,
)
storage.record_ban_event(
    group_id=1094538078,
    user_id=2846018938,
    operator_id=12345,  # bot 自己（后来禁言）
    duration=60,
    banned_at=2_000_000,
)
op = storage.latest_operator(group_id=1094538078, user_id=2846018938)
assert op == 12345, f"应返回最近事件 operator=12345，实际 {op}"
print("场景1 ✓ latest_operator 返回最近禁言操作者")

# 场景 2: 无记录返回 None
op = storage.latest_operator(group_id=999, user_id=999)
assert op is None, f"无记录应返回 None，实际 {op}"
print("场景2 ✓ 无记录返回 None")

# 场景 3: prune 保留最近 N 条
for i in range(3, 10):
    storage.record_ban_event(
        group_id=1094538078,
        user_id=2846018938,
        operator_id=1000 + i,
        duration=60,
        banned_at=i * 1_000_000,
    )
storage.prune_events(keep_per_pair=3)

conn = sqlite3.connect(storage._get_db_path())
try:
    count = conn.execute(
        "SELECT COUNT(*) FROM ban_events"
        " WHERE group_id=1094538078 AND user_id=2846018938"
    ).fetchone()[0]
finally:
    conn.close()
assert count == 3, f"prune 后应剩 3 条，实际 {count}"
print(f"场景3 ✓ prune 保留最近 3 条（实际 {count} 条）")

print("\nstorage 全部验证通过 ✅")
