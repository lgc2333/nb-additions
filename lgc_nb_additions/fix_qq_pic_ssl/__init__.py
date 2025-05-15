from nonebot.plugin import PluginMetadata

from . import main as main

__plugin_meta__ = PluginMetadata(
    name="修复 QQ 图床 SSL 错误",
    description="如名",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters=None,
    extra={"License": "MIT", "Author": "LgCookie"},
)
