from contextlib import suppress

with suppress(ImportError):
    from . import onebot_v11 as _  # noqa: F401
