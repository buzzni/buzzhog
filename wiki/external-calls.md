# 외부 호출

확인 기준 커밋: 70371e9eb38

이 포크가 PostHog 소유 서버나 제3자 서비스로 내보내는 호출 중, 코드에서 확인한 것만 적는다.
각 행에 위치(`파일:심볼` 또는 파일)와 끄는 방법을 둔다. "끄는 방법 미확인"은 코드에서 확인하지 못했다는 뜻이다.
의존성 라이선스는 [licenses.md](licenses.md), 브랜딩 위치는 [branding.md](branding.md)를 본다.

공개 저장소라 비밀값은 적지 않는다. 아래에서 말하는 `phc_` 또는 짧은 토큰은 코드에 하드코딩된 PostHog 프로젝트 공개 토큰이며, 이 문서에는 옮기지 않았다.

## 요약

| 구분 | 목적지 | 기본 동작 | 끄는 방법 |
| --- | --- | --- | --- |
| 서버 텔레메트리 (Python) | PostHog 프로젝트로 `posthoganalytics` 이벤트·예외·플래그 조회 | 켜짐(`TEST`·`DEBUG`·`SELF_CAPTURE`가 아닐 때) | 환경변수 `OPT_OUT_CAPTURE` |
| 브라우저 텔레메트리 | `https://internal-cf.posthog.com` | 켜짐 | `OPT_OUT_CAPTURE`가 참이거나 `js_posthog_api_key`가 비면 로더를 넣지 않음. 상세는 아래 |
| 하비 설치 스크립트 | `https://us.i.posthog.com/batch/` | 설치 시작과 완료 이벤트 전송 | 스크립트 수정 외 방법 미확인 |
| GeoIP 파일 내려받기 | `https://mmdbcdn.posthog.net/` | 이미지 빌드·설치 때 1회 | 스크립트·Dockerfile 수정 |
| 사용량 보고 | 과금 서비스 | 이 포크에서는 사실상 꺼짐 | `ee` 부재가 이미 막음 |
| Rust 서비스 메트릭·캡처 | `https://us.i.posthog.com/capture` | 서비스 설정 기본값 | 서비스 환경변수 |
| 프런트엔드 외부 origin | CSP가 허용한 목록 | 허용만 한다. 호출은 기능이 쓸 때 | CSP 코드 수정 |
| 제품 기능이 쓰는 제3자 API | Slack, GitHub, Stripe 등 | 연동을 켠 팀만 | 해당 연동 미설정 |

## 서버 텔레메트리 (`posthoganalytics`)

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 초기화 | `AppConfig.ready()`가 `posthoganalytics.api_key`, `super_properties`(리전, 서비스명, 환경), 예외 자동 캡처(`enable_exception_autocapture = True`)를 설정 | `posthog/apps.py:ready` (`posthoganalytics.api_key = ...` 줄 근처) |
| 끄기 | `settings.TEST` 이거나 환경변수 `OPT_OUT_CAPTURE`가 비어 있지 않으면 `posthoganalytics.disabled = True` | `posthog/apps.py:ready` |
| 설정 변수 | `OPT_OUT_CAPTURE` 설정값(기본 `False`). `docker-compose.hobby.yml`이 `${OPT_OUT_CAPTURE:-false}`로 전달 | `posthog/settings/base_variables.py:OPT_OUT_CAPTURE`, `docker-compose.hobby.yml:183` |
| 자기 캡처 | `DEBUG` 이거나 `SELF_CAPTURE`가 참이면 `disabled`로 두고 인스턴스 자신으로 보내도록 따로 구성한다. 개발 서버 기동 시 `development server launched` 이벤트를 별도 클라이언트로 PostHog 쪽에 보낸다 | `posthog/apps.py:ready`, `posthog/settings/base_variables.py:SELF_CAPTURE` |
| 플래그 정의 | 비활성이 아니면 `posthoganalytics.load_feature_flags()`로 플래그 정의를 가져온다. 개인 API 키는 환경변수 `POSTHOG_PERSONAL_API_KEY`에서 읽는다 | `posthog/apps.py:ready` |
| 클라우드 호스트 판별 | `https://us.posthog.com`이면 `https://us.i.posthog.com`, 아니면 EU 호스트 | `posthog/cloud_utils.py` (104행 근처) |
| 호스트 상수 | `PH_US_HOST`, `PH_EU_HOST`. `ph_scoped_capture`는 `is_cloud()`일 때만 클라이언트를 만든다 | `posthog/ph_client.py` |
| Celery 안 캡처 | `posthoganalytics.capture()`가 아니라 `ph_scoped_capture`를 쓰라는 저장소 규칙이 있다 | `CLAUDE.md` "Async, storage and outbound calls" |

