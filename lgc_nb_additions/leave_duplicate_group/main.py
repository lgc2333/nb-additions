import asyncio
import random
from collections import defaultdict
from collections.abc import Iterable, Iterator

from cookit.loguru import logged_suppress, warning_suppress
from debouncer import debounce
from nonebot import get_bots, get_driver, logger
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target
from nonebot_plugin_alconna.uniseg.adapters import alter_get_fetcher
from nonebot_plugin_uninfo import Session

from ..uniapi.collectors import bot_guild_join_listener, guild_quitter
from ..utils.common import extract_guild_scene

driver = get_driver()


def extract_guild_id_from_target(target: Target) -> str | None:
    if target.channel:
        return target.parent_id
    if target.private:
        return None
    return target.id


def filter_targets_by_guild_id(
    targets: Iterable[Target],
    guild_id: str,
) -> Iterator[Target]:
    return (x for x in targets if extract_guild_id_from_target(x) == guild_id)


def map_targets_by_guild(targets: Iterable[Target]) -> dict[str, set[Target]]:
    mapped = defaultdict[str, set[Target]](set)
    for x in targets:
        if g := extract_guild_id_from_target(x):
            mapped[g].add(x)
    return mapped


async def fetch_targets(bot: BaseBot) -> set[Target] | None:
    fetcher = alter_get_fetcher(bot.adapter.get_name())
    if not fetcher:
        return None
    await fetcher.refresh(bot)
    return fetcher.cache[bot.self_id]


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
                        "时雨通知：\n"
                        "检测到多个同系统账号同时在此群活动，"
                        "为避免消息重复响应出现意外情况，"
                        "系统将仅保留此账号提供服务。\n"
                        "感谢您的理解与支持！"
                    ),
                    bot=notifier,
                )
                break
    await asyncio.gather(*(safe_quit(b, guild_id) for b in quit_bots))


quit_lock = asyncio.Lock()
abort_quit_signal = asyncio.Event()


async def _bot_connect_quit(bots: dict[str, BaseBot]):
    if len(bots) <= 1:
        return

    targets_ret = await asyncio.gather(
        *(fetch_targets(b) for b in bots.values()),
    )
    bot_targets = {k: map_targets_by_guild(v) for k, v in zip(bots, targets_ret) if v}
    del targets_ret

    if len(bot_targets) <= 1:
        return

    bot_in_guilds = defaultdict[str, set[str]](set)
    for bot_id, guilds in bot_targets.items():
        for guild in guilds:
            bot_in_guilds[guild].add(bot_id)

    # 群聊账号去重 使当前所有已连接 Bot 之间不存在相同群
    # 退群规则: 优先退群总量多的

    actions: list[tuple[str, list[BaseBot], BaseBot, set[Target]]] = []

    for guild_id, bot_ids in bot_in_guilds.items():
        if len(bot_ids) <= 1:
            continue

        bots_in_group = [bots[x] for x in bot_ids]
        bots_in_group.sort(key=lambda x: len(bot_in_guilds[x.self_id]))

        staying_bot = bots_in_group.pop(0)
        for bot in bots_in_group:
            bot_in_guilds[guild_id].remove(bot.self_id)
        notify_targets = bot_targets[staying_bot.self_id][guild_id]
        actions.append((guild_id, bots_in_group, staying_bot, notify_targets))

    logger.info(f"Collected {len(actions)} actions")
    if not actions:
        return

    while True:
        if abort_quit_signal.is_set():
            abort_quit_signal.clear()
            logger.warning("Aborted")
            return
        args = actions.pop(0)
        logger.info(
            f"Quitting {' & '.join([x.self_id for x in args[1]])} from {args[0]}",
        )
        await quit_and_notice(*args)
        if not actions:
            break
        await asyncio.sleep(random.uniform(5, 10))


async def bot_connect_quit_task(bots: dict[str, BaseBot]):
    async with quit_lock:
        abort_quit_signal.clear()
        with logged_suppress("Failed to run quit task"):
            await _bot_connect_quit(bots)


def filter_same_adapter_bot(bot: BaseBot, should_filter: dict[str, BaseBot]):
    adapter_name = bot.adapter.get_name()
    return {
        k: v for k, v in should_filter.items() if v.adapter.get_name() == adapter_name
    }


@driver.on_bot_disconnect
@driver.on_bot_connect
@debounce(0.5)
async def _(bot: BaseBot):
    if not guild_quitter.supported(bot):
        logger.debug(f"{bot.adapter.get_name()} not supported")
        return

    if abort_quit_signal.is_set():
        logger.info("Aborting, then will re-run, skip execute task")
    abort_quit_signal.set()

    bots = filter_same_adapter_bot(bot, get_bots())
    asyncio.create_task(bot_connect_quit_task(bots))


@bot_guild_join_listener
@debounce(0.5)
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

        targets_ret = await asyncio.gather(
            *(fetch_targets(b) for b in bots.values()),
        )
        in_group_other_infos = [
            (b, t)
            for b, t in zip(bots.values(), targets_ret)
            if (t and next(filter_targets_by_guild_id(t, scene.id), None))
        ]

        if not in_group_other_infos:
            return

        await quit_and_notice(
            scene.id,
            (x for x, _ in in_group_other_infos),
            bot,
            in_group_other_infos[0][1],
        )
