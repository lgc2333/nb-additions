import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable, Coroutine
from contextlib import suppress
from functools import partial, wraps
from typing import Any

from cookit import DecoListCollector, with_semaphore
from debouncer import debounce
from debouncer.debounce import Debounced
from nonebot.adapters import Bot as BaseBot
from nonebot_plugin_alconna.uniseg import (
    SupportAdapter,
    SupportScope,
    Target,
    get_bot as alconna_get_bot,
)
from nonebot_plugin_alconna.uniseg.adapters import alter_get_fetcher
from nonebot_plugin_uninfo import Session


class AsyncCallableListCollector[**P, R](DecoListCollector[Callable[P, Awaitable[R]]]):
    def __init__(
        self,
        data: list[Callable[P, Awaitable[R]]] | None = None,
        concurrency: int | None = None,
    ) -> None:
        super().__init__(data)
        self.concurrency = concurrency

    async def gather(self, *args: P.args, **kwargs: P.kwargs) -> list[R]:
        if self.concurrency:
            sem = asyncio.Semaphore(self.concurrency)
            callables = [with_semaphore(sem)(f) for f in self.data]
        else:
            callables = self.data
        return await asyncio.gather(*(f(*args, **kwargs) for f in callables))


def parse_target(v: str) -> Target:
    """<(scope)/(platform)>[:private/channel][:(parent_id)]<:(target_id)>
    圆括号中的内容需要替换成对应意义的信息，尖括号代表必选项，方括号代表可选"""

    args = v.split(":")

    platform_str = args.pop(0)
    scope: SupportScope | None = None
    adapter: SupportAdapter | None = None
    if platform_str in SupportScope.__members__:
        scope = SupportScope.__members__[platform_str]
    elif platform_str in SupportAdapter.__members__:
        adapter = SupportAdapter.__members__[platform_str]
    else:
        raise ValueError("Wrong scope / adapter")

    if not len(args):
        raise ValueError("Target syntax error")
    private = False
    channel = False
    if (private := args[0] == "private") or (channel := args[0] == "channel"):
        args.pop(0)

    if not (1 <= (args_len := len(args)) <= 2):
        raise ValueError("Target syntax error")
    parent_id = args.pop(0) if args_len > 1 else ""
    target_id = args.pop(0)
    return Target(
        id=target_id,
        parent_id=parent_id,
        channel=channel,
        private=private,
        scope=scope,
        adapter=adapter,
    )


def target_validator(v: str | None) -> str | None:
    if v:
        parse_target(v)
    return v


async def bot_for_target_predicate(target: Target, bot: BaseBot) -> bool:
    fetcher = alter_get_fetcher(bot.adapter.get_name())
    if not fetcher:
        return False
    async for x in fetcher.fetch(bot, target):
        if x.verify(target):
            return True
    return False


async def get_bot_for_target(target: Target) -> BaseBot:
    return await alconna_get_bot(
        predicate=partial(bot_for_target_predicate, target),
        index=0,
    )


def extract_guild_scene(ev: Session):
    if (s := ev.group) or (s := ev.guild):
        return s
    return None


def confuse_string(string: str, head: int = 2, tail: int = 2, symbol: str = "*") -> str:
    if not string:
        return ""
    string_len = len(string)
    if string_len <= head + tail:
        return string
    return string[:head] + symbol * (string_len - head - tail) + string[-tail:]


type CoT[T] = Coroutine[Any, Any, T]
type DebounceDeco[**P, R] = Callable[
    [Callable[P, CoT[R]]],
    Debounced[P, CoT[R | None]],
]


def call_limiter[K, **P, R](
    key_getter: Callable[P, CoT[K]],
    debounce_time: float = 0.5,
):
    def deco(f: Callable[P, CoT[R]]) -> Callable[P, CoT[R | None]]:
        debounces = defaultdict[K, DebounceDeco[[], R | None]](
            lambda: debounce(debounce_time),
        )
        tasks: dict[K, asyncio.Task[R]] = {}

        @wraps(f)
        async def wrapper(*args: P.args, **kwargs: P.kwargs):
            key = await key_getter(*args, **kwargs)

            async def create_task():
                if key in tasks:
                    tasks[key].cancel()
                task = asyncio.create_task(f(*args, **kwargs))
                tasks[key] = task
                with suppress(asyncio.CancelledError):
                    return await task
                return None

            return await debounces[key](create_task)()

        return wrapper

    return deco
