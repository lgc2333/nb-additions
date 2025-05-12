from nonebot.plugin import PluginMetadata, inherit_supported_adapters

from . import main as main

__plugin_meta__ = PluginMetadata(
    name="请求转发",
    description="把 Bot 收到的好友与邀群请求转发到指定群由邀请用户或超管处理",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters=inherit_supported_adapters("lgc_nb_additions.uniapi"),
    extra={"License": "MIT", "Author": "LgCookie"},
)