플래그와 이벤트가 어느 프로젝트로 가는지는 하드코딩된 공개 토큰이 정한다.
자체 호스팅 운영자는 `OPT_OUT_CAPTURE`를 참으로 두어 서버 쪽 전송을 끈다. 켜 둔 배포에서 실제로 패킷이 나가는지는 실행해 보지 않았다(미확인).

## 브라우저 텔레메트리 (`posthog-js`)

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 호스트와 토큰 | 기본 분기는 `POSTHOG_JS_CLOUD_HOST` = `https://internal-cf.posthog.com`와 공개 토큰 | `posthog/constants.py:POSTHOG_JS_CLOUD_HOST`, `posthog/constants.py:POSTHOG_JS_CLOUD_TOKEN`, `posthog/utils.py:get_context_for_template` 인근의 `js_posthog_*` 설정 |
| 분기 | E2E 테스트면 고정 토큰, `SELF_CAPTURE`면 `api_host`를 빈 문자열로 둬 `location.origin`(자기 자신)으로 보낸다. 그 외에는 위 클라우드 호스트 | `posthog/utils.py` (545~580행 근처) |
| 초기화 | `window.JS_POSTHOG_API_KEY`가 있을 때만 `posthog.init(...)`. 세션 녹화·예외 캡처·메트릭을 켠다 | `frontend/src/loadPostHogJS.tsx:loadPostHogJS` |
| 옵트아웃 | 가장한 세션(`IMPERSONATED_SESSION`)이면 `opt_out_capturing()`. 그렇지 않으면 `opt_in_capturing()` | `frontend/src/loadPostHogJS.tsx:loadPostHogJS` |
| 서버 쪽 차단 | 템플릿이 `{% if not opt_out_capture and js_posthog_api_key %}`일 때만 `posthog-js` 설정 블록을 넣는다. 컨텍스트 값 `opt_out_capture`는 `settings.OPT_OUT_CAPTURE` | `posthog/templates/head.html` (44행), `posthog/utils.py` (520행 근처) |
| 로드 안 함 | 키가 없으면 `fake_token`으로 초기화하고 `opt_out_capturing_by_default: true` | `frontend/src/loadPostHogJS.tsx` (233~243행 근처) |

브라우저 쪽도 `OPT_OUT_CAPTURE`를 참으로 두면 로더 블록이 페이지에 들어가지 않는다. 블록 안에서 `window.JS_POSTHOG_API_KEY`를 채우는지 여부로 `posthog.init`이 결정되므로, 실제 브라우저 요청이 사라지는지는 실행해 보지 않았다(미확인).

## 하비(자체 호스팅) 설치 스크립트

| 위치 | 호출 | 비고 |
| --- | --- | --- |
| `bin/deploy-hobby` (70~76행 근처) | `curl`로 `https://us.i.posthog.com/batch/`에 `magic_curl_install_start` 이벤트와 입력한 도메인 | 설치 시작 시 도메인이 PostHog 서버로 간다 |
| `bin/hobby-installer/core/telemetry.go:SendInstallStartEvent`, `SendInstallCompleteEvent` | 같은 엔드포인트로 `magic_curl_install_start`, `magic_curl_install_complete` | 전송을 끄는 설정은 확인하지 못했다. `OPT_OUT`·`DO_NOT_TRACK` 검색 결과 없음 |
| `bin/deploy-hobby` (196행) | `https://mmdbcdn.posthog.net/`에서 GeoLite2 City 파일 내려받기 | 도메인이 `posthog.net` |
| `bin/deploy-hobby` (249행, 260행) | Docker GPG 키와 `docker-compose` 릴리스를 `download.docker.com`, `github.com`에서 받는다 | 제3자 |
| `bin/download-mmdb` (17행), `Dockerfile` (288행) | `mmdbcdn.posthog.net` | 이미지 빌드·개발 환경 |
| `bin/hobby-installer/core/geoip.go` | GeoIP 내려받기 | 같은 호스트로 추정. 미확인 |

