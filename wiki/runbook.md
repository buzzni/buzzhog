# 빌드·배포 런북

확인 기준 커밋: 8390c1ea200

이미지를 직접 빌드하고, 셀프호스트(hobby) 스택에 배포하고, 마이그레이션을 돌리고, 업그레이드·롤백하는 절차를 적는다.
환경변수 전체 표는 [설정 레퍼런스](configuration.md)를 본다.
시스템 구성은 [시스템 구성도](architecture.md), 외부로 나가는 호출은 [외부 호출](external-calls.md)을 본다.

코드에서 확인한 사실만 적고, 근거를 `파일:심볼` 또는 파일 경로로 단다.
실행해 보지 않은 절차는 "미확인"으로 표시한다. 이 문서를 쓰는 동안 Docker 빌드와 compose 기동은 실행하지 않았다.

## 먼저 알아둘 것: 이 포크에서 기본값은 업스트림을 가리킨다

배포 스크립트와 compose 파일은 PostHog 업스트림의 저장소와 이미지를 기본값으로 쓴다.
그대로 실행하면 이 포크의 코드가 아니라 업스트림 이미지가 뜬다.

| 위치 | 기본값 | 근거 |
| --- | --- | --- |
| 설치 스크립트가 clone하는 저장소 | `https://github.com/PostHog/posthog.git` | `bin/deploy-hobby`, `bin/hobby-installer/core/git.go:posthogRepoURL` |
| Django·worker 이미지 | `$REGISTRY_URL:$POSTHOG_APP_TAG`. `REGISTRY_URL` 기본값은 `posthog/posthog` | `docker-compose.hobby.yml`, `bin/deploy-hobby` |
| Node 서비스 이미지 | `${REGISTRY_URL}-node:${POSTHOG_NODE_TAG:-latest}` | `docker-compose.hobby.yml` (`plugins`, `ingestion-*`, `recording-api`) |
| Rust·Go 서비스 이미지 | `ghcr.io/posthog/posthog/<서비스>:master`. 변수로 바꿀 수 없다 | `docker-compose.base.yml` (`capture`, `feature-flags`, `personhog-*`, `livestream` 등), `docker-compose.hobby.yml` (`cymbal`) |
| 업그레이드 스크립트 받는 곳 | `raw.githubusercontent.com/posthog/posthog/HEAD/bin/upgrade-hobby` | `bin/deploy-hobby` 마지막 안내 문구 |
| 이 포크의 원격 | `https://github.com/buzzni/buzzhog.git` | `git remote -v` |

이 포크의 코드를 배포하려면 아래를 모두 직접 해야 한다.

