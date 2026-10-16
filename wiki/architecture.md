# 시스템 구성도

확인 기준 커밋: 79b3714e131

이 저장소는 PostHog 포크다.
아래 그림은 이벤트 수집·저장·조회에 관여하는 주요 구성 요소를 코드에서 확인한 범위로 정리한 것이다.
이벤트 하나가 지나가는 경로의 상세는 [데이터 흐름](data-flow.md)을 본다.

```mermaid
flowchart LR
    SDK[SDK / 클라이언트] -->|HTTP| CAP[capture<br/>rust/capture]
    SDK -->|/flags| FLAGS[feature-flags<br/>rust/feature-flags]
    CAP -->|Kafka| K[(Kafka)]
    CAP <--> R[(Redis)]
    K --> ING[ingestion<br/>nodejs/src/ingestion]
    K --> REPLAY[replay ingestion<br/>nodejs/src/ingestion/pipelines/sessionreplay]
    ING -->|clickhouse_events_json 등| K
    K -->|Kafka 엔진 + MV| CH[(ClickHouse)]
    ING <--> PG[(메인 Postgres)]
    ING <--> R
    ING --> PH[personhog<br/>rust/personhog-*]
    WEB[Django 웹/API<br/>posthog/, products/] <--> PG
    WEB --> PH
    PH --> PDB[(persons DB)]
    WEB -->|HogQL 쿼리| CH
    WEB <--> R
    FLAGS <--> R
    CEL[Celery 워커] <--> R
    CEL <--> PG
    CEL --> CH
    TMP[Temporal 워커<br/>posthog/temporal] <--> PG
    TMP --> CH
    WEB --> OBJ[(객체 스토리지<br/>SeaweedFS)]
    REPLAY --> OBJ
    FE[프런트엔드<br/>frontend/, products/*/frontend] --> WEB
```

그림은 주요 연결만 그린다.
Redis 연결은 capture(`rust/capture/src/config.rs:redis_url`), Node ingestion(`nodejs/src/ingestion/config.ts`의 `REDIS_URL`), Django·Celery에서 확인했다.
feature-flags의 Redis 연결은 그림에 넣었지만 설정 위치는 직접 확인하지 않았다(미확인).
세션 리플레이는 capture가 `session_recording_snapshot_item_events`에 쓰고, replay ingestion이 읽어 SeaweedFS(`SESSION_RECORDING_V2_S3_*`)와 `clickhouse_session_replay_events` 토픽으로 보낸다(`nodejs/src/ingestion/pipelines/sessionreplay/config.ts`).

## 구성 요소

| 구성 요소 | 위치 | 역할 |
| --- | --- | --- |
| capture | `rust/capture/` | SDK 요청을 받아 Kafka로 보내는 Rust 수집 서비스. 토픽 기본값은 `rust/capture/src/config.rs`에 있다 |
| ingestion | `nodejs/src/ingestion/` | Kafka에서 이벤트를 읽어 person·group 처리 후 ClickHouse용 토픽으로 다시 쓰는 Node 컨슈머. 프로세스 진입점은 `nodejs/src/servers/ingestion-general-server.ts`이고, 이 서버가 `nodejs/src/ingestion/ingestion-consumer.ts`의 `IngestionConsumer`를 만든다 |
| Django 웹/API | `posthog/`, `products/` | REST API, 관리자, HogQL 쿼리 실행. 라우팅 골격은 `posthog/api/__init__.py`, 설정은 `posthog/settings/web.py` |
| ClickHouse | `posthog/clickhouse/`, `posthog/models/*/sql.py` | 이벤트·person·세션 저장소. 스키마와 마이그레이션이 여기 있다 |
| Postgres | `posthog/models/`, `products/*/backend/models/` | 메인 DB: 조직·팀·인사이트·플래그 등 설정성 데이터. person·group·cohort 데이터는 Django 연결이 아닌 별도 persons DB에 있고 personhog 뒤에서 접근한다(`posthog/settings/data_stores.py`의 persons DB 주석, `posthog/personhog_client/README.md`) |
| Celery | `posthog/celery.py`, `posthog/tasks/` | 주기 작업과 비동기 작업. 브로커는 Redis |
| Temporal | `posthog/temporal/` | 장기 워크플로(내보내기, 삭제, 데이터 모델링 등) |
| Redis | 설정은 `posthog/settings/` | 캐시와 Celery 브로커(`posthog/settings/celery.py:CELERY_BROKER_URL`). capture와 Node ingestion도 Redis를 쓴다 |
| 객체 스토리지 | SeaweedFS. 설정은 `posthog/settings/object_storage.py`(`OBJECT_STORAGE_*`), 세션 리플레이 v2는 `nodejs/src/ingestion/pipelines/sessionreplay/config.ts`(`SESSION_RECORDING_V2_S3_*`) | 루트 `AGENTS.md`의 설명에 따라 일반 스토리지(`objectstorage`)와 세션 리플레이 v2(`seaweedfs`) 둘 다 SeaweedFS |
| 프런트엔드 | `frontend/`, `products/*/frontend/` | React 앱 |

