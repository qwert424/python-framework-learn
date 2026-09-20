# Depends.py
from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Depends:
    _overrides: dict[Callable[..., Any], Callable[..., Any]] = {}

    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        actual = self._overrides.get(self.func, self.func)
        return actual(*args, **kwds)

    @classmethod
    def override(
        cls,
        original: Callable[..., Any],
        replacement: Callable[..., Any],
    ) -> None:
        cls._overrides[original] = replacement

    @classmethod
    def clear_override(cls, func: Callable[..., Any] | None = None) -> None:
        if func is not None:
            cls._overrides.pop(func, None)
        else:
            cls._overrides.clear()
