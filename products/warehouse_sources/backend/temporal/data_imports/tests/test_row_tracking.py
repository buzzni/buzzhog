import uuid

import pytest
from posthog.test.base import BaseTest
from unittest import mock

from django.test import override_settings

from parameterized import parameterized
from redis import exceptions as redis_exceptions

from posthog.redis import get_async_client

from products.warehouse_sources.backend.temporal.data_imports.row_tracking import (
    decrement_rows,
    finish_row_tracking,
    get_all_rows_for_team,
    get_rows,
    increment_rows,
    setup_row_tracking,
)

_READ_ONLY_REPLICA_ERROR = redis_exceptions.ReadOnlyError("You can't write against a read only replica.")
_MISCONF_ERROR = redis_exceptions.ResponseError(
    "MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to disk. "
    "Commands that may modify the data set are disabled, because this instance is configured to report "
    "errors during writes if RDB snapshotting fails (stop-writes-on-bgsave-error option). Please check "
    "the Redis logs for details about the RDB error."
)

# Every row-tracking entry point the import calls, with the value it must return when Redis refuses
# every command.
_ENTRY_POINTS = [
    ("setup_row_tracking", lambda team_id, schema_id: setup_row_tracking(team_id, schema_id), None),
    ("increment_rows", lambda team_id, schema_id: increment_rows(team_id, schema_id, 10), None),
    ("decrement_rows", lambda team_id, schema_id: decrement_rows(team_id, schema_id, 10), None),
    ("finish_row_tracking", lambda team_id, schema_id: finish_row_tracking(team_id, schema_id), None),
    ("get_rows", lambda team_id, schema_id: get_rows(team_id, schema_id), 0),
    ("get_all_rows_for_team", lambda team_id, _schema_id: get_all_rows_for_team(team_id), 0),
]

_FAIL_OPEN_CASES = [
    (f"{entry_point_name}_{error_name}", call, fallback, error)
    for entry_point_name, call, fallback in _ENTRY_POINTS
    for error_name, error in [("read_only_replica", _READ_ONLY_REPLICA_ERROR), ("misconf", _MISCONF_ERROR)]
]


class _CacheReadFailsClient:
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def get(self, *args, **kwargs):
        raise redis_exceptions.ConnectionError("Error connecting to redis:6379.")


class _FirstIncrementFailsClient:
    def __init__(self, inner):
        self._inner = inner
        self._remaining_failures = 1

    def __getattr__(self, name):
        return getattr(self._inner, name)

    async def hincrby(self, *args, **kwargs):
        if self._remaining_failures:
            self._remaining_failures -= 1
            raise redis_exceptions.ConnectionError("Error connecting to redis:6379.")

        return await self._inner.hincrby(*args, **kwargs)


class TestRowTrackingRedisUnavailable(BaseTest):
    @parameterized.expand(
        [
            (
                "connection_error",
                redis_exceptions.ConnectionError(
                    "Error connecting to redis:6379. Temporary failure in name resolution."
                ),
            ),
            (
                "misconf_error",
                redis_exceptions.ResponseError(
                    "MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to "
                    "disk. Commands that may modify the data set are disabled, because this instance is configured "
                    "to report errors during writes if RDB snapshotting fails (stop-writes-on-bgsave-error option). "
                    "Please check the Redis logs for details about the RDB error."
                ),
            ),
        ]
    )
    @pytest.mark.asyncio
    async def test_setup_row_tracking_does_not_raise_when_redis_is_unreachable(self, _name, exception):
        # get_async_client only builds a lazy client - the ping is the first real
        # connection attempt. If it fails, the client must not be used again, or the
        # next command (hset) raises the same connection error, this time uncaught.
        # Row tracking already fails open when redis is unavailable, so a Redis-side
        # error (unreachable, or refusing writes because RDB snapshotting failed) is a
        # transient infra blip, not a bug, and must not be reported to error tracking.
        unreachable_client = mock.AsyncMock()
        unreachable_client.ping.side_effect = exception

        with (
            mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.get_async_client",
                return_value=unreachable_client,
            ),
            mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.capture_exception"
            ) as mock_capture_exception,
            override_settings(DATA_WAREHOUSE_REDIS_HOST="localhost", DATA_WAREHOUSE_REDIS_PORT="6379"),
        ):
            await setup_row_tracking(self.team.pk, str(uuid.uuid4()))

        unreachable_client.hset.assert_not_called()
        mock_capture_exception.assert_not_called()

    @parameterized.expand(_FAIL_OPEN_CASES)
    @pytest.mark.asyncio
    async def test_row_tracking_fails_open_when_redis_refuses_every_command(self, _name, call, fallback, exception):
        # A successful ping doesn't guarantee the following command succeeds: Redis can refuse a
        # write because it can't persist an RDB snapshot, and a failover can point the client at a
        # read only replica. Row tracking is bookkeeping for the import that calls it, so no
        # command may raise into that import, and a transient infra blip is not worth an
        # error-tracking issue.
        refusing_client = mock.AsyncMock()
        refusing_client.ping.return_value = True
        for command in ("hset", "expire", "hincrby", "hdel", "hexists", "hget", "hgetall"):
            getattr(refusing_client, command).side_effect = exception

        with (
            mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.get_async_client",
                return_value=refusing_client,
            ),
            mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.capture_exception"
            ) as mock_capture_exception,
            override_settings(DATA_WAREHOUSE_REDIS_HOST="localhost", DATA_WAREHOUSE_REDIS_PORT="6379"),
        ):
            assert await call(self.team.pk, str(uuid.uuid4())) == fallback

        mock_capture_exception.assert_not_called()

    @pytest.mark.asyncio
    async def test_increment_rows_keeps_the_count_through_a_transient_failure(self):
        # A single connection blip used to drop the increment, which makes the billing limit read
        # a count that is short by one batch for the rest of the sync.
        schema_id = str(uuid.uuid4())

        with override_settings(DATA_WAREHOUSE_REDIS_HOST="localhost", DATA_WAREHOUSE_REDIS_PORT="6379"):
            await setup_row_tracking(self.team.pk, schema_id)

            with mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.get_async_client",
                side_effect=lambda url: _FirstIncrementFailsClient(get_async_client(url)),
            ):
                await increment_rows(self.team.pk, schema_id, 10)

            assert await get_rows(self.team.pk, schema_id) == 10

            await finish_row_tracking(self.team.pk, schema_id)

    @pytest.mark.asyncio
    async def test_row_tracking_uses_the_shared_redis_when_no_dedicated_host_is_configured(self):
        # An unset host used to fall back to localhost:6379, where nothing listens in a deployed
        # environment, so every row-tracking call raised a connection error.
        with (
            mock.patch(
                "products.warehouse_sources.backend.temporal.data_imports.row_tracking.get_async_client",
                return_value=mock.AsyncMock(),
            ) as mock_get_async_client,
            override_settings(
                DATA_WAREHOUSE_REDIS_HOST=None,
                DATA_WAREHOUSE_REDIS_PORT=None,
                REDIS_URL="redis://shared-redis.example.com:6379/",
            ),
        ):
            await setup_row_tracking(self.team.pk, str(uuid.uuid4()))

        mock_get_async_client.assert_called_once_with("redis://shared-redis.example.com:6379/")
