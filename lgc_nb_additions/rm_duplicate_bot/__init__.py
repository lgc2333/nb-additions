# ruff: noqa: E402

from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_alconna")

from . import main as main

__plugin_meta__ = PluginMetadata(
    name="群聊账号去重",
    description="使当前所有已连接 Bot 之间不存在相同群",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additionals",
    config=None,
    supported_adapters={"~onebot.v11"},
    extra={"License": "MIT", "Author": "LgCookie"},
)
