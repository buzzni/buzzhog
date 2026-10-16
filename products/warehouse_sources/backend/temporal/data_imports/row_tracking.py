import uuid
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypeVar

from django.conf import settings

import structlog
from redis import exceptions as redis_exceptions
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from posthog.exceptions_capture import capture_exception
from posthog.redis import get_async_client

if TYPE_CHECKING:
    pass


logger = structlog.get_logger(__name__)

T = TypeVar("T")

# A connect blip, a "too many open files" refusal and a replica redirect during a failover all
# clear on their own, usually inside a second. Row tracking runs inside the import that calls it,
# so the retry stays short: the import waits for every attempt.
_retry_transient_redis_errors = retry(
    retry=retry_if_exception_type(
        (
            redis_exceptions.ConnectionError,
            redis_exceptions.TimeoutError,
            redis_exceptions.ReadOnlyError,
        )
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.1, max=1),
    reraise=True,
)


def _get_hash_key(team_id: int) -> str:
    return f"posthog:data_warehouse_row_tracking:{team_id}"


def _redis_url() -> str | None:
    """The dedicated warehouse Redis, or the shared one when no dedicated instance is configured.

    The fallback used to be localhost. Nothing listens there in a deployed environment, so an
    environment that sets neither DATA_WAREHOUSE_REDIS_HOST nor POSTHOG_REDIS_HOST turned every
    row-tracking call into a connection error. The shared Redis is the same fallback the other
    per-product instances take (see SESSION_RECORDING_REDIS_URL), and settings refuse to start
    without it, so a genuinely unconfigured install fails at startup instead of here.
    """
    if settings.DATA_WAREHOUSE_REDIS_HOST and settings.DATA_WAREHOUSE_REDIS_PORT:
        return f"redis://{settings.DATA_WAREHOUSE_REDIS_HOST}:{settings.DATA_WAREHOUSE_REDIS_PORT}/"

    return settings.REDIS_URL or None


async def _fail_open(description: str, command: Callable[[], Awaitable[T]], fallback: T) -> T:
    """Run a row-tracking Redis command, retry a transient failure, then return `fallback`.

    Row tracking is bookkeeping for the billing estimate, so no Redis failure may reach the import
    that called it. A retried command runs twice if Redis applied the first attempt and the reply
    was lost, which at most counts one batch of rows twice until the next sync resets the counter.
    """
    try:
        return await _retry_transient_redis_errors(command)()
    except redis_exceptions.RedisError as e:
        await logger.awarning(f"Redis error while {description}, failing open", error=str(e))
        return fallback


@asynccontextmanager
async def _get_redis():
    """Returns an async Redis client for row tracking operations."""
    redis = None
    url = _redis_url()

    if url is None:
        await logger.aerror("No Redis is configured for row tracking, failing open")
    else:
        try:
            client = get_async_client(url)

            async def _ping() -> None:
                await client.ping()

            # get_async_client only builds a lazy client, so the ping is the first real connection
            # attempt. Hand the client to the caller only once it answers, so that a caller's
            # `if not redis: return` guard skips the real command instead of raising the same
            # error uncaught.
            await _retry_transient_redis_errors(_ping)()
            redis = client
        except redis_exceptions.RedisError as e:
            # Row tracking already fails open when redis is unavailable (every caller
            # checks `if not redis: return`), so a Redis-side blip - unreachable, refusing
            # writes because RDB snapshotting failed, loading, etc. - isn't a bug, and
            # shouldn't be reported to error tracking.
            await logger.awarning("Redis error while getting row tracking client, failing open", error=str(e))
        except Exception as e:
            capture_exception(e)

    yield redis


async def setup_row_tracking(team_id: int, schema_id: uuid.UUID | str) -> None:
    async with _get_redis() as redis:
        if not redis:
            return

        async def _command() -> None:
            await redis.hset(_get_hash_key(team_id), str(schema_id), 0)
            await redis.expire(_get_hash_key(team_id), 60 * 60 * 24 * 7)  # 7 day expire

        await _fail_open("setting up row tracking", _command, None)


async def increment_rows(team_id: int, schema_id: uuid.UUID | str, rows: int) -> None:
    async with _get_redis() as redis:
        if not redis:
            return

        async def _command() -> None:
            await redis.hincrby(_get_hash_key(team_id), str(schema_id), rows)

        await _fail_open("incrementing row tracking", _command, None)


async def decrement_rows(team_id: int, schema_id: uuid.UUID | str, rows: int) -> None:
    async with _get_redis() as redis:
        if not redis:
            return

        async def _command() -> None:
            if not await redis.hexists(_get_hash_key(team_id), str(schema_id)):
                return

            value = await redis.hget(_get_hash_key(team_id), str(schema_id))
            if not value:
                return

            value_int = int(value)
            if value_int - rows < 0:
                await redis.hset(_get_hash_key(team_id), str(schema_id), 0)
            else:
                await redis.hincrby(_get_hash_key(team_id), str(schema_id), -rows)

        await _fail_open("decrementing row tracking", _command, None)


async def finish_row_tracking(team_id: int, schema_id: uuid.UUID | str) -> None:
    async with _get_redis() as redis:
        if not redis:
            return

        async def _command() -> None:
            await redis.hdel(_get_hash_key(team_id), str(schema_id))

        await _fail_open("finishing row tracking", _command, None)


async def get_rows(team_id: int, schema_id: uuid.UUID | str) -> int:
    async with _get_redis() as redis:
        if not redis:
            return 0

        async def _command() -> int:
            if await redis.hexists(_get_hash_key(team_id), str(schema_id)):
                value = await redis.hget(_get_hash_key(team_id), str(schema_id))
                if value:
                    return int(value)

            return 0

        return await _fail_open("reading row tracking", _command, 0)


async def get_all_rows_for_team(team_id: int) -> int:
    async with _get_redis() as redis:
        if not redis:
            return 0

        async def _command() -> int:
            pairs = await redis.hgetall(_get_hash_key(team_id))
            return sum(int(v) for v in pairs.values())

        return await _fail_open("reading team row tracking", _command, 0)