1. 모든 이미지를 빌드해 자기 레지스트리에 올린다. ([이미지 직접 빌드](#이미지-직접-빌드))
2. `REGISTRY_URL`을 자기 레지스트리로 바꾼다. 이것은 Django와 Node 이미지에만 적용된다.
3. Rust·Go 서비스는 compose 파일의 `image:` 값을 직접 고친다.
4. 설치 스크립트가 clone하는 저장소를 이 포크로 바꾼다. 스크립트를 쓰지 않고 [수동 배포](#수동-배포-순서)를 따라도 된다.

이 포크에는 CI 워크플로가 없다. `.github/workflows`가 존재하지 않는다.
`Dockerfile` 주석이 가리키는 `container-images-cd.yml`도 없으므로, 이미지 빌드와 푸시는 사람이 한다.

## 이미지 구성

| Dockerfile | 이미지 | 내용 | 비고 |
| --- | --- | --- | --- |
| `Dockerfile` | Django 앱(web, worker, temporal-django-worker 등이 공유) | 프런트엔드 빌드, Python 의존성, `collectstatic`, GeoIP 파일, 플러그인 트랜스파일러, 비루트 사용자 `posthog`(uid 10001) | 마지막 단계에서 `USER root`로 끝난다. `bin/docker-server`가 `setpriv`로 `nobody`로 낮춘다 |
| `Dockerfile.node` | `${REGISTRY_URL}-node` | `nodejs/`의 인제스천, CDP, 세션 리플레이 서비스 | 빌드에 `ghcr.io/posthog/rust-node-container` 베이스 이미지를 쓴다 |
| `rust/Dockerfile` | 서비스별 Rust 이미지 | `--build-arg BIN=<바이너리>`로 하나씩 빌드한다 | `capture`, `feature-flags`, `personhog-*`, `hypercache-server`, `cymbal` 등 |
| `livestream/Dockerfile` | `livestream` | Go 서비스 | |
| `Dockerfile.recording-rasterizer` | 리플레이 영상 렌더러 | Chromium·ffmpeg 포함 Temporal 워커 | hobby compose에는 없다 |
| `Dockerfile.llm-analytics` | LLM 분석 Temporal 워커 | ML 의존성 포함 | hobby compose에는 없다 |
| `Dockerfile.dagster-ml` | Dagster ML | 기본 이미지 위에 `inbox-ranking` 의존성 그룹을 더한다 | `BASE_IMAGE` 빌드 인자가 필수다 |
| `Dockerfile.ml-mirror-image-scrub` | 이미지 스크럽 사이드카 | ONNX 모델 포함 | hobby compose에는 없다 |
| `Dockerfile.playwright`, `Dockerfile.sandbox`, `rust/Dockerfile.sqlx-migrate` | 개발·테스트용 | | 배포 대상이 아니다 |

hobby 스택이 실제로 쓰는 것은 앞의 네 가지(Django, Node, Rust, livestream)다. 근거: `docker-compose.hobby.yml`, `docker-compose.base.yml`.

### Django 이미지의 빌드 단계

`Dockerfile`은 다단계 빌드다.

1. `frontend-build`: pnpm으로 프런트엔드를 빌드한다.
2. `sourcemap-upload`: 비밀값 `posthog_upload_sourcemaps_cli_api_key`가 있을 때만 소스맵을 올린다. 비밀값이 없으면 업로드 없이 넘어가고 `.map` 파일이 이미지에 남는다.
3. `node-scripts-build`: 플러그인 트랜스파일러와 canvas 빌더를 만든다.
4. `posthog-build`: `uv sync --locked --no-dev`로 Python 의존성을 깔고 `collectstatic`과 `render_wizard_tool_catalog`를 실행한다.
5. `fetch-geoip-db`: `https://mmdbcdn.posthog.net/`에서 GeoLite2 파일을 받는다. 빌드 시점에 외부 호출이 생긴다.
6. 최종 단계: 위 산출물을 합치고 `compileall`로 바이트코드를 미리 만든다. 기본 `CMD`는 `./bin/docker`다.

## 이미지 직접 빌드

BuildKit이 필요하다. `Dockerfile`이 `RUN --mount=type=cache`와 `--mount=type=secret`을 쓴다.
저장소 루트에서 실행한다.

```bash
# Django 앱 이미지
docker build \
  --build-arg COMMIT_HASH="$(git rev-parse HEAD)" \
  -t <레지스트리>/<이름>:<태그> .

# Node 서비스 이미지. 이름 규칙은 compose의 ${REGISTRY_URL}-node 이다
docker build -f Dockerfile.node -t <레지스트리>/<이름>-node:<태그> .

# Rust 서비스 이미지 (바이너리마다 한 번씩, 빌드 컨텍스트는 rust/)
docker build --build-arg BIN=capture -t <레지스트리>/capture:<태그> rust/

# livestream (컨텍스트는 livestream/ 로 가정. 미확인)
docker build -t <레지스트리>/livestream:<태그> livestream/
```

근거: `Dockerfile` 머리 주석과 `ARG COMMIT_HASH`, `Dockerfile.node` 머리 주석, `rust/Dockerfile` (`ARG BIN`), `docker-compose.base.yml`의 `build.context: rust/`와 `args.BIN`.

Rust 서비스의 `BIN` 값은 `docker-compose.base.yml`과 `docker-compose.hobby.yml`의 `build.args.BIN`에서 확인한다.
hobby compose에 나오는 것은 `capture`, `capture-logs`, `property-defs-rs`, `personhog-replica`, `personhog-router`, `feature-flags`, `hypercache-server`, `cymbal`이다. 같은 바이너리를 여러 서비스가 `CAPTURE_MODE` 등 환경변수로 달리 쓴다.

### 알려진 빌드 문제: `ee/` 디렉터리가 없다

이 포크는 비 FOSS 코드를 제거했고 `ee/` 디렉터리가 없다. 근거: [결정 기록](adr/0001-remove-non-foss.md), 작업 트리에서 `ee` 경로 부재 확인.
그런데 `Dockerfile`이 `ee`를 복사한다.

- `Dockerfile:244`: `COPY ee ee/` (posthog-build 단계)
- `Dockerfile:400`: `COPY --chown=posthog:posthog ee ee/` (최종 단계)
- `Dockerfile:423`: `compileall` 대상 목록에 `ee`

Docker는 존재하지 않는 `COPY` 원본에서 빌드를 멈추므로, 위 줄을 고치기 전에는 Django 이미지 빌드가 실패할 것으로 보인다.
실제 빌드는 실행하지 않아 **미확인**이다. 이 문서가 코드를 바꾸지는 않는다.
Python 쪽은 `ee`가 없어도 동작하게 되어 있다. `posthog/settings/web.py`와 `posthog/settings/ee.py`가 `ee.apps` import 실패를 무시한다.

### 빌드 인자와 비밀값

| 이름 | 종류 | 의미 | 근거 |
| --- | --- | --- | --- |
| `COMMIT_HASH` | 빌드 인자 | `/code/commit.txt`에 기록된다. 소스맵 릴리스 이름에도 쓴다 | `Dockerfile` |
| `POSTHOG_RELEASE_ID` | 빌드 인자 → 환경변수 | 오류 추적 릴리스 ID. 비워 두면 SDK가 무시한다 | `Dockerfile` |
| `POSTHOG_CLI_VERSION`, `POSTHOG_CLI_INSTALLER_SHA256` | 빌드 인자 | 소스맵 업로드 CLI 버전과 체크섬 | `Dockerfile` (sourcemap-upload) |
| `GITHUB_ACTIONS`, `GITHUB_SHA`, `GITHUB_REF_NAME`, `GITHUB_REPOSITORY`, `GITHUB_SERVER_URL` | 빌드 인자 | 소스맵 릴리스 메타데이터. 로컬 빌드에서는 비워도 된다 | `Dockerfile` |
| `posthog_upload_sourcemaps_cli_api_key` | BuildKit 비밀값 | 있어야 소스맵을 올린다. 없으면 건너뛴다 | `Dockerfile` |

소스맵을 올리면 PostHog 업스트림의 오류 추적으로 나간다. 이 포크에서 끄려면 비밀값을 주지 않는다.

## 셀프호스트 배포 (hobby)

`docker-compose.hobby.yml`은 단일 서버에 전체 스택을 올리는 구성이다.
`bin/deploy-hobby`는 첫 설치용 스크립트다.

### 요구 사항

- Ubuntu만 지원한다. 스크립트가 `/etc/os-release`를 확인하고 아니면 종료한다. 근거: `bin/deploy-hobby`
- 메모리 8GB 이상을 권장한다고 스크립트가 경고한다. 근거: `bin/deploy-hobby` 머리 출력
- 도메인에 A 레코드가 걸려 있어야 한다. IP 주소는 안 된다. TLS 인증서를 Caddy가 이 도메인으로 받는다. 근거: `bin/deploy-hobby`
- 80, 443 포트가 열려 있어야 한다. 근거: `docker-compose.hobby.yml` (`proxy.ports`)
- Docker와 docker-compose v2.33.1을 스크립트가 설치한다. 이미 Docker가 있으면 Docker 설치는 건너뛴다. 근거: `bin/deploy-hobby`

### 설치 스크립트가 하는 일

`bin/deploy-hobby <태그> <도메인> [스테이징TLS]` 순서다. 인자를 안 주면 대화형으로 묻는다.

1. 이전 스택이 있으면 멈춘다.
2. 설치 시작 이벤트를 `https://us.i.posthog.com/batch/`로 보낸다. 끄는 옵션은 없다. ([외부 호출](external-calls.md))
3. `apt`로 `git`을 깔고 `PostHog/posthog`를 `posthog/` 디렉터리로 clone한다. 이미 있으면 `fetch` 후 태그에 따라 체크아웃한다.
   - `latest`: 현재 브랜치를 `origin`에 맞춰 `reset --hard`
   - 40자리 해시: 그 커밋
   - `latest-release`: 가장 최근 태그. 스크립트가 "더 이상 태그 릴리스를 만들지 않는다"고 경고한다
   - 그 외: `release-` 접두사를 뗀 태그
4. `.env`가 없을 때만 새로 만든다. 있으면 그대로 둔다. ([`.env`에 들어가는 값](#env에-들어가는-값))
5. GeoLite2 파일을 `./share/`에 받는다.
6. `compose/start`, `compose/temporal-django-worker`, `compose/wait`를 쓴다.
7. `posthog/docker-compose.base.yml`, `posthog/docker-compose.hobby.yml`, `posthog/.env.services`를 작업 디렉터리로 복사한다. hobby 파일은 `docker-compose.yml`이 된다.
8. `docker-compose -f docker-compose.yml up -d --no-build --pull always`를 최대 3번 시도한다. 실패 사이에 30초 쉰다.
9. `SKIP_HEALTH_CHECK`가 없으면 `localhost/_health`가 200을 줄 때까지 최대 10분 기다린다. 성공하면 완료 이벤트를 다시 `us.i.posthog.com`으로 보낸다.

Go로 쓴 설치기 `bin/hobby-installer`도 있다. TUI와 `--ci` 모드를 지원하고 같은 순서를 따른다. 근거: `bin/hobby-installer/README.md`, `bin/hobby-installer/core/`.
Go 설치기도 `us.i.posthog.com`으로 텔레메트리를 보낸다. 근거: `bin/hobby-installer/core/telemetry.go`.

### `.env`에 들어가는 값

`bin/deploy-hobby`가 처음 만드는 `.env`다.

| 변수 | 생성 방식 | 바꿔도 되나 |
| --- | --- | --- |
| `POSTHOG_SECRET` | 무작위 56자 | 안 된다. Django `SECRET_KEY`가 되며 바꾸면 세션이 무효가 된다 |
| `ENCRYPTION_SALT_KEYS` | `openssl rand -hex 16` (32자) | 안 된다. 바꾸면 이미 암호화된 데이터를 못 읽는다 |
| `BROWSERLESS_SECRET` | `openssl rand -hex 32` | 되지만 브라우저 렌더링 컨테이너와 같이 재시작해야 한다 |
| `INTERNAL_REQUEST_TOKEN` | `openssl rand -hex 32` | `feature-flags`와 web·worker가 같은 값이어야 한다 |
| `DOMAIN` | 입력값 | 바꾸면 TLS 인증서와 `SITE_URL`이 바뀐다 |
| `TLS_BLOCK`, `CADDY_TLS_BLOCK` | 스테이징 인자를 줄 때 Let's Encrypt 스테이징 CA 지시문 | |
| `CADDY_HOST` | `"$DOMAIN, http://, https://"` | |
| `REGISTRY_URL` | 기본 `posthog/posthog` | 포크 이미지를 쓰려면 바꾼다 |
| `POSTHOG_APP_TAG` | 설치 때 고른 태그 | 업그레이드 때 바꾼다 |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | 입력했을 때만 추가 | 비어 있어도 된다 |

근거: `bin/deploy-hobby`, `bin/hobby-installer/core/env.go` (`dedicatedSecretKeys`).
재실행 때 `.env`를 덮어쓰지 않는 이유는 `POSTHOG_SECRET`과 `ENCRYPTION_SALT_KEYS`가 바뀌면 운영 중인 인스턴스가 깨지기 때문이다. 스크립트 주석에 같은 설명이 있다.

### 수동 배포 순서

스크립트를 쓰지 않고, 이 포크를 직접 배포할 때의 순서다.
스크립트가 만드는 파일 구조를 그대로 따르므로 아래 레이아웃을 맞춘다.

```text
<작업 디렉터리>/
  posthog/                  이 포크의 checkout (compose의 ./posthog/... 경로가 여기를 본다)
  docker-compose.yml        posthog/docker-compose.hobby.yml 복사본
  docker-compose.base.yml   posthog/docker-compose.base.yml 복사본
  .env.services             posthog/.env.services 복사본
  .env                      아래 4번
  compose/start, compose/wait, compose/temporal-django-worker
  share/GeoLite2-City.mmdb
```

1. 서버에 Docker와 docker-compose를 설치하고 이 포크를 `posthog/`에 clone한다.
2. 이미지를 빌드해 레지스트리에 올린다. Rust·Go 이미지의 `image:` 값을 바꿀 때는 복사한 `docker-compose.yml`과 `docker-compose.base.yml`을 둘 다 확인한다. hobby 파일이 `extends`로 base 파일의 서비스를 가져오기 때문이다.
3. GeoLite2 파일을 `./share/GeoLite2-City.mmdb`에 둔다. `plugins`, `cymbal`, `feature-flags`가 이 디렉터리를 마운트한다.
4. `.env`를 만든다. 위 표의 변수를 채운다. 비밀값은 직접 무작위로 만든다.
5. `compose/start`, `compose/wait`, `compose/temporal-django-worker`를 `bin/deploy-hobby`와 같은 내용으로 만든다. 실행 권한을 준다.
   - `compose/start`: `./compose/wait` → `./bin/migrate` → `./bin/docker-server`
   - `compose/wait`: `clickhouse:9000`과 `db:5432`가 열릴 때까지 5초 간격으로 확인하는 Python 스크립트
   - `compose/temporal-django-worker`: `./bin/temporal-django-worker`
6. `docker-compose -f docker-compose.yml up -d --no-build --pull always`를 실행한다. `--no-build`는 compose의 `build:` 항목을 무시하게 한다. 레지스트리에서 받을 수 없는 이미지가 있으면 여기서 실패한다.
7. `curl -s -o /dev/null -w '%{http_code}' localhost/_health`가 200을 줄 때까지 기다린다. 첫 기동은 마이그레이션 때문에 5~10분 걸린다고 스크립트가 안내한다.
8. 브라우저에서 `https://<도메인>`을 열어 관리자 계정을 만든다. (화면 동작은 미확인)

`web` 서비스의 기동 명령은 `/compose/start`다. 그래서 `web` 컨테이너가 시작할 때마다 마이그레이션이 먼저 돈다.
`worker`는 `./bin/docker-worker-celery --with-scheduler`를 실행한다. 근거: `docker-compose.base.yml` (`worker`), `docker-compose.hobby.yml` (`web.command`).

### 서비스 기동 순서와 의존성

compose의 `depends_on`이 정하는 큰 흐름이다. 근거: `docker-compose.hobby.yml`.

1. 저장소: `db`(Postgres 15.12), `redis7`, `valkey`, `clickhouse`, `zookeeper`, `kafka`(Redpanda), `objectstorage`, `seaweedfs`
2. `kafka-init`: `docker/kafka/topics.txt`의 토픽을 만든다. 파티션 1개, 복제 1로 만든다
3. Rust·Node 서비스: `capture`, `feature-flags`, `personhog-*`, `plugins`, `ingestion-*`, `recording-api`
4. `web`, `worker`, `temporal-django-worker`
5. `proxy`(Caddy): `web`, `livestream`에 의존한다

`web`이 `bin/migrate`를 돌리는 동안 `/_health`는 응답하지 않는다.

## 마이그레이션 실행

`bin/migrate`가 한 번에 모두 처리한다. `web` 컨테이너가 기동할 때마다 실행한다.
사람이 수동으로 돌릴 때도 같은 스크립트를 쓴다. 근거: `bin/migrate`.

```bash
# 전부 실행 (hobby 컨테이너 안에서)
docker-compose exec web ./bin/migrate

# 일부만 실행
docker-compose exec web ./bin/migrate --scope=postgres
docker-compose exec web ./bin/migrate --scope=clickhouse
```

`--scope`는 여러 번 줄 수 있다. 유효한 값은 `cyclotron`, `behavioral-cohorts`, `flags-read-store`, `clickhouse`, `postgres`, `persons`, `async`, `tasks-oauth`, `temporal-schedules`다.
`docker-compose exec web`은 compose 서비스 이름에서 유추한 명령이며 실행해 보지 않았다(미확인).

### 실행 순서

| 순서 | 내용 | hobby에서 | 근거 |
| --- | --- | --- | --- |
| 1 | `rust/bin/migrate-cyclotron-node`, `migrate-behavioral-cohorts`, `migrate-flags-read-store` | 건너뜀. `DEPLOYMENT=hobby`면 실행하지 않는다 | `bin/migrate` |
| 2 | ClickHouse: `manage.py migrate_clickhouse` 후 `manage.py sync_replicated_schema` | 실행 | `bin/migrate` |
| 3 | Postgres: `manage.py migrate --noinput`, 이어서 `manage.py migrate_product_databases` | 실행 | `bin/migrate` |
| 4 | 인물 DB: `manage.py apply_persons_migrations --hobby` | 실행. hobby는 인물 테이블이 메인 DB에 있다 | `bin/migrate` |
| 5 | 비동기 마이그레이션: `run_async_migrations --complete-noop-migrations`, `--check` | 실행 | `bin/migrate` |
| 6 | `setup_tasks_oauth` | 건너뜀 | `bin/migrate` |
| 7 | `schedule_temporal_workflows` (90초 제한, 실패해도 계속) | 건너뜀 | `bin/migrate` |

2번과 3번은 둘 다 선택됐을 때 병렬로 돈다. ClickHouse가 백그라운드에서 돌고 Postgres가 앞에서 돈다.
기본 `scope`를 주지 않으면 모든 단계가 선택된다.

### Postgres 재시도와 환경변수

잠금 경쟁으로 실패하면 지수 백오프로 다시 시도한다.

| 변수 | 기본값 | 의미 |
| --- | --- | --- |
| `MIGRATE_MAX_RETRIES` | `10` | 최대 시도 횟수 |
| `MIGRATE_RETRY_DELAY` | `3` | 첫 대기 시간(초) |
| `MIGRATE_BACKOFF` | `2` | 대기 시간에 곱하는 배수 |
| `MIGRATE_LOCK_TIMEOUT` | `20000` | 마이그레이션 연결의 `lock_timeout`(밀리초). `posthog/settings/data_stores.py`에서 읽는다 |
| `POSTHOG_POSTGRES_DIRECT_HOST` | 없음 | 있으면 `default_direct` DB로 직접 연결한다 (PgBouncer 우회) |

종료 코드 78은 "지원하지 않는 DB 버전"이며 재시도하지 않는다.
`DEPLOYMENT`가 비어 있지 않으면 `--production` 플래그가 붙는다.

### 시작 시 마이그레이션 확인

`bin/docker-server`와 `bin/docker-worker`는 먼저 `bin/migrate-check`를 실행한다.
`manage.py migrate --check`, `migrate_clickhouse --check`, `run_async_migrations --check`를 차례로 돌린다.
`POSTHOG_SKIP_MIGRATION_CHECKS`가 비어 있지 않으면 건너뛴다. hobby compose는 `worker`에 `POSTHOG_SKIP_MIGRATION_CHECKS: '1'`을 준다. 근거: `bin/migrate-check`, `docker-compose.hobby.yml`.

### 서비스 버전 범위

`posthog/settings/service_requirements.py`에 Postgres `>=14.0.0`, Redis `>=7.0.0,<8.0.0`, ClickHouse `>=24.8,<=25.12`가 적혀 있다.
compose의 ClickHouse 기본 이미지는 `clickhouse/clickhouse-server:26.9.13.15`이다. 근거: `docker-compose.base.yml`.
두 값이 어긋나 보인다. 이 범위를 실제로 검사하는 곳은 비동기 마이그레이션 실행기(`posthog/async_migrations/runner.py:check_service_version_requirements`)다.
어긋남이 실제로 문제를 일으키는지는 **미확인**이다. `SKIP_SERVICE_VERSION_REQUIREMENTS`로 검사를 끌 수 있으나, 코드가 "위험하다"고 경고한다.

## 업그레이드

### 스크립트로

`bin/upgrade-hobby`를 설치 디렉터리(`posthog/` 폴더와 `.env`가 있는 곳)에서 실행한다.
다운타임이 몇 분 생긴다고 스크립트가 알린다. 사용자가 `y`로 확인하면 진행한다.

1. 이름 붙은 `clickhouse-data`, `postgres-data` 볼륨이 있는지 확인한다. 없으면 데이터 유실 경고를 보이고 다시 묻는다.
2. Docker 데이터 디렉터리가 80% 넘게 찼으면 `docker system prune -a --force`를 권한다. 90%를 넘으면 계속할지 다시 묻는다.
3. `.env`의 값을 따옴표 규칙에 맞게 고치고, 없는 `CADDY_HOST`, `CADDY_TLS_BLOCK`, `INTERNAL_REQUEST_TOKEN`, `BROWSERLESS_SECRET`, `ENCRYPTION_SALT_KEYS`를 채운다.
4. `ENCRYPTION_SALT_KEYS`가 `^[A-Za-z0-9_-]{32}$` 형식이 아니면 중단한다.
5. MinIO 제거 안내를 한 번 보이고 확인을 받는다. 확인하면 `.env`에 `OBJECT_STORAGE_MINIO_REMOVED=acknowledged`를 기록한다. 자세한 내용은 `docs/internal/hobby-minio-removal.md`와 `bin/migrate-storage-hobby`를 본다.
6. 기존 compose 파일이 `postgres:12`면 Postgres 12→15 이전을 제안한다. 백업을 `backup_pg12_<시각>.sql.gz`로 만들고 검증한 뒤, `postgres-data` 볼륨을 지우고, 새 스택에서 복원한다.
7. `posthog/`에서 `git pull --prune`을 실행한다.
8. compose 파일을 새로 복사한다. `bin/helpers/render-hobby-compose.sh`가 `envsubst`로 `$DOMAIN`, `$POSTHOG_SECRET`, `$ENCRYPTION_SALT_KEYS`, `$REGISTRY_URL`, `$POSTHOG_APP_TAG`, `$TLS_BLOCK`만 치환한다.
9. `docker-compose pull` 후 `docker-compose stop`.
10. `compose/start`를 다시 쓴다.
11. 재시작 여부를 묻고, `y`면 `docker-compose up -d`로 올린다. 새 컨테이너가 `bin/migrate`를 돌린다.

근거: `bin/upgrade-hobby`, `bin/helpers/render-hobby-compose.sh`.
이 포크에서는 `git pull`이 clone한 저장소의 `origin`을 따른다. `posthog/`를 이 포크로 clone했다면 이 포크에서 가져온다.

### 이미지만 바꿔서 (수동)

1. 새 이미지를 빌드해 올린다.
2. `.env`의 `POSTHOG_APP_TAG`(와 필요하면 `POSTHOG_NODE_TAG`)를 새 태그로 바꾼다.
3. `docker-compose pull`
4. `docker-compose up -d`
5. `docker-compose logs -f web`에서 `All migrations completed successfully.`가 나오는지 확인한다. 이 문구는 `bin/migrate` 마지막 줄이다.
6. `curl -s -o /dev/null -w '%{http_code}' localhost/_health`가 200인지 확인한다.

### 올리기 전에 할 일

- Postgres는 `pg_dumpall`로 백업한다. 업그레이드 스크립트가 쓰는 명령은 `docker-compose exec -T db pg_dumpall --clean -U posthog | gzip > backup.sql.gz`이다. 근거: `bin/upgrade-hobby`
- ClickHouse와 객체 스토리지(`objectstorage-data`, `seaweedfs` 볼륨)를 백업하는 스크립트는 코드에서 찾지 못했다. **미확인**. 볼륨 단위로 복사하는 방법이 있으나 이 문서는 검증하지 못했다.
- `.env`를 복사해 둔다. `POSTHOG_SECRET`과 `ENCRYPTION_SALT_KEYS`를 잃으면 복구할 수 없다.

## 롤백

전용 롤백 스크립트는 없다. `bin/` 아래에서 찾지 못했다.
Django 마이그레이션은 앞으로만 간다고 가정하고 움직이는 것이 안전하다. 새 버전이 스키마를 바꿨다면 이미지만 되돌려서는 이전 코드와 스키마가 맞지 않을 수 있다.
다음은 위 사실에서 끌어낸 권고이며, 직접 실행해 확인하지 않았다.

1. 업그레이드 전에 만든 Postgres 백업(`pg_dumpall` 결과)을 준비한다.
2. `docker-compose down`으로 스택을 내린다. `-v`는 쓰지 않는다. 볼륨이 지워진다.
3. 문제가 DB 스키마와 무관하면 `.env`의 `POSTHOG_APP_TAG`를 이전 값으로 되돌리고 `docker-compose up -d`를 실행한다.
4. 스키마가 바뀌었다면 `postgres-data` 볼륨을 지우고 백업을 복원한다. 명령은 `bin/upgrade-hobby`의 수동 안내와 같다: `docker volume rm postgres-data`, `docker-compose up -d db`, `gunzip -c backup.sql.gz | docker-compose exec -T db psql -U posthog`
5. ClickHouse 스키마는 `migrate_clickhouse`가 앞으로만 적용한다. 되돌리는 절차는 코드에서 찾지 못했다. **미확인**

버전을 고정하려면 `POSTHOG_APP_TAG`에 태그 대신 40자리 커밋 해시를 쓸 수 있다. 설치 스크립트가 이 형식을 따로 처리한다. 근거: `bin/deploy-hobby`.
이 포크가 만든 이미지에 이 규칙이 그대로 통하는지는 레지스트리 운영 방식에 달려 있다(미확인).

## 상태 확인과 문제 해결

| 확인 | 명령 | 근거 |
| --- | --- | --- |
| 웹 헬스 | `curl -s -o /dev/null -w '%{http_code}' localhost/_health` | `bin/deploy-hobby`, `posthog/settings/access.py:SECURE_REDIRECT_EXEMPT` |
| 컨테이너 상태 | `docker-compose ps` | |
| 로그 | `docker-compose logs -f web`, `... worker`, `... db clickhouse` | `bin/deploy-hobby` 실패 안내 |
| feature-flags 준비 | 컨테이너 안에서 `curl -f http://localhost:3001/_readiness` | `docker-compose.base.yml` (`feature-flags.healthcheck`) |
| 객체 스토리지 준비 | `/tmp/objectstorage-ready` 파일 존재 | `docker-compose.base.yml` (`objectstorage.healthcheck`) |
| 디스크 | `df -h`, `docker system df` | `bin/upgrade-hobby` |

헬스 체크가 10분 안에 통과하지 않으면 설치 스크립트가 실패로 끝낸다. 스크립트가 꼽는 흔한 원인은 이미지 풀 실패, DB 마이그레이션 지연, 메모리 부족이다.

자주 겪는 증상은 compose 파일 주석에 이유가 적혀 있다.

- 세션 리플레이 재생이 500이면 `recording-api`의 `SESSION_RECORDING_V2_S3_*`가 `seaweedfs`를 가리키지 않는 경우다.
- 플래그 테스트가 "Internal request token not configured"로 실패하면 `INTERNAL_REQUEST_TOKEN`이 web·worker와 `feature-flags`에서 다르거나 비어 있는 경우다.
- `cymbal`이 계속 재시작되면 `CYMBAL_REMOTE_RESOLUTION_HOST`가 비어 있는 경우다.

위 세 항목은 `docker-compose.hobby.yml`의 주석을 옮긴 것이며 재현해 보지 않았다.

## 로컬 개발 기동 (요약)

개발용 스택은 hobby와 다르다. 자세한 안내는 `CLAUDE.md`의 Commands 절과 `docs/internal/dev-env-vars.md`를 본다.

- `hogli start` 또는 `./bin/start`: 대화형 TUI로 전체 개발 스택을 올린다.
- `hogli up -d`: 분리 모드로 올린다. `hogli wait`로 준비를 기다리고 `hogli down`으로 내린다.
- 개발용 compose는 `docker-compose.dev.yml`(와 `docker-compose.dev-full.yml`)이다. 인프라 컨테이너는 `docker-compose.base.yml`을 공유한다.
- 환경변수는 셸, flox `[vars]`, `.env.local`, `.env.development`, `.env.services` 순으로 우선한다. 근거: `docs/internal/dev-env-vars.md`
- 테스트는 `hogli test <경로>`로 돌린다.

개발 모드(`DEBUG`)는 인증을 느슨하게 한다. 운영 인스턴스에 `DEBUG`를 켜지 않는다. 근거: `posthog/settings/base_variables.py`, `posthog/settings/utils.py:assert_debug_not_in_production`.

## 미확인 항목

- 이 포크 코드로 만든 Django 이미지가 `ee/` 부재 상태에서 빌드되는지 (`Dockerfile:244`, `Dockerfile:400`)
- `livestream/Dockerfile`의 빌드 컨텍스트와 인자
- ClickHouse·객체 스토리지 백업·복원 절차와 ClickHouse 스키마 롤백
- `docker-compose exec web ./bin/migrate`를 비롯해 이 문서의 `docker-compose` 명령 실행 결과
- ClickHouse 서비스 버전 범위와 compose 기본 이미지의 어긋남이 일으키는 실제 문제
- 설치 스크립트의 텔레메트리를 끄는 방법. 스크립트를 고치는 방법 외에는 찾지 못했다

Decided in: buzzhog-uxbl
