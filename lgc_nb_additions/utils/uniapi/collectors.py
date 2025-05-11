from collections.abc import Awaitable, Callable
from typing import Any, override

from cookit import TypeDecoCollector
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target

from ...utils.common import AsyncCallableListCollector

type GroupQuitter = Callable[[BaseBot, Target], Awaitable[Any]]
type GroupJoinListener = Callable[[BaseBot, Target], Awaitable[Any]]


class BotTypeCollector[T](TypeDecoCollector[BaseBot, T]):
    def supported(self, bot: BaseBot | type[BaseBot]) -> bool:
        if not isinstance(bot, type):
            bot = type(bot)
        return bot in self.data


class GroupQuitterCollector(BotTypeCollector[GroupQuitter]):
    @override
    def __call__[V: GroupQuitter](self, key: type[BaseBot]) -> Callable[[V], V]: ...


group_quitter = GroupQuitterCollector()


class BotGroupJoinListCollector(
    AsyncCallableListCollector[[BaseBot, Target], Awaitable[Any]],
):
    @override
    def __call__[T: GroupJoinListener](self, obj: T) -> T: ...


bot_group_join_listener = BotGroupJoinListCollector()
