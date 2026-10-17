# 외부 호출

확인 기준 커밋: 70371e9eb38
재확인: 2026-10-16. 리뷰 지적 13~28을 코드에서 다시 열어 확인했다. `milestone/buzzhog-vltl`의 제품 코드는 이 커밋과 같다(`wiki/`, `.moai/` 밖 차이 없음).

이 포크가 PostHog 소유 서버나 제3자 서비스로 내보내는 호출 중, 코드에서 확인한 것만 적는다.
각 행에 위치(`파일:심볼`, 필요하면 줄)와 끄는 방법을 둔다.
"미확인"은 코드나 실행으로 확인하지 못했다는 뜻이다. "코드 수정 필요"는 설정이나 환경변수로 끄는 길을 찾지 못했다는 뜻이고, 고칠 위치를 함께 적는다.
"과금 서비스", "제3자 API"의 `ee` 관련 행은 에픽 `buzzhog-dsv8`(병합 `ca37aa9e209`) 기준으로 고쳤다. 다른 행의 줄 번호는 확인 기준 커밋 `70371e9eb38` 때의 것이라, `posthog/tasks/usage_report.py`처럼 그 에픽이 고친 파일은 줄이 밀렸을 수 있다.
이 페이지는 동작을 기록할 뿐이다. 제품 코드는 고치지 않았다. 고칠 곳은 맨 아래 "코드 수정이 필요한 곳"에 모았다.
의존성 라이선스는 [licenses.md](licenses.md), 브랜딩과 밖으로 나가는 신원 문자열은 [branding.md](branding.md)를 본다.

공개 저장소라 비밀값은 적지 않는다. 아래의 "하드코딩 공개 토큰"은 코드에 박힌 PostHog 프로젝트 공개 토큰이며, 값은 이 문서에 옮기지 않았다.
"하비 기본 설치"는 `bin/deploy-hobby`와 `docker-compose.hobby.yml`로 설치하고 `.env`에 아무것도 더하지 않은 상태를 말한다.

## 요약

| 구분 | 목적지 | 하비 기본 설치에서 | 끄는 방법 |
| --- | --- | --- | --- |
| 사용량 보고 이벤트 (매일 03:45 UTC) | `https://us.i.posthog.com` (SDK 기본 호스트), 하드코딩 공개 토큰 | 켜짐. 조직명, 사이트 주소, 비클라우드면 사용자 이메일·이름 포함 | 설정으로 못 끔. 코드 수정 필요(예약 작업 제거 또는 `get_ph_client` 교체). 유일한 차단은 PostHog 클라우드 쪽 플래그 |
| AI observability 사용량 보고 (매일 04:15 UTC) | 같음 | 켜짐(AI 이벤트가 있는 조직만) | 위와 같음 |
| 서버 텔레메트리, `web` 프로세스 | `https://us.i.posthog.com` | 꺼짐. compose가 넘기는 문자열 `"false"`도 끄는 값으로 읽힌다 | 환경변수 `OPT_OUT_CAPTURE`(비어 있지 않은 아무 값) |
| 서버 텔레메트리, `worker`(Celery와 beat, UI에서 시작한 비동기 마이그레이션 포함)·`temporal-django-worker` | 같음 | 켜짐. compose가 이 서비스들에 `OPT_OUT_CAPTURE`를 넘기지 않는다 | compose 수정 필요(각 서비스 `environment`에 추가) |
| 원격 플래그 평가 | `https://us.i.posthog.com/flags` | 서버 SDK가 켜진 프로세스에서 켜짐. PostHog 클라우드의 플래그 값이 포크의 일부 동작을 정한다 | 그 프로세스의 서버 SDK를 끔 |
| 브라우저 텔레메트리 (앱 페이지, 공유·임베드 페이지) | `https://internal-cf.posthog.com` | 켜짐. 이메일, 조직명·슬러그, 프로젝트명 포함 | `web`의 `OPT_OUT_CAPTURE`를 `true`·`1`·`yes` 같은 참 값으로. `"false"`는 끄지 못함 |
| 툴바 인증 페이지 (`layout.html`) | `https://internal-cf.posthog.com`, `stackpath.bootstrapcdn.com` | 켜짐. `OPT_OUT_CAPTURE`를 보지 않음 | 코드 수정 필요 |
| 고객 사이트에서 도는 툴바 | `https://internal-cf.posthog.com`, 하드코딩 공개 토큰 | 앱의 실행 링크로 열면 켜짐(사용자 이메일 포함) | 코드 수정 필요 |
| 앱 페이지가 만드는 툴바 posthog-js 인스턴스 | `OPT_OUT_CAPTURE`가 참이면 SDK 기본 호스트(`https://us.i.posthog.com`)의 assets 주소, 하드코딩 공개 토큰 | 앱 페이지마다 원격 설정을 요청한다. `OPT_OUT_CAPTURE`를 참으로 두어도 남는다(코드로 확인, 실행하지 않음) | 코드 수정 필요 |
| 기본으로 요청하는 제3자 자원 | Gravatar, Cloudinary(PostHog 계정), `posthog.com` | 켜짐 | 코드 수정 필요 |
| 커뮤니티 스킬 카탈로그 동기화 (매시간) | `raw.githubusercontent.com/PostHog/community-skills` | 켜짐. 받은 내용이 DB에 들어간다 | 설정 못 찾음. 코드 수정 필요 |
| MCP 레지스트리 동기화 (매일) | `registry.modelcontextprotocol.io`, 등록된 MCP 서버들 | PostHog 클라우드 플래그 `mcp-registry`가 정함 | 서버 SDK를 끄면 꺼짐(평가 실패 시 꺼짐) |
| 하비 설치·업그레이드 스크립트 | `us.i.posthog.com/batch/`, 업스트림 GitHub 저장소, Docker Hub `posthog/posthog`, `ghcr.io/posthog/posthog/*:master`, `mmdbcdn.posthog.net`, Let's Encrypt | 설치·업그레이드 때. 이 포크가 아니라 업스트림을 설치한다 | 스크립트 수정 필요. 판매 전에 바꿀 기본값 |
| GeoIP 파일 내려받기 | `https://mmdbcdn.posthog.net/` | 이미지 빌드·설치·업그레이드 때 | 스크립트·Dockerfile 수정 |
| desktop 앱 업데이트 확인 (매시간) | `https://desktop-releases.posthog.com/stable` | 패키징된 macOS·Windows 빌드에서 켜짐 | 환경변수 `ELECTRON_DISABLE_AUTO_UPDATE`. 피드 주소는 코드 수정 |
| desktop 앱 텔레메트리 | `https://internal-c.posthog.com` | 빌드 때 `VITE_POSTHOG_API_KEY`가 없으면 꺼짐 | 빌드 때 키를 넣지 않음 |
| Rust 서비스 메트릭·캡처 | `https://us.i.posthog.com/capture` | 키 없으면 꺼짐(기본) | `POSTHOG_API_KEY`를 넣지 않음 |
| Node.js 서비스 캡처 | `POSTHOG_HOST_URL` | 키 없으면 꺼짐(기본) | `POSTHOG_API_KEY`를 넣지 않음 |
| 세션 리플레이 이미지 크롤러 (Node.js) | 리플레이에 나온 외부 이미지 호스트 | 하비 compose에 없어 돌지 않음 | 해당 서버 모드를 실행하지 않음 |
| CSP 위반 보고 | `https://us.i.posthog.com/report/` | 보내지 않음 | 기본 꺼짐(`is_cloud()`일 때만) |
| 연동 기능의 제3자 API | Slack, GitHub, GitLab, Stripe, AWS SES 등 | 연동·자격 증명을 설정했을 때. SES 상태 조회는 10분마다 예약됨(자격 증명 없을 때 동작 미확인) | 해당 연동 미설정 |

## 클라우드 판별

