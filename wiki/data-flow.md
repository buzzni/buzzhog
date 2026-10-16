# 데이터 흐름

확인 기준 커밋: 79b3714e131

이벤트 하나가 수집되어 쿼리 가능해지기까지의 경로를 코드에서 확인한 범위로 적는다.
전체 구성은 [시스템 구성도](architecture.md)를 본다.

## 이벤트 수집 → 저장

1. SDK가 `rust/capture/`로 HTTP 요청을 보낸다.
2. capture가 일반 분석 이벤트를 Kafka 토픽 `events_plugin_ingestion`에 쓴다. 오버플로는 `events_plugin_ingestion_overflow`, 과거 데이터는 `events_plugin_ingestion_historical`, 실패분은 `events_plugin_ingestion_dlq`로 간다. 데이터 종류에 따라 레인이 나뉜다. `$exception`은 `ingestion-errortracking-main`, AI 이벤트는 `events_plugin_ingestion_ai`, heatmap은 `heatmaps_ingestion`, client warning은 `ingestion-clientwarnings-main-1`, replay는 `session_recording_snapshot_item_events`(오버플로는 `session_recording_snapshot_item_overflow`)로 간다. 기본값은 `rust/capture/src/config.rs:OutputsConfig`에 있고, 종류별 분기는 `rust/capture/src/pipeline.rs`(`DataType::ExceptionErrorTracking` → `PipelineLane::ErrorTracking` 등)에 있다.
3. `nodejs/src/ingestion/`의 컨슈머(`ingestion-consumer.ts`)가 이 토픽을 읽는다. person·group 처리 등을 거친다. 프로세스 진입점은 `nodejs/src/servers/ingestion-general-server.ts`다. 다른 모드로 `rust/ingestion-consumer`가 Kafka를 읽어 gRPC로 Node 워커에 나눠 주는 구성도 있다(`PLUGIN_SERVER_MODE=ingestion-api`). 운영에서 어느 모드를 쓰는지는 미확인이다.
4. 컨슈머가 결과를 ClickHouse용 토픽(`clickhouse_events_json`, `clickhouse_person` 등)에 쓴다(`nodejs/src/ingestion/config.ts`: `INGESTION_CONSUMER_CONSUME_TOPIC`은 `KAFKA_EVENTS_PLUGIN_INGESTION`, `INGESTION_OUTPUT_EVENTS_TOPIC`은 `KAFKA_EVENTS_JSON`).
5. ClickHouse의 Kafka 엔진 테이블과 materialized view가 토픽을 읽어 저장 테이블에 넣는다. 기존 스키마는 `kafka_events_json` → `events_json_mv` → `writable_events`(Distributed) → `sharded_events`다. 새 스키마(native JSON)는 `kafka_events_json_native_json` → `events_json_table_mv` → `writable_events_json`(Distributed) → `sharded_events_json`이다. 두 Kafka 엔진 테이블은 같은 `clickhouse_events_json` 토픽을 서로 다른 consumer group으로 읽는다. 정의는 `posthog/models/event/sql.py`(`KAFKA_EVENTS_TABLE_JSON_SQL`, `EVENTS_TABLE_JSON_MV_SQL`, `WRITABLE_EVENTS_TABLE_SQL`, `KAFKA_EVENTS_NATIVE_JSON_TABLE_SQL`, `EVENTS_JSON_TABLE_MV_SQL`, `WRITABLE_EVENTS_JSON_TABLE_SQL`)에 있다.
6. Django가 HogQL 쿼리를 ClickHouse 쿼리로 변환해 `events` 분산 테이블을 읽는다(근거: `posthog/hogql/`, `posthog/models/event/sql.py:DISTRIBUTED_EVENTS_TABLE_SQL`). new events schema가 켜지면 `events_json`을 읽는다. 쿼리 modifier `useNewEventsSchema`, 인스턴스 설정, 팀 허용 목록 순으로 판단한다(`posthog/hogql/database/schema/events.py:events_table_clickhouse_table_ref`, `posthog/models/event/new_events_schema.py:use_new_events_schema`, 테이블 이름은 `posthog/clickhouse/events_json.py`).

3~5단계의 세부 변환은 직접 추적하지 않았다. 토픽 이름과 SQL 정의 파일 이름은 코드에서 확인했다.

## Kafka 토픽

