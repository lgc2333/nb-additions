from functools import cached_property
from typing import Annotated

from cookit.pyd import model_with_alias_generator
from nonebot import get_plugin_config, logger
from nonebot_plugin_alconna.uniseg import Target
from pydantic import AfterValidator, BaseModel, Field

from ..utils.common import parse_target, target_validator


@model_with_alias_generator(lambda x: f"lgc_req_forward_{x}")
class ConfigModel(BaseModel):
    alconna_apply_fetch_targets: bool = Field(
        default=False,
        alias="alconna_apply_fetch_targets",
    )

    target: Annotated[str | None, AfterValidator(target_validator)] = None

    @cached_property
    def parsed_target(self) -> Target | None:
        return parse_target(self.target) if self.target else None


config: ConfigModel = get_plugin_config(ConfigModel)

if not config.parsed_target:
    logger.warning("Target unset, plugin will not work")