여러 경로가 `is_cloud()`로 PostHog 클라우드인지 가른다.

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 판별 | `is_cloud()`는 `derive_run_mode(settings.CLOUD_DEPLOYMENT, settings.DEBUG)`의 결과로 정한다. `CLOUD_DEPLOYMENT`가 `US`·`EU`·`DEV`·`E2E`면 그 모드이고, `LOCAL`이면 `LOCAL`이다. 그 밖의 값이면 `DEBUG`일 때 `LOCAL`, 아니면 `HOBBY`다 | `posthog/cloud_utils.py:is_cloud`(32행), `posthog/run_mode.py:derive_run_mode`(46~65행) |
| 스위치 | 클라우드 경로 전체를 가르는 값은 `CLOUD_DEPLOYMENT` 하나다. 하비 compose는 이 값을 넣지 않는다 | 같음, `docker-compose.hobby.yml` |
| 수집 호스트 | `get_api_host()`는 `SITE_URL`이 `https://us.posthog.com`이면 `https://us.i.posthog.com`, `https://eu.posthog.com`이면 `https://eu.i.posthog.com`을 돌려준다. 그 밖에는 `SITE_URL` 자신을 돌려준다 | `posthog/cloud_utils.py:get_api_host`(103~108행) |
| 지역 | `get_instance_region()`은 `settings.CLOUD_DEPLOYMENT`를 그대로 돌려준다. 하비에서는 `None` | `posthog/utils.py:get_instance_region` |

## 사용량 보고 (Celery 예약 작업)

이 포크에서도 매일 PostHog 클라우드로 사용량 보고 이벤트가 나간다.
과금 서비스로 가는 전송은 코드에서 지웠다(아래 "과금 서비스"). 이벤트 전송은 `ee`와 무관하고, `OPT_OUT_CAPTURE`로도 꺼지지 않는다.

### 흐름

| 단계 | 내용 | 근거 |
| --- | --- | --- |
| 예약 | `send_org_usage_reports`를 매일 03:45(UTC)에 조건 없이 등록한다 | `posthog/tasks/scheduled.py:setup_periodic_tasks`(682~686행) |
| 실행 위치 | 하비의 `worker`가 `--with-scheduler`로 beat를 함께 돌리고, 기본 큐 목록에 `usage_reports`가 있다 | `docker-compose.base.yml:worker`(`./bin/docker-worker-celery --with-scheduler`), `bin/celery-queues.env` |
| 진입 | `send_org_usage_reports`가 `send_all_org_usage_reports.delay()`를 부른다 | `posthog/tasks/tasks.py:send_org_usage_reports`(1121행) |
| 중단 검사 | `posthoganalytics.feature_enabled("disable-usage-reports", "internal_billing_events")`가 참일 때만 멈춘다. 전역 SDK가 꺼져 있으면 SDK는 `None`을 돌려주므로 멈추지 않는다 | `posthog/tasks/usage_report.py:send_all_org_usage_reports`(3753행), posthoganalytics 7.67.1 `client.py:_get_feature_flag_result`(`if self.disabled: return None`) |
| 조직별 전송 | 조직마다 `capture_report.delay(...)`를 부른다(`dry_run`·`skip_capture_event`가 아닐 때) | 같은 함수(3849행) |
| 이벤트 기록 | `capture_report`가 `report_utils.capture_event`를 부른다 | `posthog/tasks/usage_report.py:capture_report`(2815행), `posthog/tasks/report_utils.py:capture_event`(39행) |
| 비클라우드 분기 | `is_cloud()`가 아니면 `distinct_id=get_machine_id()`(MAC 주소의 md5), `groups={"instance": SITE_URL}`, `"scope": "machine"`으로 보낸다. 넘겨받은 `distinct_id`는 이 분기에서 쓰지 않는다 | `posthog/tasks/report_utils.py:capture_event`(68~92행), `posthog/utils.py:get_machine_id` |
| 클라이언트 | `get_ph_client`는 하드코딩 공개 토큰으로 별도 `PostHogClient`를 만든다. 호출부는 `sync_mode=True`를 준다. 별도 클라이언트라 `posthoganalytics.disabled`도 `OPT_OUT_CAPTURE`도 보지 않는다 | `posthog/tasks/usage_report.py:get_ph_client`(555~556행), 같은 파일 2824·3772행 |
| 호스트 | `get_ph_client`는 호스트를 넘기지 않는다. SDK의 기본 호스트는 `https://us.i.posthog.com`이고, `disabled` 기본값은 `False`다 | posthoganalytics 7.67.1(`uv.lock`) `request.py:DEFAULT_HOST`(186~188행), `client.py:Client.__init__`(`disabled=False`, 688행) |

### 보내는 데이터

| 이벤트 | 담기는 내용 | 근거 |
| --- | --- | --- |
| `organization usage report` | 조직별 사용량 카운터 전체, `organization_id`, `organization_name`, `organization_created_at`, `organization_user_count`, `team_count`, 팀별 카운터 | `posthog/tasks/usage_report.py:OrgReport`(430~440행), `_get_full_org_usage_report`(3577행) |
| 같은 이벤트의 인스턴스 정보 | `deployment_infrastructure`(환경변수 `DEPLOYMENT`, 하비는 `hobby`), `realm`, `site_url`, `product`, `instance_tag` | `posthog/tasks/usage_report.py:get_instance_metadata`(467행~) |
| 같은 이벤트, 비클라우드만 | `helm`, `clickhouse_version`, `table_sizes`, 설치·활성 플러그인 이름별 개수, `users_who_logged_in`·`users_who_signed_up`. 두 목록은 전날 로그인·가입한 인스턴스 전체 사용자의 `id`, `distinct_id`이고, 사용자가 `anonymize_data`가 아니면 `first_name`, `email`도 담는다. 이 목록은 모든 조직의 보고에 똑같이 들어간다 | 같은 함수(497~546행), `_get_full_org_usage_report`가 인스턴스 정보를 조직 보고에 합침 |
| `organization usage report failure` | 앞 전송이 실패했을 때 오류 문자열 | `capture_report` |
| 조직 그룹 속성 (`group_identify`) | `member_count`, `project_count`, `dashboard_count`, `ff_count`, `survey_count` | `capture_report`(2847행) |
| `organization usage report per person` | 구성원마다 `has_non_zero_usage`, `org_membership_level`, `role_at_organization` | `capture_report`(2880행 부근) |
| `usage reports starting`, `usage reports complete` | `total_orgs`, 지역, 기간, 처리 시간, `groups={"instance": SITE_URL}` | `send_all_org_usage_reports`(3823~3836행, 3875~3891행) |

### AI observability 사용량 보고

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 예약 | `send_ai_observability_usage_reports`를 매일 04:15(UTC)에 조건 없이 등록한다 | `posthog/tasks/scheduled.py:setup_periodic_tasks`(697~701행) |
| 클라이언트 | `PostHogClient(PH_US_API_KEY, sync_mode=True)`인 별도 클라이언트. 호스트 인자가 없어 SDK 기본 호스트로 간다 | `posthog/tasks/ai_observability_usage_report.py:get_ph_client`(30~38행), `posthog/ph_client.py:PH_US_API_KEY` |
| 전송 | `capture_ai_observability_report`가 같은 `report_utils.capture_event`로 `llm analytics usage` 이벤트를 보낸다 | 같은 파일 `capture_ai_observability_report`(1161행~) |
| 내용 | AI 이벤트가 있는 조직의 `organization_id`, `organization_name`, 기간, AI 이벤트 종류별 개수, 비용 합계 | 같은 파일 `_get_all_ai_observability_reports`(1015~1027행 부근) |
| 중단 검사 | 클라우드 플래그 `llm-analytics-disable-usage-reports`. 전역 SDK가 꺼져 있으면 멈추지 않는다 | 같은 파일 `send_ai_observability_usage_reports`(1243행) |

### 과금 서비스

에픽 `buzzhog-dsv8`이 과금 서비스로 가는 코드를 지웠다. 근거: [ADR 0002](adr/0002-remove-ee-residue-keep-extension-points.md).

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| SQS 전송 | 없다. `ee.sqs.SQSProducer`로 큐에 넣던 코드(`_queue_report`)를 지웠다 | `git grep -n -i sqs posthog/tasks/usage_report.py`가 비어 있다 |
| `send_report_to_billing_service` | 지웠다. 이 태스크를 부르는 곳도 없다 | `git grep send_report_to_billing_service`가 비어 있다 |
| `EE_AVAILABLE` | `ee.apps`를 import하지 못하면 `False`. 이 포크에는 `ee/`가 없어 거짓이다. 확장 지점으로 남겼다. 라이선스 확인(`get_cached_instance_license`)이나 일부 예약 작업(`find_flags_with_enriched_analytics`)의 조건으로 읽는다 | `posthog/settings/ee.py`, `posthog/tasks/usage_report.py:get_instance_metadata`(467행), `posthog/tasks/scheduled.py`(943행) |
| `BILLING_SERVICE_URL` | 정의되지 않는다(`ee.settings`가 정의하던 값). `posthog/api/id_jag.py`는 `getattr(..., "")`로 읽어 빈 값이 된다. 관리자 조직 화면의 billing 링크는 지웠다 | `posthog/api/id_jag.py`(170행), `posthog/admin/admins/organization_admin.py` |

