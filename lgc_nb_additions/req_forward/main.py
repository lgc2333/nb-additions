from arclet.alconna import Alconna, Arg, Args, CommandMeta
from cookit import format_timedelta
from nonebot import get_bot, logger
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent
from nonebot.permission import SUPERUSER
from nonebot_plugin_alconna import Query, UniMessage, on_alconna
from nonebot_plugin_orm import async_scoped_session, get_session
from nonebot_plugin_uninfo import Uninfo

from ..uniapi.collectors import (
    FriendRequestData,
    GuildInviteRequestData,
    friend_request_listener,
    friend_request_processor,
    guild_invite_request_listener,
    guild_invite_request_processor,
)
from ..utils.common import confuse_string, extract_guild_scene
from .config import config
from .db import (
    EXPIRE_TIME,
    RequestInfo,
    RequestStatus,
    RequestType,
    generate_request_id,
    is_expired,
)

alc = Alconna(
    "confirm-req",
    Args(
        Arg("req_id", str, notice="请求ID"),
    ),
    meta=CommandMeta(description="请求转发"),
)
confirm_req = on_alconna(
    alc,
    skip_for_unmatch=False,
    auto_send_output=True,
    use_cmd_start=True,
)


@confirm_req.handle()
async def _(
    bot: BaseBot,
    ev: Uninfo,
    raw_ev: BaseEvent,
    ss: async_scoped_session,
    q_req_id: Query[str] = Query("~req_id"),
):
    async with ss.begin():
        req = await ss.get(RequestInfo, q_req_id.result)
        if (not req) or (req.status is RequestStatus.CONFIRMED) or is_expired(req):
            await UniMessage.text("未找到该请求").finish(reply_to=True)

        if req.user_id != ev.user.id and not await SUPERUSER(bot, raw_ev):
            await UniMessage.text("你无权操作此请求").finish(reply_to=True)

        try:
            bot = get_bot(req.bot_id)
            if req.type == RequestType.FRIEND:
                confirm_status = (
                    await friend_request_processor.get_from_type_or_instance(bot)(
                        bot,
                        req.identifier,
                        approve=True,
                    )
                )
            else:
                confirm_status = (
                    await guild_invite_request_processor.get_from_type_or_instance(bot)(
                        bot,
                        req.identifier,
                        approve=True,
                    )
                )
        except Exception:
            logger.exception("Failed to confirm req")
            await UniMessage.text("请求确认失败，请联系维护者").finish(reply_to=True)

        if confirm_status is not False:
            req.status = RequestStatus.CONFIRMED
            await ss.commit()

    status_msg = {
        True: "请求已通过",
        False: "请求通过失败",
        None: "已执行通过操作，是否成功通过请自行留意，如未通过请尝试重新操作，或联系维护者",
    }
    await UniMessage.text(status_msg[confirm_status]).finish(reply_to=True)


@friend_request_listener
async def _(bot: BaseBot, data: FriendRequestData):
    uid = data.session.user.id
    async with get_session() as ss:
        rid = generate_request_id()
        ss.add(
            RequestInfo(
                id=rid,
                type=RequestType.FRIEND,
                bot_id=bot.self_id,
                user_id=uid,
                identifier=data.identifier,
            ),
        )
        await ss.commit()

    logger.info(
        f"Friend request from {uid}, identifier: {data.identifier}, request id: {rid}",
    )
    if config.parsed_target:
        await config.parsed_target.send(
            UniMessage.text("收到来自 ")
            .at(uid)
            .text(
                f" ({uid}) 的好友请求"
                f"，请您在 {format_timedelta(EXPIRE_TIME)} 内发送以下内容自行同意："
                f"\nconfirm-req {rid}",
            ),
            bot=await config.parsed_target.select(),
        )


@guild_invite_request_listener
async def _(bot: BaseBot, data: GuildInviteRequestData):
    scene = extract_guild_scene(data.session)
    if not scene:
        return

    uid = data.session.user.id
    async with get_session() as ss, ss.begin() as t:
        rid = generate_request_id()
        ss.add(
            RequestInfo(
                id=rid,
                type=RequestType.GUILD_INVITE,
                bot_id=bot.self_id,
                user_id=uid,
                identifier=data.identifier,
            ),
        )
        await t.commit()

    logger.info(
        f"Guild invite request to {scene.id} from {uid}"
        f", identifier: {data.identifier}"
        f", request id: {rid}",
    )
    if config.parsed_target:
        await config.parsed_target.send(
            UniMessage.text("收到来自 ")
            .at(uid)
            .text(
                f" ({uid}) 的邀群请求 ({confuse_string(scene.id)})"
                f"，请您在 {format_timedelta(EXPIRE_TIME)} 内发送以下内容自行同意：\n"
                f"confirm-req {rid}",
            ),
            bot=await config.parsed_target.select(),
        )
