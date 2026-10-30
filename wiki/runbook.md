# 빌드·배포 런북

확인 기준 커밋: 00b30b71042 (`milestone/buzzhog-tfjd`)

이미지를 직접 빌드하고, 셀프호스트(hobby) 스택에 배포하고, 마이그레이션을 돌리고, 업그레이드·롤백하는 절차를 적는다.
환경변수 전체 표는 [설정 레퍼런스](configuration.md)를 본다.
시스템 구성은 [시스템 구성도](architecture.md), 외부로 나가는 호출은 [외부 호출](external-calls.md)을 본다.

코드에서 확인한 사실만 적고, 근거를 `파일:심볼` 또는 파일 경로로 단다.
실행해 보지 않은 절차는 "미확인"으로 표시한다.
각 절은 "실행해 확인한 것"과 "코드만 읽은 것"을 나눠 적는다.
마지막 갱신(`buzzhog-ozkf`)에서 실행한 범위는 [맨 아래 표](#실행한-것과-읽기만-한-것)에 모았다.

## 먼저 알아둘 것: 이 포크에서 기본값은 업스트림을 가리킨다

배포 스크립트와 compose 파일은 PostHog 업스트림의 저장소와 이미지를 기본값으로 쓴다.
그대로 실행하면 이 포크의 코드가 아니라 업스트림 이미지가 뜬다.

| 위치                             | 기본값                                                                                                                                   | 근거                                                                                                                          |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| 설치 스크립트가 clone하는 저장소 | `https://github.com/PostHog/posthog.git`                                                                                                 | `bin/deploy-hobby`, `bin/hobby-installer/core/git.go:posthogRepoURL`                                                          |
| Django·worker 이미지             | `$REGISTRY_URL:$POSTHOG_APP_TAG`. `REGISTRY_URL` 기본값은 `posthog/posthog`                                                              | `docker-compose.hobby.yml`, `bin/deploy-hobby`                                                                                |
| Node 서비스 이미지               | `${REGISTRY_URL}-node:${POSTHOG_NODE_TAG:-latest}`                                                                                       | `docker-compose.hobby.yml` (`plugins`, `ingestion-*`, `recording-api`)                                                        |
| Rust·Go 서비스 이미지            | `ghcr.io/posthog/posthog/<이미지>:master`. 이미지 이름은 바이너리 기준이다(예: `replay-capture`도 `capture:master`). 변수로 바꿀 수 없다 | `docker-compose.base.yml` (`capture`, `feature-flags`, `personhog-*`, `livestream` 등), `docker-compose.hobby.yml` (`cymbal`) |
| 업그레이드 스크립트 받는 곳      | `raw.githubusercontent.com/posthog/posthog/HEAD/bin/upgrade-hobby`                                                                       | `bin/deploy-hobby` 마지막 안내 문구                                                                                           |
| 이 포크의 원격                   | `https://github.com/buzzni/buzzhog.git`                                                                                                  | `git remote -v`                                                                                                               |

이 포크의 코드를 배포하려면 아래를 모두 직접 해야 한다.

1. 모든 이미지를 빌드해 레지스트리에 올린다. `develop`에 들어간 코드는 [포크 이미지 CI](#포크-이미지-ci-ghcr)가 GHCR에 올린다. 그 밖에는 [이미지 직접 빌드](#이미지-직접-빌드)를 따른다.
2. `REGISTRY_URL`을 자기 레지스트리로 바꾼다. 이것은 Django와 Node 이미지에만 적용된다.
3. Rust·Go 서비스는 compose 파일의 `image:` 값을 직접 고친다.
4. 설치 스크립트가 clone하는 저장소를 이 포크로 바꾼다. 스크립트를 쓰지 않고 [수동 배포](#수동-배포-순서)를 따라도 된다.

3번의 수정은 작업 디렉터리의 복사본이 아니라 `posthog/` checkout의 compose 파일에 둔다.
`bin/upgrade-hobby`가 업그레이드 때마다 `posthog/docker-compose.base.yml`과 `posthog/docker-compose.hobby.yml`을 작업 디렉터리로 다시 복사해 복사본의 수정을 덮어쓰기 때문이다. 근거: `bin/upgrade-hobby`.

### 포크 이미지 CI (GHCR)

`.github/workflows/fork-images.yml`이 `develop` push와 수동 실행(`workflow_dispatch`)에서 hobby 스택의 이미지를 모두 빌드해 GHCR에 올린다.
`Dockerfile` 주석이 가리키는 업스트림의 `container-images-cd.yml`은 이 포크에 없고, 이 워크플로가 그 자리를 맡는다.

| 이미지                                                          | Dockerfile                                     | GHCR 경로                                       |
| --------------------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------- |
| Django(web, worker, temporal-django-worker, migrate)           | `Dockerfile`                                   | `ghcr.io/buzzni/buzzhog/posthog`                |
| Node(plugins, ingestion-\*)                                     | `Dockerfile.node`                              | `ghcr.io/buzzni/buzzhog/posthog-node`           |
| Rust(바이너리마다 하나)                                         | `rust/Dockerfile --build-arg BIN=<바이너리>`   | `ghcr.io/buzzni/buzzhog/<바이너리>`             |
| livestream                                                      | `livestream/Dockerfile`                        | `ghcr.io/buzzni/buzzhog/livestream`             |
| ClickHouse 26.9.13.15 + 설정·UDF(`aggregate_funnel`은 소스 빌드) | `docker/clickhouse/Dockerfile`                 | `ghcr.io/buzzni/buzzhog/clickhouse`             |

Rust 바이너리는 `capture`, `capture-logs`, `property-defs-rs`, `feature-flags`, `personhog-replica`, `personhog-router`, `hypercache-server`, `cymbal`이다.
Django 경로가 `posthog`, Node 경로가 `posthog-node`라서 `REGISTRY_URL=ghcr.io/buzzni/buzzhog/posthog`로 두면 compose의 `${REGISTRY_URL}-node` 규칙과 맞는다.

- 태그는 `<브랜치>-<YYYYMMDD>-<sha7>`(예: `develop-20261027-da1bb27`)다. 날짜는 커밋 날짜(UTC)라서 같은 커밋을 다시 돌리면 같은 태그가 나온다. `latest`, `master`, `develop` 같은 움직이는 태그는 올리지 않는다.
- 인증은 `GITHUB_TOKEN`(`permissions: packages: write`)이다. 따로 넣을 비밀값은 없다.
- runner는 GitHub-hosted(`ubuntu-24.04`) 고정이다. 이 저장소는 public이라 self-hosted runner를 쓰면 포크 PR 코드가 그 runner의 네트워크 안에서 돌 수 있다.
- Harbor(`harbor.idc1.buzzni.com`)는 사설 IP라 GitHub-hosted runner가 닿지 못한다. IDC로 가져오는 일(Harbor 복제나 proxy cache)은 워크플로 밖에서 Harbor 쪽에 설정한다.
- `linux/amd64`만 빌드한다.
- 실행 결과의 job summary에 이미지 참조와 digest가 남는다.

워크플로가 처음 만든 GHCR 패키지는 private이다. 패키지마다 한 번, 패키지 설정(Package settings > Danger Zone > Change visibility)에서 public으로 바꿔야 인증 없이 pull할 수 있다. REST API에는 패키지 가시성을 바꾸는 호출이 없어 워크플로로 하지 않는다.

ClickHouse 이미지는 `docker-compose.hobby.yml`이 마운트하는 설정 파일과 `posthog/user_scripts`를 이미지 안에 넣는다.
UDF는 데이터 볼륨(`/var/lib/clickhouse`) 밖인 `/usr/local/share/clickhouse/user_scripts`에 두고, `config.d/user-scripts.xml`이 그 경로를 가리킨다.
빌드 방법은 `docker/clickhouse/Dockerfile` 머리 주석에 있다.

### dev 클러스터 자동 배포 (k8s-manifests)

같은 워크플로의 `deploy-dev` job이 빌드 뒤에 `buzzni/k8s-manifests` `main`의 `k8s-idc/buzzhog-dev/` 이미지 태그를 이번 실행의 태그로 바꾸는 커밋을 push한다.
ArgoCD Application `k8s-idc-buzzhog-dev`가 그 커밋을 클러스터에 반영한다. auto sync가 꺼져 있으면 사람이 sync해야 반영된다.
k8s-manifests의 `docs/guides/developer/cicd.md`와 `docs/examples/github-actions/build-and-update-manifest.yaml`을 따른다.

흐름:

1. `tag` job이 태그를 정하고, `build` 매트릭스가 이미지를 GHCR에 올린다. 일부 이미지가 실패해도 다른 이미지는 계속 빌드한다.
2. `deploy-dev`는 `develop` 브랜치이고 저장소가 `buzzni/buzzhog`일 때만 돈다. 빌드 일부가 실패해도 돈다(`!cancelled()`).
3. 이미지마다 GHCR에 이번 태그가 있는지 본다(`docker buildx imagetools inspect`). 없는 이미지(빌드 실패)는 지금 태그를 그대로 둔다.
4. deploy key로 k8s-manifests를 임시 디렉터리(`umask 077`, `trap`으로 삭제)에 clone한다.
5. 이미지 이름과 같은 이름의 컨테이너 중 이미지 저장소가 `ghcr.io/buzzni/buzzhog/<이미지>`인 것을 모두 같은 태그로 바꾼다(digest 고정 yq 컨테이너). 바뀌는 컨테이너 수가 `DEPLOY_IMAGES`의 기대값과 다르면 job이 실패한다.
6. staged-diff 가드: 바뀐 파일이 `DEPLOY_FILES` 안에 있고, mode·rename 변경이 없고, 바뀐 줄이 모두 `image:` 줄인지 확인한다.
7. 바뀐 것이 없으면 커밋 없이 성공한다. 있으면 `deploy: buzzhog (dev): automated image update (<sha7>)` 커밋을 push한다. push가 거절되면 최신 `main`에서 처음부터 다시 만들어 최대 4번 시도한다.
8. job summary에 이미지마다 갱신·변경 없음·건너뜀과 그 이유를 표로 남긴다.

| 이미지          | 컨테이너 수 | 매니페스트                                                      |
| --------------- | ----------- | --------------------------------------------------------------- |
| `posthog`       | 4           | `app/django.yaml`(web, worker, temporal-django-worker), `app/migrate-job.yaml`(migrate) |
| `posthog-node`  | 6           | `app/node.yaml`(plugins, ingestion-\*, recording-api)            |
| `capture`       | 2           | `app/rust.yaml`(capture, replay-capture)                         |
| 그 밖의 Rust    | 1씩         | `app/rust.yaml`(capture-logs, feature-flags, hypercache-server, personhog-replica, personhog-router, property-defs-rs) |
| `livestream`    | 1           | `app/livestream.yaml`                                            |
| `clickhouse`    | 1           | `clickhouse/clickhouse-installation.yaml`                        |

- `posthog` 컨테이너 네 개는 한 커밋에서 함께 바뀐다. migrate Job과 web·worker가 서로 다른 Django 빌드를 보지 않는다.
- 없는 `posthog` 태그로 바꾸면 migrate Sync hook이 `ImagePullBackOff`로 sync를 최대 1시간(`activeDeadlineSeconds`) 붙잡는다. 그래서 GHCR에 없는 태그로는 바꾸지 않는다.
- ClickHouse 태그가 바뀌면 CH pod가 다시 뜬다. 지금 배포된 태그의 커밋과 이번 커밋에서 빌드 입력(`docker/clickhouse`, `funnel-udf`, `posthog/user_scripts`, `posthog/idl`, 이 워크플로 파일)의 git tree가 같으면 바꾸지 않는다. 같은지 확인하지 못하면 바꾼다.
- `cymbal`, browserless(외부 이미지), alpine initContainer, prod 매니페스트는 건드리지 않는다. prod는 [prod 승격](#prod-승격-k8s-manifests)으로 올린다.
- 매니페스트에 workload를 더하거나 빼면 `DEPLOY_IMAGES`의 개수도 고쳐야 한다. 안 고치면 job이 실패하고 아무것도 바뀌지 않는다.
- 이 저장소는 public이라 deploy key는 `push: develop`과 `workflow_dispatch`에서만 쓴다. `pull_request` 트리거는 없다. runner는 GitHub-hosted다.

사람이 할 일:

- 조직 secret `K8S_MANIFESTS_DEPLOY_KEY`의 selected repositories에 `buzzni/buzzhog`를 넣는다(조직 관리자). 없으면 `deploy-dev`가 "K8S_MANIFESTS_DEPLOY_KEY is not available"로 실패한다.
- dev Application의 auto sync를 켠다. Django 이미지가 GHCR에 올라온 뒤에 켠다.

확인: 가짜 GHCR·로컬 bare 저장소로 이 step을 돌려 봤다(Django 미빌드 시 건너뜀, 재실행 no-op, image 외 줄 변경 시 실패, 개수 불일치 시 실패, ClickHouse 입력 변경 시에만 갱신). GitHub Actions에서 실제로 push해 보지는 않았다(미확인).

### prod 승격 (k8s-manifests)

prod는 다시 빌드하지 않는다. dev에 지금 배포된 이미지 태그를 그대로 prod로 올린다.
워크플로는 `.github/workflows/promote-prod.yml`(`Promote to prod`)이고, 사람이 Actions 화면에서 `Run workflow`로 시작할 때만 돈다(`workflow_dispatch`만 있다. push·tag·`pull_request` 트리거는 없다). 저장소가 `buzzni/buzzhog`가 아니면 job이 돌지 않는다.

입력 `components`는 선택이다. 비우면 모든 이미지를 올리고, `posthog posthog-node`처럼 이미지 이름을 공백이나 쉼표로 적으면 그 이미지만 올린다. dev 매니페스트에 없는 이름을 적으면 실패한다.

흐름:

1. `deploy-dev`와 같은 방식으로 k8s-manifests `main`을 clone한다(조직 secret `K8S_MANIFESTS_DEPLOY_KEY`, `umask 077` 임시 디렉터리와 `trap` 삭제, 고정 github.com ed25519 host key).
2. `k8s-idc/buzzhog-dev/` 아래에서 `ghcr.io/buzzni/buzzhog/<이미지>:<태그>` image 줄이 있는 파일을 모두 찾는다. 파일마다 image 줄을 순서대로 읽고, yq로 그 줄이 어느 컨테이너의 것인지 맞춰 본다.
3. 같은 이름의 `k8s-idc/buzzhog-prod/` 파일에서 같은 순서의 image 줄을 읽는다. 컨테이너 이름과 이미지 저장소가 위치마다 같아야 한다.
4. 태그가 다른 줄만 dev 태그로 바꾼다. 그 줄 하나만 고쳐 쓰고 파일의 나머지는 건드리지 않는다.
5. 바뀌는 태그가 GHCR에 있는지 본다(`docker buildx imagetools inspect`). 없으면 실패한다.
6. staged-diff 가드: 바뀐 파일이 위에서 읽은 prod 파일뿐이고, mode·rename 변경이 없고, 바뀐 줄이 모두 buzzhog image 줄이며 지운 줄과 더한 줄의 수가 바꾼 줄 수와 같은지 확인한다.
7. 바뀐 것이 없으면 `Nothing to promote.`를 찍고 커밋 없이 성공한다. 있으면 `[k8s-idc] buzzhog-prod: promote images from buzzhog-dev (<새 태그>)` 커밋을 `main`에 push한다. push가 거절되면 최신 `main`에서 처음부터 다시 만들어 최대 4번 시도한다.
8. job summary에 결과(push한 커밋, 바꿀 것 없음, 실패)와 바뀐 줄마다 (파일, 컨테이너, 이전 태그 → 새 태그)를 표로 남긴다. 실패한 실행의 표는 push하지 않은 준비분이다.

다음일 때 아무것도 push하지 않고 실패한다:

- dev 파일에 대응하는 prod 파일이 없다. 예: `k8s-idc/buzzhog-prod/app/`이 아직 없다. 오류에 없는 파일 목록이 나온다.
- 한 파일의 buzzhog image 줄 수가 dev와 prod에서 다르다. 또는 dev에는 없는 파일에서 prod가 buzzhog 이미지를 쓴다.
- 같은 위치의 컨테이너 이름이나 이미지 저장소가 다르다.
- image 줄과 yq가 읽은 컨테이너 목록이 맞지 않는다(한 줄에 image가 두 번, 따옴표·anchor로 쓴 image 등).

prod에 반영하는 방법:

1. dev에서 확인한 뒤 `Promote to prod`를 실행한다. 일부 이미지만 올리려면 `components`를 채운다. `posthog`는 web·worker·temporal-django-worker·migrate가 한 커밋에서 같이 바뀐다.
2. job summary에서 바뀐 태그를 확인한다.
3. ArgoCD UI에서 `k8s-idc-buzzhog-prod`를 sync한다. prod Application은 auto sync가 꺼져 있어서 push만으로는 배포되지 않는다. sync하면 migrate Sync hook이 먼저 돈다.
4. ClickHouse 태그가 바뀌었으면 sync 때 CH pod가 다시 뜬다. dev에서 ClickHouse 태그가 바뀌지 않았으면 prod도 바뀌지 않는다(`deploy-dev`가 빌드 입력이 같을 때 ClickHouse 태그를 그대로 두기 때문이다).

되돌리기: k8s-manifests에서 승격 커밋을 revert하고 다시 sync한다. 이 워크플로로는 되돌릴 수 없다. dev 태그를 prod로 복사만 한다.

확인: k8s-manifests `origin/main`을 bare 저장소로 복제해 이 step을 로컬에서 돌려 봤다(docker·GHCR 조회는 가짜). prod `app/`이 없을 때 실패, 태그가 다를 때 image 줄 20개만 바뀐 커밋 1개, 재실행 no-op, `components` 필터, 없는 component, GHCR에 없는 태그, 줄 수 불일치 실패. GitHub Actions에서 실제로 push해 보지는 않았다(미확인).

## 이미지 구성

| Dockerfile                                    | 이미지                                                   | 내용                                                                                                                   | 비고                                                                                           |
| --------------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `Dockerfile`                                  | Django 앱(web, worker, temporal-django-worker 등이 공유) | 프런트엔드 빌드, Python 의존성, `collectstatic`, GeoIP 파일, 플러그인 트랜스파일러, 비루트 사용자 `posthog`(uid 10001) | 마지막 단계에서 `USER root`로 끝난다. `bin/docker-server`가 `setpriv`로 `nobody`로 낮춘다      |
| `Dockerfile.node`                             | `${REGISTRY_URL}-node`                                   | `nodejs/`의 인제스천, CDP, 세션 리플레이 서비스                                                                        | 빌드에 `ghcr.io/posthog/rust-node-container` 베이스 이미지를 쓴다                              |
| `rust/Dockerfile`                             | 서비스별 Rust 이미지                                     | `--build-arg BIN=<바이너리>`로 하나씩 빌드한다                                                                         | `capture`, `feature-flags`, `personhog-*`, `hypercache-server`, `cymbal` 등                    |
| `livestream/Dockerfile`                       | `livestream`                                             | Go 서비스                                                                                                              |                                                                                                |
| `Dockerfile.recording-rasterizer`             | 리플레이 영상 렌더러                                     | Chromium·ffmpeg 포함 Temporal 워커                                                                                     | hobby compose에는 없다                                                                         |
| `Dockerfile.llm-analytics`                    | LLM 분석 Temporal 워커                                   | ML 의존성 포함                                                                                                         | hobby compose에는 없다                                                                         |
| `Dockerfile.dagster-ml`                       | Dagster ML                                               | 기본 이미지 위에 `inbox-ranking` 의존성 그룹을 더한다                                                                  | `BASE_IMAGE` 빌드 인자가 필수다                                                                |
| `Dockerfile.ml-mirror-image-scrub`            | 이미지 스크럽 사이드카                                   | ONNX 모델 포함                                                                                                         | hobby compose에는 없다                                                                         |
| `Dockerfile.playwright`, `Dockerfile.sandbox` | 개발·테스트용                                            | 로컬 Playwright, 개발 샌드박스                                                                                         | hobby 배포 대상이 아니다                                                                       |
| `rust/Dockerfile.sqlx-migrate`                | Rust 쪽 DB 마이그레이션 컨테이너                         | persons, behavioral cohorts, cyclotron 마이그레이션                                                                    | hobby는 쓰지 않는다. hobby에서는 `bin/migrate`가 이 단계를 건너뛰거나 Django 명령으로 대신한다 |

hobby 스택이 실제로 쓰는 것은 앞의 네 가지(Django, Node, Rust, livestream)다. 근거: `docker-compose.hobby.yml`, `docker-compose.base.yml`.

### Django 이미지의 빌드 단계

`Dockerfile`은 다단계 빌드다.

1. `frontend-build`: pnpm으로 프런트엔드를 빌드한다.
2. `sourcemap-upload`: 비밀값 `posthog_upload_sourcemaps_cli_api_key`가 있을 때만 소스맵을 올린다. 비밀값이 없으면 업로드 없이 넘어가고 `.map` 파일이 이미지에 남는다.
3. `node-scripts-build`: 플러그인 트랜스파일러를 빌드하고 canvas 빌더의 운영 의존성을 설치한다.
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

# Rust 서비스 이미지 (바이너리마다 한 번씩, compose가 쓰는 빌드 컨텍스트는 rust/. 아래 주의 참조)
docker build --build-arg BIN=capture -t <레지스트리>/capture:<태그> rust/

# livestream (컨텍스트는 livestream/. 빌드 인자 없음)
docker build -t <레지스트리>/livestream:<태그> livestream/
```

근거: `Dockerfile` 머리 주석과 `ARG COMMIT_HASH`, `Dockerfile.node`의 `COPY` 경로(저장소 루트 기준), `rust/Dockerfile` (`ARG BIN`), `docker-compose.base.yml`의 `build.context: rust/`와 `args.BIN`, `livestream/Dockerfile`(컨텍스트 루트에서 `go.mod`를 복사하고, `go.mod`는 `livestream/`에만 있다).

Rust 서비스의 `BIN` 값은 `docker-compose.base.yml`과 `docker-compose.hobby.yml`의 `build.args.BIN`에서 확인한다.
hobby compose에 나오는 것은 `capture`, `capture-logs`, `property-defs-rs`, `personhog-replica`, `personhog-router`, `feature-flags`, `hypercache-server`, `cymbal`이다. 같은 바이너리를 여러 서비스가 `CAPTURE_MODE` 등 환경변수로 달리 쓴다.

주의: `rust/Dockerfile`은 `PROTO_ROOT=../proto`를 쓴다. 크레이트 디렉터리 기준이므로 빌드 컨텍스트 루트에 `proto/`가 있어야 한다.
`.proto` 파일은 저장소 루트의 `proto/`에 있고 `rust/` 안에는 없다. 근거: `rust/personhog-proto/build.rs`, `rust/cymbal-proto/build.rs` 등.
그래서 컨텍스트를 `rust/`로 주면 proto 크레이트에 기대는 바이너리(`capture-logs`, `property-defs-rs`, `personhog-*`, `feature-flags`, `cymbal`)는 빌드가 실패할 것으로 보인다.
포크 이미지 CI는 빌드 전에 `cp -r proto rust/proto`로 `proto/`를 컨텍스트 안에 넣는다. 손으로 빌드할 때도 같이 한다.
이 방식으로 `capture`를 로컬(linux/arm64)에서 빌드해 성공했다. 나머지 바이너리는 CI 실행으로 확인한다(**미확인**).

### `ee/` 디렉터리가 없다

이 포크는 비 FOSS 코드를 제거했고 `ee/` 디렉터리가 없다. 근거: [ADR 0001](adr/0001-remove-non-foss.md).
에픽 `buzzhog-dsv8`(병합 `ca37aa9e209`)이 `Dockerfile`의 `COPY ee ee/` 두 줄과 `compileall` 대상의 `ee`를 지웠다. `Dockerfile.llm-analytics`와 `.dockerignore`도 같이 고쳤다.
근거: `git show 0ac1ea3a6a1 -- Dockerfile`.
`ee`를 무조건 import하던 코드도 걷어 냈다. 남은 `from ee` import 4개 파일은 `ImportError`를 받는 조건부 확장 지점이다([ADR 0002](adr/0002-remove-ee-residue-keep-extension-points.md)).

확인 범위는 다음과 같다.

- 이미지 안에서 가입 `201`, 핵심 API `200`을 받았다.
- 마지막 수정(설정 14개 추가)은 이미지를 다시 빌드하지 않고, 수정한 `posthog/`와 `products/`를 기존 이미지에 마운트해서 확인했다.
  그래서 지금 `Dockerfile`로 처음부터 빌드한 결과는 **미확인**이다.
- 빌드 인자 없이 새로 빌드하는 전체 과정은 이 문서를 쓰는 동안 돌리지 않았다.

### 빌드 인자와 비밀값

| 이름                                                                                        | 종류                 | 의미                                                                            | 근거                            |
| ------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------- | ------------------------------- |
| `COMMIT_HASH`                                                                               | 빌드 인자            | `/code/commit.txt`에 기록된다. 소스맵 릴리스 버전(`--release-version`)에도 쓴다 | `Dockerfile`                    |
| `POSTHOG_RELEASE_ID`                                                                        | 빌드 인자 → 환경변수 | 오류 추적 릴리스 ID. 비워 두면 SDK가 무시한다                                   | `Dockerfile`                    |
| `POSTHOG_CLI_VERSION`, `POSTHOG_CLI_INSTALLER_SHA256`                                       | 빌드 인자            | 소스맵 업로드 CLI 버전과 체크섬                                                 | `Dockerfile` (sourcemap-upload) |
| `GITHUB_ACTIONS`, `GITHUB_SHA`, `GITHUB_REF_NAME`, `GITHUB_REPOSITORY`, `GITHUB_SERVER_URL` | 빌드 인자            | 소스맵 릴리스 메타데이터. 로컬 빌드에서는 비워도 된다                           | `Dockerfile`                    |
| `posthog_upload_sourcemaps_cli_api_key`                                                     | BuildKit 비밀값      | 있어야 소스맵을 올린다. 없으면 건너뛴다                                         | `Dockerfile`                    |

소스맵을 올리면 PostHog 업스트림의 오류 추적으로 나간다(`POSTHOG_CLI_ENV_ID=2`. `rust/Dockerfile` 주석이 이 값을 업스트림 내부 프로젝트라고 적는다). 이 포크에서 끄려면 비밀값을 주지 않는다.

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
   - 40자리 해시: 그 커밋. 이 경우만 `fetch` 없이 바로 체크아웃한다
   - `latest-release`: 가장 최근 태그. 스크립트가 "더 이상 태그 릴리스를 만들지 않는다"고 경고한다
   - 그 외: `release-` 접두사를 뗀 태그
4. `.env`가 없을 때만 새로 만든다. 있으면 그대로 둔다. ([`.env`에 들어가는 값](#env에-들어가는-값))
5. GeoLite2 파일을 `./share/`에 받는다.
6. `compose/start`, `compose/temporal-django-worker`, `compose/wait`를 쓴다.
7. `posthog/docker-compose.base.yml`, `posthog/docker-compose.hobby.yml`, `posthog/.env.services`를 작업 디렉터리로 복사한다. hobby 파일은 `docker-compose.yml`이 된다.
8. `docker-compose -f docker-compose.yml up -d --no-build --pull always`를 최대 3번 시도한다. 실패 사이에 30초 쉰다.
9. `SKIP_HEALTH_CHECK`가 없으면 `localhost/_health`가 200을 줄 때까지 최대 10분 기다린다. 성공하면 완료 이벤트를 다시 `us.i.posthog.com`으로 보낸다.

Go로 쓴 설치기 `bin/hobby-installer`도 있다. TUI와 `--ci` 모드를 지원하고 대체로 같은 순서를 따른다.
다른 점도 있다. `.env`가 있으면 그대로 두지 않고 업그레이드용으로 고치고, 기존 볼륨이 있으면 비동기 마이그레이션 검사를 돌리고, 헬스 체크를 최대 45분 기다린다. 근거: `bin/hobby-installer/README.md`, `bin/hobby-installer/core/install.go:GetInstallSteps`.
Go 설치기도 `us.i.posthog.com`으로 텔레메트리를 보낸다. 근거: `bin/hobby-installer/core/telemetry.go`.

### `.env`에 들어가는 값

`bin/deploy-hobby`가 처음 만드는 `.env`다.
표의 마지막 세 줄(텔레메트리 변수 다섯 개)은 스크립트가 쓰지 않는다. 필요할 때 직접 추가하는 선택 값이다.

| 변수                                                                             | 생성 방식                                              | 바꿔도 되나                                                   |
| -------------------------------------------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------- |
| `POSTHOG_SECRET`                                                                 | 무작위 56자                                            | 안 된다. Django `SECRET_KEY`가 되며 바꾸면 세션이 무효가 된다 |
| `ENCRYPTION_SALT_KEYS`                                                           | `openssl rand -hex 16` (32자)                          | 안 된다. 바꾸면 이미 암호화된 데이터를 못 읽는다              |
| `BROWSERLESS_SECRET`                                                             | `openssl rand -hex 32`                                 | 되지만 브라우저 렌더링 컨테이너와 같이 재시작해야 한다        |
| `INTERNAL_REQUEST_TOKEN`                                                         | `openssl rand -hex 32`                                 | `feature-flags`와 web·worker가 같은 값이어야 한다             |
| `DOMAIN`                                                                         | 입력값                                                 | 바꾸면 TLS 인증서와 `SITE_URL`이 바뀐다                       |
| `TLS_BLOCK`, `CADDY_TLS_BLOCK`                                                   | 스테이징 인자를 줄 때 Let's Encrypt 스테이징 CA 지시문 |                                                               |
| `CADDY_HOST`                                                                     | `"$DOMAIN, http://, https://"`                         |                                                               |
| `REGISTRY_URL`                                                                   | 기본 `posthog/posthog`                                 | 포크 이미지를 쓰려면 바꾼다                                   |
| `POSTHOG_APP_TAG`                                                                | 설치 때 고른 태그                                      | 업그레이드 때 바꾼다                                          |
| `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`                                            | 입력했을 때만 추가                                     | 비어 있어도 된다                                              |
| `POSTHOG_TELEMETRY_HOST`, `POSTHOG_TELEMETRY_API_KEY`                            | 스크립트가 만들지 않는다. 쓰려면 직접 추가한다         | 둘 다 있어야 서버가 텔레메트리를 보낸다. 없으면 보내지 않는다 |
| `POSTHOG_TELEMETRY_USAGE_REPORTS`, `POSTHOG_TELEMETRY_USAGE_REPORTS_INCLUDE_PII` | 스크립트가 만들지 않는다. 기본 `false`                 | 사용량 보고와 사용자 이메일·이름 포함 여부                    |
| `OPT_OUT_CAPTURE`                                                                | 스크립트가 만들지 않는다. 기본 `false`                 | 참이면 위 값이 있어도 보내지 않는다                           |

근거: `bin/deploy-hobby`, `bin/hobby-installer/core/env.go` (`dedicatedSecretKeys`), `docker-compose.base.yml` (`worker_env`).
텔레메트리 변수의 뜻과 보내는 데이터는 [외부 호출](external-calls.md#텔레메트리-설정)을 본다.
`POSTHOG_TELEMETRY_HOST`는 `https://`나 `http://`로 시작해야 한다.
스킴이 없으면(`t.example.com`처럼) 키가 있어도 보내지 않는다. 근거: `posthog/telemetry.py:get_telemetry_target`
**실행해 확인함:** 값을 넣고 `docker compose -f docker-compose.hobby.yml config`로 렌더링하면 `web`, `worker`, `temporal-django-worker`, `asyncmigrationscheck`의 `environment`에 이 다섯 변수가 들어간다.
`.env`는 compose 치환에만 쓰이지만 `docker-compose.base.yml`의 `worker_env`가 `${변수:-기본값}`으로 받아 컨테이너에 넘기므로 `.env`에 적으면 충분하다.
컨테이너를 실제로 띄워 전송이 멈추는지는 확인하지 않았다(**미확인**).
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
2. 이미지를 빌드해 레지스트리에 올린다. Rust·Go 이미지의 `image:` 값을 바꿀 때는 `docker-compose.hobby.yml`과 `docker-compose.base.yml`을 둘 다 확인한다. hobby 파일이 `extends`로 base 파일의 서비스를 가져오기 때문이다. 수정은 `posthog/` checkout 쪽 파일에 하고 작업 디렉터리로 복사한다. `bin/upgrade-hobby`가 복사본을 덮어쓰기 때문이다.
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
2. `kafka-init`: `docker/kafka/topics.txt`의 토픽을 만든다. 파티션 1개, 복제 1로 만든다. `property-defs-rs`, `property-defs-ai`, `cymbal`은 이것이 끝나야 뜬다
3. `personhog-replica` → `personhog-router`
4. `web`(저장소와 `personhog-router`에 의존) → `worker`(`web`에도 의존). `temporal-django-worker`는 `temporal`, `browserless`, `personhog-router` 등에 의존한다
5. `proxy`(Caddy): `web`, `livestream`에 의존한다

`capture`, `feature-flags`, `plugins`, `ingestion-*`, `recording-api`는 `web`이 기다리지 않는다. 저장소에만 의존하거나 의존이 없어 따로 뜬다.

`web`이 `bin/migrate`를 돌리는 동안에는 웹 서버가 아직 뜨지 않았으므로 `/_health`가 200을 주지 않는다.

### 이번 마일스톤에서 배포가 달라진 점

| 이전                                                        | 지금                                                                                                                                         | 근거                                                                   |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 서버가 PostHog 사 호스트로 텔레메트리를 보낸다              | `POSTHOG_TELEMETRY_HOST`와 `POSTHOG_TELEMETRY_API_KEY`가 둘 다 있을 때만 보낸다. 사용량 보고는 `POSTHOG_TELEMETRY_USAGE_REPORTS`도 켜야 한다 | `posthog/telemetry.py`, [외부 호출](external-calls.md#텔레메트리-설정) |
| hobby compose는 `web`에만 `OPT_OUT_CAPTURE`를 준다          | `worker_env`가 `web`, `worker`, `temporal-django-worker`, `asyncmigrationscheck`에 `OPT_OUT_CAPTURE`와 텔레메트리 변수 넷을 준다             | `docker-compose.base.yml`, `docker-compose.hobby.yml`                  |
| `OPT_OUT_CAPTURE=false`라고 적어도 꺼지는 경우가 있다       | 불리언으로 읽는다. 문자열 `"false"`는 끄지 않는다                                                                                            | [외부 호출](external-calls.md#opt_out_capture의-의미)                  |
| 설치 스크립트가 `us.i.posthog.com`으로 설치 이벤트를 보낸다 | 그대로다. `OPT_OUT_CAPTURE`로 끄지 못한다                                                                                                    | `bin/deploy-hobby`, `bin/hobby-installer/core/telemetry.go`            |
| `Dockerfile`이 `ee/`를 복사한다                             | 복사하지 않는다                                                                                                                              | `Dockerfile`, [`ee/` 디렉터리가 없다](#ee-디렉터리가-없다)             |
| 설정 > 인증에서 SCIM을 켠다                                 | SCIM 프로비저닝이 없다. `scim_enabled=true`는 무시된다                                                                                       | `posthog/api/identity_provider_config.py`                              |
| 업스트림 DB를 그대로 이어 쓴다                              | 링크한 절의 조건이 맞을 때만 마이그레이션 기록 두 줄을 먼저 넣고 이어 쓴다. DB가 이 포크보다 새 업스트림으로 만든 것이면 이어 쓰지 않는다    | [ee 제거 전 DB](#ee-제거-전-db에서-생기는-문제)                        |

설치 스크립트의 텔레메트리 두 줄(시작·완료 이벤트)은 `bin/deploy-hobby`를 고쳐야 없앨 수 있다. Go 설치기는 `bin/hobby-installer/core/telemetry.go`를 고쳐야 한다.
이 일은 backlog `buzzhog-zebn`에 남아 있다. 에픽 `buzzhog-pk6n` 밖으로 넘긴 일이다.

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

| 순서 | 내용                                                                                        | hobby에서                                    | 근거          |
| ---- | ------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------- |
| 1    | `rust/bin/migrate-cyclotron-node`, `migrate-behavioral-cohorts`, `migrate-flags-read-store` | 건너뜀. `DEPLOYMENT=hobby`면 실행하지 않는다 | `bin/migrate` |
| 2    | ClickHouse: `manage.py migrate_clickhouse` 후 `manage.py sync_replicated_schema`            | 실행                                         | `bin/migrate` |
| 3    | Postgres: `manage.py migrate --noinput`, 이어서 `manage.py migrate_product_databases`       | 실행                                         | `bin/migrate` |
| 4    | 인물 DB: `manage.py apply_persons_migrations --hobby`                                       | 실행. hobby는 인물 테이블이 메인 DB에 있다   | `bin/migrate` |
| 5    | 비동기 마이그레이션: `run_async_migrations --complete-noop-migrations`, `--check`           | 실행                                         | `bin/migrate` |
| 6    | `setup_tasks_oauth`                                                                         | 건너뜀                                       | `bin/migrate` |
| 7    | `schedule_temporal_workflows` (90초 제한, 실패해도 계속)                                    | 건너뜀                                       | `bin/migrate` |

2번과 3번은 둘 다 선택됐을 때 병렬로 돈다. ClickHouse가 백그라운드에서 돌고 Postgres가 앞에서 돈다.
기본 `scope`를 주지 않으면 모든 단계가 선택된다.

### Postgres 재시도와 환경변수

실패하면 원인을 가리지 않고 지수 백오프로 다시 시도한다(종료 코드 78만 예외, 아래 참조). 코드 주석은 잠금 경쟁을 주된 이유로 든다.

| 변수                           | 기본값  | 의미                                                                                                                                                                                                            |
| ------------------------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MIGRATE_MAX_RETRIES`          | `10`    | 최대 시도 횟수                                                                                                                                                                                                  |
| `MIGRATE_RETRY_DELAY`          | `3`     | 첫 대기 시간(초)                                                                                                                                                                                                |
| `MIGRATE_BACKOFF`              | `2`     | 대기 시간에 곱하는 배수                                                                                                                                                                                         |
| `MIGRATE_LOCK_TIMEOUT`         | `20000` | 직접 연결(`default_direct`, 제품 DB의 `*_db_direct`)에만 붙는 `lock_timeout`(밀리초). `POSTHOG_POSTGRES_DIRECT_HOST`가 없는 hobby 기본 구성에서는 적용되지 않는다. `posthog/settings/data_stores.py`에서 읽는다 |
| `POSTHOG_POSTGRES_DIRECT_HOST` | 없음    | 있으면 `default_direct` DB로 직접 연결한다 (PgBouncer 우회)                                                                                                                                                     |

종료 코드 78은 "지원하지 않는 DB 버전"이며 재시도하지 않는다.
`DEPLOYMENT`가 비어 있지 않으면 `--production` 플래그가 붙는다.

### 시작 시 마이그레이션 확인

`bin/docker-server`, `bin/docker-worker`, `bin/docker-worker-celery`는 `bin/migrate-check`를 실행한다. hobby `worker`가 실행하는 것은 `bin/docker-worker-celery`다.
`manage.py migrate --check`, `migrate_clickhouse --check`, `run_async_migrations --check`를 차례로 돌린다.
`POSTHOG_SKIP_MIGRATION_CHECKS`가 비어 있지 않으면 건너뛴다. hobby compose는 `worker`에 `POSTHOG_SKIP_MIGRATION_CHECKS: '1'`을 준다. 근거: `bin/migrate-check`, `bin/docker-worker-celery`, `docker-compose.hobby.yml`.

### 빈 DB에서 처음 실행

빈 Postgres에서 `manage.py migrate --noinput`이 끝까지 돈다. 끝난 뒤 적용하지 않은 마이그레이션이 0개다.
과거에는 지운 `ee` 마이그레이션에 걸려 `NodeNotFoundError`(`posthog.1345 → ee.0061`)로 멈췄다.
RBAC 모델 다섯 개를 `access_control` 앱으로 옮기고 그 테이블을 만드는 마이그레이션을 새로 써서 풀었다([ADR 0002](adr/0002-remove-ee-residue-keep-extension-points.md)).
테이블 이름은 `ee_role`처럼 `ee_` 접두사가 그대로다.

이 포크 코드로 이미 `migrate`한 DB는 없다(사람 확인).
**업스트림 이미지로 만든 DB를 이 코드로 올리면 막힌다.** `ee` 앱 기록과 `ee_*` 테이블이 이미 있는데 `access_control.0000`이 적용되지 않은 상태이기 때문이다.
임시 DB로 흉내 내서 `InconsistentMigrationHistory`로 멈추는 것과, 두 줄을 `django_migrations`에 넣어 푸는 것을 확인했다. 절차와 한계는 [ee 제거 전 DB에서 생기는 문제](#ee-제거-전-db에서-생기는-문제)에 있다.
hobby에서는 `web`이 시작할 때마다 `bin/migrate`가 이 오류로 실패하고 재시도한다. 이미지를 올리기 전에 DB 쪽을 고친다.

### ClickHouse 없이 이미지를 띄울 때

`bin/migrate-check`가 `migrate_clickhouse --check`를 돌리므로, ClickHouse에 닿지 않는 호스트에서는 `bin/docker-server` 같은 시작 스크립트가 여기서 막힌다.
`POSTHOG_SKIP_MIGRATION_CHECKS=1`을 주면 이 확인을 건너뛴다(위 "시작 시 마이그레이션 확인").
건너뛰어도 `/_readyz`는 ClickHouse에 닿을 때까지 `503`을 준다. ClickHouse 없이 Postgres와 Redis만으로 확인한 결과다: 가입과 핵심 API는 응답했고, Postgres의 `migrate --check`는 통과했다.
이 조합은 로컬 확인용이다. 운영에서는 ClickHouse를 같이 띄운다.

### 서비스 버전 범위

`posthog/settings/service_requirements.py`에 Postgres `>=14.0.0`, Redis `>=7.0.0,<8.0.0`, ClickHouse `>=24.8,<=25.12`가 적혀 있다.
compose의 ClickHouse 기본 이미지는 `clickhouse/clickhouse-server:26.9.13.15`이다. 근거: `docker-compose.base.yml`.
두 값이 어긋나 보이지만, 이 목록(`SERVICE_VERSION_REQUIREMENTS`)을 읽는 곳은 테스트(`posthog/test/test_version_requirement.py`)뿐이다.
비동기 마이그레이션 실행기(`posthog/async_migrations/runner.py:check_service_version_requirements`)는 이 목록이 아니라 각 마이그레이션 정의의 `service_version_requirements`를 검사한다.
`SKIP_SERVICE_VERSION_REQUIREMENTS`도 켜면 "위험하다"는 경고 로그를 남길 뿐, 이 값을 읽는 다른 코드는 없다.
그래서 범위가 어긋나도 기동을 막는 검사는 코드에서 찾지 못했다. ClickHouse 26.9가 실제로 잘 동작하는지는 **미확인**이다.

## 업그레이드

### 스크립트로

`bin/upgrade-hobby`를 설치 디렉터리(`posthog/` 폴더와 `.env`가 있는 곳)에서 실행한다. 예: `bash posthog/bin/upgrade-hobby`.
스크립트가 `.env`, `posthog/`, `compose/`를 현재 디렉터리 기준 상대 경로로 다루기 때문이다.
다운타임이 몇 분 생긴다고 스크립트가 알린다. 사용자가 `y`로 확인하면 진행한다.

1. 이름 붙은 `clickhouse-data`, `postgres-data` 볼륨이 있는지 확인한다. 없으면 데이터 유실 경고를 보이고 다시 묻는다.
2. Docker 데이터 디렉터리 사용률이 80% 이상이면 `docker system prune -a --force`를 권한다. 그래도 90% 이상이면 계속할지 다시 묻는다.
3. `.env`의 값을 따옴표 규칙에 맞게 고친다. `CADDY_HOST`가 없으면 `DOMAIN`으로, `CADDY_TLS_BLOCK`이 없으면 `TLS_BLOCK`으로 채운다.
4. `ENCRYPTION_SALT_KEYS`가 없으면 새로 만든다. 있는데 `^[A-Za-z0-9_-]{32}$` 형식이 아니면 중단한다.
5. 없는 `INTERNAL_REQUEST_TOKEN`, `BROWSERLESS_SECRET`을 채운다. 대화형 터미널이면 비어 있는 `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`를 묻는다.
6. MinIO 제거 안내를 한 번 보이고 확인을 받는다. 확인하면 `.env`에 `OBJECT_STORAGE_MINIO_REMOVED=acknowledged`를 기록한다. 자세한 내용은 `docs/internal/hobby-minio-removal.md`와 `bin/migrate-storage-hobby`를 본다.
7. `posthog/docker-compose.hobby.yml`이 `postgres:12`면 Postgres 12→15 이전을 제안한다. 백업을 `backup_pg12_<시각>.sql.gz`로 만들고 검증한 뒤, `postgres-data` 볼륨을 지우고, 새 스택에서 복원한다.
8. `posthog/`에서 `git pull --prune`을 실행한다. 그 전에 `posthog/posthog/version.py`가 있으면 비동기 마이그레이션 검사가 필요하다고 표시해 둔다.
9. GeoLite2 파일이 없으면 받는다. docker-compose v2.33.1 바이너리를 다시 받는다.
10. compose 파일을 새로 복사한다. hobby 파일은 `bin/helpers/render-hobby-compose.sh`가 `envsubst`로 `$DOMAIN`, `$POSTHOG_SECRET`, `$ENCRYPTION_SALT_KEYS`, `$REGISTRY_URL`, `$POSTHOG_APP_TAG`, `$TLS_BLOCK`만 치환해 `docker-compose.yml`로 쓴다. 다른 `$` 참조는 그대로 남아 compose가 `.env`에서 채운다.
11. `docker-compose pull`. 8번에서 표시했거나 `CHECK_ASYNC_MIGRATIONS`로 강제하면 `asyncmigrationscheck`를 돌린다. 이어서 `docker-compose stop`.
12. `compose/start`를 다시 쓴다.
13. 재시작 여부를 묻고, `y`면 `docker-compose up -d`로 올린다. 새 컨테이너가 `bin/migrate`를 돌린다.

근거: `bin/upgrade-hobby`, `bin/helpers/render-hobby-compose.sh`.
이 포크에서는 `git pull`이 clone한 저장소의 `origin`을 따른다. `posthog/`를 이 포크로 clone했다면 이 포크에서 가져온다.
`posthog/`가 브랜치가 아닌 커밋이나 태그에 체크아웃돼 있으면(설치 때 40자리 해시, `latest-release`, 태그를 준 경우) `git pull`이 실패하고 `set -e` 때문에 스크립트가 멈출 것으로 보인다. 이때는 그 전 단계에서 이미 `.env`를 고친 뒤다. 실행해 보지 않았다(**미확인**).

10번 때문에 한 번 업그레이드한 뒤의 `docker-compose.yml`에는 위 여섯 값이 글자로 박힌다.
그 뒤로 `.env`에서 `REGISTRY_URL`, `POSTHOG_APP_TAG`, `DOMAIN` 등을 바꿔도 반영되지 않는다.
반영하려면 업그레이드 스크립트와 같은 방법으로 다시 렌더링하거나, `docker-compose.yml`을 직접 고친다.
`set -a; . ./.env; set +a; bash posthog/bin/helpers/render-hobby-compose.sh < posthog/docker-compose.hobby.yml > docker-compose.yml`
(`bin/upgrade-hobby`의 해당 줄을 옮긴 것이며 따로 실행해 보지 않았다.)
`POSTHOG_NODE_TAG`는 치환 목록에 없으므로 렌더링 뒤에도 `.env`에서 바꿀 수 있다.

### 이미지만 바꿔서 (수동)

1. 새 이미지를 빌드해 올린다.
2. `.env`의 `POSTHOG_APP_TAG`(와 필요하면 `POSTHOG_NODE_TAG`)를 새 태그로 바꾼다. `bin/upgrade-hobby`를 한 번이라도 돌렸다면 `POSTHOG_APP_TAG`는 `docker-compose.yml`에 박혀 있으므로 [위 방법](#스크립트로)으로 다시 렌더링하거나 `docker-compose.yml`을 직접 고친다. Rust·Go 이미지는 `:master` 고정이라 태그로 바꿀 수 없다.
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
3. 문제가 DB 스키마와 무관하면 Django 이미지 태그를 이전 값으로 되돌리고 `docker-compose up -d`를 실행한다. 업그레이드 스크립트로 올렸다면 태그는 `.env`가 아니라 `docker-compose.yml`에 박혀 있다([업그레이드](#스크립트로) 참조). Node 이미지(`POSTHOG_NODE_TAG`, 기본 `latest`)와 Rust·Go 이미지(`:master`)는 이 태그로 되돌아가지 않는다.
4. 스키마가 바뀌었다면 `postgres-data` 볼륨을 지우고 백업을 복원한다. 명령은 `bin/upgrade-hobby`의 수동 안내와 같다: `docker volume rm postgres-data`, `docker-compose up -d db`, `gunzip -c backup.sql.gz | docker-compose exec -T db psql -U posthog`. 실제 볼륨 이름은 `docker volume ls`로 먼저 확인한다. compose 파일이 볼륨에 `name:`을 주지 않으므로 compose 프로젝트 이름이 앞에 붙어 있을 수 있다(미확인).
5. ClickHouse 스키마는 `migrate_clickhouse`가 앞으로만 적용한다. 되돌리는 절차는 코드에서 찾지 못했다. **미확인**

`POSTHOG_APP_TAG`에 태그 대신 40자리 커밋 해시를 줄 수 있다. 설치 스크립트가 이 형식을 따로 처리해 그 커밋을 체크아웃하고, 같은 값을 Django 이미지 태그로 쓴다. 근거: `bin/deploy-hobby`.
고정되는 것은 `posthog/` checkout과 Django 이미지뿐이다. Node·Rust·Go 이미지는 위 3번과 같은 이유로 고정되지 않는다. 또 이렇게 설치하면 이후 `bin/upgrade-hobby`의 `git pull`이 멈출 수 있다([업그레이드](#스크립트로) 참조).
이 포크가 만든 이미지에 이 태그 규칙이 그대로 통하는지는 레지스트리 운영 방식에 달려 있다(미확인).

## 상태 확인과 문제 해결

| 확인               | 명령                                                            | 근거                                                                    |
| ------------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| 웹 헬스            | `curl -s -o /dev/null -w '%{http_code}' localhost/_health`      | `bin/deploy-hobby`, `posthog/settings/access.py:SECURE_REDIRECT_EXEMPT` |
| 컨테이너 상태      | `docker-compose ps`                                             |                                                                         |
| 로그               | `docker-compose logs -f web`, `... worker`, `... db clickhouse` | `bin/deploy-hobby` 실패 안내                                            |
| feature-flags 준비 | 컨테이너 안에서 `curl -f http://localhost:3001/_readiness`      | `docker-compose.base.yml` (`feature-flags.healthcheck`)                 |
| 객체 스토리지 준비 | `/tmp/objectstorage-ready` 파일 존재                            | `docker-compose.base.yml` (`objectstorage.healthcheck`)                 |
| 디스크             | `df -h`, `docker system df`                                     | `bin/upgrade-hobby`                                                     |

헬스 체크가 10분 안에 통과하지 않으면 설치 스크립트가 실패로 끝낸다. 스크립트가 꼽는 흔한 원인은 이미지 풀 실패, DB 마이그레이션 지연, 메모리 부족이다.

자주 겪는 증상은 compose 파일 주석에 이유가 적혀 있다.

- 세션 리플레이 재생이 500이면 `recording-api`의 `SESSION_RECORDING_V2_S3_*`가 `seaweedfs`를 가리키지 않는 경우다.
- 플래그 테스트가 "Internal request token not configured"로 실패하면 `INTERNAL_REQUEST_TOKEN`이 web·worker와 `feature-flags`에서 다르거나 비어 있는 경우다.
- `cymbal`이 계속 재시작되면 `CYMBAL_REMOTE_RESOLUTION_HOST`나 `INTERNAL_API_SECRET`이 비어 있는 경우다. hobby는 둘 다 채워 넘긴다(`INTERNAL_API_SECRET`은 `$POSTHOG_SECRET`).

위 세 항목은 `docker-compose.hobby.yml`의 주석을 옮긴 것이며 재현해 보지 않았다.

## 로컬 개발 기동

개발용 스택은 hobby와 다르다.
`hogli`가 Docker 인프라와 앱 프로세스를 한꺼번에 올린다.
영문 원문 안내는 `docs/published/handbook/engineering/developing-locally.md`다.
이 절은 그 안내를 이 포크의 현재 상태에 맞춰 줄인 것이다.

이 절의 명령은 대부분 코드와 문서에서 읽은 것이다.
전체 개발 스택(`hogli start`)은 올려 보지 않았다.
실행한 것은 빈 Postgres와 그 DB로 흉내 낸 업스트림 DB에 `manage.py migrate`를 돌린 것, hobby compose의 `docker compose config` 렌더링뿐이다. ([실행한 것과 읽기만 한 것](#실행한-것과-읽기만-한-것))

### 받아서 기동까지

1. 이 포크를 받는다. 원격은 `https://github.com/buzzni/buzzhog.git`이다.
   개발 문서의 `git clone` 줄은 `PostHog/posthog`를 가리키므로 그대로 쓰지 않는다. 근거: `docs/published/handbook/engineering/developing-locally.md` ("Cloning the repository")
2. Docker를 깐다. 메모리 4GB 이상(8GB 권장), CPU 4코어 이상을 준다. 근거: 같은 문서 ("Common gotchas")
3. `/etc/hosts`에 서비스 이름을 넣는다. 연결 오류가 날 때만 필요하다고 문서가 적는다.

   ```text
   127.0.0.1 db redis7 kafka clickhouse clickhouse-coordinator objectstorage seaweedfs temporal
   ```

4. 저장소 루트에서 `flox activate`를 한다. Python 의존성(`uv sync`)과, `node_modules/`가 없을 때 JS 의존성이 깔린다. Flox가 없을 때는 `docs/published/handbook/engineering/manual-dev-setup.md`를 본다. 근거: 같은 문서 ("Setup with Flox")
5. `hogli start`(= `./bin/start`)를 실행한다. phrocs라는 터미널 UI가 모든 프로세스 로그를 모아 보여 준다. 앱은 `http://localhost:8010`에 뜬다.
   - 화면 없이 띄우려면 `hogli up -d`(또는 `hogli start -d`). `hogli wait`로 준비를 기다리고 `hogli down`으로 내린다.
   - phrocs나 `hogli down`을 끝내도 compose 컨테이너는 남는다. `hogli docker:services:down`으로 내리고, 볼륨까지 지우려면 `hogli docker:services:remove`다.
   - 켤 서비스는 `hogli dev:setup`에서 고른다. 기본은 제품 분석에 필요한 최소 구성이다.

근거: `bin/start`, `hogli.yaml` (`start`, `dev:setup`), `docs/published/handbook/engineering/developing-locally.md`.
환경변수는 셸, flox `[vars]`, `.env.local`, `.env.development`, `.env.services` 순으로 우선한다. 근거: `docs/internal/dev-env-vars.md`
저장소 루트의 `.env`는 `bin/start`가 읽지 않는다.
`flox activate`가 읽어 셸 환경에 넣으므로, 셸 단계에서 적용된다. `.env`가 없으면 `.env.example`을 복사해 만든다. 근거: `.flox/env/on-activate.sh` (Step 4)
개발용 인프라 compose는 `docker-compose.dev.yml`(과 `docker-compose.dev-full.yml`)이다. 인프라 컨테이너는 `docker-compose.base.yml`을 공유한다.

개발 모드(`DEBUG`)는 인증을 느슨하게 한다. 운영 인스턴스에 `DEBUG`를 켜지 않는다. 근거: `posthog/settings/base_variables.py`, `posthog/settings/utils.py:assert_debug_not_in_production`.

### 마이그레이션

`hogli start`가 마이그레이션 프로세스를 같이 띄운다. 근거: `bin/mprocs.yaml`

| 프로세스                                                                                            | 하는 일                                                                                               |
| --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `migrate-postgres`                                                                                  | `bin/hogli db:restore-schema-if-fresh` 후 `bin/migrate --scope=postgres`                              |
| `migrate-clickhouse`                                                                                | ClickHouse 마이그레이션                                                                               |
| `migrate-persons-db`, `migrate-cyclotron`, `migrate-behavioral-cohorts`, `migrate-flags-read-store` | 인물 DB와 Rust 서비스용 DB. `migrate-flags-read-store`는 자동으로 시작하지 않는다(`autostart: false`) |
| `ensure-local-setup`                                                                                | `bin/ensure-local-setup`. 위저드 OAuth 앱과 태스크 샌드박스 OAuth 앱만 만든다                         |

수동으로 돌릴 때는 `hogli migrations:run`(= `bin/migrate`, `DEBUG=1`)이다. 근거: `hogli.yaml` (`migrations:run`)
DB 상태 확인과 되돌리기는 `hogli migrations:status`, `migrations:down`, `migrations:up`, `migrations:sync`다.

**빈 DB에서 스키마를 내려받는 지름길을 끄는 것을 권한다.**
`.env.development`가 `POSTHOG_SCHEMA_RESTORE_IN_DEV=auto`를 준다.
`migrate-postgres`가 시작할 때 DB가 비어 있으면 `hogli`가 `PostHog/posthog`의 `master` 브랜치 CI 산출물(`migrated-schema`)을 내려받아 복원한 뒤 마이그레이션을 돌린다.
GitHub 토큰(`GH_TOKEN`, `GITHUB_TOKEN`, `gh auth token` 중 하나)이 없거나 받기에 실패하면 "falling back to migrations"를 찍고 마이그레이션만 돌린다. 근거: `tools/hogli-commands/hogli_commands/github_auth.py:github_token`
"호환되는 산출물"의 기준은 이름, 만료, 크기, 브랜치뿐이고 마이그레이션 그래프를 비교하지 않는다.
그래서 GitHub 인증이 있는 환경에서는 업스트림 스키마(삭제된 `ee` 앱의 마이그레이션 기록 포함)가 이 포크의 DB로 들어와 아래 [ee 제거 전 DB](#ee-제거-전-db에서-생기는-문제) 문제를 만들 수 있다.
`.env.local`에 `POSTHOG_SCHEMA_RESTORE_IN_DEV=off`를 적으면 항상 이 포크의 마이그레이션으로 DB를 만든다.
근거: `.env.development`, `tools/hogli-commands/hogli_commands/db_schema.py` (`restore_schema_if_fresh`, `_handle_restore_failure`, `_filter_and_sort_candidates`, `GITHUB_REPOSITORY`, `DEFAULT_BASE_BRANCH`).
이 지름길을 실제로 돌려 보지 않았다. GitHub 인증이 없어 내려받기를 시험할 수 없었다(**미확인**).
`hogli dev:reset`의 "Restore pre-migrated schema from CI?" 질문도 같은 산출물을 쓴다.
이 질문은 `POSTHOG_SCHEMA_RESTORE_IN_DEV`를 읽지 않는다. `off`를 적어 두어도 `y`로 답하면 업스트림 스키마를 복원한다.
기본값 `N`으로 답하면 `migrations:run`으로 이 포크의 마이그레이션을 돌린다.
근거: `hogli.yaml` (`dev:reset`), `tools/hogli-commands/hogli_commands/db_schema.py` (`db_restore_schema`), `tools/hogli/src/hogli/command_types.py` (`_prompt_user`, `default=False`)

### 로그인과 데모 데이터

가입 화면에서 새 계정을 만들거나, 데모 데이터를 만든다.

- phrocs에서 `generate-demo-data`를 골라 `r`을 누른다. 자동으로 시작하지 않는 프로세스다. 명령으로는 `hogli dev:demo-data`(= `python manage.py generate_demo_data`)다.
- 기본 계정은 `test@posthog.com`, 비밀번호 `12345678`이다. `--email`, `--password`로 바꾼다. 끝나면 로그인 URL(`http://localhost:8010/login?email=...`)을 찍는다.
- `DEBUG`와 `ALLOW_DEV_LOGIN`이 모두 켜져 있으면(`.env.development`가 둘 다 켠다) 로그인 화면이 활성 사용자 목록을 보여 주고 비밀번호 없이 들어가게 한다.
- `hogli dev:reset`은 볼륨을 지우고, 마이그레이션하고, 데모 데이터를 `--skip-flag-sync`로 만들고, 플래그를 동기화한다.

근거: `bin/mprocs.yaml` (`generate-demo-data`), `posthog/management/commands/generate_demo_data.py`, `posthog/api/authentication.py:DevLoginViewSet`, `.env.development`, `hogli.yaml` (`dev:demo-data`, `dev:reset`).

### 개인 API 키와 로컬 플래그

개발용 고정 개인 API 키는 없어졌다.
`DEV_API_KEY`가 업스트림에서는 `ee/settings.py`에만 있었고 이 포크에는 `ee/`가 없어 정의가 사라졌기 때문이다.
`hogli dev:api-key`, `manage.py setup_local_api_key`, `ALLOW_DEV_API_KEY_REVEAL`, 설정 화면의 키 노출도 함께 지웠다.
근거: 에픽 `buzzhog-r0gt`의 `Decided alone` 노트, 커밋 `12bca50f9e8`.

- 키가 필요하면 `http://localhost:8010/settings/user-api-keys`에서 직접 만든다.
- 서버 쪽 로컬 플래그 평가에는 환경변수 `POSTHOG_PERSONAL_API_KEY`를 쓴다. 없으면 로컬 평가 플래그는 꺼진다. 근거: `posthog/apps.py`, `docs/published/handbook/engineering/developing-locally.md` ("Working with feature flags")
- `DEBUG=1`이면 `SELF_CAPTURE`가 켜져 분석이 이 인스턴스 자신으로 간다. 로컬에서 플래그를 쓰려면 같은 인스턴스에 쓰려는 플래그 키로 플래그를 만들거나 `DEBUG=1 python3 manage.py sync_feature_flags`로 전부 만든다. 근거: `posthog/settings/base_variables.py`
- `generate_demo_data`와 `sync_feature_flags_from_api`는 `POSTHOG_TELEMETRY_HOST`와 `POSTHOG_TELEMETRY_API_KEY`가 없으면 "Skipping feature flag sync"를 찍고 넘어간다. 업스트림 호스트로 가던 호출이 없어졌다. 근거: `posthog/management/commands/sync_feature_flags_from_api.py`

### 모바일 앱 `mobilehog`

로컬 스택에 붙는 Expo 앱이다. 로그인이 바뀌었다.

1. 저장소 루트의 `.env`에 `SANDBOX_PROVIDER=docker`가 있는지 본다. `flox activate`가 만든 `.env`는 `.env.example`의 복사본이라 이 줄이 이미 있다.
   없으면 한 줄 적는다. `.env`는 `flox activate`가 읽으므로, 셸을 다시 활성화한 뒤 스택을 다시 띄운다. 스택만 다시 띄우면 바뀐 값이 들어가지 않는다.
   근거: `.env.example`, `.flox/env/on-activate.sh`, `bin/start` (`source_env_defaults`가 `.env.local`, `.env.development`, `.env.services`만 읽는다)
2. 앱의 로그인 화면이 이메일과 비밀번호를 `/api/login/`으로 보낸 뒤, 그 사용자의 개인 API 키 `mobilehog local`을 만들어 이후 베어러 토큰으로 쓴다. 키가 이미 있으면 새로 만들지 않고 돌려서(roll) 쓴다. 같은 사용자로 먼저 로그인한 기기는 다시 로그인해야 한다. 서버가 사용자당 개인 API 키를 10개로 제한하고 로그아웃이 키를 폐기하지 않아서, 로그인마다 새 키를 만들면 한도에서 막히기 때문이다.
3. 실행: `cd products/desktop && pnpm install`, 처음에는 `pnpm --filter @posthog/mobilehog ios`, 이후에는 `pnpm --filter @posthog/mobilehog start`. 호스트는 `src/config.ts`(`http://localhost:8010`)에 있고, 실기기에서는 LAN IP로 바꾼다.

근거: `products/desktop/apps/mobilehog/README.md`, `products/desktop/apps/mobilehog/src/lib/auth.ts`, 에픽 `buzzhog-r0gt`의 `Decided alone` 노트.
실기기 로그인은 시험하지 않았다. 에픽 보고에 따르면 `@posthog/shared`를 빌드하지 않은 상태에서는 mobilehog vitest 파일 다섯 개가 실패한다(**미확인**, 보고서에서 옮김).

### 데스크톱 앱

`products/desktop`의 개발 빌드는 `http://localhost:8010`의 OAuth로 붙는다.
로컬 PostHog에 OAuth 애플리케이션을 등록하는 절차는 `products/desktop/docs/LOCAL-DEVELOPMENT.md`에 있다.
이번 마일스톤은 이 절차를 바꾸지 않았다. 읽기만 했고 실행하지 않았다.

### ee 제거 전 DB에서 생기는 문제

업스트림 코드로 만든 DB(업스트림 이미지로 올린 hobby DB, 업스트림 CI 스키마를 복원한 로컬 DB)에는 `ee` 앱의 마이그레이션 기록과 `ee_*` 테이블이 이미 있다.
이 포크는 RBAC 모델 다섯 개를 `access_control` 앱으로 옮기고 `(access_control, 0000_rbac_models)`와 `0004_featureflagroleaccess`를 새로 썼다. 두 마이그레이션은 `ee_role` 같은 같은 이름의 테이블을 만든다. ([ADR 0002](adr/0002-remove-ee-residue-keep-extension-points.md))
이 DB를 이 포크 코드로 `migrate`하면 막힌다.

**실행해 확인함** (임시 Postgres 15 컨테이너, 이 포크 코드, Redis 컨테이너 하나, 모두 작업 뒤 삭제):

1. 빈 DB에서 `manage.py migrate --noinput`이 끝까지 돈다. 끝난 뒤 `manage.py migrate --check`가 종료 코드 0이고 `hogli migrations:status`가 "Migrations are in sync"(3106개 적용, 코드와 일치)를 말한다. `ee_*` 테이블 13개가 생긴다.
2. 업스트림 DB를 흉내 내려고 `django_migrations`에서 `access_control`의 `0000_rbac_models`와 `0004_featureflagroleaccess` 두 줄을 지우고, 가짜 `ee` 기록 두 줄을 넣었다. `ee_*` 테이블은 그대로 두었다. 이 상태에서 `migrate`는 `DuplicateTable`이 아니라 `InconsistentMigrationHistory: Migration posthog.1344_squash_2026_09_07_finalize_fks is applied before its dependency access_control.0000_rbac_models`로 멈춘다.
3. `manage.py migrate access_control 0000 --fake`도 같은 오류로 거절된다. Django가 `--fake` 전에 기록의 일관성을 먼저 검사하기 때문이다.
4. `django_migrations`에 그 두 줄을 직접 넣으면 `migrate`가 "No migrations to apply."로 끝나고 종료 코드 0이다. 남은 가짜 `ee` 기록은 고아로 잡히지 않는다. `buzzhog-kxsw` 이후 `ee`는 `ee/migrations/__init__.py`가 있을 때만 관리 대상이다(`common/migration_utils/__init__.py:_present_optional_app_paths`).

대처는 4번이다. 다음 세 가지가 모두 맞을 때만 쓴다.

- 두 마이그레이션이 만들 테이블 다섯 개가 이미 있고 모양이 같다.
- `access_control`의 `0001`~`0003`이 이미 적용돼 있다. `0004`는 `0003`에 기대므로, `0003`이 없는 DB에 `0004` 기록을 넣으면 다시 `InconsistentMigrationHistory`가 난다. 근거: `products/access_control/backend/migrations/0004_featureflagroleaccess.py` (`dependencies`)
- DB의 `posthog` 마이그레이션이 이 포크보다 앞서 있지 않다. 이 포크의 마지막 `posthog` 마이그레이션은 `posthog/migrations/max_migration.txt`에 있다.
  업스트림 `master` CI 스키마나 이 포크보다 새 업스트림 이미지로 만든 DB에는 이 포크 코드에 없는 스키마 변경이 들어 있을 수 있다. 그런 DB는 기록만 맞춰도 코드와 스키마가 어긋날 수 있으므로 SQL 대신 DB를 다시 만든다.

아래의 확인용 `SELECT` 두 줄은 코드에서 끌어낸 것이며 실행해 보지 않았다.
`INSERT`가 넣는 두 줄은 4번에서 넣은 것과 같다.

```sql
-- 먼저 ee_role, ee_rolemembership, ee_organizationresourceaccess,
-- ee_accesscontrol, ee_featureflagroleaccess 테이블이 있는지 확인한다 (\dt ee_*)
-- 0001~0003이 나와야 하고 0000, 0004는 없어야 한다. 이미 있으면 INSERT하지 않는다
SELECT name FROM django_migrations WHERE app = 'access_control' ORDER BY name;
-- posthog/migrations/max_migration.txt의 이름보다 크면 이 SQL을 쓰지 않는다
SELECT max(name) FROM django_migrations WHERE app = 'posthog';
INSERT INTO django_migrations (app, name, applied) VALUES
  ('access_control', '0000_rbac_models', now()),
  ('access_control', '0004_featureflagroleaccess', now());
```

로컬은 `hogli db:pg`(= `psql postgres://posthog:posthog@localhost:5432/posthog`)로 실행한다. 근거: `hogli.yaml` (`db:pg`)
hobby는 `web`이 새 이미지로 뜨기 전에, `docker-compose up -d db` 뒤 `docker-compose exec db psql -U posthog -d posthog`로 같은 SQL을 실행한다. 이 hobby 명령은 실행해 보지 않았다(**미확인**).

데이터가 중요하지 않은 로컬 DB는 지우고 다시 만드는 편이 빠르다.
`.env.local`에 `POSTHOG_SCHEMA_RESTORE_IN_DEV=off`를 적고 `hogli docker:services:remove`로 볼륨을 지운 뒤 `hogli start`로 시작한다.
`hogli dev:reset`(볼륨을 모두 지운다)을 쓸 때는 스키마 복원 질문에 `N`으로 답한다([마이그레이션](#마이그레이션) 참조).

확인하지 못한 것이 둘 있다.

- 진짜 업스트림 DB의 `ee` 마이그레이션 이름과 테이블 모양이다. 가짜 기록과 이 포크가 만든 테이블로 흉내 냈을 뿐이다. 모양이 다르면 4번의 SQL이 맞지 않는다.
- `DuplicateTable`이 나는 경우다. `buzzhog-kxsw`의 노트는 `access_control.0000`이 그렇게 멈출 수 있다고 적는데, 위 실험은 앞선 `posthog` 마이그레이션이 이미 적용된 DB여서 일관성 검사가 먼저 걸렸다. `posthog` 마이그레이션이 덜 적용된 DB에서 어떻게 되는지는 재현하지 못했다. `hogli migrations:sync`는 중복 테이블 오류에서 `--fake`를 권하는 코드가 있지만(`tools/hogli-commands/hogli_commands/migrations.py:_handle_duplicate_error`) 이 DB에서 돌려 보지 않았다.

ADR 0002는 "이 포크 코드로 `migrate`한 DB는 없다"를 안전 근거로 들었다. 업스트림 DB를 옮기는 경우는 그 근거 밖이다.

### 이번 마일스톤에서 로컬이 달라진 점

| 이전                                                   | 지금                                                                                                                                                                                            | 근거                                                                                                                     |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `hogli dev:api-key`, 고정 개발 키, 설정 화면의 키 노출 | 없음. 키는 직접 만든다                                                                                                                                                                          | `hogli.yaml`, 커밋 `12bca50f9e8`                                                                                         |
| `ensure-local-setup`이 개발 키도 만든다                | 위저드와 태스크 샌드박스 OAuth 앱만 만든다                                                                                                                                                      | `bin/ensure-local-setup`                                                                                                 |
| 서버 텔레메트리가 PostHog 사 호스트로 간다             | `POSTHOG_TELEMETRY_HOST`와 `POSTHOG_TELEMETRY_API_KEY`가 둘 다 있을 때만 간다. 개발 모드의 자기 인스턴스 `SELF_CAPTURE`가 먼저다                                                                | `posthog/telemetry.py:get_telemetry_target`, `posthog/apps.py` (`ready`), [외부 호출](external-calls.md#텔레메트리-설정) |
| `hogli` 개발 도구 텔레메트리가 켜져 있다               | `hogli.yaml`의 `telemetry` 키·호스트가 비어 있어 보내지 않는다. 환경변수 `POSTHOG_TELEMETRY_HOST`와 `POSTHOG_TELEMETRY_API_KEY`를 주면 hogli도 그곳으로 보낸다. 서버 텔레메트리와 같은 이름이다 | `hogli.yaml`, `tools/hogli/src/hogli/telemetry.py` (`_host`, `_api_key`, `is_enabled`)                                   |
| 백엔드가 `ee/` 변경도 감시한다                         | `ee/`를 감시하지 않는다                                                                                                                                                                         | `bin/start-backend`                                                                                                      |
| 설정 > 인증에서 SCIM을 켠다                            | `scim_enabled=true`는 무시되고 `false`는 토큰을 지운다. SCIM 프로비저닝 엔드포인트가 없다                                                                                                       | `posthog/api/identity_provider_config.py`                                                                                |
| mobilehog가 고정 개발 키로 로그인한다                  | 이메일·비밀번호로 로그인해 `mobilehog local` 키를 만든다                                                                                                                                        | `products/desktop/apps/mobilehog/src/lib/auth.ts`                                                                        |

## 실행한 것과 읽기만 한 것

이 문서를 마지막으로 고칠 때(`buzzhog-ozkf`) 한 일이다.
위쪽 절의 "실행해 확인함" 두 곳(`.env` 텔레메트리 변수, ee 제거 전 DB)은 아래 표의 실행이다.
그 밖의 확인 기록(이미지 안의 가입 `201`, ClickHouse 없이 띄운 확인 등)은 각 에픽(`buzzhog-uxbl`, `buzzhog-dsv8`)의 기록이고, 이번에 다시 돌리지 않았다.

| 항목                                                                                                                                    | 상태      | 어떻게                                                                                           |
| --------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------ |
| 빈 Postgres 15에서 `manage.py migrate --noinput` 완료, 이후 `migrate --check` 종료 코드 0, `hogli migrations:status`가 "in sync"        | 실행      | 임시 컨테이너(Postgres, Redis), 작업 뒤 삭제                                                     |
| 업스트림 DB 흉내(`access_control` 두 줄 삭제)에서 `InconsistentMigrationHistory`, `--fake` 거절, 두 줄 삽입 뒤 "No migrations to apply" | 실행      | 같은 임시 DB                                                                                     |
| `docker compose -f docker-compose.hobby.yml config`에 텔레메트리 변수 다섯 개가 들어간다                                                | 실행      | 렌더링만. 컨테이너는 올리지 않았다                                                               |
| `hogli start`, `hogli up -d`, 데모 데이터, 로그인 화면, 스키마 복원 지름길                                                              | 읽기만    | `bin/start`, `bin/mprocs.yaml`, `hogli.yaml`, `tools/hogli-commands/hogli_commands/db_schema.py` |
| mobilehog 로그인, 데스크톱 앱 로컬 연결                                                                                                 | 읽기만    | 앱 README, `auth.ts`, `products/desktop/docs/LOCAL-DEVELOPMENT.md`                               |
| hobby 설치·업그레이드·롤백 절차, 이미지 빌드                                                                                            | 읽기만    | 스크립트와 compose 파일. 위쪽 각 절의 "미확인" 표시를 따른다                                     |
| 진짜 업스트림 DB를 이 코드로 올리는 일                                                                                                  | 하지 않음 | 업스트림 이미지와 DB가 없다                                                                      |

## 미확인 항목

- 지금 `Dockerfile`로 처음부터 빌드한 Django 이미지가 뜨는지. `ee` 정리 뒤의 확인은 수정한 코드를 기존 이미지에 마운트해서 했다
- `rust/` 컨텍스트에 `proto/`가 없을 때 Rust 이미지를 어떻게 빌드하는지
- ClickHouse·객체 스토리지 백업·복원 절차와 ClickHouse 스키마 롤백
- `docker-compose exec web ./bin/migrate`를 비롯해 이 문서의 `docker-compose` 명령 실행 결과, 실제 볼륨 이름
- `posthog/`가 브랜치가 아닌 곳에 체크아웃돼 있을 때 `bin/upgrade-hobby`가 멈추는지
- ClickHouse 26.9가 이 코드와 실제로 잘 동작하는지
- 설치 스크립트의 텔레메트리를 끄는 방법. 스크립트를 고치는 방법 외에는 찾지 못했다
- 진짜 업스트림 DB에서 `ee` 마이그레이션 이름과 `ee_*` 테이블 모양이 이 포크가 만드는 것과 같은지
- `posthog` 마이그레이션이 덜 적용된 DB에서 `access_control.0000`이 `DuplicateTable`로 멈추는지
- 전체 개발 스택(`hogli start`)이 이 포크에서 처음부터 끝까지 도는지
- GitHub 인증이 있을 때 `hogli`의 스키마 복원 지름길이 업스트림 스키마를 가져오는지(코드로만 읽음)
- `fork-images.yml`의 `deploy-dev` job이 GitHub Actions에서 k8s-manifests에 실제로 push하는지(deploy key, GHCR 조회, `gh api`는 로컬에서 가짜로 대신했다)
- `promote-prod.yml`이 GitHub Actions에서 k8s-manifests에 실제로 push하는지(deploy key, GHCR 조회, yq 컨테이너는 로컬에서 가짜로 대신했다)

Decided in: buzzhog-uxbl, buzzhog-dsv8, buzzhog-ozkf