과금 서비스로 보내는 전송이 없어도 위 "사용량 보고"의 PostHog 클라우드 이벤트는 그대로 나간다.

### 끄는 방법

설정이나 환경변수로 끄는 방법은 찾지 못했다.
멈추는 길은 PostHog 클라우드 프로젝트의 플래그 `disable-usage-reports`(AI 보고는 `llm-analytics-disable-usage-reports`)뿐이고, 이 포크 운영자가 정할 수 없다.
끄려면 코드 수정이 필요하다: `posthog/tasks/scheduled.py`의 두 예약 등록을 지우거나, 두 `get_ph_client`가 꺼진 클라이언트를 돌려주게 바꾼다.

## 서버 텔레메트리 (`posthoganalytics`)

### 초기화

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 전역 설정 | `AppConfig.ready()`가 `posthoganalytics.api_key`(하드코딩 공개 토큰), `super_properties`(지역, 서비스명, 환경), 예외 자동 캡처(`enable_exception_autocapture = True`)를 설정한다. 호스트는 정하지 않아 SDK 기본 호스트로 간다 | `posthog/apps.py:PostHogConfig.ready`(62~92행) |
| 끄기 | `settings.TEST`이거나 `os.environ.get("OPT_OUT_CAPTURE", False)`가 참이면 `posthoganalytics.disabled = True` | `posthog/apps.py:ready`(101~102행) |
| 자기 캡처 | 그 밖에 `DEBUG`이거나 `SELF_CAPTURE`가 참이면 전역 SDK를 끄고 인스턴스 자신으로 보내도록 따로 구성한다. 개발 서버가 `RUN_MAIN=true`로 뜰 때 `development server launched` 이벤트를 별도 클라이언트로 PostHog 쪽에 보낸다 | `posthog/apps.py:ready`(103~133행), `posthog/settings/base_variables.py:SELF_CAPTURE` |
| 플래그 정의 | 전역 SDK가 켜져 있으면 `flag_definition_cache_provider`를 HyperCache로 두고, 정의가 없으면 `load_feature_flags()`를 부른다. 개인 API 키는 환경변수 `POSTHOG_PERSONAL_API_KEY`에서 읽는다. 하비에는 이 키가 없어, 로컬 정의가 없는 플래그는 SDK가 평가할 때마다 `/flags/?v=2`로 원격 요청한다 | `posthog/apps.py:ready`(64~67행, 139~144행), posthoganalytics 7.67.1 `client.py`(`_get_feature_flag_details_from_server` 분기, `request.py:flags`) |
| Celery 안 캡처 | `posthoganalytics.capture()`가 아니라 `ph_scoped_capture`를 쓰라는 저장소 규칙이 있다 | `CLAUDE.md` "Async, storage and outbound calls" |

### `OPT_OUT_CAPTURE`의 실제 의미

같은 변수를 두 가지로 읽는다.

| 읽는 곳 | 해석 | 값이 문자열 `"false"`일 때 |
| --- | --- | --- |
| `posthog/apps.py:ready`(101행), `posthog/ph_client.py:get_client`(231행), `posthog/api/user.py:redirect_to_site`(2149행) | 원시 환경변수. 비어 있지 않은 아무 문자열이면 참 | 끈다 |
| `posthog/settings/base_variables.py:OPT_OUT_CAPTURE`(56행) → 템플릿 컨텍스트 `opt_out_capture`(`posthog/utils.py:_build_template_context`, 520행) | `str_to_bool`. `y`·`yes`·`t`·`true`·`on`·`1`만 참 | 끄지 않는다 |

`docker-compose.hobby.yml:183`은 `web`에 `OPT_OUT_CAPTURE: ${OPT_OUT_CAPTURE:-false}`를 준다.
그래서 하비 기본 설치의 `web`은 서버 SDK가 꺼지고(문자열 `"false"`), 브라우저 로더는 켜진다(`str_to_bool("false")`는 거짓).
`.env`에 `OPT_OUT_CAPTURE=true`를 넣으면 `web`의 서버 SDK와 `head.html`의 브라우저 로더가 꺼진다.
다만 앱 페이지가 따로 만드는 툴바 posthog-js 인스턴스는 남는다(아래 "`head.html` 차단을 거치지 않는 경로").

### 프로세스별로 받는 값

| 하비 서비스 | `OPT_OUT_CAPTURE`를 받는가 | 전역 SDK | 근거 |
| --- | --- | --- | --- |
| `web` | 받음 | 기본 설치에서 꺼짐 | `docker-compose.hobby.yml:183` |
| `worker` (Celery 작업자와 beat) | 받지 않음 | 켜짐 | `docker-compose.hobby.yml:95~155`, `docker-compose.base.yml:358~370`(`env_file: .env.services`) |
| `temporal-django-worker` | 받지 않음 | 켜짐 | `docker-compose.hobby.yml:505~559`, `docker-compose.base.yml:841~847` |
| `asyncmigrationscheck`, `migrate` | 받지 않음 | 돌지 않음. base가 두 서비스에 `deploy.replicas: 0`을 준다(763·770행). `migrate`는 하비 compose에 없다 | `docker-compose.hobby.yml:458~466`, `docker-compose.base.yml:755~773` |
| `web`의 시작 스크립트(`compose/start` → `./bin/migrate`) | 받음(`web` 컨테이너 안) | 기본 설치에서 꺼짐. no-op 비동기 마이그레이션을 여기서 마친다(`run_async_migrations --complete-noop-migrations`) | `bin/deploy-hobby`(207~212행), `bin/migrate`(213행) |

`.env.services`에도 `OPT_OUT_CAPTURE`는 없다.
docker compose는 `.env`를 변수 치환에만 쓰므로, `.env`에 넣어도 `web` 밖의 서비스에는 닿지 않는다.
켜진 프로세스에서는 하드코딩 공개 토큰으로 서버 이벤트, 자동 캡처한 예외(`apps.py:70`), 원격 플래그 평가가 나간다.
워커에서도 끄려면 compose 파일의 해당 서비스 `environment`에 값을 더해야 한다(코드 수정 필요).

### 원격 플래그가 정하는 동작

서버 SDK가 켜진 프로세스는 PostHog 클라우드 프로젝트의 플래그 값을 물어본다. 그 값이 포크의 동작을 바꾼다.

| 플래그 | 정하는 것 | 근거 |
| --- | --- | --- |
| `disable-usage-reports`, `llm-analytics-disable-usage-reports` | 사용량 보고 중단 | 위 "사용량 보고" |
| `login-from-new-device-notification` | 새 기기 로그인 메일 발송. 켜지면 메일을 보낸 뒤 `get_client()`로 `login notification sent` 이벤트에 `ip_address`, `geoip_country`, `geoip_city`, `short_user_agent`, `login_method`를 담아 보낸다. 메일 설정이 없으면 플래그를 묻기 전에 끝난다. 클라우드 쪽 플래그 값은 미확인 | `posthog/tasks/email.py:login_from_new_device_notification`(1851~1910행) |
| `mcp-registry` | MCP 레지스트리 크롤링과 서버 탐침. 평가가 실패하거나 SDK가 꺼져 있으면 꺼진다 | `products/mcp_registry/backend/tasks/tasks.py:is_pipeline_enabled`(23~35행) |

### `get_client()`와 `ph_scoped_capture`

`posthog/ph_client.py:get_client`(214~249행)는 지역이 `US`·`EU`면 늘 클라이언트를 만든다. `disabled`는 원시 `OPT_OUT_CAPTURE`로 정한다(231행).
`ph_scoped_capture`가 돌려주는 `ScopedCapture.__call__`은 `is_cloud()`일 때만 보낸다(121~123행). 그래서 하비에서 `ph_scoped_capture`는 보내지 않는다.
`get_client()`를 직접 쓰는 곳은 이 검사가 없다.

