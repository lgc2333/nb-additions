from typing import TYPE_CHECKING

from nonebot import on_notice
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v11 import (
    Bot,
    FriendRequestEvent,
    GroupIncreaseNoticeEvent,
    GroupRequestEvent,
)
from nonebot_plugin_alconna.uniseg import Target, get_target

from ..collectors import (
    FriendRequestData,
    GroupInviteRequestData,
    bot_group_join_listener,
    friend_request_listener,
    friend_request_processor,
    group_invite_request_listener,
    group_invite_request_processor,
    group_quitter,
)


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


@on_notice().handle()
async def _(bot: Bot, ev: FriendRequestEvent):
    await friend_request_listener.gather(
        bot,
        FriendRequestData(user_id=str(ev.user_id), identifier=ev.flag, raw=ev),
    )


@friend_request_processor(Bot)
async def _(bot: BaseBot, data: FriendRequestData, approve: bool) -> bool | None:
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_friend_add_request(flag=data.identifier, approve=approve)
    return None


async def group_invite_rule(ev: GroupRequestEvent):
    return ev.sub_type == "invite"


@on_notice(rule=group_invite_rule).handle()
async def _(bot: Bot, ev: GroupRequestEvent):
    await group_invite_request_listener.gather(
        bot,
        GroupInviteRequestData(
            user_id=str(ev.user_id),
            group_id=str(ev.group_id),
            identifier=ev.flag,
            raw=ev,
        ),
    )


@group_invite_request_processor(Bot)
async def _(bot: BaseBot, data: GroupInviteRequestData, approve: bool) -> bool | None:
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)
    await bot.set_group_add_request(
        flag=data.identifier,
        sub_type="invite",
        approve=approve,
    )
    return None
