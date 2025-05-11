from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, override

from cookit import TypeDecoCollector
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import Target
from pydantic import BaseModel

from ..utils.common import AsyncCallableListCollector


class BotTypeCollector[T](TypeDecoCollector[BaseBot, T]):
    def supported(self, bot: BaseBot | type[BaseBot]) -> bool:
        if not isinstance(bot, type):
            bot = type(bot)
        return bot in self.data


# region group quitter

type GroupQuitter = Callable[[BaseBot, Target], Awaitable[Any]]


class GroupQuitterCollector(BotTypeCollector[GroupQuitter]):
    if TYPE_CHECKING:

        @override
        def __call__[V: GroupQuitter](self, key: type[BaseBot]) -> Callable[[V], V]: ...


group_quitter = GroupQuitterCollector()

# endregion

# region group join listener

type GroupJoinListener = Callable[[BaseBot, Target], Awaitable[Any]]


class BotGroupJoinListenerCollector(
    AsyncCallableListCollector[[BaseBot, Target], Any],
):
    if TYPE_CHECKING:

        @override
        def __call__[T: GroupJoinListener](self, obj: T) -> T: ...


bot_group_join_listener = BotGroupJoinListenerCollector()

# endregion

# region friend request listener


class FriendRequestData(BaseModel):
    user_id: str
    identifier: str
    raw: Any = None


type FriendRequestListener = Callable[[BaseBot, FriendRequestData], Awaitable[Any]]


class FriendRequestListenerCollector(
    AsyncCallableListCollector[[BaseBot, FriendRequestData], Any],
):
    if TYPE_CHECKING:

        @override
        def __call__[T: FriendRequestListener](self, obj: T) -> T: ...


friend_request_listener = FriendRequestListenerCollector()

# endregion

# region friend request_processor


class FriendRequestProcessor(Protocol):
    async def __call__(
        self,
        bot: BaseBot,
        data: FriendRequestData,
        approve: bool,
    ) -> bool | None: ...


class FriendRequestProcessorCollector(BotTypeCollector[FriendRequestProcessor]):
    if TYPE_CHECKING:

        @override
        def __call__[V: FriendRequestProcessor](
            self,
            key: type[BaseBot],
        ) -> Callable[[V], V]: ...


friend_request_processor = FriendRequestProcessorCollector()

# endregion

# region group invite listener


class GroupInviteRequestData(BaseModel):
    user_id: str
    group_id: str
    identifier: str
    raw: Any = None


type GroupInviteRequestListener = Callable[
    [BaseBot, GroupInviteRequestData],
    Awaitable[Any],
]


class GroupInviteRequestListenerCollector(
    AsyncCallableListCollector[[BaseBot, GroupInviteRequestData], Any],
):
    if TYPE_CHECKING:

        @override
        def __call__[T: GroupInviteRequestListener](self, obj: T) -> T: ...


group_invite_request_listener = GroupInviteRequestListenerCollector()

# endregion

# region group invite processor


class GroupInviteRequestProcessor(Protocol):
    async def __call__(
        self,
        bot: BaseBot,
        data: GroupInviteRequestData,
        approve: bool,
    ) -> bool | None: ...


class GroupInviteRequestProcessorCollector(
    BotTypeCollector[GroupInviteRequestProcessor],
):
    if TYPE_CHECKING:

        @override
        def __call__[V: GroupInviteRequestProcessor](
            self,
            key: type[BaseBot],
        ) -> Callable[[V], V]: ...


group_invite_request_processor = GroupInviteRequestProcessorCollector()

# endregion
