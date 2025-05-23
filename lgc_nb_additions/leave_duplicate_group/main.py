import asyncio
import random
from collections import defaultdict
from collections.abc import Iterable
from contextlib import suppress

from cookit.loguru import logged_suppress, warning_suppress
from nonebot import get_bots, get_driver, logger
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target
from nonebot_plugin_uninfo import Interface, Scene, SceneType, Session, get_interface

from ..uniapi.collectors import bot_guild_join_listener, guild_quitter
from ..utils.common import call_limiter, extract_guild_scene

driver = get_driver()


async def fetch_scenes(interface: Interface):
    return [
        *await interface.get_scenes(SceneType.GROUP),
        *await interface.get_scenes(SceneType.GUILD),
    ]


async def safe_quit(bot: BaseBot, group_id: str):
    with warning_suppress("Failed to quit"):
        await guild_quitter.get_from_type_or_instance(bot)(bot, group_id)


async def quit_and_notice(
    guild_id: str,
    quit_bots: Iterable[BaseBot],
    notifier: BaseBot | None = None,
    notify_targets: Iterable[Target] | None = None,
):
    if notifier and notify_targets:
        for target in notify_targets:
            with warning_suppress(f"Failed to send tip to {target}"):
                await target.send(
                    (
                        "为避免多账号同时接收相同消息导致出现意外情况，"
                        "系统将仅保留此账号提供服务，感谢理解"
                    ),
                    bot=notifier,
                )
                break
    await asyncio.gather(*(safe_quit(b, guild_id) for b in quit_bots))


async def fetch_notify_targets(bot: BaseBot, scene: Scene) -> list[Target]:
    if scene.type <= SceneType.GROUP:
        return [Target.group(scene.id)]

    if not (itf := get_interface(bot)):
        logger.warning(f"Cannot get interface for bot {bot.self_id}")
        return []

    with warning_suppress(
        f"Failed to get bot {bot.self_id} guild {scene.id} channels",
    ):
        children = await itf.get_scenes(
            SceneType.CHANNEL_TEXT,
            parent_scene_id=scene.id,
        )
        return [Target.channel_(channel_id=x.id, guild_id=scene.id) for x in children]

    return []


quit_lock = asyncio.Lock()


async def _bot_connect_quit(bots: dict[str, BaseBot]):
    if len(bots) <= 1:
        return

    scenes_ret = await asyncio.gather(
        *(fetch_scenes(it) for b in bots.values() if (it := get_interface(b))),
    )
    bot_scenes = {k: {x.id: x for x in v} for k, v in zip(bots, scenes_ret) if v}
    del scenes_ret

    if len(bot_scenes) <= 1:
        return

    # guild_id: set[bot_id]
    guild_inner_bots = defaultdict[str, set[str]](set)
    for bot_id, guilds in bot_scenes.items():
        for guild in guilds:
            guild_inner_bots[guild].add(bot_id)

    # 群聊账号去重 使当前所有已连接 Bot 之间不存在相同群
    # 退群规则: 优先退群总量多的

    actions: list[tuple[str, list[BaseBot], BaseBot, list[Target]]] = []

    for guild_id, bot_ids in guild_inner_bots.items():
        if len(bot_ids) <= 1:
            continue

        bots_in_guild = [bots[x] for x in bot_ids]
        bots_in_guild.sort(key=lambda x: len(bot_scenes[x.self_id]))

        staying_bot = bots_in_guild.pop(0)
        for bot in bots_in_guild:
            del bot_scenes[bot.self_id][guild_id]

        scene = bot_scenes[staying_bot.self_id][guild_id]
        notify_targets = await fetch_notify_targets(staying_bot, scene)

        actions.append((guild_id, bots_in_guild, staying_bot, notify_targets))

    logger.info(f"Collected {len(actions)} actions")
    if not actions:
        return

    while True:
        args = actions.pop(0)
        logger.info(
            f"Quitting {' & '.join([x.self_id for x in args[1]])} from {args[0]}",
        )
        await quit_and_notice(*args)
        if not actions:
            break
        await asyncio.sleep(random.uniform(5, 10))


def filter_same_adapter_bot(bot: BaseBot, should_filter: dict[str, BaseBot]):
    adapter_name = bot.adapter.get_name()
    return {
        k: v for k, v in should_filter.items() if v.adapter.get_name() == adapter_name
    }


async def bot_connect_limiter_key_getter(bot: BaseBot):
    return bot.adapter.get_name()


@driver.on_bot_disconnect
@driver.on_bot_connect
@call_limiter(bot_connect_limiter_key_getter)
async def _(bot: BaseBot):
    if not guild_quitter.supported(bot):
        logger.debug(f"{bot.adapter.get_name()} not supported")
        return

    bots = filter_same_adapter_bot(bot, get_bots())
    with (
        logged_suppress("Failed to run quit task"),
        suppress(asyncio.CancelledError),
    ):
        async with quit_lock:
            await _bot_connect_quit(bots)


async def guild_join_limiter_key_getter(bot: BaseBot, ev: Session):  # noqa: ARG001
    scene = extract_guild_scene(ev)
    assert scene
    return f"{ev.adapter}:{scene.id}"


@bot_guild_join_listener
@call_limiter(guild_join_limiter_key_getter)
async def _(bot: BaseBot, ev: Session):
    if not guild_quitter.supported(bot):
        logger.debug(f"{bot.adapter.get_name()} not supported")
        return

    # 退出除被邀请 Bot 的所有本实例 Bot

    async with quit_lock:
        bots = filter_same_adapter_bot(bot, get_bots())
        if bot.self_id not in bots:
            return
        del bots[bot.self_id]
        if len(bots) <= 1:
            return
        scene = extract_guild_scene(ev)
        if not scene:
            return

        scenes_ret = await asyncio.gather(
            *(fetch_scenes(it) for b in bots.values() if (it := get_interface(b))),
        )
        bot_scenes = {k: {x.id: x for x in v} for k, v in zip(bots, scenes_ret) if v}
        del scenes_ret

        in_guild_other_bots = [bots[b] for b, s in bot_scenes.items() if scene.id in s]
        if not in_guild_other_bots:
            return

        await quit_and_notice(
            scene.id,
            in_guild_other_bots,
            bot,
            await fetch_notify_targets(bot, scene),
        )
