"""Force filelock FileLock(is_singleton=True) for SeleniumBase UC GUI clicks.

filelock>=3.20 detects nested locks held by different instances in the same
thread and raises Deadlock. SeleniumBase nests FileLock(pyautogui.lock) inside
`uc_gui_click_*` / `uc_gui_handle_*` (especially with retry=True).

filelock 3.32 decides `is_singleton` in FileLockMeta.__call__ BEFORE __init__,
so subclassing and setdefault()-in-__init__ (the old patch) does nothing.
We wrap the metaclass __call__ so every FileLock is constructed as a singleton.
"""
from __future__ import annotations

from pathlib import Path

_PATCHED = False


def patch_filelock_singleton(root: Path | None = None) -> bool:
    """Patch filelock so nested SeleniumBase GUI locks do not deadlock.

    Call BEFORE importing seleniumbase when possible, then call
    `rebind_seleniumbase_filelock()` after import.
    """
    global _PATCHED
    import filelock

    if getattr(filelock, "_indeed_singleton_meta_patched", False):
        _clear_stale_locks(root)
        return True

    meta = getattr(filelock, "FileLockMeta", None)
    if meta is None:
        # Older filelock: fall back to constructor wrapper.
        _Orig = filelock.FileLock

        def _FileLock(lock_file, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs["is_singleton"] = True
            return _Orig(lock_file, *args, **kwargs)

        filelock.FileLock = _FileLock  # type: ignore[misc,assignment]
    else:
        _orig_call = meta.__call__

        def _call_singleton(cls, lock_file, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs["is_singleton"] = True
            return _orig_call(cls, lock_file, *args, **kwargs)

        meta.__call__ = _call_singleton  # type: ignore[method-assign,assignment]

    filelock._indeed_singleton_meta_patched = True  # type: ignore[attr-defined]
    _PATCHED = True
    _clear_stale_locks(root)
    return True


def rebind_seleniumbase_filelock() -> None:
    """Re-point already-imported SeleniumBase modules at patched FileLock."""
    import filelock

    modules = (
        "seleniumbase.core.browser_launcher",
        "seleniumbase.fixtures.page_actions",
        "seleniumbase.core.sb_cdp",
        "seleniumbase.undetected",
    )
    for name in modules:
        try:
            mod = __import__(name, fromlist=["*"])
        except Exception:
            continue
        if hasattr(mod, "FileLock"):
            try:
                mod.FileLock = filelock.FileLock  # type: ignore[attr-defined]
            except Exception:
                pass


def _clear_stale_locks(root: Path | None) -> None:
    candidates = [Path("downloaded_files/pyautogui.lock")]
    if root is not None:
        candidates.append(root / "downloaded_files" / "pyautogui.lock")
    for lock in candidates:
        try:
            if lock.exists():
                lock.unlink()
        except Exception:
            pass
