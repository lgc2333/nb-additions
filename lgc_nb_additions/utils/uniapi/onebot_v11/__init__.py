from typing import TYPE_CHECKING

from nonebot import on_notice
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v11 import Bot, GroupIncreaseNoticeEvent
from nonebot_plugin_alconna.uniseg import Target, get_target

from ..collectors import bot_group_join_listener, group_quitter


@group_quitter(Bot)
async def _(bot: BaseBot, target: Target):
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_group_leave(group_id=int(target.id))


async def bot_group_join_rule(ev: GroupIncreaseNoticeEvent):
    return ev.is_tome()


@on_notice(rule=bot_group_join_rule).handle()
async def _(bot: Bot):
    target = get_target()
    await bot_group_join_listener.gather(bot, target)