## 사용량 보고와 과금

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 전송 | `send_report_to_billing_service`가 `BILLING_SERVICE_URL`의 `/api/usage`로 POST | `posthog/tasks/usage_report.py:send_report_to_billing_service` |
| 가드 | 함수 맨 앞에서 `settings.EE_AVAILABLE`이 거짓이면 반환 | 같은 함수 |
| `EE_AVAILABLE` | `ee.apps`를 import하지 못하면 `False` | `posthog/settings/ee.py` |
| 이 포크 | `ee/` 디렉터리가 없어 `EE_AVAILABLE`은 `False`다. 사용량 보고는 과금 서비스로 나가지 않는다 | `ls ee` 실패, `posthog/settings/ee.py` |
| 주의 | `BILLING_SERVICE_URL`은 `ee.settings`에서만 정의된다. `posthog/api/id_jag.py:170`, `posthog/admin/admins/organization_admin.py:326`은 `settings.BILLING_SERVICE_URL`을 읽는다. `ee` 없이 이 값이 정의되는지 확인하지 못했다 | 미확인 |
| 예약 작업 | `send_org_usage_reports`는 `posthog/tasks/scheduled.py`에 등록되어 있다 | `posthog/tasks/scheduled.py` (684행 근처) |
| 내부 플래그 | `disable-usage-reports` 플래그가 켜지면 중단 | `posthog/tasks/usage_report.py` (3753행 근처) |

## 업데이트 확인

설치된 버전을 PostHog 서버에 물어보는 코드는 찾지 못했다.
검색한 이름: `check_for_updates`, `latest_version`, `version_check`, `UPDATE_CHECK`, `get_latest_version`. 매치는 테스트와 SDK 상태 API(`posthog/api/sdk_health.py`, SDK 버전이며 PostHog 자체 업데이트 확인이 아님)뿐이었다.
`releases.posthog.com`은 PostHog CLI 설치 스크립트와 릴리스 산출물 주소다(`cli/README.md`, `cli/CHANGELOG.md`). 서버가 부르는 호출이 아니라 사용자가 CLI를 설치할 때 쓰는 주소다.

## Rust 서비스

| 위치 | 호출 | 비고 |
| --- | --- | --- |
| `rust/common/posthog/src/lib.rs` | 서비스 내부 텔레메트리. 전역 클라이언트 초기화와 `$exception` 수동 캡처(프로세스당 분당 10건 상한). `endpoint`에 호스트를 받고 캡처 경로 접미사를 지운다. `api_key`가 없으면 클라이언트를 만들지 않는다 | 키가 없으면 꺼진다 |
| `rust/cymbal/src/modes/processing/config.rs` | `envconfig` 기본값 `https://us.i.posthog.com/capture` | 환경변수로 덮어쓴다 |
| `rust/cymbal/src/modes/{notifications,resolution}/config.rs`, `rust/cymbal/src/core/types/langs/js.rs` | PostHog 호스트 상수·기본값 | 용도 미확인 |

## Node.js 서비스

`nodejs/src/ingestion/pipelines/sessionreplay/ml-mirror-image-fetch/web-bot-auth.ts`와 `request-identity.ts`가 `posthog.com` 계열 호스트를 쓴다. 이미지를 가져올 때 보내는 신원 헤더로 보이며 정확한 용도는 확인하지 못했다.

## 프런트엔드 외부 origin (CSP)

`CSPMiddleware`가 HTML 응답마다 정책을 만든다. 정책에 없는 origin은 브라우저가 조용히 막는다.

