from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("nonebot_plugin_apscheduler")
require("nonebot_plugin_alconna")
require("nonebot_plugin_uninfo")
require("nonebot_plugin_orm")

require("lgc_nb_additions.uniapi")
require("lgc_nb_additions.target_sync")

require("lgc_nb_additions.leave_duplicate_group")
require("lgc_nb_additions.req_forward")

__version__ = "0.1.0"
__plugin_meta__ = PluginMetadata(
    name="LgCookie Additions",
    description="一些个人的实用小插件",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additions",
    config=None,
    supported_adapters=inherit_supported_adapters("lgc_nb_additions.uniapi"),
    extra={
        "License": "MIT",
        "Author": "LgCookie",
        "pmn": {"hidden": True},
    },
)
