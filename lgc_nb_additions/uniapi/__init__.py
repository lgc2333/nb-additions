from contextlib import suppress

from nonebot.plugin import PluginMetadata

with suppress(ImportError):
    from . import onebot_v11 as _  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="UniAPI",
    description="提供简单的统一 API 兼容层",
    usage="没有",
    type="library",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters={"~onebot.v11"},
    extra={"License": "MIT", "Author": "LgCookie"},
)
