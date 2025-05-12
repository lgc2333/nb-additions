import enum
import random
import string

from nonebot_plugin_orm import Model
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class RequestStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"


class RequestType(enum.StrEnum):
    FRIEND = "friend"
    GUILD_INVITE = "guild_invite"


def generate_request_id() -> str:
    return "".join(random.sample(string.ascii_letters + string.digits, k=8))


class ReqForwardRequestInfo(Model):
    id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        default=generate_request_id,
    )
    status: Mapped[RequestStatus] = mapped_column(default=RequestStatus.PENDING)
    type: Mapped[RequestType]
    bot_id: Mapped[str]
    user_id: Mapped[str]
    identifier: Mapped[str]
