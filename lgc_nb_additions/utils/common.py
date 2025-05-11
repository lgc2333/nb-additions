import asyncio
from collections.abc import Awaitable, Callable

from cookit import DecoListCollector, with_semaphore
from nonebot_plugin_alconna.uniseg import SupportAdapter, SupportScope, Target


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
    scope: str | None = None
    adapter: str | None = None
    if platform_str in SupportScope._member_names_:
        scope = platform_str
    elif platform_str in SupportAdapter._member_names_:
        adapter = platform_str
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
