# products/ 모듈 목록과 의존 관계표

확인 기준 커밋: 70371e9eb38

`products/` 아래의 product 디렉터리 100개를 한 줄씩 정리한다.
각 줄은 역할, 규모, 다른 product와 `posthog/` 코어 사이의 import 의존, 그리고 이 포크에서 유지할지 뺄지에 대한 판단을 담는다.
규모와 의존 숫자는 모두 스크립트로 집계했다. 명령과 스크립트는 맨 끝 [집계 방법](#집계-방법)에 있다.
product 구조와 격리 규칙의 원문은 [`products/README.md`](../products/README.md), [`products/architecture.md`](../products/architecture.md), [`docs/internal/monorepo-layout.md`](../docs/internal/monorepo-layout.md)에 있다.
시스템 전체 그림은 [시스템 구성도](architecture.md), 용어는 [용어집](glossary.md)을 본다.

> 판단 열은 **후보**다. 결정이 아니다. 코드에서 확인한 결합도와 성격(PostHog 자체 운영용, 퇴역, Cloud 전용)만 근거로 삼았다. 실제로 뺄지는 ADR에서 정한다.

## 요약

### 숫자로 본 전체

- `products/` 아래 디렉터리는 100개다. 나머지 8개 항목은 파일이다(`README.md`, `__init__.py`, `architecture.md`, `conftest.py`, `db_routing.yaml`, `isolation_baseline.txt`, `model_crossing_uses_baseline.txt`, `ruff.toml`). 근거: `ls products/`
- `backend/` 디렉터리가 있는 모듈은 87개, `frontend/` 디렉터리가 있는 모듈은 80개다. `backend/`가 있어도 `demo`는 `posthog/settings/web.py`의 `PRODUCTS_APPS`에 없다.
- 코드 규모는 `warehouse_sources`(약 133만 줄, `source.py`가 있는 커넥터 디렉터리 1,382개, 근거: `products/warehouse_sources/backend/temporal/data_imports/sources/`)와 `desktop`(약 72만 줄, 별도 pnpm 워크스페이스)이 압도적으로 크다. 그다음은 `signals`(31만), `tasks`(21만), `ai_observability`(20만), `product_analytics`(19만)다.
- 판단 분포: 핵심 16, 유지 44, 검토 30, 제거 후보 10.

### 핵심 (빼면 안 되는 모듈)

`posthog/` 코어나 다른 product 다수가 import하므로, 빼려면 코어 코드를 같이 고쳐야 하는 모듈이다.

| 모듈 | 들어오는 import (product 수 · 코어 · 프론트) |
|---|---|
| `access_control` | 51 · 104 · 25 |
| `warehouse_sources` | 20 · 109 · 14 |
| `product_analytics` | 25 · 47 · 158 |
| `feature_flags` | 16 · 63 · 71 |
| `dashboards` | 15 · 45 · 73 |
| `cohorts` | 15 · 58 · 21 |
| `cdp` | 17 · 53 · 10 |
| `experiments` | 9 · 42 · 174 |
| `data_modeling` | 10 · 42 · 11 |
| `data_warehouse` | 11 · 10 · 86 |
| `exports` | 11 · 32 · 0 |
| `event_definitions` | 11 · 30 · 4 |
| `actions` | 12 · 23 · 12 |
| `notifications` | 15 · 11 · 5 |
| `persons` | 15 · 0 · 59 (프론트 전용) |
| `data_tools` | 6 · 6 · 0 |

`security`도 코어 파일 13개가 29곳에서 import한다. 가입·로그인·OAuth·위저드·프로젝트 시크릿 키 경로가 `products.security.backend.facade`의 접근 판정 함수와 타입을 쓰고, `posthog/urls.py`가 허브 API URL을, Temporal 워커가 동기화 스케줄을 가져간다(근거: `posthog/api/signup.py`, `posthog/auth.py`, `posthog/api/oauth/views.py`, `posthog/temporal/schedule.py`). 성격은 PostHog 보안 허브 연동이라 "제거 후보"로 두었지만(근거: `products/security/README.md`), 빼려면 이 29곳을 먼저 끊어야 한다.

### 독립적으로 떼어 낼 수 있는 후보

다른 product와 주고받는 import가 각각 1개 이하이고, 코어·프론트에서 들어오는 import가 3곳 이하인 모듈이다.
`desktop`, `ingestion`, `support`를 뺀 나머지는 코어(`posthog/` 또는 프론트 `frontend/src`)를 import한다. 여기서 "독립"은 다른 product와의 import 관계만 뜻한다.

- 기능이 있는 모듈: `visual_review`(4만 줄, 스크린샷 기준 이미지 비교), `streamlit_apps`, `mcp_registry`, `managed_migrations`, `legal_documents`, `aeo`, `apm`, `webmcp`, `field_notes`, `replay`, `warehouse_sources_queue`(`warehouse_sources` 전용)
- 별도 워크스페이스: `desktop`(Electron·모바일 앱, 루트 pnpm 워크스페이스에서 빠져 있음. 근거: `docs/internal/monorepo-layout.md`)
- 껍데기·퇴역: `links`, `live_debugger`, `user_interviews`, `inbox`, `toolbar`, `session_replay`, `ingestion`(스킬 문서만), `games`, `support`(지원팀 CLI)
- 조건에는 맞지만 떼어 낼 수 없는 모듈: `llm_analytics`. import는 없지만 `ai_observability`의 첫 마이그레이션이 이 앱의 마지막 마이그레이션에 기댄다(근거: `products/ai_observability/backend/migrations/0001_adopt_llm_analytics_models.py`의 `("llm_analytics", "0033_release_to_ai_observability")`).

### 강결합 묶음

서로 import하는(양방향) 쌍이 72개다. 이 쌍을 따라가면 아래 묶음이 나온다. 묶음 안의 모듈은 하나만 떼어 내기 어렵다.

1. **데이터 웨어하우스** — `data_warehouse` ↔ `warehouse_sources` ↔ `data_modeling` ↔ `managed_warehouse`, `revenue_analytics`, `data_quality` ↔ `data_catalog`. 한 방향으로 `data_tools`, `warehouse_sources_queue`, `warehouse_suggestions`, `endpoints`가 붙는다. `data_warehouse` → `warehouse_sources` import만 183줄이다(Python 131, TypeScript 52).
2. **에이전트·AI** — `tasks` ↔ `signals` ↔ `posthog_ai` ↔ `slack_app`, `canvas`, `context_layer`, `skills`, `engineering_analytics`, `replay_vision`, `ai_observability`. 한 방향으로 `business_knowledge`, `review_hog`, `stamphog`, `commands`, `wizard`, `autoresearch`, `streamlit_apps`, `account_audits`, `today`가 `tasks`나 `signals`에 기댄다. 반대 방향으로는 `tasks`, `signals`, `canvas`가 `mcp_store`를 import한다(`mcp_store`가 import하는 product는 `cdp`뿐이다). `signals`는 product 31개를 import해 가장 강하게 결합돼 있다.
3. **분석 코어** — `product_analytics` ↔ `dashboards` ↔ `exports`, `actions`, `cohorts`, `alerts`, `endpoints`, `data_catalog`, `subscriptions`, `web_analytics`, `customer_analytics`, `notebooks` ↔ `dashboards`, `mcp_analytics` ↔ `dashboards`.
4. **플래그·실험** — `feature_flags` ↔ `experiments`, `approvals`, `surveys`, `product_tours`, `early_access_features`. `experiments` ↔ `actions`도 양방향이다.
5. **관측성** — `logs` ↔ `tracing` ↔ `metrics`, `logs` ↔ `alerts` / `alerts_platform`, `logs` ↔ `error_tracking`. `apm`을 import하는 product는 `logs`뿐이다(근거: `products/logs/backend/anomaly_scan.py`). `apm` 자신은 다른 product를 import하지 않는다.
6. **CDP·워크플로** — `cdp` ↔ `actions` / `batch_exports`, `workflows` ↔ `messaging` / `early_access_features` / `persons` / `customer_analytics` / `error_tracking`.

묶음 사이의 다리: `posthog_ai`는 `product_analytics`, `feature_flags`, `error_tracking`, `logs`, `notebooks`, `cdp`와 양방향이다. 에이전트·AI 묶음을 빼려면 이 다리를 먼저 끊어야 한다. 프론트에서는 코어 `frontend/src`가 `posthog_ai`를 91곳에서 import한다.

### `ee/` 제거의 흔적

이 포크는 `ee/` 디렉터리를 지웠다(커밋 `e289996cf97` "Sync and remove all non-FOSS parts"). 그런데 product 34개의 비테스트 파일에 아직 `from ee...` import가 남아 있다. 표의 `ee` import 열이 그 파일 수다.

- 많이 남은 곳: `tasks` 15, `exports` 10, `replay_vision` 8, `posthog_ai` 6, `workflows` 4, `experiments` 4
- 가장 많이 가리키는 대상: `ee.hogai.*`(AI 에이전트 런타임), `ee.tasks.subscriptions`, `ee.billing.quota_limiting`, `ee.clickhouse.*`
- `tach.toml`에는 `"ee"`가 45번 나온다. product 모듈 43개의 `depends_on`에 43번, 코어 `posthog` 모듈의 `depends_on`에 1번, `ee` 모듈 자체의 선언(`path = "ee"`)에 1번이다.
- 이 import가 모듈 로드 시점에 실패하는지, 지연 import라 특정 경로에서만 실패하는지는 **미확인**이다. 서버를 띄워 확인하지 않았다.

## 표

열 설명:

- **역할 (플래그) — 근거**: 한 줄 역할과 그 근거가 된 첫 파일. 플래그는 `internal`(PostHog 자체 운영용), `stub`(거의 빈 모듈), `cloud`(PostHog Cloud 운영 전제), `external`(주 기능에 외부 서비스가 필요)이다.
- **BE / FE**: `backend/`, `frontend/` 디렉터리가 있는지. `frontend/`에 생성 타입(`generated/`)만 있어도 O다.
- **파일 / LOC**: `.py .ts .tsx .js .jsx .rs .go` 파일 수와 줄 수. 테스트는 포함, `migrations/`·`generated/`·`node_modules/`·`__snapshots__/`는 제외.
- **나가는 의존**: 이 모듈의 비테스트 코드가 import하는 다른 product. Python `from products.X`와 TypeScript `products/X`·`@posthog/products-X`를 합친 import 줄 수 순.
- **들어옴**: 이 모듈을 import하는 다른 product 수 · `posthog/` 코어의 참조 수 · 코어 프론트(`frontend/src`)의 참조 수.
- **`ee` import**: 지워진 `ee/`를 import하는 비테스트 파일 수.
- **판단**: 핵심 / 유지 / 검토 / 제거 후보와 한 줄 근거.

| 모듈 | 역할 (플래그) — 근거 | BE | FE | 파일 | LOC | 나가는 의존 (상위 4) | 들어옴: product · 코어 · 프론트 | `ee` import | 판단 · 근거 |
|---|---|---|---|---:|---:|---|---|---:|---|
| `access_control` | `Role`·`RoleMembership`로 역할 기반 접근 권한(RBAC)을 관리하는 모듈 — `products/access_control/backend/models` | O | O | 62 | 18,292 | `event_definitions` | 51 · 104 · 25 | — | **핵심** 코어 104곳·product 51개가 import |
| `account_audits` | 웹훅 요청으로 `account-audit` 작업을 시작하고 마무리하는 모듈 — `products/account_audits/backend/facade/api.py` | O | O | 22 | 1,361 | `notebooks`, `skills`, `tasks`, `signals` | 0 · 1 · 0 | — | **검토** `tasks`·`signals` 에이전트 실행에 기대는 작은 모듈 |
| `actions` | `Action`·`ActionStep`으로 이벤트 선택 규칙(액션)을 관리하는 모듈 — `products/actions/backend/models` | O | O | 54 | 7,252 | `access_control`, `cdp`, `cohorts`, `experiments` 외 2 | 12 · 23 · 12 | — | **핵심** 코어 23곳·product 12개가 import |
| `aeo` | `AEOPrompt`·`AEOCitationCheck`로 AI 답변 엔진의 도메인 인용을 점검하는 POC 모듈 (external) — `products/aeo/README.md` | O | — | 25 | 1,941 | — | 1 · 2 · 0 | — | **검토** POC, `web_analytics`만 사용 |
| `ai_observability` | `EvaluationConfig`·`LLMPrompt` 중심의 LLM 트레이스, 평가, 프롬프트 관리 모듈 (external) — `products/ai_observability/README.md` | O | O | 928 | 196,476 | `access_control`, `signals`, `exports`, `posthog_ai` 외 8 | 7 · 81 · 25 | 3 | **유지** 독립 기능, `ee` import 3곳 정리 필요 |
| `ai_training` | `AITrainingDeletionRequest`로 ML 학습 데이터 삭제 요청을 처리하는 모듈 — `products/ai_training/README.md` | O | — | 21 | 846 | — | 0 · 6 · 0 | — | **제거 후보** PostHog 자체 ML 학습 데이터 삭제 통제(코어 6곳 결합) |
| `alerts` | `Alert`·`Threshold`로 인사이트 알림을 평가하고 `llm` 감지기를 두는 모듈 (external) — `products/alerts/AGENTS.md` | O | O | 186 | 40,733 | `alerts_platform`, `product_analytics`, `cdp`, `access_control` 외 1 | 11 · 27 · 18 | 2 | **유지** `product_analytics`·`logs`와 상호 의존 |
| `alerts_platform` | `PlatformAlertConfiguration`·`PlatformAlert`로 플랫폼 알림 설정과 전달을 다루는 모듈 — `products/alerts_platform/backend/models` | O | O | 110 | 17,366 | `logs`, `notifications`, `access_control` | 4 · 8 · 0 | — | **유지** `alerts`·`logs`·`billing_alerts`가 기반으로 사용 |
| `analytics_platform` | `PreaggregationJob`으로 사전 집계 작업 상태와 precompute 디버그 화면을 관리하는 모듈 — `products/analytics_platform/backend/models/preaggregation_job.py` | O | O | 20 | 8,282 | — | 3 · 2 · 0 | — | **유지** `web_analytics`·`experiments` 사전 집계 기반 |
| `annotations` | `Annotation` 모델로 차트 주석을 저장하고 API로 제공하는 모듈 — `products/annotations/backend/models` | O | O | 36 | 4,098 | `error_tracking`, `dashboards`, `product_analytics` | 3 · 0 · 6 | — | **유지** 작고 결합 낮음 |
| `apm` | `unified-apm-product` 플래그로 막아 둔 미출시 APM 이상 탐지 백엔드 모듈 — `products/apm/backend/feature_flags.py` | O | — | 41 | 3,019 | — | 1 · 0 · 0 | — | **검토** 미출시 플래그 뒤 코드, `logs`만 사용 |
| `approvals` | `ChangeRequest`·`ApprovalPolicy`로 게이트된 작업의 변경 요청을 승인하는 모듈 — `products/approvals/backend/models.py` | O | — | 38 | 11,397 | `feature_flags`, `access_control`, `notifications` | 4 · 3 · 0 | 1 | **유지** `feature_flags`와 상호 의존 |
| `autoresearch` | `AutoresearchModel`·`AutoresearchRun`으로 목표 이벤트 예측 모델을 탐색·학습하는 모듈 (external) — `products/autoresearch/AGENTS.md` | O | O | 167 | 41,589 | `tasks`, `actions`, `cohorts`, `feature_flags` 외 2 | 0 · 2 · 0 | — | **검토** `tasks` 에이전트 묶음에 기댐, 들어오는 의존 없음 |
| `batch_exports` | `BatchExport`·`BatchExportDestination`으로 이벤트를 외부 목적지로 내보내는 모듈 (external) — `products/batch_exports/backend/models` | O | O | 258 | 78,164 | `access_control`, `notifications`, `cdp` | 3 · 13 · 10 | 2 | **유지** `cdp`·`data_warehouse`가 사용 |
| `billing` | 백엔드 없이 빌링 API 생성 클라이언트, MCP 도구 정의, 사용량 스킬, 프론트 e2e 테스트만 있는 모듈 (stub) — `products/billing/frontend/generated/api.ts` | — | O | 5 | 828 | — | 0 · 0 · 17 | — | **검토** 백엔드 없음, 프론트 코어 17곳이 import |
| `billing_alerts` | 조직 단위 `BillingAlertConfiguration`으로 빌링 사용량 알림을 평가하는 모듈 (cloud) — `products/billing_alerts/README.md` | O | O | 46 | 7,258 | `alerts`, `alerts_platform` | 0 · 2 · 1 | 1 | **제거 후보** PostHog Cloud 빌링 전용(`posthog.cloud_utils`), 들어오는 의존 없음 |
| `business_intelligence` | `BIWorksheetsScene` 워크시트 기반 BI 분석 화면만 제공하는 프론트엔드 모듈 — `products/business_intelligence/manifest.tsx` | — | O | 122 | 20,910 | `data_warehouse`, `product_analytics`, `warehouse_sources` | 0 · 0 · 22 | — | **유지** 프론트 전용, 코어 프론트 22곳이 import |
| `business_knowledge` | `KnowledgeLibrary`·`KnowledgeChunk`로 웹과 GitHub 자료를 모아 지식 라이브러리를 만드는 모듈 (external) — `products/business_knowledge/backend/models` | O | O | 143 | 30,519 | `tasks`, `access_control`, `posthog_ai` | 2 · 2 · 6 | 2 | **검토** 에이전트 묶음(`tasks`), `ee` import 2곳 |
| `canvas` | `Canvas`·`CanvasBuild`로 캔버스 소스를 빌드하고 저장하는 모듈 — `products/canvas/backend/models.py` | O | O | 213 | 40,000 | `tasks`, `workflows`, `mcp_store`, `access_control` 외 3 | 4 · 8 · 6 | — | **검토** 에이전트 묶음(`tasks`와 상호 의존) |
| `cdp` | `HogFunction`·`HogFunctionTemplate`로 외부 목적지에 이벤트를 전달하는 CDP 모듈 (external) — `products/cdp/backend/models/hog_function_template.py` | O | O | 181 | 37,928 | `actions`, `cohorts`, `batch_exports`, `posthog_ai` | 17 · 53 · 10 | 2 | **핵심** 코어 53곳·product 17개가 import |
| `cohorts` | `Cohort` 모델로 코호트 정의·계산·백필을 관리하는 모듈 — `products/cohorts/backend/models/cohort.py` | O | O | 86 | 24,061 | `product_analytics` | 15 · 58 · 21 | — | **핵심** 코어 58곳·product 15개가 import |
| `commands` | GitHub App으로 받은 PR 댓글의 `@posthog` 명령을 파싱해 각 제품으로 보내는 모듈 (external) — `products/commands/README.md` | O | — | 35 | 3,299 | `security`, `review_hog`, `stamphog`, `tasks` | 1 · 0 · 0 | — | **검토** `@posthog` PR 명령 라우터(`github-commands` 롤아웃 뒤), `review_hog`·`stamphog`·`tasks`의 진입점, `slack_app`만 사용 |
| `context_layer` | `ContextLayerConfig`·`WikiPageProposal`로 조직 마크다운 위키를 git 번들로 관리하는 모듈 (external) — `products/context_layer/README.md` | O | O | 29 | 6,816 | `tasks`, `access_control` | 1 · 2 · 0 | — | **검토** 에이전트 묶음(`tasks`와 상호 의존) |
| `conversations` | `EmailThread`·`ConversationDelivery`로 지원 티켓과 이메일, Slack 연동을 처리하는 모듈 (external) — `products/conversations/backend/models` | O | O | 377 | 100,560 | `business_knowledge`, `access_control`, `customer_analytics`, `signals` 외 6 | 6 · 16 · 24 | — | **유지** 고객 지원 기능, 결합 큼(나감 10개) |
| `core_events` | `Core events` 메뉴 항목만 등록하는 manifest 전용 모듈 (stub) — `products/core_events/manifest.tsx` | — | O | 2 | 19 | — | 0 · 0 · 4 | — | **유지** manifest만 있음, 코어 프론트 4곳이 import |
| `cross_project_dashboards` | `CrossProjectDashboard`·`CrossProjectDashboardTile`로 여러 프로젝트 타일을 묶는 모듈 — `products/cross_project_dashboards/backend/models.py` | O | O | 53 | 5,498 | `product_analytics`, `access_control` | 0 · 0 · 3 | — | **유지** 작고 들어오는 의존 없음 |
| `customer_analytics` | `Account`·`Meeting`으로 고객 계정과 Google 캘린더·Gmail 동기화를 다루는 모듈 (external) — `products/customer_analytics/backend/models` | O | O | 520 | 129,909 | `warehouse_sources`, `access_control`, `signals`, `notebooks` 외 10 | 5 · 17 · 29 | 1 | **유지** 결합 큼(나감 14개), 단독 분리는 어려움 |
| `dashboards` | `Dashboard`·`DashboardTile`로 대시보드, 타일, 템플릿을 관리하는 모듈 — `products/dashboards/backend/models` | O | O | 275 | 47,336 | `conversations`, `access_control`, `error_tracking`, `experiments` 외 12 | 15 · 45 · 73 | 1 | **핵심** 코어 45곳·프론트 73곳·product 15개가 import |
| `data_catalog` | `Metric`·`TableCertification`으로 메트릭 카탈로그와 테이블 인증을 관리하는 모듈 — `products/data_catalog/backend/models` | O | O | 122 | 23,563 | `data_modeling`, `access_control`, `posthog_ai`, `data_warehouse` 외 4 | 4 · 15 · 7 | — | **유지** 데이터 묶음 |
| `data_modeling` | `DAG`·`GitHubSyncConfig`로 저장 쿼리의 의존 그래프와 GitHub 동기화를 다루는 모듈 (external) — `products/data_modeling/backend/models` | O | O | 200 | 35,066 | `data_quality`, `warehouse_sources`, `data_warehouse`, `access_control` 외 2 | 10 · 42 · 11 | — | **핵심** 코어 42곳, 데이터 묶음 중심 |
| `data_quality` | `DataQualityCheck`·`DataQualitySuiteRun`으로 데이터 품질 검사를 실행하고 기록하는 모듈 (external) — `products/data_quality/backend/models` | O | O | 137 | 28,763 | `data_modeling`, `data_catalog`, `warehouse_sources`, `access_control` 외 2 | 3 · 20 · 2 | — | **유지** 데이터 묶음 |
| `data_tools` | `DataWarehouseJoin`·`DataWarehouseExpression`로 쿼리 도구의 조인과 표현식을 저장하는 모듈 — `products/data_tools/backend/models/join.py` | O | — | 15 | 285 | — | 6 · 6 · 0 | — | **핵심** 작지만 product 6개·코어 6곳이 import |
| `data_warehouse` | `TeamDataWarehouseConfig`로 외부 DB와 SaaS 소스를 연결해 웨어하우스 테이블을 만드는 모듈 (external) — `products/data_warehouse/backend/direct_snowflake.py` | O | O | 405 | 87,511 | `warehouse_sources`, `data_modeling`, `access_control`, `managed_warehouse` 외 6 | 11 · 10 · 86 | 2 | **핵심** 프론트 86곳·product 11개가 import, 데이터 묶음 중심 |
| `demo` | `MatrixManager`와 `HedgeboxMatrix`로 데모 데이터를 생성한다 — `products/demo/backend/facade/api.py` | O | — | 35 | 7,893 | `dashboards`, `product_analytics`, `cohorts`, `actions` 외 7 | 1 · 9 · 0 | — | **유지** 개발용 데모 데이터, product 11개를 import |
| `desktop` | PostHog Desktop과 모바일 앱, 에이전트 프레임워크의 소스 저장소다 — `products/desktop/README.md` | — | — | 4,669 | 715,489 | — | 0 · 1 · 0 | — | **검토** 독립 pnpm 워크스페이스(약 72만 줄), 다른 product와 import 없음 |
| `early_access_features` | 얼리 액세스 기능 목록을 저장하는 `EarlyAccessFeature` 모델이다 — `products/early_access_features/backend/models.py` | O | O | 27 | 6,726 | `feature_flags`, `error_tracking`, `access_control`, `workflows` 외 3 | 2 · 6 · 5 | — | **유지** `feature_flags`와 상호 의존 |
| `endpoints` | 저장된 쿼리를 `EndpointVersion`으로 버전 관리해 API 엔드포인트로 노출한다 — `products/endpoints/backend/models.py` | O | O | 101 | 32,859 | `data_modeling`, `product_analytics`, `managed_warehouse`, `signals` 외 2 | 2 · 4 · 5 | — | **유지** `data_modeling`·`product_analytics` 위에 얹힘 |
| `engineering_analytics` | 팀이 연결한 GitHub 저장소의 PR과 CI 데이터를 웨어하우스 뷰로 분석한다 (external) — `products/engineering_analytics/README.md` | O | O | 371 | 72,258 | `warehouse_sources`, `access_control`, `signals`, `data_modeling` | 3 · 3 · 0 | — | **검토** 기능 플래그 뒤 제품(`PostHog/posthog`로 dogfood), `signals`와 상호 의존 |
| `error_tracking` | `ErrorTrackingIssue`의 병합, 할당, 지문으로 에러 이슈를 관리한다 — `products/error_tracking/backend/models.py` | O | O | 532 | 85,299 | `posthog_ai`, `signals`, `workflows`, `cdp` 외 7 | 12 · 28 · 38 | 1 | **유지** 독립 기능, 들어오는 의존 product 12개 |
| `event_definitions` | 이벤트와 속성 정의를 `EventDefinition`, `PropertyDefinition`으로 저장한다 — `products/event_definitions/backend/models/__init__.py` | O | O | 12 | 660 | — | 11 · 30 · 4 | 1 | **핵심** 코어 30곳·product 11개가 import |
| `experiments` | `Experiment`와 `WebExperiment`로 A/B 실험의 설정과 상태를 관리한다 — `products/experiments/backend/models/` | O | O | 411 | 131,477 | `feature_flags`, `access_control`, `product_analytics`, `actions` 외 9 | 9 · 42 · 174 | 4 | **핵심** 코어 42곳·프론트 174곳이 import |
| `exports` | `Subscription`과 `ExportedAsset`으로 정기 전송과 자산 내보내기를 다룬다 — `products/exports/backend/models/subscription.py` | O | O | 81 | 25,898 | `product_analytics`, `dashboards`, `access_control`, `posthog_ai` 외 3 | 11 · 32 · 0 | 10 | **핵심** 코어 32곳·product 11개가 import, `ee` import 10곳 |
| `feature_flags` | `FeatureFlag` 모델로 기능 플래그와 예약 변경·정책을 관리하는 모듈 — `products/feature_flags/backend/models/feature_flag.py` | O | O | 214 | 84,480 | `approvals`, `cohorts`, `access_control`, `experiments` 외 8 | 16 · 63 · 71 | 1 | **핵심** 코어 63곳·프론트 71곳·product 16개가 import |
| `field_notes` | 툴바에서 남긴 UI 필드 노트를 `FieldNote`로 저장해 MCP 에이전트에 넘긴다 — `products/field_notes/backend/models.py` | O | O | 8 | 365 | — | 0 · 0 · 0 | — | **검토** 작고 의존 없음(독립) |
| `games` | 내장 미니 게임 3종(368Hedgehogs, FlappyHog, ShipIt) 씬을 제공한다 — `products/games/manifest.tsx` | — | O | 8 | 1,553 | — | 0 · 0 · 0 | — | **제거 후보** 미니 게임, 의존 없음 |
| `groups` | 그룹 목록 씬과 백엔드 앱을 제공하며 모델은 없다 — `products/groups/manifest.tsx` | O | O | 39 | 8,407 | `persons`, `customer_analytics`, `notebooks`, `event_definitions` 외 2 | 5 · 0 · 11 | — | **유지** 프론트 11곳·product 5개가 사용 |
| `growth` | `ProductPushCampaign`과 `OrganizationEnrichment`로 가입 조직 보강과 제품 푸시를 다룬다 (internal,external) — `products/growth/backend/models.py` | O | O | 159 | 36,977 | `persons`, `warehouse_sources`, `wizard`, `tasks` 외 2 | 0 · 10 · 6 | 2 | **제거 후보** PostHog 가입 조직 보강(Clay 등)과 제품 푸시 |
| `inbox` | 자율 인박스 메뉴와 탭만 등록돼 있고 씬과 백엔드가 없다 (stub) — `products/inbox/manifest.tsx` | — | — | 1 | 33 | — | 0 · 0 · 0 | — | **검토** manifest만 있음 |
| `ingestion` | 수집 경고 해결용 스킬 문서만 담고 있으며 코드가 없다 (stub) — `products/ingestion/skills/resolving-ingestion-warnings/SKILL.md` | — | — | 0 | 0 | — | 0 · 0 · 0 | — | **유지** 스킬 문서만 있음, 코드 없음 |
| `integrations` | 환경 통합 API 작업을 MCP 도구로 노출하는 정의 파일이다 — `products/integrations/mcp/tools.yaml` | — | O | 0 | 0 | — | 4 · 0 · 17 | — | **유지** 코어 프론트 17곳이 import(생성 API) |
| `legal_documents` | BAA, DPA, MSA 법무 문서와 서명 상태를 `LegalDocument`로 관리한다 — `products/legal_documents/backend/models.py` | O | O | 48 | 7,426 | — | 0 · 3 · 0 | 1 | **제거 후보** PostHog와의 BAA·DPA·MSA 계약 문서 |
| `links` | 퇴역한 단축 링크 제품이며 `Link` 모델만 테이블 정리용으로 남았다 (stub) — `products/links/backend/models.py` | O | — | 4 | 41 | — | 0 · 0 · 0 | — | **제거 후보** 퇴역, `Link` 모델만 남음 |
| `live_debugger` | 퇴역한 라이브 디버거의 `LiveDebuggerBreakpoint` 모델만 남았다 (stub) — `products/live_debugger/backend/models.py` | O | — | 4 | 39 | — | 0 · 0 · 0 | — | **제거 후보** 퇴역, 모델만 남음 |
| `llm_analytics` | `ai_observability`로 옮긴 모델의 과거 마이그레이션과 데이터 신선도 설정(`DATA_SOURCES`)만 남은 앱이다 (stub) — `products/llm_analytics/backend/apps.py` | O | — | 4 | 24 | — | 0 · 0 · 0 | — | **유지** 마이그레이션 34개(LOC에서 빠짐)를 `ai_observability` 마이그레이션 0001이 이어 받음 |
| `logs` | 로그 조회, `LogsAlertConfiguration` 알림, 로그 보존 규칙을 다룬다 — `products/logs/backend/models.py` | O | O | 434 | 86,542 | `alerts_platform`, `alerts`, `tracing`, `posthog_ai` 외 9 | 8 · 11 · 15 | — | **유지** 관측성 묶음 중심 |
| `managed_migrations` | 외부 데이터를 가져오는 일괄 작업 `BatchImport`의 상태를 관리한다 — `products/managed_migrations/backend/models/batch_imports.py` | O | O | 24 | 6,169 | — | 0 · 0 · 0 | — | **유지** 작고 의존 없음 |
| `managed_warehouse` | 관리형 `DuckgresServer`와 Trino 기반 웨어하우스 소스 작업을 관리한다 (cloud) — `products/managed_warehouse/backend/models.py` | O | — | 97 | 29,144 | `warehouse_sources`, `data_warehouse`, `data_modeling`, `access_control` | 3 · 25 · 0 | — | **검토** PostHog 운영 `DuckgresServer` 전제, 코어 25곳 결합 |
| `marketing_analytics` | `MarketingAnalyticsGoalMapping`으로 마케팅 전환 목표를 매핑한다 — `products/marketing_analytics/backend/models/` | O | O | 234 | 69,223 | `warehouse_sources`, `data_warehouse`, `analytics_platform`, `access_control` 외 2 | 0 · 7 · 24 | 1 | **유지** 들어오는 의존 없음, 프론트 24곳 |
| `mcp_analytics` | `MCPSession`과 의도 클러스터로 MCP 도구 호출을 분석한다 — `products/mcp_analytics/backend/models.py` | O | O | 244 | 45,410 | `subscriptions`, `persons`, `dashboards`, `access_control` 외 2 | 2 · 21 · 3 | — | **유지** `dashboards`와 상호 의존 |
| `mcp_registry` | 공식 MCP 레지스트리를 크롤링해 서버를 순위 매기는 `MCPRegistryServer` 인덱스다 (external) — `products/mcp_registry/README.md` | O | O | 37 | 4,443 | `mcp_analytics` | 0 · 1 · 0 | — | **검토** 외부 MCP 레지스트리 크롤러, 들어오는 의존 없음 |
| `mcp_store` | 서드파티 MCP 서버 카탈로그 `MCPServerTemplate`을 제공하는 마켓플레이스다 (external) — `products/mcp_store/README.md` | O | O | 107 | 35,561 | `cdp` | 3 · 0 · 2 | 1 | **유지** `tasks`·`signals`·`canvas`가 사용 |
| `messaging` | Customer.io 메시지 템플릿과 수신 설정 `MessageTemplate`을 관리한다 (external) — `products/messaging/backend/services/customerio_client.py` | O | O | 68 | 8,992 | `workflows`, `cdp`, `notifications` | 1 · 4 · 0 | — | **유지** `workflows`와 상호 의존(Customer.io 클라이언트 포함) |
| `metrics` | 메트릭 대시보드 템플릿 `MetricsDashboardTemplate`과 쿼리 러너를 제공한다 — `products/metrics/backend/models.py` | O | O | 236 | 44,088 | `dashboards`, `logs`, `exports`, `tasks` 외 4 | 2 · 8 · 3 | 1 | **유지** 관측성 묶음 |
| `ml_inference` | 질문마다 AI 게이트웨이의 결정 모델에 답을 받아 돌려주는 `DecisionViewSet` API다. 결과는 저장하지 않고 Django 모델도 없다 (external) — `products/ml_inference/backend/presentation/views.py` | O | O | 28 | 2,207 | — | 6 · 0 · 2 | — | **유지** product 6개가 사용, 외부 AI 게이트웨이 필요 |
| `notebooks` | `Notebook`과 `NotebookRun`으로 노트북과 커널 실행을 관리한다 — `products/notebooks/backend/models.py` | O | O | 194 | 53,826 | `canvas`, `tasks`, `dashboards`, `access_control` 외 1 | 9 · 17 · 30 | 2 | **유지** 프론트 30곳·product 9개가 사용 |
| `notifications` | `NotificationEvent`와 읽음, 보관 상태로 인앱 알림을 관리한다 — `products/notifications/backend/models.py` | O | O | 24 | 2,409 | `access_control` | 15 · 11 · 5 | — | **핵심** product 15개가 import |
| `persons` | `Person`, `Persons` 씬으로 사람 상세와 목록 UI를 제공한다 — `products/persons/manifest.tsx` | — | O | 34 | 6,392 | `customer_analytics`, `workflows`, `conversations`, `logs` 외 3 | 15 · 0 · 59 | — | **핵심** 프론트 59곳·product 15개가 import(프론트 전용) |
| `platform_features` | 활동 로그 MCP 도구 정의와 프록시 진단 AI 도구 `DiagnoseProxyTool`만 있는 모듈 (external) — `products/platform_features/mcp/tools.yaml` | O | O | 10 | 194 | — | 4 · 0 · 45 | 1 | **유지** 프론트 45곳이 생성 API를 import, 백엔드는 `ee` 의존 도구 1개 |
| `posthog_ai` | `posthog_ai` 에이전트 화면과 다른 제품의 연동 지점을 담당한다 (external) — `products/posthog_ai/README.md` | O | O | 649 | 118,885 | `tasks`, `signals`, `platform_features`, `notebooks` 외 9 | 20 · 12 · 91 | 6 | **검토** 에이전트 묶음 중심, `ee.hogai` 제거로 import 6곳 끊김 |
| `product_analytics` | 인사이트 씬과 `project_id` 기준 접근·공유 규칙을 담당한다 — `products/product_analytics/AGENTS.md` | O | O | 619 | 188,571 | `actions`, `alerts`, `dashboards`, `cohorts` 외 13 | 25 · 47 · 158 | — | **핵심** 코어 47곳·프론트 158곳·product 25개가 import |
| `product_tours` | `ProductTour` 모델로 온보딩 투어를 저장하고 REST API를 제공한다 — `products/product_tours/ARCHITECTURE.md` | O | O | 25 | 3,872 | `feature_flags`, `access_control`, `approvals`, `surveys` | 1 · 4 · 1 | — | **검토** product.yaml에 deprecated, 담당 팀 없음 |
| `pulse` | `ProductBrief`, `Opportunity` 모델로 LLM 기반 제품 제안을 만든다 (external) — `products/pulse/backend/models.py` | O | O | 54 | 6,019 | `access_control`, `product_analytics`, `dashboards`, `annotations` 외 4 | 0 · 2 · 0 | 1 | **검토** LLM 제안, 들어오는 의존 없음 |
| `reminders` | `Reminder` 모델로 예약 알림을 만들고 발송 일정을 관리한다 — `products/reminders/backend/models/reminder.py` | O | O | 18 | 1,560 | `notifications`, `dashboards`, `experiments`, `feature_flags` 외 4 | 0 · 1 · 3 | — | **유지** 작고 들어오는 의존 없음 |
| `replay` | `ExportedRecording`으로 세션 리플레이 내보내기 기록을 관리한다 — `products/replay/backend/models/exported_recording.py` | O | O | 16 | 1,492 | `access_control` | 1 · 0 · 2 | 1 | **유지** 작음 |
| `replay_vision` | `Scanner` 설정으로 녹화 세션에 AI 스캔을 돌려 결과를 기록한다 (external) — `products/replay_vision/README.md` | O | O | 575 | 127,324 | `signals`, `alerts`, `experiments`, `access_control` 외 14 | 3 · 13 · 27 | 8 | **검토** AI 스캔, 나감 18개·`ee` import 8곳 |
| `revenue_analytics` | Stripe 데이터 소스 기반 `Revenue Analytics` 씬과 뷰를 제공한다 (external) — `products/revenue_analytics/backend/views/sources/stripe/subscription.py` | O | O | 79 | 8,561 | `warehouse_sources`, `data_warehouse`, `data_modeling`, `access_control` 외 1 | 3 · 11 · 5 | — | **유지** 데이터 묶음(Stripe 소스) |
| `review_hog` | `ReviewReport`로 GitHub PR 자동 리뷰 결과를 저장하고 게시한다 (external) — `products/review_hog/backend/models.py` | O | O | 256 | 61,625 | `signals`, `tasks`, `skills`, `stamphog` 외 3 | 1 · 2 · 0 | — | **검토** 공개 전 제한 출시(`review-hog` 플래그, 근거: `products/review_hog/ARCHITECTURE.md`), `tasks`·`signals`에 기댐 |
| `security` | `decide`로 접근 규칙을 허용·차단 판정하고 Temporal로 스냅샷을 동기화한다 (cloud,external) — `products/security/README.md` | O | — | 41 | 2,866 | — | 3 · 29 · 0 | — | **제거 후보** PostHog 보안 허브 연동, 단 코어 29곳 결합 해소 필요 |
| `session_replay` | 세션 리플레이 온보딩 단계 UI 한 파일만 있는 얇은 모듈이다 (stub) — `products/session_replay/frontend/onboarding/steps.tsx` | — | O | 1 | 122 | — | 0 · 0 · 1 | — | **유지** 온보딩 UI 한 파일 |
| `signals` | `SignalReport`로 신호를 묶어 LLM·GitHub 기반 리포트를 생성한다 (external) — `products/signals/ARCHITECTURE.md` | O | O | 1,066 | 313,458 | `tasks`, `skills`, `posthog_ai`, `warehouse_sources` 외 27 | 17 · 25 · 81 | 2 | **검토** 에이전트 묶음 중심, 나감 31개로 가장 강결합 |
| `skills` | `CommunitySkill`로 커뮤니티 스킬의 등록·설치를 관리한다 — `products/skills/backend/models/community_skills.py` | O | O | 78 | 24,600 | `ai_observability`, `signals`, `access_control` | 5 · 1 · 1 | 1 | **검토** 에이전트 묶음 |
| `slack_app` | `SlackSettings`, `SlackChannel`로 Slack 채널의 PostHog 응답 라우팅을 관리한다 (external) — `products/slack_app/backend/models.py` | O | — | 171 | 53,081 | `tasks`, `signals`, `alerts`, `feature_flags` 외 13 | 3 · 8 · 0 | 1 | **검토** 에이전트 묶음(`tasks`·`signals`와 상호 의존) |
| `stamphog` | `ReviewRun`으로 GitHub PR을 검토해 승인 여부를 정하고 게시한다 (external) — `products/stamphog/README.md` | O | O | 108 | 40,128 | `tasks` | 2 · 2 · 1 | — | **검토** 조직이 설치하는 GitHub App PR 승인 봇, `tasks` 샌드박스에 의존 |
| `streamlit_apps` | `StreamlitApp`, `StreamlitAppVersion`으로 Streamlit 앱 버전을 관리한다 — `products/streamlit_apps/backend/models.py` | O | O | 42 | 8,015 | `tasks` | 0 · 2 · 0 | — | **검토** `tasks`에만 의존, 들어오는 의존 없음 |
| `subscriptions` | 인사이트·대시보드 구독 목록과 상세 씬만 있다 (백엔드 없음) — `products/subscriptions/manifest.tsx` | — | O | 72 | 14,499 | `product_analytics` | 3 · 0 · 17 | — | **유지** 프론트 전용, 코어 프론트 17곳이 import |
| `support` | 지원팀이 프로젝트를 정리하는 일회성 CLI 스크립트 모음이다 (internal) — `products/support/scripts/AGENTS.md` | — | — | 6 | 1,136 | — | 0 · 0 · 0 | — | **제거 후보** PostHog 지원팀 일회성 CLI |
| `surveys` | `Survey`, `SurveyResponseArchive`로 설문과 응답 보관을 관리한다 — `products/surveys/backend/models.py` | O | O | 69 | 22,352 | `feature_flags`, `actions`, `access_control`, `approvals` 외 1 | 8 · 19 · 12 | 2 | **유지** 독립 기능, product 8개가 사용 |
| `tasks` | `SandboxSession`, `Channel`로 에이전트 작업 실행과 채널을 관리한다 (external) — `products/tasks/backend/models.py` | O | O | 562 | 207,149 | `slack_app`, `canvas`, `signals`, `posthog_ai` 외 11 | 20 · 24 · 54 | 15 | **검토** 에이전트 묶음 중심, `ee` import 15곳 끊김 |
| `today` | `TodayHighlights`로 사용자별 일일 하이라이트를 저장한다 — `products/today/backend/models.py` | O | O | 56 | 5,835 | `signals`, `access_control`, `conversations` | 0 · 3 · 24 | — | **검토** `signals`·`conversations` 하이라이트, 프론트 24곳 |
| `toolbar` | `Toolbar` 씬 등록만 있는 얇은 모듈이다 (`/toolbar` 경로) (stub) — `products/toolbar/manifest.tsx` | — | — | 1 | 34 | — | 0 · 0 · 0 | — | **유지** manifest만 있음 |
| `tracing` | `TracingView`, `TracesRetentionRule`로 트레이스 보기와 보존 규칙을 관리한다 — `products/tracing/backend/models.py` | O | O | 236 | 37,522 | `logs`, `persons`, `metrics`, `access_control` 외 3 | 2 · 8 · 5 | — | **유지** 관측성 묶음 |
| `user_interviews` | `UserInterview`로 사용자 인터뷰 기록과 분류·주제를 관리한다 — `products/user_interviews/backend/models.py` | O | — | 4 | 136 | — | 0 · 0 · 0 | — | **제거 후보** 모델만 있고 의존 없음 |
| `visual_review` | `Run`, `Artifact`로 스크린샷 기준 이미지 비교와 승인을 관리한다 (external) — `products/visual_review/README.md` | O | O | 177 | 40,456 | `integrations` | 0 · 1 · 0 | — | **검토** 독립 도구(의존 거의 없음), 떼어 내기 쉬움 |
| `warehouse_sources` | 외부 SaaS 데이터를 웨어하우스로 가져오는 ELT 소스를 관리한다 (external) — `products/warehouse_sources/manifest.tsx` | O | O | 7,848 | 1,332,340 | `data_warehouse`, `cdp`, `warehouse_sources_queue`, `batch_exports` 외 7 | 20 · 109 · 14 | 3 | **핵심** 코어 109곳·product 20개가 import |
| `warehouse_sources_queue` | `QueueJob`, `SourceBatch`로 웨어하우스 동기화 작업 큐를 관리한다 — `products/warehouse_sources_queue/backend/models.py` | O | — | 21 | 8,710 | — | 1 · 0 · 0 | — | **유지** `warehouse_sources` 전용 |
| `warehouse_suggestions` | `WarehouseSuggestion`으로 웨어하우스 테이블 추천 결과를 저장한다 — `products/warehouse_suggestions/backend/models.py` | O | O | 55 | 5,531 | `data_modeling`, `data_catalog`, `warehouse_sources`, `access_control` | 0 · 2 · 0 | — | **유지** 데이터 묶음, 들어오는 의존 없음 |
| `web_analytics` | 웹 분석 씬과 사전 집계 쿼리 서빙을 담당한다 — `products/web_analytics/PRECOMPUTATION.md` | O | O | 393 | 101,383 | `analytics_platform`, `access_control`, `product_analytics`, `actions` 외 6 | 1 · 39 · 32 | 2 | **유지** 코어 39곳이 import |
| `webmcp` | `WebMCPViewSet` 뷰셋으로 WebMCP 관련 REST 엔드포인트를 제공한다 — `products/webmcp/backend/presentation/views.py` | O | O | 19 | 847 | — | 0 · 1 · 1 | — | **검토** 작고 의존 없음 |
| `wizard` | `WizardRun`으로 PostHog 설치 마법사 실행과 산출물을 관리한다 (external) — `products/wizard/backend/models.py` | O | O | 209 | 22,415 | `tasks`, `warehouse_sources`, `security`, `event_definitions` 외 1 | 1 · 2 · 9 | — | **검토** PostHog 설치 마법사, `tasks` 에이전트에 의존 |
| `workflows` | `hog_flow` 모델로 트리거와 액션을 잇는 워크플로 편집·실행을 담당한다 — `products/workflows/CONTRIBUTING.md` | O | O | 666 | 131,766 | `messaging`, `cdp`, `access_control`, `cohorts` 외 13 | 11 · 26 · 35 | 4 | **유지** `cdp`·`messaging`과 함께 쓰임, 나감 17개 |

## 집계 방법

후속 작업에서 생성 스크립트로 옮길 수 있도록, 이 페이지를 만든 명령과 스크립트를 그대로 남긴다. 모두 저장소 루트에서 실행한다.

### 숫자의 한계

- 의존은 import **줄**을 정규식으로 센 값이다. 같은 줄에서 여러 이름을 가져와도 1로 센다. 함수 안의 지연 import도 센다.
- TypeScript는 `from '...'` 형태만 센다. product 사이의 동적 import(`import('products/X/...')`)는 빠진다. 이렇게 빠진 product 사이 동적 import는 모두 이미 정적 import로 잡힌 쌍이라, 쌍과 묶음은 바뀌지 않는다. 코어 프론트 집계는 `'products/X/'` 문자열을 세므로 동적 import도 들어간다.
- Django 마이그레이션 사이의 의존은 import가 아니라서 세지 않았다(`llm_analytics` 줄 참고).
- 코어 참조 수는 `posthog/` 아래 Python·TS 파일에서 `from products.X` 줄과 `'products/X/'` 문자열을 모두 센다. 경로 문자열(설정, 템플릿 경로 등)도 섞여 있다.
- 테스트 파일(`tests/`, `test/`, `__tests__/`, `evals/`, `test_*`, `*.test.*`, `*.stories.*`)은 의존 집계에서 뺐다. 파일 수와 LOC에는 들어 있다.
- `ee/` 디렉터리가 없으므로 `ee` 모듈로 들어오는 의존은 세지 않았다.
- 역할 열은 각 모듈의 `product.yaml`, `README.md`/`AGENTS.md`, `manifest.tsx`, `backend/apps.py`, 모델 클래스를 읽고 쓴 요약이다. 로직 코드까지 읽은 것은 아니다. `platform_features`, `feature_flags`, `cohorts`, `customer_analytics`는 직접 다시 확인해 고쳤다.
- 판단 열은 아래 숫자와 역할 플래그를 보고 사람이 정한 값이다(`judge.tsv`). 스크립트가 계산하지 않는다.
- 역할 TSV와 `judge.tsv`는 저장소에 없다. 표의 역할·판단 열이 그 내용이다.
- `build.py`로 표를 만든 뒤 손으로 고친 칸이 있다. 역할: `billing`, `engineering_analytics`, `llm_analytics`, `ml_inference`, `warehouse_sources`, `web_analytics`. 판단: `commands`, `desktop`, `engineering_analytics`, `llm_analytics`, `review_hog`, `stamphog`. `build.py`를 다시 돌리면 이 칸은 TSV 값으로 돌아가므로, 다시 만들 때는 이 칸을 옮겨 적는다.

### 1. 규모·의존 집계 (`scan.py`)

```bash
python3 -I scan.py . > scan.json
```

```python
import json, re, sys, tomllib
from pathlib import Path
from collections import defaultdict

root = Path(sys.argv[1])
P = root / "products"
prods = sorted(d.name for d in P.iterdir() if d.is_dir() and not d.name.startswith(("_", ".")))
code_ext = {".py", ".ts", ".tsx", ".rs", ".go", ".js", ".jsx"}
skip = {"node_modules", "__pycache__", "generated", "migrations", "__snapshots__"}
py_imp = re.compile(r"^\s*(?:from|import)\s+(products\.(\w+)|posthog\b|ee\b)", re.M)
ts_imp = re.compile(r"""from\s+['"](?:products/(\w+)|@posthog/products-([\w-]+)|scenes/|lib/|~/)""")
tach = tomllib.loads((root / "tach.toml").read_text())
tdeps = {}
for m in tach["modules"]:
    p = m["path"]
    if p.startswith("products."):
        tdeps[p.split(".")[1]] = sorted(
            {(d if isinstance(d, str) else d.get("path", "")).removeprefix("products.").split(".")[0] for d in m.get("depends_on", [])}
        )
out = {}
inbound = defaultdict(lambda: defaultdict(int))
inbound_ts = defaultdict(lambda: defaultdict(int))


def is_test_path(parts, fname):
    return bool({"tests", "test", "__tests__", "evals"} & parts) or fname.startswith("test_") or ".test." in fname or ".stories." in fname


for name in prods:
    d = P / name
    files = loc = py_files = ts_files = rs_go = 0
    test_files = 0
    dep_py = defaultdict(int)
    dep_ts = defaultdict(int)
    posthog_py = 0
    frontend_core = 0
    sub_loc = defaultdict(int)
    for f in d.rglob("*"):
        if not f.is_file() or f.suffix not in code_ext:
            continue
        rel = f.relative_to(d).parts
        parts = set(rel)
        if parts & skip:
            continue
        try:
            txt = f.read_text(errors="ignore")
        except Exception:
            continue
        n = txt.count("\n")
        files += 1
        loc += n
        sub_loc[rel[0] if len(rel) > 1 else "."] += n
        is_test = is_test_path(parts, f.name)
        if is_test:
            test_files += 1
        if f.suffix == ".py":
            py_files += 1
            if is_test:
                continue
            for mm in py_imp.finditer(txt):
                if mm.group(2):
                    if mm.group(2) != name:
                        dep_py[mm.group(2)] += 1
                else:
                    posthog_py += 1
        elif f.suffix in (".ts", ".tsx"):
            ts_files += 1
            if is_test:
                continue
            for mm in ts_imp.finditer(txt):
                o = mm.group(1) or (mm.group(2) or "").replace("-", "_")
                if o:
                    if o != name:
                        dep_ts[o] += 1
                else:
                    frontend_core += 1
        else:
            rs_go += 1
    yaml = (d / "product.yaml").read_text() if (d / "product.yaml").exists() else ""
    title = re.search(r"^name:\s*(.+)$", yaml, re.M)
    out[name] = dict(
        backend=(d / "backend").is_dir(),
        frontend=(d / "frontend").is_dir(),
        other=sorted(x.name for x in d.iterdir() if x.is_dir() and x.name not in ("backend", "frontend", "__pycache__")),
        files=files,
        loc=loc,
        py=py_files,
        ts=ts_files,
        rs_go=rs_go,
        tests=test_files,
        sub_loc=dict(sub_loc),
        dep_py=dict(dep_py),
        dep_ts=dict(dep_ts),
        posthog_py=posthog_py,
        frontend_core=frontend_core,
        tach=tdeps.get(name),
        title=title.group(1).strip() if title else None,
        readme=(d / "README.md").exists(),
        agents=(d / "AGENTS.md").exists(),
    )
    for o in dep_py:
        inbound[o][name] += dep_py[o]
    for o in dep_ts:
        inbound_ts[o][name] += dep_ts[o]

outside = {}
for top in ["posthog", "common", "frontend/src", "nodejs/src", "services", "ee"]:
    base = root / top
    if not base.exists():
        continue
    for f in base.rglob("*"):
        if not f.is_file() or f.suffix not in (".py", ".ts", ".tsx"):
            continue
        if set(f.parts) & {"node_modules", "generated", "__snapshots__", "migrations"}:
            continue
        if is_test_path(set(f.parts), f.name):
            continue
        txt = f.read_text(errors="ignore")
        for mm in re.finditer(
            r"(?:^\s*(?:from|import)\s+products\.(\w+)|['\"]products/(\w+)/|@posthog/products-([\w-]+))", txt, re.M
        ):
            o = mm.group(1) or mm.group(2) or (mm.group(3) or "").replace("-", "_")
            key = top.split("/")[0]
            inbound[o]["<" + key + ">"] += 1
for name in out:
    out[name]["inbound_py"] = dict(inbound.get(name, {}))
    out[name]["inbound_ts"] = dict(inbound_ts.get(name, {}))
json.dump(out, sys.stdout, indent=1, ensure_ascii=False)
```

### 2. 양방향 의존 쌍과 결합 정도 (`mutual.py`)

```bash
python3 -I mutual.py scan.json
```

```python
import json, sys

d = json.load(open(sys.argv[1]))
edges = set()
for n, v in d.items():
    for o in v["dep_py"]:
        if o in d:
            edges.add((n, o))
    for o in v["dep_ts"]:
        if o in d:
            edges.add((n, o))
mutual = sorted({tuple(sorted(e)) for e in edges if (e[1], e[0]) in edges})
print("mutual:", len(mutual))
for a, b in mutual:
    print(a, "<->", b)
# isolated: no product edges in/out (python+ts)
for n, v in d.items():
    outs = {o for o in list(v["dep_py"]) + list(v["dep_ts"]) if o in d}
    ins = {k for k in list(v["inbound_py"]) + list(v["inbound_ts"]) if not k.startswith("<")}
    core = v["inbound_py"].get("<posthog>", 0)
    fe = v["inbound_py"].get("<frontend>", 0)
    print(f"DEG {n} out={len(outs)} in={len(ins)} core_in={core} fe_in={fe}")
```

독립 후보 목록은 위 결과에 아래 조건을 건 것이다.

```bash
python3 -I -c "
import json,sys
d=json.load(open(sys.argv[1]))
for n,v in sorted(d.items()):
    outs={o for o in list(v['dep_py'])+list(v['dep_ts']) if o in d}
    ins={k for k in list(v['inbound_py'])+list(v['inbound_ts']) if not k.startswith('<')}
    core=v['inbound_py'].get('<posthog>',0); fe=v['inbound_py'].get('<frontend>',0)
    if len(ins)<=1 and len(outs)<=1 and core<=3 and fe<=3: print(n,len(outs),len(ins),core,fe,v['loc'])
" scan.json
```

### 3. 지워진 `ee/`를 가리키는 import

```bash
# product별 비테스트 파일 수
grep -rlE '^\s*(from|import) ee(\.| )' --include=*.py products | grep -vE '/tests?/|/test_[^/]*$|_test\.py$|conftest' | awk -F/ '{print $2}' | sort | uniq -c | sort -rn
# 가장 많이 가리키는 대상 (테스트 포함)
grep -rhoE '^\s*(from|import) ee\.[a-z_]+(\.[a-z_]+)?' --include=*.py products | sed 's/^ *//' | awk '{print $2}' | sort | uniq -c | sort -rn | head -12
# tach.toml에 남은 "ee" (줄 수)
grep -c '"ee"' tach.toml
# 그 45줄의 내역: depends_on에 "ee"를 둔 모듈 수와 product가 아닌 모듈
python3 -I -c "
import tomllib
t=tomllib.loads(open('tach.toml').read())
deps=[m['path'] for m in t['modules'] if 'ee' in [d if isinstance(d,str) else d.get('path') for d in m.get('depends_on',[])]]
print(len(deps), [p for p in deps if not p.startswith('products.')], [m['path'] for m in t['modules'] if m['path']=='ee'])
"
```

### 4. 요약의 개별 숫자

```bash
# backend/, frontend/ 디렉터리가 있는 모듈 수 (87, 80)
python3 -I -c "import json;d=json.load(open('scan.json'));print(sum(v['backend'] for v in d.values()), sum(v['frontend'] for v in d.values()))"
# source.py가 있는 커넥터 디렉터리 수 (1,382)
find products/warehouse_sources/backend/temporal/data_imports/sources -maxdepth 1 -mindepth 1 -type d -exec test -e '{}/source.py' ';' -print | wc -l
# backend/가 있는데 PRODUCTS_APPS에 없는 모듈 (demo)
python3 -I -c "
import re,json
t=open('posthog/settings/web.py').read()
apps=set(re.findall(r'\"products\.(\w+)', re.search(r'PRODUCTS_APPS\s*=\s*\[(.*?)\n\]', t, re.S).group(1)))
d=json.load(open('scan.json'))
print(sorted(n for n,v in d.items() if v['backend'] and n not in apps))
"
```

### 5. 표 생성 (`build.py`)

역할 TSV(`module<TAB>역할<TAB>플래그<TAB>근거`)와 판단 TSV(`module<TAB>판단<TAB>근거`)를 받아 표를 만든다.

```bash
python3 -I build.py . scan.json roles_00.tsv,roles_01.tsv,roles_02.tsv judge.tsv > table.md
```

```python
import json, sys, re, subprocess
from pathlib import Path

root = Path(sys.argv[1])
scan = json.load(open(sys.argv[2]))
roles = {}
for f in sys.argv[3].split(","):
    for line in open(f):
        p = line.rstrip("\n").split("\t")
        roles[p[0]] = (p[1], p[2], p[3])
judge = {}
for line in open(sys.argv[4]):
    p = line.rstrip("\n").split("\t")
    judge[p[0]] = (p[1], p[2])
overrides = {
    "platform_features": ("활동 로그 MCP 도구 정의와 프록시 진단 AI 도구 `DiagnoseProxyTool`만 있는 모듈", "external", "products/platform_features/mcp/tools.yaml, products/platform_features/backend/max_tools.py"),
    "feature_flags": ("`FeatureFlag` 모델로 기능 플래그와 예약 변경·정책을 관리하는 모듈", "none", "products/feature_flags/backend/models/feature_flag.py, products/feature_flags/manifest.tsx"),
    "cohorts": ("`Cohort` 모델로 코호트 정의·계산·백필을 관리하는 모듈", "none", "products/cohorts/backend/models/cohort.py, products/cohorts/backend/backfill"),
    "customer_analytics": ("`Account`·`Meeting`으로 고객 계정과 Google 캘린더·Gmail 동기화를 다루는 모듈", "external", "products/customer_analytics/backend/models, products/customer_analytics/backend/AGENTS.md"),
}
roles.update(overrides)

# non-test files importing ee.*, per product
ee = {}
out = subprocess.run(["grep", "-rlE", r"^\s*(from|import) ee(\.| )", "--include=*.py", "products"], cwd=root, capture_output=True, text=True).stdout
for path in out.split():
    if re.search(r"/tests?/|/test_[^/]*$|_test\.py$|conftest", path):
        continue
    n = path.split("/")[1]
    ee[n] = ee.get(n, 0) + 1


def fmt_deps(v):
    m = {}
    for k, c in list(v["dep_py"].items()) + list(v["dep_ts"].items()):
        if k in scan:
            m[k] = m.get(k, 0) + c
    items = sorted(m.items(), key=lambda kv: -kv[1])
    s = ", ".join(f"`{k}`" for k, _ in items[:4])
    if len(items) > 4:
        s += f" 외 {len(items) - 4}"
    return s or "—"


def b(x):
    return "O" if x else "—"


rows = []
for n in sorted(scan):
    v = scan[n]
    role, flags, ev = roles.get(n, ("미확인", "", ""))
    role = role.rstrip(".")
    ev0 = ev.split(",")[0].strip()
    if ev0 and not ev0.startswith("products/"):
        ev0 = "products/" + ev0
    ins = {k for k in list(v["inbound_py"]) + list(v["inbound_ts"]) if not k.startswith("<")}
    core = v["inbound_py"].get("<posthog>", 0)
    fe = v["inbound_py"].get("<frontend>", 0)
    j, why = judge[n]
    fl = "" if flags in ("none", "") else f" ({flags})"
    rows.append(
        f"| `{n}` | {role}{fl} — `{ev0}` | {b(v['backend'])} | {b(v['frontend'])} | {v['files']:,} | {v['loc']:,} | {fmt_deps(v)} | {len(ins)} · {core} · {fe} | {ee.get(n, 0) or '—'} | **{j}** {why} |"
    )
print("| 모듈 | 역할 (플래그) — 근거 | BE | FE | 파일 | LOC | 나가는 의존 (상위 4) | 들어옴: product · 코어 · 프론트 | `ee` import | 판단 · 근거 |")
print("|---|---|---|---|---:|---:|---|---|---:|---|")
print("\n".join(rows))
```

Decided in: buzzhog-y4g8