| 위치 | 보내는 것 | 클라우드 검사 |
| --- | --- | --- |
| `posthog/tasks/email.py:login_from_new_device_notification`(1899행) | `login notification sent`와 IP·위치 정보 | 없음(플래그가 켜져야 실행) |
| `posthog/temporal/weekly_digest/activities.py`(1045행) | 주간 요약 `transactional email` 이벤트. `organization_name`, `organization_id`, 팀별 요약 내용, 사용자 `distinct_id` | 없음. 예약은 `posthog/temporal/schedule.py:create_weekly_digest_schedule`로 조건 없이 등록되지만, 큐가 `weekly-digest-task-queue`라 하비 `temporal-django-worker`(기본 `general-purpose-task-queue`, `posthog/settings/temporal.py:276`)가 처리하는지는 미확인 |
| `products/warehouse_sources/backend/tasks/tasks.py:validate_data_warehouse_table_columns`(147행) | `distinct_id=team_id`로 성공·실패 이벤트 | 없음 |
| `products/surveys/backend/desktop_feedback.py:_capture_feedback_event`(159행) | desktop 피드백을 `survey sent`로 보냄 | 없음(사용자가 피드백을 보낼 때) |
| `products/signals/dags/inbox_ranking/training/telemetry.py`(330행) | 학습 텔레메트리 | 있음(`is_cloud() or DEBUG`, 310행) |
| `products/workflows/backend/services/data_suggestions/service.py`(472행) | 데이터 제안 이벤트 | 있음(`is_cloud()`) |
| `products/posthog_ai/eval_harness/harness/lifecycle.py`(308·313행) | 평가 도구. 313행은 `disabled=False`를 직접 준다 | 개발 도구, 운영 경로 아님 |
| `products/growth/backend/management/commands/backfill_*.py` | 관리 명령 | 운영자가 직접 실행할 때만 |

### 보내는 대표 이벤트 (전역 클라이언트)

전부를 세지는 않았다. 개인정보나 조직 정보가 담기는 것 위주로 적는다.

| 이벤트 | 담기는 내용 | 실행 위치 | 근거 |
| --- | --- | --- | --- |
| `Async migration start`, `Async migration completed` 등 | 마이그레이션 이름, 첫 활성 사용자의 현재 조직명(`organization_name`), `groups={"instance": SITE_URL, "organization": ...}`, `distinct_id=get_machine_id()` | UI에서 시작한 마이그레이션은 Celery `worker`에서 돈다(`OPT_OUT_CAPTURE` 못 받음, `posthog/async_migrations/utils.py:trigger_migration`). 시작 때 `web`이 마치는 no-op 마이그레이션의 `Async migration completed`는 `web`에서 나가므로 기본 설치에서 꺼짐 | `posthog/async_migrations/utils.py:send_analytics_to_posthog`(35~42행), 호출 `runner.py:53`, `utils.py:213`, `utils.py:298` |
| `user signed up` | 가입 경로, 역할, 유입 경로 자유 입력, `$set`에 `get_analytics_metadata()`(이메일은 `anonymize_data`가 아닐 때), `instance_url` | 요청을 받은 프로세스(하비 기본 `web`은 꺼짐) | `posthog/event_usage.py:report_user_signed_up`(35~90행), `posthog/models/user.py:get_analytics_metadata` |
| `report_user_action`이 보내는 이벤트 | `$set_once`에 사용자 이메일. 이 함수는 `anonymize_data`를 보지 않는다 | 같음 | `posthog/event_usage.py:report_user_action`(644~653행) |
| 그룹 | `groups()`가 `instance`(SITE_URL), `organization`, `project`(팀 UUID)를 붙인다 | 같음 | `posthog/event_usage.py:groups`(751~763행) |

### `OPT_OUT_CAPTURE`를 켠 뒤에도 남는 경로

- 사용량 보고 두 가지(별도 클라이언트, 위 절).
- `web` 밖의 프로세스(compose가 값을 넘기지 않음).
- 툴바 인증 페이지, 고객 사이트의 툴바, 앱 페이지가 만드는 툴바 인스턴스(아래 "브라우저 텔레메트리").
- 기본 제3자 자원, 커뮤니티 스킬 동기화, 하비 스크립트, desktop 앱 업데이트 확인.

## 브라우저 텔레메트리 (`posthog-js`)

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 호스트와 토큰 | 기본 분기는 `POSTHOG_JS_CLOUD_HOST` = `https://internal-cf.posthog.com`와 하드코딩 공개 토큰, `ui_host`는 `https://us.posthog.com` | `posthog/constants.py:POSTHOG_JS_CLOUD_HOST`(410행), `posthog/utils.py:_build_template_context`(577~580행) |
| 분기 | E2E 테스트면 고정 토큰, `SELF_CAPTURE`면 `js_posthog_host`를 빈 문자열로 둬 자기 자신으로 보낸다. 그 밖의 모든 인스턴스는 위 클라우드 호스트 | `posthog/utils.py:_build_template_context`(554~580행) |
| 서버 쪽 차단 | `head.html`은 `{% if not opt_out_capture and js_posthog_api_key %}`일 때만 설정 블록을 넣는다. `opt_out_capture`는 `str_to_bool`로 읽은 `settings.OPT_OUT_CAPTURE` | `posthog/templates/head.html`(44행), `posthog/utils.py`(520행) |
| 초기화 | `window.JS_POSTHOG_API_KEY`가 있을 때만 `posthog.init(...)`. 세션 녹화(`streamNetworkBody: true`), 예외 캡처, 네트워크 메트릭, 자동 캡처(복사한 텍스트 포함), `person_profiles: 'always'`를 켠다 | `frontend/src/loadPostHogJS.tsx:loadPostHogJS`(69~215행) |
| 옵트아웃 | 가장한 세션(`IMPERSONATED_SESSION`)이면 `opt_out_capturing()`, 아니면 `opt_in_capturing()` | 같은 함수(94·110~112행) |
| 키 없음 | 키가 없으면 `fake_token`으로 초기화하고 `advanced_disable_flags: true`, `opt_out_capturing_by_default: true`. 이때 브라우저 요청이 실제로 없어지는지는 실행해 보지 않았다(미확인) | 같은 파일(232~245행) |
| 보내는 데이터 | 로그인하면 `posthog.identify(user.distinct_id)`, `people.set({email, realm})`(이메일은 `anonymize_data`면 `null`), `group('project', ...)`에 프로젝트 이름·UUID·시간대, `group('organization', ...)`에 조직 이름·슬러그·생성일·구성원 수·프로젝트 수·조직 메타데이터, `customer_id`가 있으면 `group('customer', ...)`. 여기에 자동 캡처 이벤트와 세션 녹화가 더해진다 | `frontend/src/scenes/userLogic.ts`(742~781행), `loadPostHogJS.tsx` |
| 공유·임베드 페이지 | 공개 공유 링크와 임베드(`exporter`), 쿼리 렌더 페이지도 `head.html`을 넣고 `loadPostHogJS()`를 부른다. 로그인하지 않은 열람자도 같은 클라우드 프로젝트로 추적된다 | `frontend/src/exporter/index.html`(`{% include "head.html" %}`), `frontend/src/exporter/index.tsx`(21행), `frontend/src/render-query/index.tsx`(16행) |
| 원격으로 제어되는 것 | 플래그와 원격 설정을 클라우드 프로젝트에서 받는다. `opt_in_site_apps: true`라 클라우드 프로젝트가 정한 site app 스크립트가 포크 UI에 실릴 수 있고, `disable_surveys`는 가장한 세션에서만 참이라 클라우드 설문이 뜰 수 있다. 실제로 무엇을 내려받아 실행하는지는 SDK 동작이라 미확인 | `loadPostHogJS.tsx`(90~92행) |
| 플래그 게이트 | 자체 호스팅(클라우드도 디버그도 자기 캡처도 아님)에서는 `featureFlagLogic`이 posthog-js가 받은 플래그 값을 버리고 서버가 넘긴 목록만 쓴다. 그 목록은 환경변수 `PERSISTED_FEATURE_FLAGS`에, 서버 SDK가 로컬 HyperCache에서 읽은 플래그 정의 중 조건 없이 100% 배포된 것을 더한 것이다. 하비 기본 설치의 `web`은 서버 SDK가 꺼져 있어 환경변수 목록만 남는다. 그래서 대부분의 UI 게이트는 클라우드가 정하지 못한다. 예외로 `posthog.getFeatureFlag()`를 직접 읽는 곳(예: `frontend/src/lib/holidays.tsx`, `frontend/src/products.tsx:511`)은 클라우드 값을 쓴다. 처음 호출된 플래그마다 `$feature_flag_called` 이벤트를 보낸다 | `frontend/src/lib/logic/featureFlagLogic.ts:areClientFeatureFlagsHonored`, `spyOnFeatureFlags`, `notifyFlagIfNeeded`, `posthog/settings/feature_flags.py:PERSISTED_FEATURE_FLAGS`, `posthog/utils.py:get_persisted_feature_flags_for_app_context`, `_build_flag_provider`, `products/feature_flags/backend/persisted_flags.py:get_dynamic_persisted_feature_flags` |

