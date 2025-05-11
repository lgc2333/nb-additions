from nonebot import require
from nonebot.plugin import PluginMetadata, inherit_supported_adapters

require("lgc_nb_additions.uniapi")

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
    extra={"License": "MIT", "Author": "LgCookie"},
)