상수는 `posthog/kafka_client/topics.py`의 `KAFKA_*` 변수에 있다(예: `KAFKA_EVENTS_JSON`, `KAFKA_PERSON`, `KAFKA_GROUPS`).
실제 이름은 `KAFKA_PREFIX`와 `SUFFIX`가 앞뒤에 붙는다.
`events_plugin_ingestion`, `_overflow`, `_historical`은 환경변수(`KAFKA_EVENTS_PLUGIN_INGESTION_TOPIC` 등, `get_from_env`)로 이름 전체를 바꿀 수 있다.
Node 쪽은 `nodejs/src/common/config/kafka-topics.ts`에 같은 상수를 미러로 두며, 파일 첫 줄이 `topics.py`와 맞추라고 적고 있다.

| 분류 | 토픽 (접두·접미 제외) |
| --- | --- |
| 이벤트 | `clickhouse_events_json`, `exceptions_ingestion`, `events_plugin_ingestion`, `events_plugin_ingestion_overflow`, `events_plugin_ingestion_historical`, `events_dead_letter_queue`, `realtime_only_events_json` |
| person·group | `clickhouse_person`, `clickhouse_person_distinct_id`, `clickhouse_person_override`(레거시, 미사용), `clickhouse_groups`, `clickhouse_person_unique_id`(주석상 DEPRECATED) |
| 세션 리플레이 | `session_recording_events`(레거시: ClickHouse 마이그레이션 0063이 옛 MV를 DROP하느라 상수만 남아 있다, `topics.py` 주석), `clickhouse_session_replay_events`, `clickhouse_session_replay_features`, `clickhouse_session_recording_events` |
| 에러 트래킹 | `clickhouse_error_tracking_issue_fingerprint`, `clickhouse_error_tracking_fingerprint_issue_state`, `clickhouse_error_tracking_issue_fingerprint_embeddings` |
| 임베딩 | `clickhouse_document_embeddings`, `document_embeddings_input`, `document_embedding_results` |
| CDP·코호트 | `cdp_internal_events`, `cdp_backfill_events`, `cohort_membership_changed`, `clickhouse_hog_invocation_results`, `clickhouse_message_assets` |
| 데이터 웨어하우스 | `cdp_data_warehouse_source_table`, `data_warehouse_source_webhooks`, `data_warehouse_source_webhooks_dlq`, `warehouse_person_property_updates`, `warehouse_person_property_updates_dlq` |
| 메트릭·사용량 | `clickhouse_app_metrics`(DEPRECATED), `clickhouse_app_metrics2`, `clickhouse_metrics_time_to_see_data`, `clickhouse_tophog`, `clickhouse_billing_usage_records`, `distinct_id_usage_events_json` |
| 로그·트레이스 | `logs_ingestion`, `logs_ingestion_dlq`, `ingestion-traces`, `ingestion-traces-dlq` |
| 실행 로그 | `log_entries`, `plugin_log_entries`, `log_entries_v2_test`(기능 실행 로그 계열. 위 OTEL 로그 수집과 다르다. `log_entries`는 hog function, Temporal 작업(`posthog/temporal/common/logger.py`) 등 여러 곳이 쓰고 `log_source` 열로 구분한다(`posthog/clickhouse/log_entries.py`). `log_entries_v2_test`는 시험용 임시 테이블이다(`posthog/clickhouse/log_entries_v2_test.py` 주석)) |
| 기타 | `clickhouse_property_values`(속성값 자동완성용), `clickhouse_ingestion_warnings`, `clickhouse_performance_events`, `clickhouse_heatmap_events`, `clickhouse_ai_events_json`, `clickhouse_flag_evaluations`, `notification_events`, `signals_report_completed`, `flags_cache_invalidation`, `flags_cache_invalidation_dlq` |

목록은 `topics.py`의 상수 전체에서 추출했다.
capture가 쓰는 토픽 중 `ingestion-errortracking-main`, `heatmaps_ingestion`, `session_recording_snapshot_item_events` 등은 `topics.py`가 아니라 `rust/capture/src/config.rs`에서 정의된다. `events_plugin_ingestion_dlq`, `_ai`, `_async`, `session_recording_snapshot_item_*`는 Node 미러(`kafka-topics.ts`)에도 있다.

## ClickHouse 주요 테이블

