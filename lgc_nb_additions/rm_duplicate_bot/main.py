import asyncio
import random
from collections import defaultdict

from cookit.loguru import logged_suppress, warning_suppress
from nonebot import get_bots, get_driver, logger
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target
from nonebot_plugin_alconna.uniseg.adapters import alter_get_fetcher

from .adapters.base import bot_group_join_listener, group_quitter

driver = get_driver()


async def fetch_targets(bot: BaseBot) -> set[Target] | None:
    fetcher = alter_get_fetcher(bot.adapter.get_name())
    if not fetcher:
        return None
    await fetcher.refresh(bot)
    return fetcher.cache[bot.self_id]


async def safe_quit(bot: BaseBot, target: Target):
    with warning_suppress("Failed to quit"):
        await group_quitter.get_from_type_or_instance(bot)(bot, target)


async def quit_and_notice(
    target: Target,
    notifier: BaseBot,
    tasks: list[BaseBot],
):
    with warning_suppress("Failed to send tip"):
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
    await asyncio.gather(*(safe_quit(b, target) for b in tasks))


quit_lock = asyncio.Lock()


async def _bot_connect_quit(bots: dict[str, BaseBot]):
    targets_ret = await asyncio.gather(
        *(fetch_targets(b) for b in bots.values()),
    )

    bot_targets = [(k, v) for k, v in zip(bots.values(), targets_ret) if v]
    del targets_ret

    if len(bot_targets) <= 1:
        return

    bot_groups = [(k, {t for t in v if not t.private}) for k, v in bot_targets]
    del bot_targets

    bot_group_count: dict[str, int] = {b.self_id: len(g) for b, g in bot_groups}

    group_id_map: dict[str, Target] = {}
    for _, groups in bot_groups:
        for g in (v for v in groups if v.id not in group_id_map):
            group_id_map[g.id] = g

    group_bots: dict[str, list[BaseBot]] = defaultdict(list)
    for bot, groups in bot_groups:
        for g in groups:
            group_bots[g.id].append(bot)

    del bot_groups

    # 群聊账号去重 使当前所有已连接 Bot 之间不存在相同群
    # 退群规则: 优先退群总量多的

    actions: list[tuple[Target, BaseBot, list[BaseBot]]] = []

    for group_id, bots_in_group in group_bots.items():
        if len(bots_in_group) <= 1:
            continue

        bots_in_group.sort(key=lambda x: bot_group_count[x.self_id])

        group_target = group_id_map[group_id]
        staying_bot = bots_in_group[-1]
        leaving_bots = bots_in_group[:-1]
        actions.append((group_target, staying_bot, leaving_bots))

    logger.info(f"Collected {len(actions)} actions")
    if not actions:
        return

    while True:
        args = actions.pop(0)
        logger.info(f"Quitting {[x.self_id for x in args[2]]} from {args[0].id}")
        await quit_and_notice(*args)
        if not actions:
            break
        await asyncio.sleep(random.uniform(5, 10))


async def bot_connect_quit_task(bots: dict[str, BaseBot]):
    async with quit_lock:
        with logged_suppress("Failed to run quit task"):
            await _bot_connect_quit(bots)


def filter_same_adapter_bot(bot: BaseBot, should_filter: dict[str, BaseBot]):
    adapter_name = bot.adapter.get_name()
    return {
        k: v for k, v in should_filter.items() if v.adapter.get_name() == adapter_name
    }


@driver.on_bot_connect
async def _(bot: BaseBot):
    if type(bot) not in group_quitter.data:
        logger.debug(f"{bot.adapter.get_name()} not supported")
        return
    bots = filter_same_adapter_bot(bot, get_bots())
    if len(bots) <= 1:
        return
    asyncio.create_task(bot_connect_quit_task(bots))


@bot_group_join_listener
async def _(bot: BaseBot, target: Target):
    if type(bot) not in group_quitter.data:
        logger.debug(f"{bot.adapter.get_name()} not supported")
        return

    bots = filter_same_adapter_bot(bot, get_bots())
    del bots[bot.self_id]
    if len(bots) <= 1:
        return

    # 退出除被邀请 Bot 的所有本实例 Bot

    targets_ret = await asyncio.gather(
        *(fetch_targets(b) for b in bots.values()),
    )
    in_group_other_bots = [
        b
        for b, t in zip(bots.values(), targets_ret)
        if (t and next((x for x in t if x.id == target.id and (not x.private)), None))
    ]

    if not in_group_other_bots:
        return

    async with quit_lock:
        await quit_and_notice(target, bot, in_group_other_bots)
