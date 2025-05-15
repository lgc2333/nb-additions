from cookit.loguru import warning_suppress
from nonebot import logger
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg.adapters import alter_get_fetcher
from nonebot_plugin_uninfo import Session

from ..uniapi.collectors import bot_guild_join_listener, bot_guild_quit_listener
from ..utils.common import call_limiter


async def limiter_key_getter(bot: BaseBot, _: Session):  # noqa: ARG001
    return bot.self_id


@bot_guild_join_listener
@bot_guild_quit_listener
@call_limiter(limiter_key_getter)
async def _(bot: BaseBot, _: Session):
    if fn := alter_get_fetcher(bot.adapter.get_name()):
        logger.info(f"Refreshing targets of bot {bot.self_id}")
        with warning_suppress(f"Failed to refresh targets of bot {bot.self_id}"):
            await fn.refresh(bot)
            logger.success(f"Finished refreshing targets of bot {bot.self_id}")
