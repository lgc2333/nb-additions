from pathlib import Path

from nonebot.plugin import PluginMetadata, load_plugins

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

load_plugins(str(Path(__file__).parent.joinpath("plugins").resolve()))
