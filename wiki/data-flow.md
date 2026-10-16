# 데이터 흐름

이벤트 하나가 수집되어 쿼리 가능해지기까지의 경로를 코드에서 확인한 범위로 적는다.
전체 구성은 [시스템 구성도](architecture.md)를 본다.

## 이벤트 수집 → 저장

1. SDK가 `rust/capture/`로 HTTP 요청을 보낸다.
2. capture가 이벤트를 Kafka 토픽 `events_plugin_ingestion`에 쓴다. 오버플로는 `events_plugin_ingestion_overflow`, 과거 데이터는 `events_plugin_ingestion_historical`, 실패분은 `events_plugin_ingestion_dlq`로 간다. 기본값은 `rust/capture/src/config.rs`에 있다.
3. `nodejs/src/ingestion/`의 컨슈머(`ingestion-consumer.ts`)가 이 토픽을 읽는다. person·group 처리 등을 거친다.
4. 컨슈머가 결과를 ClickHouse용 토픽(`clickhouse_events_json`, `clickhouse_person` 등)에 쓴다.
5. ClickHouse의 Kafka 엔진 테이블과 materialized view가 토픽을 읽어 `sharded_events` 등 저장 테이블에 넣는다. 정의는 `posthog/models/event/sql.py`(`KAFKA_EVENTS_TABLE_JSON_SQL`, `EVENTS_TABLE_JSON_MV_SQL` 등)에 있다.
6. Django가 HogQL 쿼리를 ClickHouse 쿼리로 변환해 `events` 분산 테이블을 읽는다.

3~5단계의 세부 변환은 직접 추적하지 않았다. 토픽 이름과 SQL 정의 파일 이름은 코드에서 확인했다.

## Kafka 토픽

상수는 `posthog/kafka_client/topics.py`에 있다.
실제 이름은 `KAFKA_PREFIX`와 `SUFFIX`가 앞뒤에 붙는다.

| 분류 | 토픽 (접두·접미 제외) |
| --- | --- |
| 이벤트 | `clickhouse_events_json`, `exceptions_ingestion`, `events_plugin_ingestion`, `events_plugin_ingestion_overflow`, `events_plugin_ingestion_historical`, `events_dead_letter_queue`, `realtime_only_events_json` |
| person·group | `clickhouse_person`, `clickhouse_person_distinct_id`, `clickhouse_person_override`, `clickhouse_groups`, `clickhouse_person_unique_id`(주석상 DEPRECATED) |
| 세션 리플레이 | `session_recording_events`, `clickhouse_session_replay_events`, `clickhouse_session_replay_features`, `clickhouse_session_recording_events` |
| 에러 트래킹 | `clickhouse_error_tracking_issue_fingerprint`, `clickhouse_error_tracking_fingerprint_issue_state`, `clickhouse_error_tracking_issue_fingerprint_embeddings` |
| 임베딩 | `clickhouse_document_embeddings`, `document_embeddings_input`, `document_embedding_results` |
| CDP·코호트 | `cdp_internal_events`, `cdp_backfill_events`, `cohort_membership_changed`, `clickhouse_hog_invocation_results`, `clickhouse_message_assets` |
| 데이터 웨어하우스 | `cdp_data_warehouse_source_table`, `data_warehouse_source_webhooks`, `data_warehouse_source_webhooks_dlq`, `warehouse_person_property_updates`, `warehouse_person_property_updates_dlq` |
| 메트릭·사용량 | `clickhouse_app_metrics`(DEPRECATED), `clickhouse_app_metrics2`, `clickhouse_metrics_time_to_see_data`, `clickhouse_tophog`, `clickhouse_billing_usage_records`, `distinct_id_usage_events_json`, `clickhouse_property_values` |
| 로그·트레이스 | `logs_ingestion`, `logs_ingestion_dlq`, `ingestion-traces`, `ingestion-traces-dlq`, `log_entries`, `plugin_log_entries` |
| 기타 | `clickhouse_ingestion_warnings`, `clickhouse_performance_events`, `clickhouse_heatmap_events`, `clickhouse_ai_events_json`, `clickhouse_flag_evaluations`, `notification_events`, `signals_report_completed`, `flags_cache_invalidation`, `flags_cache_invalidation_dlq` |

목록은 이 파일의 상수 전체에서 추출했다.
capture가 쓰는 토픽 중 `session_recording_snapshot_item_events` 등은 `posthog/kafka_client/topics.py`가 아니라 `rust/capture/src/config.rs`에서 정의된다.

## ClickHouse 주요 테이블

| 테이블 | 스키마 위치 |
| --- | --- |
| `events`(분산), `sharded_events` | `posthog/models/event/sql.py` |
| `person`, `person_distinct_id2` | `posthog/models/person/sql.py` |
| `sessions` | `posthog/models/sessions/sql.py` |
| `groups` | `posthog/models/group/sql.py` |

마이그레이션은 `posthog/clickhouse/migrations/`에 번호순으로 쌓인다(최신 번호는 `max_migration.txt`).
그 밖의 ClickHouse 정의는 `posthog/clickhouse/` 아래에 있다.

## Postgres 주요 모델

| 모델 | 위치 |
| --- | --- |
| `Organization` | `posthog/models/organization.py` |
| `Project` | `posthog/models/project.py` |
| `Team` | `posthog/models/team/team.py` |
| `GroupTypeMapping` | `posthog/models/group_type_mapping.py` |
| `Cohort` | `products/cohorts/backend/models/cohort.py` |
| `Dashboard` | `products/dashboards/backend/models/dashboard.py` |
| `Insight` | `products/product_analytics/backend/models/insight.py` |
| `FeatureFlag` | `products/feature_flags/backend/models/feature_flag.py` |
| `Action` | `products/actions/backend/models/action.py` |

person·group 데이터는 Postgres 테이블에 ORM으로 직접 접근하지 않고 personhog 클라이언트를 거친다. 규칙은 루트 `AGENTS.md`의 "Person and group data"를 본다.

## 외부 데이터를 넣고 직접 쿼리할 때 주의점

- 모든 테넌트 데이터는 `team_id`로 격리된다. 직접 쿼리할 때도 `team_id` 조건이 빠지면 다른 팀 데이터가 섞인다.
- `events`는 분산 테이블이고 실제 데이터는 `sharded_events`에 있다. 쓰기는 반드시 Kafka 토픽 → Kafka 엔진 경로를 거치는 것이 이 저장소의 전제다. 저장 테이블에 직접 INSERT하는 방식은 지원 경로인지 확인하지 못했다(미확인).
- person 속성과 목록은 ClickHouse(HogQL)에서 읽고, 신원 해석만 personhog를 쓴다(루트 `AGENTS.md`).
- 이벤트 스키마에는 기존 테이블과 native JSON 테이블이 공존한다(`posthog/models/event/new_events_schema.py`). 어느 쪽을 읽는지 확인한다.
- 직접 쿼리는 HogQL로 하는 편이 안전하다. HogQL은 `team_id` 조건을 자동으로 붙인다(미확인: 코드 경로는 `posthog/hogql/`).

용어는 [용어집](glossary.md)을 본다.

Decided in: buzzhog-6y7m
