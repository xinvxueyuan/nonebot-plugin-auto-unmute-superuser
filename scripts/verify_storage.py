"""storage 模块纯逻辑验证（mock localstore，不依赖 NoneBot 运行时）。"""

import sys
import tempfile
import types
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="aus_test_"))

fake_localstore = types.ModuleType("nonebot_plugin_localstore")
fake_localstore.get_plugin_data_dir = lambda: _tmp / "data"  # noqa: E731
sys.modules["nonebot_plugin_localstore"] = fake_localstore

fake_nonebot = types.ModuleType("nonebot")
fake_nonebot.logger = types.SimpleNamespace(
    debug=lambda *a, **k: None,
    info=lambda *a, **k: None,
    exception=lambda *a, **k: None,
    warning=lambda *a, **k: None,
)
fake_nonebot.require = lambda name: None  # noqa: E731
sys.modules["nonebot"] = fake_nonebot

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "plugins"))

from nonebot_plugin_auto_unmute_superuser import storage  # noqa: E402

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
import sqlite3  # noqa: E402

conn = sqlite3.connect(storage._get_db_path())
try:
    count = conn.execute(
        "SELECT COUNT(*) FROM ban_events WHERE group_id=1094538078 AND user_id=2846018938"
    ).fetchone()[0]
finally:
    conn.close()
assert count == 3, f"prune 后应剩 3 条，实际 {count}"
print(f"场景3 ✓ prune 保留最近 3 条（实际 {count} 条）")

print("\nstorage 全部验证通过 ✅")
