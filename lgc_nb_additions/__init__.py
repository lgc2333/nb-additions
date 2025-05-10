from nonebot import require
from nonebot.plugin import PluginMetadata

__version__ = "0.1.0"
__plugin_meta__ = PluginMetadata(
    name="LgCookie Additionals",
    description="一些个人的实用小插件",
    usage="没有",
    type="application",
    homepage="https://github.com/lgc2333/nb-additionals",
    config=None,
    supported_adapters=None,
    extra={"License": "MIT", "Author": "LgCookie"},
)

require("lgc_nb_additions.leave_duplicate_group")