### `head.html` 차단을 거치지 않는 경로

| 경로 | 동작 | 근거 | 끄는 방법 |
| --- | --- | --- | --- |
| 툴바 인증 페이지 | `layout.html`이 `head.html`을 넣은 뒤, `opt_out_capture`를 보지 않고 따로 `posthog.init(js_posthog_api_key, ...)`을 부른다. 기본 분기에서는 `https://internal-cf.posthog.com/static/1/array.js`를 외부 스크립트로 넣는다. 같은 파일이 `https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css`를 불러온다. 이 레이아웃은 `authorize_and_redirect.html`, `authorize_and_link.html`이 쓰고 `posthog/api/oauth/toolbar_views.py`(64~72행)가 렌더한다 | `frontend/src/layout.html`(7~26행) | 코드 수정 필요 |
| 고객 사이트의 툴바 | PostHog 앱 밖(`window.POSTHOG_APP_CONTEXT`가 없는 페이지)에서 돌면 하드코딩 `DEFAULT_API_KEY`와 `https://internal-cf.posthog.com`으로 초기화한다. `instrument`가 참이면 `opt_in_capturing()`, `identify(distinctId, {email})`, `toolbar loaded` 이벤트를 보낸다 | `frontend/src/toolbar/toolbarPosthogJS.ts`(6~45행), `frontend/src/toolbar/toolbarConfigLogic.ts:initInstrumentation`(701~725행) | 코드 수정 필요 |
| 앱 페이지의 툴바 인스턴스 | 웹 앱이 툴바 모듈을 import해서 앱 페이지마다 이 인스턴스가 만들어진다(`toolbarPosthogJS.ts:22~23` 주석). 앱 안에서는 `window.JS_POSTHOG_API_KEY`와 `window.JS_POSTHOG_HOST`를 쓴다. `OPT_OUT_CAPTURE`가 참이면 `head.html`이 이 둘을 넣지 않으므로(`POSTHOG_APP_CONTEXT`는 그대로 넣는다) 키는 `DEFAULT_API_KEY`가 되고, 호스트는 SDK 기본값 `https://us.i.posthog.com`이 된다. `opt_out_capturing_by_default`라 이벤트는 보내지 않는다. 그러나 posthog-js 1.438.8은 초기화 끝에 동의 여부와 상관없이 원격 설정(`/array/<토큰>/config.js`)을 요청하고, `advanced_disable_flags`일 때만 건너뛴다. 이 인스턴스는 그 값을 주지 않는다. 브라우저로 실행해 확인하지는 않았다 | `frontend/src/toolbar/toolbarPosthogJS.ts`(6~45행), `posthog/templates/head.html`(44·72~74행), posthog-js 1.438.8 `dist/module.js`의 원격 설정 로더 | 코드 수정 필요(`advanced_disable_flags: true`를 주거나, 키가 없으면 초기화하지 않음) |
| 툴바 실행 경로별 `instrument` | 서버 경로 `redirect_to_site`는 원시 `OPT_OUT_CAPTURE`가 비어 있을 때만 `instrument`와 이메일을 넣는다(하비 기본 설치에서는 넣지 않음). 앱의 실행 링크 `directToolbarUrl`과 실행 코드 복사 `copyLaunchCode`는 늘 `instrument: true`와 사용자 이메일을 넣는다 | `posthog/api/user.py:redirect_to_site`(2149~2152행), `frontend/src/lib/components/AuthorizedUrlList/authorizedUrlListLogic.ts:directToolbarUrl`(180~201행), `copyLaunchCode`(673~682행) | 코드 수정 필요 |

## 기본으로 요청하는 제3자 자원 (브라우저)

아래는 기능을 켜지 않아도 화면을 열면 나가는 요청이다.

| 대상 | 동작 | 근거 | 끄는 방법 |
| --- | --- | --- | --- |
| Gravatar | 이메일을 소문자로 바꿔 md5를 구하고 `https://www.gravatar.com/avatar/<해시>?s=96&d=404`를 아바타마다 요청한다. 사용자가 헤지호그를 프로필로 고른 때만 건너뛴다. 인스턴스 설정은 없다 | `frontend/src/lib/utils/gravatar.ts:gravatarUrl`(5~9행), `frontend/src/lib/lemon-ui/ProfilePicture/ProfilePicture.tsx`(54~63행) | 코드 수정 필요 |
| Cloudinary (`res.cloudinary.com/dmukukwp6`, PostHog 계정) | 온보딩 SDK 목록, 인사이트 빠른 시작, AI observability 아이콘, CDP·워크플로 템플릿 아이콘 등의 이미지. 집계: 18개 파일 83줄, 그중 `frontend/src/scenes/onboarding/sdks/allSDKs.tsx` 37줄 | 명령: `git grep -c 'res.cloudinary.com/dmukukwp6' -- frontend/src products posthog ':!*test*' ':!*.stories.*' ':!frontend/src/mocks' ':!*__mocks__*'` | 코드 수정 필요 |
| `posthog.com` | 500 오류 페이지마다 `https://posthog.com/service-error`를 iframe으로 넣는다. 같은 페이지가 `head.html`도 넣는다 | `posthog/templates/500.html`(18행) | 코드 수정 필요 |
| Bootstrap CDN | 툴바 인증 페이지 | 위 표 `layout.html` | 코드 수정 필요 |

## 프런트엔드 외부 origin (CSP)

