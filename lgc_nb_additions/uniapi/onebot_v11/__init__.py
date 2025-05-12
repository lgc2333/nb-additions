from typing import TYPE_CHECKING

from nonebot import on_notice, on_request
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v11 import (
    Bot,
    FriendRequestEvent,
    GroupIncreaseNoticeEvent,
    GroupRequestEvent,
)
from nonebot_plugin_uninfo import Uninfo

from ..collectors import (
    FriendRequestData,
    GuildInviteRequestData,
    bot_guild_join_listener,
    friend_request_listener,
    friend_request_processor,
    guild_invite_request_listener,
    guild_invite_request_processor,
    guild_quitter,
)


@guild_quitter(Bot)
async def _(bot: BaseBot, guild_id: str):
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_group_leave(group_id=int(guild_id))


async def bot_group_join_rule(ev: GroupIncreaseNoticeEvent):
    return ev.is_tome()


@on_notice(rule=bot_group_join_rule).handle()
async def _(bot: Bot, ev: Uninfo):
    await bot_guild_join_listener.gather(bot, ev)


@on_request().handle()
async def _(bot: Bot, ev: FriendRequestEvent, s: Uninfo):
    await friend_request_listener.gather(
        bot,
        FriendRequestData(session=s, identifier=ev.flag, raw=ev),
    )


@friend_request_processor(Bot)
async def _(bot: BaseBot, identifier: str, approve: bool):
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_friend_add_request(flag=identifier, approve=approve)


async def group_invite_rule(ev: GroupRequestEvent):
    return ev.sub_type == "invite"


@on_request(rule=group_invite_rule).handle()
async def _(bot: Bot, ev: GroupRequestEvent, s: Uninfo):
    await guild_invite_request_listener.gather(
        bot,
        GuildInviteRequestData(session=s, identifier=ev.flag, raw=ev),
    )


@guild_invite_request_processor(Bot)
async def _(bot: BaseBot, identifier: str, approve: bool):
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_group_add_request(flag=identifier, sub_type="invite", approve=approve)
