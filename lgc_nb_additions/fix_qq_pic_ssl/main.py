import ssl
from functools import wraps

from httpx import AsyncClient

_old_init = AsyncClient.__init__


@wraps(_old_init)
def _new_init(self: AsyncClient, **kwargs):
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT")
    kwargs["verify"] = context
    _old_init(self, **kwargs)


AsyncClient.__init__ = _new_init