`CSPMiddleware`가 HTML 응답마다 정책을 만든다.
하비(자체 호스팅)에서는 앱 정책을 `Content-Security-Policy-Report-Only`로 보낸다. 브라우저는 위반을 막지 않는다. 하비는 `CSP_REPORT_ENDPOINT`가 비어 있어 `report-uri`도 붙지 않으므로, 위반은 어디로도 보고되지 않고 브라우저 콘솔에만 남는다. 강제되는 것은 `frame-ancestors`뿐이다.
그래서 자체 호스팅에서 CSP는 외부 호출을 막는 장치가 아니다. 아래 목록은 "허용하는 범위"로만 읽는다.

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 헤더 종류 | 하비면 report-only, 그 밖(클라우드, E2E, `DEBUG`로 도는 자체 호스팅의 `LOCAL` 모드)은 강제. 토큰 없는 `/exporter`와 `/external_surveys/<id>`는 어디서나 report-only다(`REPORT_ONLY_ROUTES`, 103행, `fullmatch`). 공유 페이지 `/exporter/<token>`은 여기에 들지 않는다 | `posthog/csp_middleware.py:app_csp_header_name`(123~130행), 503~505행 |
| PostHog 와일드카드 | `resource_url = "https://*.posthog.com"`(DEBUG·TEST·`.dev.posthog.dev`가 아닐 때). 이 값이 `style-src`, `script-src`, `font-src`, `img-src`, `connect-src`에 들어간다. 좁힌 정책은 `is_cloud()`일 때만 쓴다. 이 포크 도메인으로 바꾸려면 292행을 고쳐야 한다 | 같은 파일 292·322·346·352·391·393·419행 |
| `script-src` | `'self'`, nonce, `'wasm-unsafe-eval'`, PostHog 와일드카드, `https://*.i.posthog.com`, `https://js.stripe.com`, `https://challenges.cloudflare.com`, `https://editor.unlayer.com/embed.js`. `unsafe-eval`은 없다 | 346행 |
| `style-src` | `'self'`, `'unsafe-inline'`, PostHog 와일드카드, `https://fonts.googleapis.com` | 322행 |
| `font-src` | `'self'`, `data:`, PostHog 와일드카드, `https://app-static.eu.posthog.com`, `https://app-static-prod.posthog.com`, `https://fonts.gstatic.com` | 352행 |
| `img-src` | `https:` 전체, PostHog 와일드카드, `https://posthog.com`, `https://www.gravatar.com`, `https://res.cloudinary.com`, `https://platform.slack-edge.com`, `https://raw.githubusercontent.com` | 391행 |
| `media-src` | `'self'`, `data:`, `blob:`, `https://res.cloudinary.com` | 374행 |
| `connect-src` | `'self'`, `https://www.posthogstatus.com`, PostHog 와일드카드, `https://raw.githubusercontent.com/PostHog/terminal-assets/`, 개체 저장소 주소 | 393행 |
| `connect-src`의 터미널 자산 | 터미널 장면이 `terminal-packages.json`의 `baseUrl`(20·33·101·104행)에서 Node.js, pi, Doom(Freedoom), Neovim 등의 패키지를 내려받는다. 메뉴는 `FEATURE_FLAGS.POSTHOG_TERMINAL`(`posthog-terminal`)로 가린다. 자체 호스팅에서는 이 게이트가 클라우드 값이 아니라 `PERSISTED_FEATURE_FLAGS`를 따른다. 내려받는 구성요소의 라이선스는 [licenses.md](licenses.md)의 "잠금 파일 밖 제3자 구성요소"를 본다 | `frontend/src/scenes/terminal/terminal-packages.json`, `terminalPackages.ts`(46~56행), `terminalRuntime.ts`(30행), `frontend/src/scenes/AuthenticatedShell.tsx`(91행), `frontend/src/lib/constants.tsx`(180행) |
| `frame-src` | `'self'`, `https:` 전체 | 396행 |
| `form-action` | `'self'`, `https://accounts.google.com` | 406행 |
| `frame-ancestors` | `'self'`, `https://posthog.com`, `https://preview.posthog.com`. 자체 호스팅에서도 이 두 PostHog 도메인이 앱을 프레임으로 넣을 수 있다 | `app_frame_ancestor_sources`(110~120행) |
| 관리자 화면 | `frame-src https://posthog.com`, 글꼴 `https://fonts.gstatic.com` | 249·262행 |
| 위반 보고 | `CSP_REPORT_ENDPOINT`가 없으면 `is_cloud()`일 때만 PostHog로 보고한다. 하비 compose는 빈 값을 넘겨 보고하지 않는다 | `csp_report_endpoint`(20~28행), `docker-compose.hobby.yml`(`CSP_REPORT_ENDPOINT: ${CSP_REPORT_ENDPOINT:-}`) |

CSP를 바꾸려면 코드 수정이 필요하다. 이 포크 도메인을 쓰려면 같은 PR에서 해당 지시어를 넓혀야 한다(`CLAUDE.md` "Security").

## 예약 작업이 받아 오는 외부 데이터

| 작업 | 동작 | 근거 | 끄는 방법 |
| --- | --- | --- | --- |
| 커뮤니티 스킬 카탈로그 | 매시 20분에 `sync_community_skills`를 등록한다. `https://raw.githubusercontent.com/PostHog/community-skills/main/registry.json`을 `posthog/egress/` GitHub 전송으로 받아 DB의 `CommunitySkill` 카탈로그에 반영하고, 목록에 없는 항목은 지운다(soft delete). 조건은 없다. 제3자 저장소의 내용이 매시간 이 포크 DB로 들어온다 | `posthog/tasks/scheduled.py`(703~709행), `products/skills/backend/tasks.py:sync_community_skills`, `products/skills/backend/api/community_skill_sync.py:sync_community_skills_from_github`(287행~, 주소 69~73행) | 설정을 찾지 못함(`posthog/egress/`에 끄는 설정 없음). 코드 수정 필요(예약 등록 제거) |
| MCP 레지스트리 | 매일 `run_mcp_registry_sync`를 등록한다. 플래그 `mcp-registry`가 켜지면 `https://registry.modelcontextprotocol.io/v0/servers`를 크롤링하고 등록된 서버를 탐침한다 | `posthog/tasks/scheduled.py`(1219~1223행), `products/mcp_registry/backend/constants.py:OFFICIAL_REGISTRY_BASE_URL`, `crawl.py`(46행), `probe.py:probe_stalest_servers` | 워커의 서버 SDK를 끄면 플래그 평가가 실패해 꺼진다 |

## 하비(자체 호스팅) 설치 스크립트

이 스크립트들은 이 포크가 아니라 업스트림 PostHog를 설치한다. 판매 전에 바꿔야 할 기본값이다.

| 위치 | 호출 | 비고 |
| --- | --- | --- |
| `bin/deploy-hobby`(70~76행) | `curl`로 `https://us.i.posthog.com/batch/`에 `magic_curl_install_start` 이벤트. 하드코딩 공개 토큰, `distinct_id`와 속성에 입력한 도메인 | 설치 시작 때 도메인이 PostHog로 간다 |
| `bin/deploy-hobby`(306~314행) | 상태 확인이 통과하면 같은 곳으로 `magic_curl_install_complete` | 설치 완료 때 |
| `bin/hobby-installer/core/telemetry.go:SendInstallStartEvent`, `SendInstallCompleteEvent` | Go 설치기도 `posthog-go`로 같은 엔드포인트에 같은 두 이벤트를 보낸다(`install.go` 41·213행) | 끄는 설정 없음. `OPT_OUT`·`DO_NOT_TRACK` 검색 결과 없음 |
| `bin/deploy-hobby`(87행), `bin/hobby-installer/core/git.go:posthogRepoURL`(11행) | `https://github.com/PostHog/posthog.git`을 clone한다. `bin/upgrade-hobby`(357행)는 그 checkout에서 `git pull`한다 | 업스트림 코드와 compose 파일을 받는다 |
| `bin/deploy-hobby`(10·127~130행), `bin/upgrade-hobby`(14~19·252행), `bin/hobby-installer/core/env.go`(48~50행) | `REGISTRY_URL`이 비면 Docker Hub `posthog/posthog`, 태그 기본값은 `latest`(업그레이드 후반은 `latest-release`) | 업스트림 이미지가 돈다 |
| `docker-compose.base.yml`(379~748행), `docker-compose.hobby.yml`(734·778행) | Rust·Go 서비스 12개(`capture`, `capture-logs`, `replay-capture`, `property-defs-rs`, `property-defs-ai`, `livestream`, `personhog-replica`, `personhog-router`, `feature-flags`, `hypercache-server`, `cymbal`, `cymbal-resolution`)는 `ghcr.io/posthog/posthog/<이름>:master` 이미지를 받는다. 주소가 하드코딩이라 `REGISTRY_URL`로 바뀌지 않고, 태그 `master`는 고정 버전이 아니다 | 업스트림 이미지가 돈다 |
| `bin/deploy-hobby`(178행), `docker-compose.hobby.yml` `proxy` | Caddy가 `$DOMAIN`을 맡는다. 인증서를 ACME로 자동 발급하는 것은 Caddy 기본 동작이다(저장소 밖 동작, 미확인). 세 번째 인자를 주면 `acme_ca`를 Let's Encrypt staging으로 바꾼다(124행) | 제3자 인증 기관 |
| `bin/deploy-hobby`(344행) | 업그레이드 명령으로 `raw.githubusercontent.com/posthog/posthog/HEAD/bin/upgrade-hobby`를 안내한다 | 업스트림 스크립트 |
| `bin/deploy-hobby`(18·32행) | 안내 문구에 `posthog.com` 문서와 Docker Hub 태그 주소 | 출력만 |
| `bin/deploy-hobby`(196행), `bin/upgrade-hobby`(374행), `bin/hobby-installer/core/geoip.go:geoIPURL`(11행) | `https://mmdbcdn.posthog.net/`에서 GeoLite2 City 파일 | 도메인이 `posthog.net` |
| `bin/download-mmdb`(17행), `Dockerfile`(288행) | 같은 호스트 | 이미지 빌드·개발 환경 |
| `bin/deploy-hobby`(249~250·260행), `bin/upgrade-hobby`(383행), `bin/hobby-installer/core/docker.go`(83~114행) | Docker GPG 키와 저장소, `docker-compose` 릴리스를 `download.docker.com`, `github.com`에서 | 제3자 |
| `bin/hobby-installer/core/checks.go`(166행) | 연결 확인으로 `https://github.com`에 `curl` | 제3자 |

