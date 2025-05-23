import enum
import random
import string
from datetime import UTC, datetime, timedelta

from nonebot_plugin_orm import Model
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

EXPIRE_TIME = timedelta(minutes=30)
EXPIRE_TIME_STR = "30 分钟"


class RequestStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"


class RequestType(enum.StrEnum):
    FRIEND = "friend"
    GUILD_INVITE = "guild_invite"


def generate_request_id() -> str:
    return "".join(random.sample(string.ascii_letters + string.digits, k=8))


class RequestInfo(Model):
    __tablename__ = "lgc_req_forward_request_info"

    id: Mapped[str] = mapped_column(
        String(8),
        primary_key=True,
        # default=generate_request_id,
    )
    status: Mapped[RequestStatus] = mapped_column(default=RequestStatus.PENDING)
    type: Mapped[RequestType]
    bot_id: Mapped[str]
    user_id: Mapped[str]
    identifier: Mapped[str]
    modified_at: Mapped[float] = mapped_column(
        default=lambda: datetime.now(UTC).timestamp(),
        onupdate=lambda: datetime.now(UTC).timestamp(),
    )


def is_expired(info: RequestInfo):
    modified = datetime.fromtimestamp(info.modified_at, tz=UTC)
    return (datetime.now(UTC) - modified) > EXPIRE_TIME


# async def clear_expired_data():
#     logger.info("Cleaning expired requests...")
#     async with get_session() as ss, ss.begin() as tr:
#         result = await ss.execute(
#             delete(RequestInfo).where(
#                 (datetime.now(UTC) - RequestInfo.modified_at) > EXPIRE_TIME,
#             ),
#         )
#         await tr.commit()
#     logger.success(f"{result.rowcount} rows affected")


# scheduler.add_job(clear_expired_data, trigger="interval", minutes=15)