## 그 밖의 서비스

- `rust/`: Cargo 워크스페이스. `capture`, `feature-flags`, `cymbal`(에러 트래킹), `personhog-*`(person 데이터 접근), `property-defs-rs`, `kafka-deduplicator`, `usage-ingestion`, `ingestion-consumer`(Kafka를 읽어 Node ingestion 워커에 gRPC로 나눠 주는 컨슈머, `rust/ingestion-consumer/README.md`), `batch-import-worker`(데이터 가져오기) 등 다수의 크레이트가 있다. [모듈 지도](modules.md)는 `products/`만 다루므로 Rust 크레이트별 역할은 거기 없고, 각 크레이트의 `README.md`와 `rust/Cargo.toml`을 본다.
- `services/`: 제품 하나에 속하지 않는 독립 서비스. `llm-gateway`, `mcp`, `oauth-proxy`, `stripe-app`, `agent-proxy`, `credentials-service`, `hogql-language-service`, `stripe-mock`이 있다.
- `nodejs/src/`: `ingestion`, `cdp`, `session-replay`, `logs`, `messaging`, `ai-observability` 등 Node 서버 기능. 프로세스 종류는 `PLUGIN_SERVER_MODE`로 정해지고, `nodejs/src/index.ts:createServer`가 모드에 맞는 서버(`nodejs/src/servers/*-server.ts`)를 고른다. ingestion, replay, logs, metrics, error tracking 모드는 각자의 서버 클래스로 가며, CDP 계열 기본 서버(`PluginServer`)만 `nodejs/src/capabilities.ts`로 켤 기능을 정한다.
- `products/`: 제품별 Django 앱과 프런트엔드. 격리 규칙은 [products/README.md](../products/README.md), 설계는 [products/architecture.md](../products/architecture.md)를 본다.
- `devenv/intent-map.yaml`: 개발 환경의 intent와 capability를 정의한다. 어떤 프로세스를 띄울지는 `bin/mprocs.yaml`에 정의되어 있고, 각 프로세스가 `capability` 필드로 자신이 맡는 기능을 선언한다.

디렉터리 배치 규칙은 [docs/internal/monorepo-layout.md](../docs/internal/monorepo-layout.md)에 있다.

## 미확인

- 운영에서 ingestion을 Node 직접 소비 모드로 돌리는지, `rust/ingestion-consumer`를 거치는 모드(`PLUGIN_SERVER_MODE=ingestion-api`)로 돌리는지. 로컬 개발(`bin/mprocs.yaml`)은 `ingestion-v2-combined`를 쓴다.
- feature-flags 서비스의 Redis 연결 설정 위치.
- 운영 배포 토폴로지(이 저장소에서는 확인하지 못했다).

Decided in: buzzhog-6y7m
