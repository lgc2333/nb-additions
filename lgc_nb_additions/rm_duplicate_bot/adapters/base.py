import asyncio
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from cookit import TypeDecoCollector
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target

type GroupQuitter = Callable[[BaseBot, Target], Awaitable[Any]]
type GroupJoinListener = Callable[[BaseBot, Target], Awaitable[Any]]

if TYPE_CHECKING:

    class __GroupQuitterCollector(TypeDecoCollector[BaseBot, GroupQuitter]):
        def __call__[V: GroupQuitter](self, key: type[BaseBot]) -> Callable[[V], V]: ...

    group_quitter = __GroupQuitterCollector()

else:
    group_quitter = TypeDecoCollector()


bot_group_join_listeners: list[GroupJoinListener] = []


def bot_group_join_listener[F: GroupJoinListener](func: F) -> F:
    bot_group_join_listeners.append(func)
    return func


async def dispatch_bot_group_join(bot: BaseBot, target: Target):
    return await asyncio.gather(*(f(bot, target) for f in bot_group_join_listeners))