## desktop 앱 (`products/desktop`)

| 항목 | 내용 | 근거 | 끄는 방법 |
| --- | --- | --- | --- |
| 업데이트 피드 | `electron-builder`의 `publish`가 `provider: "generic"`, `url: "https://desktop-releases.posthog.com/stable"`이다. 이 설정으로 만든 설치본은 이 피드를 확인한다 | `products/desktop/apps/code/electron-builder.ts`(166~171행) | 피드 주소는 코드 수정 필요 |
| 확인 시점 | `isSupported()`가 참이면 시작 때 한 번, 그 뒤 1시간마다 `autoUpdater.checkForUpdates()`를 부른다 | `products/desktop/apps/code/src/main/platform-adapters/electron-updater.ts:check`(75행), `products/desktop/packages/core/src/updates/updates.ts`(53·119~133·439~443행) | |
| 켜지는 조건 | 패키징된 빌드(`app.isPackaged`), macOS 또는 Windows, `ELECTRON_DISABLE_AUTO_UPDATE`가 없을 때 | `electron-updater.ts:isSupported`(66~72행) | 환경변수 `ELECTRON_DISABLE_AUTO_UPDATE` |
| 텔레메트리 | 메인 프로세스는 `process.env.VITE_POSTHOG_API_KEY`가 없으면 클라이언트를 만들지 않는다. 기본 호스트는 `https://internal-c.posthog.com`. 값은 빌드 때 Vite가 박는다. 렌더러도 같은 키로 `posthog-js`를 초기화한다 | `apps/code/src/main/platform-adapters/posthog-analytics.ts:initialize`(14~31행), `apps/code/vite.main.config.mts`(662~667행), `packages/ui/src/shell/posthogAnalyticsImpl.ts`(179~200행 부근) | 빌드 때 키를 넣지 않음. 이 저장소 `.github`에서 이 키를 넣는 워크플로는 찾지 못했다 |
| Gravatar | 이메일의 SHA-256으로 `https://www.gravatar.com/avatar/<해시>?s=<크기>&d=404`를 만든다 | `products/desktop/packages/ui/src/features/auth/useGravatarUrl.ts:gravatarUrlForEmail`(10~21행) | 코드 수정 필요 |
| 그 밖 | 모바일 앱(`apps/mobile`, `apps/mobilehog`)은 로그인 지역 주소로 PostHog 클라우드(`us.posthog.com`, `eu.posthog.com`, `mcp-eu.posthog.com`)를 쓴다. desktop·모바일 앱의 외부 호출 전수 조사는 하지 않았다(미확인) | `apps/mobile/src/features/auth/lib/constants.ts`(32~34행), `apps/mobilehog/src/config.ts`(17행), `apps/mobilehog/src/lib/oauth.ts`(15행) | |

desktop 앱의 배포 식별자와 서명 신원은 [branding.md](branding.md)를 본다.

## 업데이트 확인

서버(Django)가 설치된 버전을 PostHog 서버에 물어보는 코드는 찾지 못했다.
검색한 이름: `check_for_updates`, `latest_version`, `version_check`, `UPDATE_CHECK`, `get_latest_version`. 매치는 테스트와 SDK 상태 API(`posthog/api/sdk_health.py`, SDK 버전이며 PostHog 자체 업데이트 확인이 아님)뿐이었다.
desktop 앱은 PostHog 업데이트 피드를 확인한다(위 절).
`releases.posthog.com`은 PostHog CLI 설치 스크립트와 릴리스 산출물 주소다(`cli/README.md`, `cli/CHANGELOG.md`). 서버가 부르는 호출이 아니라 사용자가 CLI를 설치할 때 쓰는 주소다.

## Rust 서비스

| 위치 | 호출 | 기본 동작 |
| --- | --- | --- |
| `rust/common/posthog/src/lib.rs` | 서비스 내부 텔레메트리. 전역 클라이언트 초기화와 `$exception` 수동 캡처(프로세스당 분당 10건 상한). `api_key`가 없으면 `disable_global()`을 부르고 클라이언트를 만들지 않는다(62~66행) | 키 없으면 꺼짐 |
| `rust/cymbal/src/modes/processing/config.rs`(28~31행), `notifications/config.rs`(29~32행), `resolution/config.rs`(22~25행), `rust/embedding-worker/src/config.rs`(16~19행) | `posthog_api_key: Option<String>`은 기본값이 없다. `posthog_endpoint` 기본값은 `https://us.i.posthog.com/capture`. 세 cymbal 모드와 embedding-worker가 같은 내부 캡처 엔드포인트를 쓴다 | 키 없으면 꺼짐(기본) |
| `rust/cymbal/src/core/types/langs/js.rs`(190행 부근) | PostHog 자산 호스트를 판별하는 문자열. 호출이 아니다 | 해당 없음 |

하비 compose와 `.env.services`는 `POSTHOG_API_KEY`를 넣지 않는다.

## Node.js 서비스

| 위치 | 동작 | 기본 동작 |
| --- | --- | --- |
| `nodejs/src/common/utils/posthog.ts`(9~14행), `nodejs/src/common/config.ts`(476~477행) | `POSTHOG_API_KEY` 기본값이 `''`이라 클라이언트를 만들지 않는다. 호스트 기본값은 `http://localhost:8010` | 키 없으면 꺼짐(기본) |
| `nodejs/src/ingestion/pipelines/sessionreplay/ml-mirror-image-fetch/` | 이미지 크롤러다. README에 따르면 AI 학습을 켠 조직의 세션 리플레이에 나온 외부 이미지를 내려받아 정제 단계로 넘긴다. 요청마다 `user-agent: PostHogImageFetcherBot/1.0 (+https://posthog.com/docs/ai-research/image-fetcher-bot)`, `referer: https://us.posthog.com/`을 보내고(`request-identity.ts` 1~7행), Web Bot Auth 서명의 Signature-Agent로 `https://us.posthog.com/.well-known/http-message-signatures-directory`를 쓴다(`web-bot-auth.ts` 3행). 포크가 이 모드를 그대로 돌리면 PostHog 크롤러로 자신을 밝힌다 | 전용 서버 모드(`nodejs/src/servers/ingestion-session-replay-ml-image-fetch-server.ts`)다. 하비 compose의 `PLUGIN_SERVER_MODE` 목록에 없어 하비에서는 돌지 않는다 |

이 신원 문자열은 [branding.md](branding.md)의 밖으로 나가는 신원 문자열과 함께 본다.

## PostHog 클라우드 API와 기타 `posthog.com` 호스트

| 호스트 | 쓰임 | 위치 |
| --- | --- | --- |
| `us.posthog.com`, `eu.posthog.com`, `app.posthog.com` | 리전 리다이렉트, CORS 허용, OAuth 클라이언트 메타데이터, 교차 리전 API | `posthog/frontend_views.py`, `posthog/utils_cors.py`, `posthog/regions.py`, `posthog/api/oauth/views.py`, `posthog/settings/integrations.py` (`POSTHOG_CONNECT_BASE_URL_US`) |
| `us.i.posthog.com/flags?v=2` | 플래그 정의를 동기화하는 관리 명령 | `posthog/management/commands/sync_feature_flags_from_api.py` |
| `us.posthog.com` | 사용자 설정 동기화 관리 명령 | `posthog/management/commands/sync_user_settings.py` |
| `app.posthog.com/batch` | 팀 이전 관리 명령 | `posthog/management/commands/migrate_team.py` |
| `us.i.posthog.com`(SDK 기본 호스트) | Helm 설치 알림 관리 명령. 하드코딩 공개 토큰으로 `helm_install` 이벤트를 보낸다. 보내기 전에 `posthoganalytics.disabled`를 `False`로 바꾸므로 `OPT_OUT_CAPTURE`를 무시한다. 이 저장소 안에서 이 명령을 부르는 곳은 없다 | `posthog/management/commands/notify_helm_install.py` |
| `us.i.posthog.com/batch/`, `eu.i.posthog.com/batch/` | 배치 내보내기 HTTP 목적지 허용 목록 | `products/batch_exports/backend/temporal/destinations/http_batch_export.py:172` |
| `mcp.posthog.com` | MCP 리소스 허용 | `posthog/settings/web.py` (1284행 주석), `posthog/api/oauth/mcp_resource_scopes.py` |
| `agent-proxy.us.posthog.com` | 에이전트 프록시 | `posthog/settings/access.py` (137행 주석) |
| `internal-cf.posthog.com` | 브라우저 텔레메트리 호스트 | `posthog/constants.py` |
| 이메일 속 `us.posthog.com` 링크 | 피드백 설문 링크 | `posthog/tasks/email.py` (2809행) |

