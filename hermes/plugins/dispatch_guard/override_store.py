"""人工授权生命周期管理。"""
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

STORE_PATH = Path.home() / ".hermes" / "gate" / "overrides" / "override_store.json"

# 共享状态：记录当前处于"提案交互中"的调用
# 格式：set of "tool_name:cmd_sig"
# 由 model_tools.py 的 _gate_clarify_in_progress 同步写入同一文件
_IN_PROGRESS_PATH = Path.home() / ".hermes" / "gate" / "proposals" / "_in_progress.json"


def _read_store():
    try:
        return json.loads(STORE_PATH.read_text())
    except Exception:
        return {"overrides": []}


def _write_store(data):
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _get_in_progress() -> set:
    """读取当前处于提案交互中的调用集合。"""
    try:
        return set(json.loads(_IN_PROGRESS_PATH.read_text()).get("calls", []))
    except Exception:
        return set()


def _is_in_progress(tool_name: str, cmd: str) -> bool:
    """检查某调用是否正处于提案交互中（应跳过 consume）。"""
    sig = f"{tool_name}:{cmd[:80]}"
    return sig in _get_in_progress()


def add_override(scope: str, lifetime: str, duration_minutes: int | None = None) -> str:
    store = _read_store()
    ov_id = f"ov_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    expires_at = None
    if lifetime == "minutes" and duration_minutes:
        expires_at = (now + timedelta(minutes=duration_minutes)).timestamp()
    keywords = [w.strip().lower() for w in scope.replace("："," ").replace(":"," ").split() if len(w.strip()) > 2]
    ov = {
        "id": ov_id, "scope": scope, "scope_keywords": keywords,
        "lifetime": lifetime, "duration_minutes": duration_minutes,
        "created_at": now.isoformat(), "expires_at": expires_at,
    }
    store.setdefault("overrides", []).append(ov)
    _write_store(store)
    return ov_id


def match_and_consume(tool_name: str, tool_args: dict) -> str | None:
    # ── 提案调用保护：提案交互中（_gate_clarify_in_progress）的调用不消费 override ──
    cmd = str(tool_args.get("command", tool_args.get("code", ""))).lower()
    if _is_in_progress(tool_name, cmd):
        return None  # 跳过，不消费

    store = _read_store()
    now = time.time()
    modified = False
    matched = None
    for ov in store.get("overrides", []):
        if ov.get("expires_at") and now > ov["expires_at"]:
            continue
        ov_tool = ov.get("tool_name", "")
        if ov_tool and ov_tool != tool_name:
            continue
        keywords = ov.get("scope_keywords", [])
        if keywords and not any(kw in cmd for kw in keywords):
            continue
        matched = ov.get("lifetime", "once")
        if matched == "once":
            store["overrides"].remove(ov)
            modified = True
        break
    store["overrides"] = [o for o in store["overrides"] if not o.get("expires_at") or now <= o.get("expires_at")]
    if modified:
        _write_store(store)
    return matched
