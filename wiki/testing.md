# 테스트와 CI 현황

확인 기준 커밋: 79b3714e131

이 페이지는 이 포크에서 테스트가 어디에 있고, 어떻게 돌리고, 무엇이 떠 있어야 하는지 정리한다.
또 CI 워크플로가 지금 어떤 상태인지, `products/` 모듈 하나를 뺄 때 깨지는 테스트를 어떻게 찾는지 적는다.
숫자는 모두 `git ls-files` 결과를 스크립트로 센 값이다. 명령은 맨 끝 [집계 방법](#집계-방법)에 있다.
개발 스택을 띄우는 순서는 [런북](runbook.md), 환경 변수는 [설정](configuration.md), 모듈별 의존은 [모듈 목록](modules.md)을 본다.
원문 규칙은 루트 [`AGENTS.md`](../AGENTS.md)의 "Commands"·"Tests" 절과 [`products/README.md`](../products/README.md)에 있다.

## 요약

- 테스트 러너는 다섯 종류다. pytest(Python), Jest(TS/JS), Vitest(독립 워크스페이스), Playwright(E2E), `cargo test`(Rust), `go test`(Go). `hogli test <경로>`가 경로를 보고 하나를 고른다.
- **이 포크에는 `.github/workflows`가 없다.** `b068ff99030`(Sync and remove all non-FOSS parts)이 워크플로 140개를 지웠다. 그래서 push나 PR에서 자동으로 도는 CI가 없다. 테스트와 린트는 로컬에서 직접 돌려야 한다.
- 워크플로가 없어도 `.github/actions/`, `.github/scripts/`와 CI 전제 도구(`hogli lint:workflows`, `hogli test:workflows`, `hogli ci:plan`, `hogli ci:preflight`)는 남아 있다. 일부는 워크플로 파일을 입력으로 받으므로 지금은 할 일이 없거나 결과가 비어 있다(아래 [남은 CI 자산](#남은-ci-자산)).
- Python 테스트는 Postgres, ClickHouse, Redis가 떠 있어야 돈다. Kafka는 ClickHouse 쪽 Kafka 엔진 테이블 생성에 쓰인다.
- 모듈을 뺄 때는 `tach`, `hogli product:lint`, import 검색 세 가지로 깨지는 곳을 찾는다.

## 테스트 위치

### Python (pytest)

파일 이름이 `test_*.py` 또는 `*_test.py`인 파일은 5,911개다.

| 위치 | 파일 수 |
| --- | ---: |
| `products/` | 4,507 |
| `posthog/` | 1,231 |
| `tools/` | 68 |
| `services/` | 60 |
| `.github/` | 19 |
| `rust/` | 10 |
| `common/` | 8 |
| `bin/` | 6 |
| `packages/` | 2 |

`products/` 안에서는 `warehouse_sources`(1,976)가 가장 많다. 그다음은 `tasks`(176), `signals`(168), `batch_exports`(112), `experiments`(106), `web_analytics`(96), `ai_observability`(96), `slack_app`(79), `product_analytics`(78), `replay_vision`(73)다.
이 패턴은 테스트 폴더 안의 보조 파일도 일부 센다. 테스트 케이스 수가 아니라 파일 수다.

설정은 루트 `pytest.ini`에 있다. 근거: `pytest.ini`.

- `DJANGO_SETTINGS_MODULE = posthog.settings`, 환경 변수 `DEBUG=1`, `TEST=1`
- `pythonpath = . common tools/hogli-commands tools/query-performance-ai packages/personhog-proto`
- `addopts`에 `--reuse-db`가 있다. 테스트 DB를 지우지 않고 다시 쓴다.
- `addopts`의 `--ignore=`로 자기 설정을 따로 가진 트리를 뺀다: `services/llm-gateway`, `services/stripe-mock`, `common/ingestion/acceptance_tests`, `tools/hogli`, `tools/hogli-commands`, `packages/owners-yaml`, `tools/traffic-sim`, `tools/query-performance-ai`, `products/desktop`, `products/stamphog/packages`, `posthog/user_scripts`
- `testpaths`는 없다. 인자 없이 `pytest`를 돌리면 루트 아래 전부를 모은다.

`--ignore`된 트리 가운데 `packages/owners-yaml`, `services/llm-gateway`, `tools/hogli`는 각자 `pyproject.toml`에 `testpaths = ["tests"]`를 둔다. `services/stripe-mock`, `rust/deltalite/python`은 각자 `pytest.ini`를 둔다.

`conftest.py`는 89개다. 위쪽 세 개가 공통 픽스처를 잡는다: 루트 `conftest.py`, `posthog/conftest.py`, `products/conftest.py`.

product 하나의 백엔드 테스트는 그 product의 `package.json`에 `backend:test` 스크립트로도 있다. 예: `products/surveys/package.json`의 `pytest -c ../../pytest.ini --rootdir ../.. backend/ -v --tb=short`.

### TypeScript/JavaScript (Jest)

`*.test.ts`, `*.test.tsx`, `*.test.js` 파일은 5,235개다.

| 위치 | 파일 수 |
| --- | ---: |
| `products/` | 2,596 |
| `frontend/` | 1,233 |
| `nodejs/` | 701 |
| `packages/` | 371 |
| `services/` | 270 |
| `common/` | 23 |
| `.github/` | 19 |
| `.semgrep/` | 14 |
| `.depot/` | 5 |
| `tools/` | 3 |

- 웹 앱의 Jest 설정은 `frontend/jest.config.ts`다. `rootDirectories()`가 `frontend/src`, `frontend/bin`, `products/`, quill 차트·컴포넌트, `packages/llm-normalizer/src`, `common/esbuilder`를 모은다. 그래서 `products/*/frontend/`의 테스트는 product 자기 `package.json`이 아니라 `@posthog/frontend`의 Jest로 돈다. 근거: `frontend/jest.config.ts:rootDirectories`, `tools/hogli-commands/hogli_commands/test_runner.py:_detect_jest_test`.
- 수집 서버(`nodejs/`)는 `nodejs/jest.config.js`를 쓴다. `*.serial.test.ts` 21개는 모두 `nodejs/`에 있다. 공유 DB를 리셋하는 테스트처럼 격리할 수 없는 경우에만 쓰는 이름이다.
- 그 밖의 Jest 설정: `common/hogvm/typescript`, `common/replay-headless`, `common/replay-shared`, `services/stripe-app`, `.github/actions/paths-filter`, `.depot/actions/paths-filter`, `nodejs/src/ingestion/pipelines/sessionreplay/ml-mirror-image-scrub-sidecar`.

### Vitest

Vitest 설정은 21개다. `products/desktop`(10), `packages/agent`(4), `services/`(4: `agent-proxy`, `credentials-service`, `mcp`, `oauth-proxy`), `tools/`(2: `openapi-codegen`, `workflow-plan`), `products/visual_review/cli`(1).
`products/desktop`과 `packages/agent`는 독립 pnpm 워크스페이스다. 루트 Jest가 모으지 않으므로 `hogli test`가 그 안의 경로를 Vitest로 보낸다. 근거: `test_runner.py:_NESTED_VITEST_ROOTS`, `_detect_desktop_vitest`.
데스크톱 전체는 `hogli desktop:test`(`pnpm --dir products/desktop test`)로 돈다. 근거: `hogli.yaml`.

### Playwright (E2E)

`*.spec.ts`는 66개다. `playwright/` 44, `products/` 20, `frontend/` 2.

- 웹 앱 E2E는 `playwright/playwright.config.ts`와 `playwright/e2e/` 아래에 있다.
- product 쪽 E2E는 `products/<name>/frontend/e2e/`에 있다(`surveys`, `billing`, `ai_observability`, `replay`, `posthog_ai`).
- 데스크톱 앱은 설정을 따로 가진다: `products/desktop/apps/code/tests/e2e/playwright.config.ts`, `products/desktop/apps/web/tests/e2e/`.
- `hogli test`는 `playwright/` 아래의 `.spec.ts`만 Playwright로 알아본다. 근거: `test_runner.py:detect_test_type`. `products/` 아래 `.spec.ts`를 `hogli test`로 돌릴 수 있는지는 미확인이다.

### Rust

`rust/` 아래 `#[test]` 또는 `#[tokio::test]`가 있는 파일은 875개다. `rust/Cargo.toml`의 workspace member는 75개다. 크레이트 바로 아래 `tests/` 디렉터리는 30개다.
파일 수가 많은 크레이트: `cohort-stream-processor`(99), `feature-flags`(97), `common`(95), `capture`(80), `cymbal`(65), `cohort-seeder`(57), `kafka-deduplicator`(47), `batch-import-worker`(39).
`rust/` 아래 Python 테스트 10개는 `rust/deltalite/python`처럼 Python 바인딩을 가진 크레이트의 것이다.

### Go

`*_test.go`는 55개다. `livestream/` 25, `services/` 12, `tools/` 10, `clickhouse-udfs/` 4, `bin/` 3, `packages/` 1.

## 로컬에서 돌리기

### `hogli test`

`hogli test <파일 또는 디렉터리>`가 경로를 보고 러너를 고른다. 근거: `tools/hogli-commands/hogli_commands/test_runner.py:detect_test_type`, `_detect_directory`.

| 경로 | 실행되는 명령 |
| --- | --- |
| `playwright/**/*.spec.ts` | `pnpm exec playwright test <경로>` |
| `posthog/`, `ee/`, `products/`, `common/`, `dags/`, `tools/`, `services/` 아래 `.py` | `pytest -s <경로>` (`REDIS_URL=redis:///`를 넣는다) |
| `*.test.ts`, `*.test.tsx` | `pnpm --filter=<가장 가까운 package.json의 name> exec jest <경로>`. `products/` 아래면 `@posthog/frontend` |
| `products/desktop/**`, `packages/agent/**` | `pnpm --dir <패키지> exec vitest run <경로>` |
| `*.rs` | 가장 가까운 `Cargo.toml` 기준 `cargo test` |
| `*.go`, `go.mod` | 가장 가까운 `go.mod`에서 `go test ./<패키지>/...` |
| `products/<name>` (최상위만) | `pnpm turbo run backend:test --filter=<그 product 패키지>` |

- 단일 테스트: `hogli test path/to/test_x.py::TestClass::test_method`. Rust는 `file.rs::test_name`, Jest는 `file.test.ts::<이름 패턴>`.
- `hogli test --changed`: 현재 브랜치에서 master와 다른 테스트 파일만 돈다. master 위에서는 의미가 없어 막힌다. 근거: `test_runner.py:_get_changed_files`.
- `hogli test <경로> --watch`: 감시 모드.
- `_PYTHON_ROOTS`에 `ee/`가 남아 있지만 이 포크에는 `ee/`가 없다(`ls ee` 실패).

그 밖의 묶음 명령. 근거: `hogli.yaml`.

- `hogli test:python` → `pytest` (루트 전체)
- `hogli test:js` → `pnpm --filter=@posthog/frontend test`
- `hogli test:e2e` → `bin/e2e-test-runner` → `phrocs --config bin/mprocs-e2e.yaml`
- `hogli test:quarantine` → `.test_quarantine.json`을 관리한다. 원래 목적은 flaky 테스트가 CI를 막지 않게 하는 것이다.

### 필요한 인프라

Python 테스트는 실제 데이터 저장소에 붙는다. 개발 스택을 먼저 띄운다(`hogli up -d`, `hogli wait`). 서비스 정의는 `docker-compose.dev.yml`에 있다(`db`, `redis7`, `clickhouse`, `zookeeper`, `kafka`, `objectstorage`, `temporal` 등).

- **Postgres**: pytest-django가 테스트 DB를 만든다. `--reuse-db`라서 처음 한 번은 마이그레이션 전체가 돌고, 그 뒤로는 재사용한다. 근거: `pytest.ini`, `posthog/conftest.py:django_db_setup`. 테스트 DB 이름은 `test_posthog`다. 근거: `test_runner.py:_seeded_test_database_ready`.
- **ClickHouse**: `TEST`일 때 DB 이름은 `posthog` + 접미사(`CLICKHOUSE_TEST_DB`)다. 근거: `posthog/settings/data_stores.py:CLICKHOUSE_TEST_DB`. 세션 시작 때 DB를 만들고 테이블을 만든다. `--reuse-db`일 때는 끝에 테이블을 비운다. `SKIP_CLICKHOUSE_RESET=1`이면 비우지 않는다. 근거: `posthog/conftest.py:_django_db_setup`, `create_clickhouse_tables`, `reset_clickhouse_tables`.
- **Kafka**: `create_clickhouse_tables`가 ClickHouse 안에 Kafka 엔진 테이블(`CREATE_KAFKA_TABLE_QUERIES`)을 만든다. 테스트가 브로커에 실제로 메시지를 보내는지는 테스트마다 다르며 이 페이지에서는 미확인이다.
- **Redis**: `hogli test`는 pytest에 `REDIS_URL=redis:///`를 넘긴다. 근거: `test_runner.py:_python_env`. `pytest`를 직접 돌리면 `posthog/settings/data_stores.py`의 기본값(`redis://redis7/<xdist 번호>`)을 쓴다.
- **Playwright E2E**: `bin/mprocs-e2e.yaml`이 E2E용 프로세스를 띄운다. 컨테이너로 돌리는 정의는 `docker-compose.playwright.yml`의 `playwright` 서비스다.
- Jest(`frontend/`)는 외부 인프라 없이 돈다. `nodejs/` Jest는 Postgres·Kafka·Redis가 필요한 테스트가 섞여 있다(`*.serial.test.ts`가 그 예). 정확한 목록은 미확인이다.

## CI 워크플로 현황

### 워크플로는 없다

`.github/workflows`는 이 포크에 없다. `git ls-files .github/workflows`가 0줄이다.
`b068ff99030`이 워크플로 140개(41,194줄)를 지웠다. 근거: `git show --stat b068ff99030 -- .github/workflows`.
이 포크가 왜 그렇게 했는지, upstream 병합 때 무엇이 충돌로 다시 들어오는지는 [업스트림 추적](upstream.md)에 있다.

그 결과:

- push, PR, merge queue, 정기 실행 어디에서도 테스트가 자동으로 돌지 않는다.
- 루트 `AGENTS.md`가 말하는 Backend CI, Trunk merge queue, Trunk Flaky Tests 업로드, Depot 러너, `test-new-events-schema` 라벨은 이 포크에서 동작하지 않는다. 그 규칙들은 upstream `PostHog/posthog`의 CI를 기준으로 쓴 것이다.
- 남은 안전장치는 로컬 git hook뿐이다. `.husky/pre-push`가 master로의 직접 push를 막고, Trunk merge queue 확인을 시도한다(`trunk`가 없으면 통과).

### 남은 CI 자산

워크플로는 지웠지만 워크플로가 부르던 부품과 CI 전제 도구는 남아 있다.

| 자산 | 상태 |
| --- | --- |
| `.github/actions/` (22개 composite action) | 부르는 워크플로가 없다. 예: `setup-python-cached`, `setup-pnpm`, `paths-filter`, `rust-compute-affected`, `trunk-quarantine-gate` |
| `.github/scripts/` | 워크플로가 부르던 검사 스크립트. 테스트 파일도 있다(Python 19, Jest 19). 일부는 로컬에서 직접 쓸 수 있다(예: `check-idor-model-coverage.py`) |
| `.github/new-events-schema-targets.txt` (75줄) | Backend CI가 새 events 스키마로 다시 돌리던 경로 목록. 지금은 읽는 곳이 없다 |
| `.github/actionlint.yaml`, `renovate.json5`, `CODEOWNERS`, `owners.yaml` | 설정 파일만 남았다 |
| `hogli lint:workflows` | 입력이 `.github/workflows/**`다. 검사할 파일이 없다. 근거: `tools/hogli-commands/hogli_commands/workflow_lint/cli.py` |
| `hogli test:workflows`, `hogli ci:plan` | `tools/workflow-plan`이 워크플로 파일을 읽는다. 실행 결과는 미확인 |
| `hogli ci:preflight` | 남아 있다. 바뀐 파일에서 닿는 CI 실패를 로컬에서 미리 잡는 도구다. 워크플로 파일에 걸린 트리거(`.github/workflows/*.yml`)는 이제 일치할 파일이 없다. 근거: `tools/hogli-commands/hogli_commands/ci_preflight.py` |
| `.test_quarantine.json` | 남아 있다. Trunk 쪽 연동이 없으므로 로컬 의미만 있다 |

### 로컬에서 CI를 대신하는 명령

워크플로가 하던 검사 가운데 이 저장소의 도구로 로컬에서 재현할 수 있는 것.

- 테스트: `hogli test --changed`, `hogli test <경로>`
- Python 린트: `ruff check .`, `ruff format --check .`
- 프런트엔드: `pnpm --filter=@posthog/frontend lint`, `pnpm --filter=@posthog/frontend typescript:check`
- 모듈 경계: `hogli lint:tach`, `hogli product:lint --all`
- 타입: `uv run mypy --cache-fine-grained .`
- 보안 규칙: `semgrep --config .semgrep/rules/security/ .`
- OpenAPI 생성물 drift: `hogli build:openapi` 뒤 `git diff`
- 한꺼번에: `hogli ci:preflight` (`--strict`, `--fix`)

## 모듈을 뺄 때 깨지는 테스트 찾기

`products/<name>`을 지우거나 옮기기 전에 다음 순서로 영향을 본다. 무엇을 뺄지 후보는 [모듈 목록](modules.md)에 있다.

### 1. import 검색

가장 직접적인 방법이다. 다른 곳에서 그 모듈을 import하면 그 파일의 테스트가 import 단계에서 깨진다.

```bash
git grep -l -E '(from|import) products\.<name>(\.|\b)' -- ':!products/<name>'
git grep -l -E "products/<name>/" -- '*.ts' '*.tsx' ':!products/<name>'
```

- Python 결과에 `test_*.py`가 있으면 그 테스트가 깨진다. `test`가 아닌 파일이 있으면 그 파일을 import하는 테스트까지 깨진다.
- TS는 `products/<name>/frontend/...` 경로 import와 `@posthog/products-<name>` 패키지 이름을 같이 찾는다.
- 문자열로만 모듈을 가리키는 곳은 import 검색에 걸리지 않는다. 다음을 따로 본다.
  - `posthog/settings/web.py`의 `PRODUCTS_APPS`
  - 각 product의 `backend/routes.py`를 모으는 URL 등록(`posthog/api/rest_router.py`, `posthog/api/routing.py`의 `register_routes`)
  - Celery·Temporal 등록, `tach.toml`의 `[[modules]]` 항목과 다른 모듈의 `depends_on`
  - `products/isolation_baseline.txt`, `products/model_crossing_uses_baseline.txt`
  - `.github/new-events-schema-targets.txt` (지금은 읽는 곳이 없지만 경로가 남는다)
- Django 앱이면 마이그레이션도 본다. 다른 앱의 마이그레이션이 그 앱을 `dependencies`로 걸었는지 찾는다. 모델·테이블 삭제는 루트 `AGENTS.md`가 `/django-migrations` 스킬을 요구한다.

### 2. `hogli lint:tach`

`tach.toml`에는 `[[modules]]`가 102개 있다. 모듈마다 `depends_on`과 공개 인터페이스(`[[interfaces]]`)를 적는다.
`hogli lint:tach`는 두 번 돈다. 근거: `tools/hogli-commands/hogli_commands/tach_lint.py:PASSES`.

1. `tach check --dependencies --exclude tests,test,**/test_*.py,**/*_test.py` — 테스트 코드를 뺀 의존 검사
2. `tach check --interfaces` — 테스트까지 포함한 인터페이스 검사

모듈을 지운 뒤 이 명령이 실패하면, 아직 그 모듈에 기대는 곳이 남은 것이다. 지우기 전에 `tach.toml`에서 그 모듈을 `depends_on`에 둔 항목을 찾으면 영향 범위를 미리 알 수 있다.

```bash
grep -n '"products.<name>' tach.toml
```

pytest 쪽 tach 플러그인은 `pytest.ini`에서 꺼져 있다(`-p no:tach`). `pytest -p tach --tach`로 켜면 바뀐 모듈에 닿지 않는 테스트를 건너뛸 수 있다고 `pytest.ini` 주석이 말한다. 이 포크에서 해 본 결과는 미확인이다.

### 3. `hogli product:lint`

`hogli product:lint <name>`은 product 하나의 구조를, `--all`은 전부를 검사한다. 근거: `tools/hogli-commands/hogli_commands/product/cli.py:cmd_lint`, `product/lint.py:lint_product`.
`backend/facade/contracts.py`가 있으면 strict 모드, 없으면 lenient 모드로 돈다. `tach.toml` 항목 검증(`validate_tach_toml`)과 baseline 검사(`check_baseline`)가 들어 있다.
모듈 하나를 지운 뒤 `hogli product:lint --all`을 돌리면 baseline 파일이나 `tach.toml`에 남은 흔적이 드러난다.

### 4. 테스트 돌리기

- 지운 모듈을 import하던 테스트 파일을 1번 결과에서 모아 `hogli test <파일>`로 돌린다.
- `products/conftest.py`와 `posthog/conftest.py`가 product 픽스처를 star-import하는지 본다. 근거: `posthog/conftest.py:pytest_terminal_summary` 주석("products/conftest.py star-imports this hook").
- 프런트엔드는 `pnpm --filter=@posthog/frontend typescript:check`가 남은 import를 잡는다.
- 지운 뒤 CI가 없으므로, 넓게 확인하려면 `hogli test:python`(오래 걸린다)이나 영향받는 최상위 디렉터리 단위로 `hogli test`를 돌린다.

## 집계 방법

모두 `git ls-files | grep -v node_modules` 목록(58,349개)에서 셌다. 커밋 `79b3714e131` 기준.

```bash
# Python
grep -E '(^|/)test_[^/]*\.py$|_test\.py$' | awk -F/ '{print $1}' | sort | uniq -c | sort -rn
# Jest
grep -E '\.test\.(ts|tsx|js)$' | awk -F/ '{print $1}' | sort | uniq -c | sort -rn
grep -E '\.serial\.test\.ts$' | wc -l
# Playwright
grep -E '(^|/)playwright\.config\.[^/]*$'
grep -E '\.spec\.ts$' | awk -F/ '{print $1}' | sort | uniq -c
# Rust
git grep -l -E '#\[(tokio::)?test\]' -- 'rust/*' | wc -l
find rust -mindepth 2 -maxdepth 2 -type d -name tests -not -path '*/target/*' | wc -l
# Go
grep -E '_test\.go$' | awk -F/ '{print $1}' | sort | uniq -c
# conftest, tach 모듈
grep -cE '(^|/)conftest\.py$'
grep -c '^\[\[modules\]\]' tach.toml
```

Decided in: buzzhog-whpf
