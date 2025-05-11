from arclet.alconna import Alconna, Arg, Args, CommandMeta
from nonebot_plugin_alconna import AlconnaMatcher, Query, on_alconna

from .config import config

alc = Alconna(
    "confirm-req",
    # Args(
    #     Arg("req_id", str, notice="请求ID"),
    # ),
    meta=CommandMeta(description="请求转发"),
)
confirm_req = on_alconna(
    alc,
    skip_for_unmatch=False,
    auto_send_output=True,
    use_cmd_start=True,
)


@confirm_req.handle()
async def _(
    # q_req_id: Query[str] = Query("~req_id"),
):
    if config.parsed_target:
        await config.parsed_target.send(str(config.parsed_target))
