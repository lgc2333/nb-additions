from cookit.nonebot.localstore import ensure_localstore_path_config
from nonebot_plugin_localstore import (
    get_plugin_cache_dir,
    get_plugin_config_dir,
    get_plugin_data_dir,
)

ensure_localstore_path_config()

cache_dir = get_plugin_cache_dir()
config_dir = get_plugin_config_dir()
data_dir = get_plugin_data_dir()


def get_cache_dir(name: str):
    return cache_dir / name


def get_config_dir(name: str):
    return config_dir / name


def get_data_dir(name: str):
    return data_dir / name