관리 명령은 운영자가 직접 실행할 때만 나간다. 예약 작업이나 요청 경로에서 자동으로 부르는지는 확인하지 못했다.

## 제3자 API (조건부)

제품 기능이 연동을 켠 팀이나 자격 증명을 넣은 운영자를 위해 호출한다.

| 서비스 | 위치 | 조건 |
| --- | --- | --- |
| GitHub | `posthog/api/github.py:GITHUB_KEYS_URI`(39행, `https://api.github.com/meta/public_keys/secret_scanning`) | GitHub 비밀 스캔 요청을 받을 때 공개 키를 가져온다. `CLAUDE.md`는 GitHub·Slack 호출을 `posthog/egress/`로 보내라고 한다 |
| GitHub, GitLab (레거시 플러그인) | `posthog/plugins/utils.py:parse_github_url`(54~62행, `api.github.com`), `parse_gitlab_url`(123~126행, `gitlab.com/api/v4`), `download_plugin_archive`(206행~) | 플러그인을 URL로 설치할 때 |
| Slack (팀 연동) | `posthog/models/integration/slack.py`(100행 `WebClient`), `products/conversations/backend/slack.py`(208행), `products/slack_app/backend/services/slack_user_oauth.py`(328행) | 팀이 Slack 연동을 설정했을 때 |
| Slack (내부 피드백) | `posthog/api/internal_feedback.py:create`(133~145행) | `INTERNAL_FEEDBACK_SLACK_BOT_TOKEN`과 채널을 설정했을 때만. 없으면 503 |
| Slack (스레드 미러) | `posthog/helpers/slack_thread_mirror.py:post_comment_to_slack_thread`(89행~) | 호출자가 만든 `WebClient`를 받기만 한다. 자체로 연결하지 않는다 |
| Customer.io (이메일 전송) | `posthog/email.py`(216행 `customerio_api_key`, 252행 `{CUSTOMER_IO_API_URL}/v1/send/email`)와 `posthog/helpers/email_utils.py`(651행 `/v1/esp/search_suppression/`). 설정은 `posthog/settings/email.py`의 `CUSTOMER_IO_API_KEY`(기본 빈 값)와 `CUSTOMER_IO_API_URL`(기본 `https://api.customer.io`)이다. 이전에는 지운 `ee` 설정이 정의했다 | `CUSTOMER_IO_API_KEY`를 넣었을 때만. 비어 있으면 `posthog/email.py:is_email_available`이 거짓이 되어 SMTP를 쓴다 |
| LLM 제공자와 게이트웨이 | 설정은 `posthog/settings/llm.py`의 `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`(기본 `gpt-4.1-mini`), `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `REPLAY_VISION_GEMINI_API_KEY`, `INKEEP_API_KEY`, `LLM_GATEWAY_URL`, `LLM_GATEWAY_API_KEY`다. 이전에는 지운 `ee` 설정이 정의했다 | 키를 넣은 기능만. 키가 비어 있으면 그 기능은 쓸 수 없다고 응답한다. `OPENAI_BASE_URL`로 호스트를 바꿀 수 있다 |
| Stripe | `posthog/settings/integrations.py`, `posthog/settings/payments.py` | 변수 미설정이면 비어 있음 |
| AWS SES | 10분마다 `poll_ses_account_enforcement`를 조건 없이 등록한다. `SESProvider()`가 `SES_ACCESS_KEY_ID`·`SES_SECRET_ACCESS_KEY`(운영 기본값 `None`)와 `SES_REGION`(기본 `us-east-1`)으로 boto3 클라이언트를 만들고 `get_account()`를 부른다. 예외는 잡아서 기록만 한다. 자격 증명이 없을 때 boto3가 실제로 네트워크 요청을 하는지는 SDK 동작이라 미확인 | `posthog/tasks/scheduled.py`(486~492행), `products/workflows/backend/tasks/ses_account_reputation.py:poll_ses_account_enforcement`(56~66행), `products/workflows/backend/providers/ses.py:SESProvider`(284~310·403~410행), `posthog/settings/ses.py` |
| 웹훅·CDP 대상 | `products/cdp/backend/templates/` | 사용자가 정한 URL |

범위가 넓어 전수 조사는 하지 않았다. 외부 서비스 호출 전반은 `posthog/egress/`를 시작점으로 후속 조사가 필요하다(미확인).

## 코드 수정이 필요한 곳

설정만으로 끌 수 없는 경로와, 바꾸려면 코드를 고쳐야 하는 위치다. 이 페이지 작업에서는 고치지 않았다.

| 경로 | 고칠 위치 |
| --- | --- |
| 사용량 보고 두 가지 | `posthog/tasks/scheduled.py`의 `send_org_usage_reports`, `send_ai_observability_usage_reports` 등록, 또는 `posthog/tasks/usage_report.py:get_ph_client`, `posthog/tasks/ai_observability_usage_report.py:get_ph_client` |
| `OPT_OUT_CAPTURE` 해석이 둘로 갈림 | `posthog/apps.py:ready`(101행), `posthog/ph_client.py:get_client`(231행), `posthog/api/user.py:redirect_to_site`(2149행)이 `settings.OPT_OUT_CAPTURE`를 읽게 하거나, compose 기본값을 바꿈 |
| 워커에 `OPT_OUT_CAPTURE`가 닿지 않음 | `docker-compose.hobby.yml`의 `worker`, `temporal-django-worker`, `asyncmigrationscheck`, 또는 `.env.services` |
| 툴바 인증 페이지의 무조건 초기화와 Bootstrap CDN | `frontend/src/layout.html`(9~26행) |
| 고객 사이트 툴바의 하드코딩 키·호스트, 늘 켜는 `instrument`, 앱 페이지 툴바 인스턴스의 원격 설정 요청 | `frontend/src/toolbar/toolbarPosthogJS.ts`(6~45행), `frontend/src/lib/components/AuthorizedUrlList/authorizedUrlListLogic.ts`(193·678행) |
| 브라우저 텔레메트리 기본 목적지 | `posthog/utils.py:_build_template_context`(577~580행), `posthog/constants.py:POSTHOG_JS_CLOUD_HOST`·`POSTHOG_JS_CLOUD_TOKEN` |
| `get_client()` 직접 사용처의 클라우드 검사 없음 | 위 "`get_client()`와 `ph_scoped_capture`" 표의 위치 |
| CSP의 PostHog 와일드카드와 `frame-ancestors` | `posthog/csp_middleware.py`(292행, `app_frame_ancestor_sources` 110~120행) |
| Gravatar, Cloudinary, 500 페이지 iframe | `frontend/src/lib/utils/gravatar.ts`, `ProfilePicture.tsx`, 위 Cloudinary 집계 명령이 찾는 파일, `posthog/templates/500.html` |
| 커뮤니티 스킬 동기화 | `posthog/tasks/scheduled.py`(703~709행) |
| 하비 스크립트 기본값(업스트림 clone, Docker Hub 이미지, 설치 이벤트, 업그레이드 안내 주소) | `bin/deploy-hobby`, `bin/upgrade-hobby`, `bin/hobby-installer/core/git.go`, `env.go`, `telemetry.go` |
| 하비 스택의 `ghcr.io/posthog/posthog/*:master` 이미지 | `docker-compose.base.yml`과 `docker-compose.hobby.yml`의 `image:` 줄 |
| desktop 업데이트 피드 | `products/desktop/apps/code/electron-builder.ts`(166~171행) |
| 이미지 크롤러 신원 헤더 | `nodejs/src/ingestion/pipelines/sessionreplay/ml-mirror-image-fetch/request-identity.ts`, `web-bot-auth.ts` |
| `BILLING_SERVICE_URL` 미정의 | `posthog/admin/admins/organization_admin.py:billing_link`(326행) |

Decided in: buzzhog-gimc, buzzhog-dsv8