| 지시어 | 허용 origin (일부) | 근거 |
| --- | --- | --- |
| `script-src` | `'self'`, nonce, `https://*.i.posthog.com`, `https://js.stripe.com`, `https://challenges.cloudflare.com`, `https://editor.unlayer.com/embed.js` | `posthog/csp_middleware.py:CSPMiddleware.__call__` (346행 근처) |
| `style-src` | `https://fonts.googleapis.com` | 같음 (322행) |
| `font-src` | `https://app-static.eu.posthog.com`, `https://app-static-prod.posthog.com`, `https://fonts.gstatic.com` | 같음 (352행) |
| `img-src` | `https:` 전체, `https://posthog.com`, `https://www.gravatar.com`, `https://res.cloudinary.com`, `https://platform.slack-edge.com`, `https://raw.githubusercontent.com` | 같음 (391행) |
| `connect-src` | `'self'`, `https://www.posthogstatus.com`, `https://raw.githubusercontent.com/PostHog/terminal-assets/`, 개체 저장소 주소 | 같음 (393행) |
| `frame-src` | `'self'`, `https:` 전체 | 같음 (396행) |
| 관리자 화면 | `frame-src https://posthog.com`, 글꼴 `https://fonts.gstatic.com` | 같음 (249~262행) |

`script-src`에는 `unsafe-eval`이 없고 `wasm-unsafe-eval`만 있다.
CSP에 이 포크 도메인을 쓰려면 같은 PR에서 이 지시어를 넓혀야 한다(`CLAUDE.md` "Security").

## PostHog 클라우드 API와 기타 `posthog.com` 호스트

| 호스트 | 쓰임 | 위치 |
| --- | --- | --- |
| `us.posthog.com`, `eu.posthog.com`, `app.posthog.com` | 리전 리다이렉트, CORS 허용, OAuth 클라이언트 메타데이터, 교차 리전 API | `posthog/frontend_views.py`, `posthog/utils_cors.py`, `posthog/regions.py`, `posthog/api/oauth/views.py`, `posthog/settings/integrations.py` (`POSTHOG_CONNECT_BASE_URL_US`) |
| `us.i.posthog.com/flags?v=2` | 플래그 정의를 동기화하는 관리 명령 | `posthog/management/commands/sync_feature_flags_from_api.py` |
| `us.posthog.com` | 사용자 설정 동기화 관리 명령 | `posthog/management/commands/sync_user_settings.py` |
| `app.posthog.com/batch` | 팀 이전 관리 명령 | `posthog/management/commands/migrate_team.py` |
| `us.i.posthog.com/batch/`, `eu.i.posthog.com/batch/` | 배치 내보내기 HTTP 목적지 허용 목록 | `products/batch_exports/backend/temporal/destinations/http_batch_export.py:172` |
| `mcp.posthog.com` | MCP 리소스 허용 | `posthog/settings/web.py` (1284행 주석), `posthog/api/oauth/mcp_resource_scopes.py` |
| `agent-proxy.us.posthog.com` | 에이전트 프록시 | `posthog/settings/access.py` (137행 주석) |
| `internal-cf.posthog.com` | 브라우저 텔레메트리 호스트 | `posthog/constants.py` |
| 이메일 속 `us.posthog.com` 링크 | 피드백 설문 링크 | `posthog/tasks/email.py` (2809행) |

관리 명령은 운영자가 직접 실행할 때만 나간다. 예약 작업이나 요청 경로에서 자동으로 부르는지는 확인하지 못했다.

## 제3자 API

제품 기능이 연동을 켠 팀을 위해 호출한다. 기본은 꺼짐이다.

| 서비스 | 위치 | 비고 |
| --- | --- | --- |
| GitHub | `posthog/api/github.py` (`GITHUB_KEYS_URI = https://api.github.com/meta/public_keys/secret_scanning`) | 비밀 스캔 공개 키. `CLAUDE.md`는 GitHub·Slack 호출을 `posthog/egress/`로 보내라고 한다 |
| Stripe | `posthog/settings/integrations.py`, `posthog/settings/payments.py` | 변수 미설정이면 비어 있음 |
| Slack | `posthog/settings/__init__.py:SLACK_APP_LOCAL_DEV_EMAIL`, `posthog/helpers/slack_thread_mirror.py` | |
| 웹훅·CDP 대상 | `products/cdp/backend/templates/` | 사용자가 정한 URL |

범위가 넓어 전수 조사는 하지 않았다. 외부 서비스 호출 전반은 `posthog/egress/`를 시작점으로 후속 조사가 필요하다(미확인).

Decided in: buzzhog-gimc
