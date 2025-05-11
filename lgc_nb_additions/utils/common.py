import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from cookit import DecoListCollector


class AsyncCallableListCollector[**P, R: Awaitable](DecoListCollector[Callable[P, R]]):
    async def gather(self, *args: P.args, **kwargs: P.kwargs) -> list[Any]:
        return await asyncio.gather(*(f(*args, **kwargs) for f in self.data))
