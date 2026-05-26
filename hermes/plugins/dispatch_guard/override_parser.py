"""从用户消息中解析门禁放行标记。"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class OverrideInfo:
    scope: str
    lifetime: str
    duration_minutes: int | None


_RE_ONCE = re.compile(r'门禁放行一次[：:]\s*(.+)', re.IGNORECASE)
_RE_TIMED = re.compile(r'门禁放行\s+(\d+)\s*分钟[：:]\s*(.+)', re.IGNORECASE)
_RE_SESSION = re.compile(r'门禁放行\s*本次对话[：:]\s*(.+)', re.IGNORECASE)
_RE_ANY = re.compile(r'门禁放行', re.IGNORECASE)


def parse_override_markers(text: str) -> Optional[OverrideInfo]:
    if not text:
        return None
    m = _RE_TIMED.search(text)
    if m:
        return OverrideInfo(scope=m.group(2).strip(), lifetime="minutes", duration_minutes=int(m.group(1)))
    m = _RE_ONCE.search(text)
    if m:
        return OverrideInfo(scope=m.group(1).strip(), lifetime="once", duration_minutes=None)
    m = _RE_SESSION.search(text)
    if m:
        return OverrideInfo(scope=m.group(1).strip(), lifetime="session", duration_minutes=None)
    return None


def is_override_command(text: str) -> bool:
    if not text:
        return False
    return bool(_RE_ANY.search(text))
