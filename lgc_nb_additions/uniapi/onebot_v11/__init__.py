import asyncio
import random
import time
from typing import TYPE_CHECKING, cast

from cookit.loguru import warning_suppress
from nonebot import get_driver, logger, on_notice, on_request
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v11 import (
    Bot,
    FriendRequestEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupRequestEvent,
)
from nonebot_plugin_alconna.uniseg import get_bot
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_uninfo import (
    Scene,
    SceneType,
    Session,
    SupportAdapter,
    SupportScope,
    Uninfo,
    User,
)
from pydantic import BaseModel, RootModel

from ...utils.store import get_cache_dir
from ..collectors import (
    FriendRequestData,
    GuildInviteRequestData,
    bot_guild_join_listener,
    bot_guild_quit_listener,
    friend_request_listener,
    friend_request_processor,
    guild_invite_request_listener,
    guild_invite_request_processor,
    guild_quitter,
)

driver = get_driver()

DOUBT_FRIEND_PFX = "doubt:"
LAST_FETCH_DOUBT_FRIENDS_TIME_FILE = (
    get_cache_dir("uniapi") / "onebot_v11_last_fetch_doubt_friends_time.txt"
)


class DoubtFriendRequestInfo(BaseModel):
    flag: str
    uin: str
    nick: str
    source: str
    reason: str
    msg: str
    group_code: str
    time: int


GetDoubtFriendsAddRequestsData = RootModel[list[DoubtFriendRequestInfo]]


def set_last_fetch_doubt_friends_time(v: int | None = None) -> int:
    if not v:
        v = int(time.time())
    if not (p := LAST_FETCH_DOUBT_FRIENDS_TIME_FILE.parent).exists():
        p.mkdir(parents=True)
    LAST_FETCH_DOUBT_FRIENDS_TIME_FILE.write_text(str(v), "u8")
    return v


def get_last_fetch_doubt_friends_time() -> int:
    if not LAST_FETCH_DOUBT_FRIENDS_TIME_FILE.exists():
        return set_last_fetch_doubt_friends_time()
    return int(LAST_FETCH_DOUBT_FRIENDS_TIME_FILE.read_text("u8"))


set_last_fetch_doubt_friends_time()


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


async def bot_group_quit_rule(ev: GroupDecreaseNoticeEvent):
    return ev.is_tome()


@on_notice(rule=bot_group_quit_rule).handle()
async def _(bot: Bot, ev: Uninfo):
    await bot_guild_quit_listener.gather(bot, ev)


@on_request().handle()
async def _(bot: Bot, ev: FriendRequestEvent, s: Uninfo):
    await friend_request_listener.gather(
        bot,
        FriendRequestData(session=s, identifier=ev.flag, raw=ev),
    )


async def fetch_and_doubt_req(
    bot: Bot,
    time_after: int | None = None,
    count: int = 10,
) -> list[DoubtFriendRequestInfo]:
    with warning_suppress(
        f"Failed to fetch or dispatch doubt friend requests of bot {bot.self_id}",
    ):
        raw = await bot.get_doubt_friends_add_request(count=count)
        data = GetDoubtFriendsAddRequestsData.model_validate(raw).root
        if not time_after:
            return data
        index = next((i for i, x in enumerate(data) if x.time < time_after), 0)
        if index > 0:
            return data[:index]
    return []


async def get_and_dispatch_doubt_friend_req(bots: list[Bot] | None = None):
    t = get_last_fetch_doubt_friends_time()
    set_last_fetch_doubt_friends_time()

    bots = bots or cast("list[Bot]", await get_bot(adapter="OneBot V11"))
    bot_requests = await asyncio.gather(*(fetch_and_doubt_req(b, t) for b in bots))
    for bot, requests in zip(bots, bot_requests):
        for req in requests:
            data = FriendRequestData(
                session=Session(
                    self_id=bot.self_id,
                    adapter=SupportAdapter.onebot11,
                    scope=SupportScope.qq_client,
                    scene=Scene(id=req.uin, type=SceneType.PRIVATE, name=req.nick),
                    user=User(id=req.uin, name=req.nick),
                ),
                identifier=f"{DOUBT_FRIEND_PFX}{req.flag}",
                raw=req,
            )
            asyncio.create_task(
                logger.catch(
                    friend_request_listener.gather,
                )(bot, data),
            )
            await asyncio.sleep(random.uniform(2, 5))


scheduler.add_job(get_and_dispatch_doubt_friend_req, "interval", minutes=1)


@driver.on_bot_connect
async def _(bot: Bot):
    asyncio.create_task(logger.catch(get_and_dispatch_doubt_friend_req)([bot]))


@friend_request_processor(Bot)
async def _(bot: BaseBot, identifier: str, approve: bool):
    if TYPE_CHECKING:
        assert isinstance(bot, Bot)

    if identifier.startswith(DOUBT_FRIEND_PFX):
        if approve:
            flag = identifier[len(DOUBT_FRIEND_PFX) :]
            await bot.set_doubt_friends_add_request(flag=flag)
        return

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
