# 용어집

코드에서 쓰이는 이름과 위치를 기준으로 정리했다.
데이터가 지나가는 경로는 [데이터 흐름](data-flow.md), 구성 요소는 [시스템 구성도](architecture.md)를 본다.

## distinct_id

SDK가 사용자를 구분하려고 이벤트에 붙이는 식별자.
하나의 person에 여러 `distinct_id`가 연결될 수 있다.
매핑은 ClickHouse `person_distinct_id2`와 Postgres 쪽에 있고, 접근은 personhog를 거친다.
정의: `posthog/models/person/`.

## person

`distinct_id`들이 합쳐진 한 사용자.
모델은 `posthog/models/person/person.py`의 `Person`이다.
속성(properties)은 ClickHouse `person` 테이블에서 읽는다([데이터 흐름](data-flow.md#외부-데이터를-넣고-직접-쿼리할-때-주의점)).

## organization / project / team

- organization: 최상위 소유 단위. `posthog/models/organization.py`.
- project: organization 아래 묶음. `posthog/models/project.py`.
- team: 데이터가 실제로 격리되는 단위. 거의 모든 테넌트 테이블에 `team_id`가 있다. `posthog/models/team/team.py`.

코드에서는 team과 project가 섞여 쓰이는 곳이 있다. 이 구분의 이력은 확인하지 못했다(미확인).

## group

person보다 큰 개체(회사, 조직 등)를 이벤트에 붙이는 기능.
group type 이름은 `GroupTypeMapping`(`posthog/models/group_type_mapping.py`)이 관리한다.
ClickHouse 테이블은 `groups`(`posthog/models/group/sql.py`).

## cohort

조건 또는 목록으로 정의한 person 집합.
모델: `products/cohorts/backend/models/cohort.py`.

## HogQL

PostHog의 SQL 방언.
ClickHouse 쿼리로 변환되어 실행된다.
구현: `posthog/hogql/`, 파서: `common/hogql_parser/`.

## session

한 방문자의 연속된 활동 묶음.
ClickHouse `sessions` 테이블이 `session_id` 단위로 집계한다(`posthog/models/sessions/sql.py`).
세션 리플레이(화면 녹화)는 별도 경로이며 토픽이 다르다.

## action

이벤트 조건을 이름 붙여 저장한 정의.
모델: `products/actions/backend/models/action.py`.

## insight

저장된 분석 쿼리와 차트 한 개.
모델: `products/product_analytics/backend/models/insight.py`.
여러 insight를 모은 화면이 dashboard(`products/dashboards/backend/models/dashboard.py`)다.

## feature flag

사용자별로 기능을 켜고 끄는 설정.
모델: `products/feature_flags/backend/models/feature_flag.py`.
평가 서비스는 Rust 크레이트 `rust/feature-flags/`에 있다.

## product

`products/<name>/` 아래의 기능 단위 Django 앱과 프런트엔드.
UI의 "제품"(Product analytics 등)과 같은 말이다.
규칙은 [products/README.md](../products/README.md).

## personhog

person·group 데이터 접근을 중개하는 서비스와 클라이언트.
Rust 크레이트 `rust/personhog-*`와 Python 클라이언트 `posthog/personhog_client/`로 구성된다.
ORM 직접 접근 금지 규칙은 루트 `AGENTS.md`에 있다.

## 같은 개념의 다른 이름

| 개념 | 다른 표기 |
| --- | --- |
| 수집 서비스 | capture, `rust/capture` |
| ingestion 컨슈머 | plugin-server 계열 이름(`KAFKA_EVENTS_PLUGIN_INGESTION` 등 토픽 이름에 남아 있음), `nodejs/` |
| person 병합 | merge, person override(`clickhouse_person_override`) |
| 이벤트 테이블 | `events`(분산), `sharded_events`(저장) |

Decided in: buzzhog-6y7m
