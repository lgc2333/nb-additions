from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol, override

from cookit import TypeDecoCollector
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_uninfo import Session
from pydantic import BaseModel

from ..utils.common import AsyncCallableListCollector


class BotTypeCollector[T](TypeDecoCollector[BaseBot, T]):
    def supported(self, bot: BaseBot | type[BaseBot]) -> bool:
        if not isinstance(bot, type):
            bot = type(bot)
        return bot in self.data


# region group quitter


class GuildQuitter(Protocol):
    async def __call__(self, bot: BaseBot, guild_id: str) -> bool | None: ...


class GroupQuitterCollector(BotTypeCollector[GuildQuitter]):
    if TYPE_CHECKING:

        @override
        def __call__[V: GuildQuitter](self, key: type[BaseBot]) -> Callable[[V], V]: ...


guild_quitter = GroupQuitterCollector()

# endregion

# region group join listener

type GuildJoinListener = Callable[[BaseBot, Session], Awaitable[Any]]


class BotGroupJoinListenerCollector(
    AsyncCallableListCollector[[BaseBot, Session], Any],
):
    if TYPE_CHECKING:

        @override
        def __call__[T: GuildJoinListener](self, obj: T) -> T: ...


bot_guild_join_listener = BotGroupJoinListenerCollector()

# endregion

# region friend request listener


class FriendRequestData(BaseModel):
    session: Session
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
        identifier: str,
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


class GuildInviteRequestData(BaseModel):
    session: Session
    identifier: str
    raw: Any = None


type GuildInviteRequestListener = Callable[
    [BaseBot, GuildInviteRequestData],
    Awaitable[Any],
]


class GuildInviteRequestListenerCollector(
    AsyncCallableListCollector[[BaseBot, GuildInviteRequestData], Any],
):
    if TYPE_CHECKING:

        @override
        def __call__[T: GuildInviteRequestListener](self, obj: T) -> T: ...


guild_invite_request_listener = GuildInviteRequestListenerCollector()

# endregion

# region group invite processor


class GuildInviteRequestProcessor(Protocol):
    async def __call__(
        self,
        bot: BaseBot,
        identifier: str,
        approve: bool,
    ) -> bool | None: ...


class GuildInviteRequestProcessorCollector(
    BotTypeCollector[GuildInviteRequestProcessor],
):
    if TYPE_CHECKING:

        @override
        def __call__[V: GuildInviteRequestProcessor](
            self,
            key: type[BaseBot],
        ) -> Callable[[V], V]: ...


guild_invite_request_processor = GuildInviteRequestProcessorCollector()

# endregion
