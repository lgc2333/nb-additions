# ruff: noqa: E402

from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_alconna")

from . import main as main

__plugin_meta__ = PluginMetadata(
    name="请求转发",
    description="把 Bot 收到的好友与邀群请求转发到指定群由邀请用户处理",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters={"~onebot.v11"},
    extra={"License": "MIT", "Author": "LgCookie"},
)
