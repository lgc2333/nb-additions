from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from . import main as main

__plugin_meta__ = PluginMetadata(
    name="Alconna Target Sync",
    description="在 Bot 进退群时刷新 Alconna 的 Target 缓存",
    usage="没有",
    type="library",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters=inherit_supported_adapters("lgc_nb_additions.uniapi"),
    extra={"License": "MIT", "Author": "LgCookie"},
)