| 테이블 | 스키마 위치 |
| --- | --- |
| `events`(분산), `sharded_events` | `posthog/models/event/sql.py` |
| `events_json`(분산), `sharded_events_json` (native JSON, 새 스키마) | `posthog/clickhouse/events_json.py`, `posthog/models/event/sql.py` |
| `person`, `person_distinct_id2`, `person_distinct_id_overrides` | `posthog/models/person/sql.py` |
| `raw_sessions` (HogQL `sessions`의 기본 원본) | `posthog/models/raw_sessions/sessions_v2.py` |
| `raw_sessions_v3` | `posthog/models/raw_sessions/sessions_v3.py` |
| `sessions` (V1, 일부 팀 한정 레거시) | `posthog/models/sessions/sql.py` |
| `groups` | `posthog/models/group/sql.py` |

세션 테이블은 HogQL 기본값(`SessionTableVersion.AUTO`, `posthog/hogql/modifiers.py`)이 V2 `raw_sessions`로 간다(`posthog/hogql/database/database.py`).
`sessions` V1은 소수의 team에만 쓰이므로(`posthog/models/sessions/sql.py`의 `ALLOWED_TEAM_IDS`와 그 위 주석) 직접 쿼리할 때 읽으면 거의 비어 있을 수 있다.
person 병합은 `person_distinct_id_overrides`로 반영된다. `person_overrides` 테이블은 쓰이지 않는 레거시다(`posthog/models/person_overrides/sql.py` 머리 주석).

마이그레이션은 `posthog/clickhouse/migrations/`에 번호순으로 쌓인다(최신 번호는 `max_migration.txt`).
그 밖의 ClickHouse 정의는 `posthog/clickhouse/` 아래에 있다.

## Postgres 주요 모델

| 모델 | 위치 |
| --- | --- |
| `Organization` | `posthog/models/organization.py` |
| `Project` | `posthog/models/project.py` |
| `Team` | `posthog/models/team/team.py` |
| `GroupTypeMapping` (persons DB, personhog 경유) | `posthog/models/group_type_mapping.py` |
| `Cohort` | `products/cohorts/backend/models/cohort.py` |
| `Dashboard` | `products/dashboards/backend/models/dashboard.py` |
| `Insight` | `products/product_analytics/backend/models/insight.py` |
| `FeatureFlag` | `products/feature_flags/backend/models/feature_flag.py` |
| `Action` | `products/actions/backend/models/action.py` |

person·group 데이터와 cohort 멤버십(`posthog_cohortpeople`)은 Django 연결이 아닌 별도 persons DB에 있다(`posthog/settings/data_stores.py`의 주석, 모델 목록은 `posthog/person_db_router.py:PERSONS_DB_MODELS`). `Cohort` 정의는 메인 DB에 있다. Django는 ORM으로 직접 접근하지 않고 personhog 클라이언트를 거치고, Node ingestion은 persons DB에 직접 쓴다. 규칙은 루트 `AGENTS.md`의 "Person and group data"를 본다.

## 외부 데이터를 넣고 직접 쿼리할 때 주의점

- 모든 테넌트 데이터는 `team_id`로 격리된다. 직접 쿼리할 때도 `team_id` 조건이 빠지면 다른 팀 데이터가 섞인다.
- `events`는 분산 테이블이고 실제 데이터는 `sharded_events`에 있다. 코드에서 확인한 가져오기 경로는 capture, 또는 `rust/batch-import-worker`가 `events_plugin_ingestion`(과거 데이터는 `_historical`, `_overflow`도 있다)에 쓰는 것이다(`rust/batch-import-worker/src/config.rs:resolve_kafka_topic`). `clickhouse_events_json`이나 저장 테이블에 직접 쓰면 Node ingestion의 person 처리를 건너뛰게 된다. 그 방식이 지원 경로인지는 확인하지 못했다(미확인).
- 이벤트 테이블 이름이 `events`와 `events_json`으로 갈리듯 세션도 `raw_sessions`가 기본이다. 위 표에서 읽을 테이블을 확인한다.
- person 속성과 목록은 ClickHouse(HogQL)에서 읽고, 신원 해석만 personhog를 쓴다(루트 `AGENTS.md`).
- 이벤트 스키마에는 기존 테이블과 native JSON 테이블이 공존한다(`posthog/models/event/new_events_schema.py`). 어느 쪽을 읽는지 확인한다.
- 직접 쿼리는 HogQL로 하는 편이 안전하다. HogQL은 `team_id` 조건을 자동으로 붙인다(근거: `posthog/hogql/printer/clickhouse.py:team_id_guard_for_table`, `ClickHousePrinter._ensure_team_id_where_clause`).

용어는 [용어집](glossary.md)을 본다.

Decided in: buzzhog-6y7m
