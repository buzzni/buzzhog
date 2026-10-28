# syntax=docker/dockerfile:1
#
# ClickHouse server with this fork's configuration and UDFs baked in.
#
# The build context is docker/clickhouse/. The repository root cannot be the context, because the
# root .dockerignore is an allow list that drops funnel-udf/, posthog/user_scripts/ and posthog/idl/.
# Those directories come in as named build contexts instead:
#
#   docker buildx build \
#     --build-context funnel-udf=funnel-udf \
#     --build-context user-scripts=posthog/user_scripts \
#     --build-context idl=posthog/idl \
#     -f docker/clickhouse/Dockerfile docker/clickhouse
#
# aggregate_funnel is compiled here from funnel-udf/, so the image never runs the prebuilt binary
# that is committed in posthog/user_scripts. The other UDF binaries have no source in this
# repository and are copied as committed.
#
# The scripts live outside /var/lib/clickhouse, which is the data volume: a volume mounted there
# would hide anything the image put under it. config.d/user-scripts.xml points ClickHouse at them.

ARG CLICKHOUSE_VERSION=26.9.13.15

FROM rust:1.91-bookworm AS funnel-udf-build
# A musl build is static, so the binary does not depend on the glibc of the ClickHouse base image.
RUN apt-get update && apt-get install -y --no-install-recommends musl-tools && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY --from=funnel-udf . .
# The stage runs on the target platform, so uname -m names the target architecture. The output
# name follows run_udf.sh, which picks <udf>_aarch64 on aarch64 and <udf>_x86_64 elsewhere.
RUN --mount=type=cache,target=/usr/local/cargo/registry,sharing=locked \
    --mount=type=cache,target=/src/target,sharing=locked \
    arch="$(uname -m)" && \
    rustup target add "${arch}-unknown-linux-musl" && \
    cargo build --locked --release --target "${arch}-unknown-linux-musl" && \
    mkdir -p /out && \
    cp "target/${arch}-unknown-linux-musl/release/funnels" "/out/aggregate_funnel_${arch}"

FROM clickhouse/clickhouse-server:${CLICKHOUSE_VERSION}

ENV CLICKHOUSE_USER_SCRIPTS=/usr/local/share/clickhouse/user_scripts

COPY --from=user-scripts --chmod=0755 . ${CLICKHOUSE_USER_SCRIPTS}/
COPY --from=funnel-udf-build --chmod=0755 /out/ ${CLICKHOUSE_USER_SCRIPTS}/

# The same files docker-compose.hobby.yml mounts, so the image runs without the checkout.
COPY config.xml /etc/clickhouse-server/config.xml
COPY config.d/default.xml /etc/clickhouse-server/config.d/default.xml
COPY users.xml /etc/clickhouse-server/users.xml
COPY user_defined_function.xml /etc/clickhouse-server/user_defined_function.xml
# Only init-db.sh. autoresearch-row-policies.sql names the autoresearch user, which only
# users-dev.xml defines, so with users.xml it fails and the first start exits.
COPY docker-entrypoint-initdb.d/init-db.sh /docker-entrypoint-initdb.d/init-db.sh
# init-db.sh copies /idl into format_schemas on the first start.
COPY --from=idl . /idl/
RUN printf '<clickhouse>\n    <user_scripts_path>%s/</user_scripts_path>\n</clickhouse>\n' "${CLICKHOUSE_USER_SCRIPTS}" \
        > /etc/clickhouse-server/config.d/user-scripts.xml
