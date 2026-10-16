# 설정·환경변수 레퍼런스

확인 기준 커밋: 8390c1ea200

셀프호스트(hobby) 스택의 환경변수를 서비스별로 정리한다.
배포 절차는 [빌드·배포 런북](runbook.md), 서비스 구성은 [시스템 구성도](architecture.md)를 본다.

Django 설정(`posthog/settings/`)은 환경변수가 약 930곳에서 읽힌다. 전부 옮기지 않았다.
hobby 스택이 실제로 넘기는 값과, 운영자가 알아야 하는 핵심 값을 표로 정리하고, 나머지는 [설정 파일 지도](#설정-파일-지도)로 안내한다.
값은 모두 코드에서 확인했고 근거를 `파일:심볼` 또는 파일 경로로 달았다. Node와 Rust 서비스 내부의 기본값은 읽지 않았다(미확인). 해당 절에서 밝힌다.

공개 저장소이므로 실제 비밀값은 적지 않는다. 표의 "기본값"은 코드에 들어 있는 값이다. 개발용 기본 비밀값은 운영에서 쓰면 안 된다.

## 먼저: 한 번 정하면 바꾸면 안 되는 값

운영 중인 인스턴스에서 이 값을 바꾸면 데이터를 못 읽거나 세션이 끊긴다. 설치 직후 `.env`를 백업한다.

| 변수 | 왜 바꾸면 안 되나 | 바꿔야 할 때 | 근거 |
| --- | --- | --- | --- |
| `SECRET_KEY` (hobby에서는 `.env`의 `POSTHOG_SECRET`) | Django 서명 키다. 바꾸면 세션, CSRF 토큰, 서명된 링크가 무효가 된다. hobby compose가 `SECRET_KEY: $POSTHOG_SECRET`으로 넘긴다 | 이전 값을 `SECRET_KEY_FALLBACKS`(쉼표 구분)에 넣고 새 값으로 바꾼다 | `posthog/settings/access.py:SECRET_KEY`, `SECRET_KEY_FALLBACKS`, `docker-compose.hobby.yml` |
| `ENCRYPTION_SALT_KEYS` | 암호화 필드의 Fernet 키다. 항목 하나가 정확히 32바이트여야 한다. 바꾸면 이미 저장된 암호화 값을 복호화하지 못한다. 쉼표로 여러 키를 줄 수 있다 | 새 키를 목록에 더하는 방식으로만 교체한다. 목록 순서의 의미는 코드에서 확인하지 못했다(미확인) | `posthog/settings/access.py:ENCRYPTION_SALT_KEYS`, `bin/upgrade-hobby` (형식 검사) |
| `SALT_KEY` | 예전 버전 호환용 값이다. 코드 주석이 "레거시, 하위 호환용"이라고 적는다 | 기존 값을 유지한다 | `posthog/settings/access.py:SALT_KEY` |
| `JWT_SIGNING_KEY` | PostHog가 발급한 JWT의 서명 키다. 비우면 `SECRET_KEY`를 쓴다. 바꾸면 이미 발급된 토큰이 무효가 된다 | 이전 값을 `JWT_SIGNING_KEY_FALLBACKS`에 넣는다 | `posthog/settings/access.py:JWT_SIGNING_KEY` |
| `INTERNAL_API_SECRET` | Django와 Node 서비스 사이 공유 비밀이다. hobby는 비어 있으면 `POSTHOG_SECRET`을 쓴다 | `INTERNAL_API_SECRET_FALLBACKS`로 무중단 교체를 지원한다 | `posthog/settings/data_stores.py:INTERNAL_API_SECRET`, `docker-compose.hobby.yml` |
| `INTERNAL_REQUEST_TOKEN` | Django→`feature-flags` 호출 인증 토큰이다. 두 쪽이 같아야 한다 | 두 쪽을 함께 바꾸고 재시작한다 | `docker-compose.hobby.yml`, `posthog/settings/data_stores.py:INTERNAL_REQUEST_TOKEN` |
| `CLICKHOUSE_DATABASE`, `CLICKHOUSE_CLUSTER` | 기존 테이블이 이 DB와 클러스터 이름에 만들어져 있다. 바꾸면 기존 데이터가 보이지 않는다 | 새 설치에서만 정한다 | `posthog/settings/data_stores.py` |
| `OBJECT_STORAGE_BUCKET`, `SESSION_RECORDING_V2_S3_BUCKET`, `SESSION_RECORDING_V2_S3_PREFIX` | 객체가 이 이름 아래 저장돼 있다. 바꾸면 기존 객체를 못 찾는다 | 새 설치에서만 정한다 | `posthog/settings/object_storage.py`, `posthog/settings/session_replay_v2.py` |
| `DOMAIN` (hobby) | Caddy가 이 도메인으로 TLS 인증서를 받고, `SITE_URL`과 `LIVESTREAM_HOST`가 여기서 만들어진다. 이미 심은 추적 코드와 링크가 이 주소를 가리킨다 | 도메인 이전 계획과 함께 | `docker-compose.hobby.yml` |

위 표의 "바꾸면 깨진다"는 설명 가운데 `SECRET_KEY`, `ENCRYPTION_SALT_KEYS`, `JWT_SIGNING_KEY`는 설정 코드의 주석과 형식 검사에서 근거를 확인했다. `CLICKHOUSE_*`와 버킷 이름은 구조상 그렇다는 추론이며 실제로 바꿔 보지 않았다.

### 기본 비밀값이 있다는 점

개발·hobby 편의를 위한 기본값이 코드에 들어 있다.

- `SECRET_KEY`가 기본값(`<randomly generated secret key>`)이면 `DEBUG`와 `TEST`가 아닐 때 서버가 종료된다. 근거: `posthog/settings/access.py`
- `ENCRYPTION_SALT_KEYS`는 기본값이 있다(공개된 값). 설정 없이 띄우면 알려진 키로 암호화된다. hobby 설치 스크립트가 무작위 값을 만들어 준다.
- `INTERNAL_API_SECRET`은 `DEBUG`나 `TEST`일 때만 공개된 개발용 값을 쓴다. 그 밖에는 빈 문자열이고 내부 API 요청이 거부된다.
- `docker-compose.base.yml`의 `capture-logs`는 `JWT_SECRET: '<randomly generated secret key>'`를 쓴다. hobby 파일이 이 값을 덮어쓰지 않는다. 운영에서는 직접 바꿔야 한다. 이 값이 실제로 어디에 쓰이는지는 읽지 않았다(미확인).
- DB 비밀번호(`posthog`), ClickHouse 사용자 비밀번호(`apipass` 등), 객체 스토리지 키(`object_storage_root_user` 등)는 compose와 `.env.services`에 고정돼 있다. 외부에 노출하지 않는 내부 네트워크 전제다. DB 포트는 hobby compose에서 호스트로 열지 않는다. 근거: `docker-compose.base.yml`, `.env.services`

## 값이 정해지는 방식

- Django 설정은 `get_from_env`와 `os.getenv`로 환경변수를 읽는다. `get_from_env`는 값이 비어 있어도(빈 문자열) 없는 것으로 보고 기본값을 쓴다. 기본값도 없고 `optional`도 아니면 `ImproperlyConfigured`로 서버가 뜨지 않는다. 근거: `posthog/settings/utils.py:get_from_env`
- 불리언은 `str_to_bool`이 해석한다. 어떤 문자열을 참으로 보는지는 확인하지 않았다(미확인).
- 기본값 중에는 `DEBUG`, `TEST`에 따라 달라지는 것이 많다. 아래 표의 기본값은 `DEBUG`와 `TEST`가 아닌 운영 기준이다. 개발 기본값이 다르면 따로 적었다.
- **인스턴스 설정(동적 설정)**: 이메일 등 일부 값은 환경변수가 기본값이고, DB에 저장된 값이 있으면 그 값이 우선한다. `${SITE_URL}/admin/posthog/instancesetting/`에서 고친다. 근거: `posthog/settings/dynamic_settings.py`, `posthog/models/instance_setting.py:get_instance_setting`
- hobby에서 변수가 컨테이너에 닿는 길은 셋이다.
  1. `.env`의 값이 compose 파일의 `$VAR`, `${VAR:-기본값}` 치환에 쓰인다.
  2. compose의 `environment:`가 컨테이너 환경변수가 된다.
  3. `worker`와 `web`은 `env_file: .env.services`도 읽는다. 근거: `docker-compose.base.yml`
- compose 안의 `$$`는 compose 치환을 피하려는 이스케이프다. `bin/upgrade-hobby`가 `envsubst`를 쓰므로 변수가 늘면 `bin/helpers/render-hobby-compose.sh`의 치환 목록도 맞춰야 한다. 근거: `bin/helpers/render-hobby-compose.sh`

## hobby `.env`

compose 파일이 읽는 변수다. 설치 스크립트가 만드는 값은 [런북](runbook.md#env에-들어가는-값)에 있다.

| 변수 | 필수 | 기본값 | 의미 | 근거 |
| --- | --- | --- | --- | --- |
| `DOMAIN` | 예 | 없음 | 서비스 도메인. `SITE_URL`, `LIVESTREAM_HOST`, `CADDY_HOST`의 원천 | `docker-compose.hobby.yml` |
| `POSTHOG_SECRET` | 예 | 없음 | Django `SECRET_KEY`. 위 "바꾸면 안 되는 값" 참조 | 같음 |
| `ENCRYPTION_SALT_KEYS` | 예 | 없음 | 위 참조 | 같음 |
| `REGISTRY_URL` | 예 | 설치 스크립트가 `posthog/posthog`로 채움 | Django 이미지 이름. Node 이미지는 `${REGISTRY_URL}-node` | 같음 |
| `POSTHOG_APP_TAG` | 예 | 설치 스크립트가 채움 | Django 이미지 태그 | 같음 |
| `POSTHOG_NODE_TAG` | 아니오 | `latest` | Node 이미지 태그 | 같음 |
| `TLS_BLOCK`, `CADDY_TLS_BLOCK` | 아니오 | 빈 값 | Caddy 전역 옵션. 스테이징 인증서를 쓸 때 `acme_ca ...`를 넣는다 | `docker-compose.hobby.yml`, `docker-compose.base.yml` (`proxy`) |
| `CADDY_HOST` | 아니오 | 설치 스크립트가 `"$DOMAIN, http://, https://"`로 채움 | Caddy 사이트 주소. 없으면 `http://localhost:8000` | `docker-compose.base.yml` (`proxy`) |
| `INTERNAL_REQUEST_TOKEN` | 사실상 예 | 빈 값 | `feature-flags`와 web·worker가 공유하는 토큰. 비면 플래그 테스트 평가가 실패한다 | `docker-compose.hobby.yml` |
| `INTERNAL_API_SECRET` | 아니오 | `POSTHOG_SECRET` | Django와 `recording-api` 사이 비밀 | 같음 |
| `BROWSERLESS_SECRET` | 아니오 | `POSTHOG_SECRET` | `browserless` 컨테이너 토큰. 별도 값을 권장 | 같음 |
| `HEATMAP_BROWSERLESS_SCREENSHOT_COOKIES_ENABLED` | 아니오 | `false` | 히트맵 스크린샷에 쿠키를 쓸지 | 같음 |
| `ANTHROPIC_API_KEY` | 아니오 | 빈 값 | AI 기능용 키. 없으면 AI 기능이 꺼진다 | 같음 |
| `OPENAI_API_KEY` | 아니오 | 빈 값 | SQL·정규식 AI 보조용 키 | 같음 |
| `OPENAI_BASE_URL` | 아니오 | `https://api.openai.com/v1` | OpenAI 호환 엔드포인트. 사내 게이트웨이를 쓸 수 있다 | 같음 |
| `OPENAI_MODEL` | 아니오 | `gpt-4.1-mini` | 사용 모델 | 같음 |
| `OPT_OUT_CAPTURE` | 아니오 | `false` | 서버 텔레메트리 끄기. [외부 호출](external-calls.md) 참조 | 같음 (`web`) |
| `CSP_REPORT_ENDPOINT` | 아니오 | 빈 값 | CSP 위반 보고 주소. 비면 보고하지 않는다 | 같음 |
| `CLICKHOUSE_SERVER_IMAGE` | 아니오 | `clickhouse/clickhouse-server:26.9.13.15` | ClickHouse 이미지 | `docker-compose.base.yml` |
| `DOCKER_REGISTRY_PREFIX` | 아니오 | 빈 값 | `db` 이미지 앞에 붙는 레지스트리 접두사 | `docker-compose.hobby.yml` |
| `SEAWEEDFS_DOCKER_NAME` | 아니오 | `seaweedfs-main` | `seaweedfs` 컨테이너 이름 | 같음 |
| `OBJECT_STORAGE_MINIO_REMOVED` | 아니오 | 없음 | 업그레이드 스크립트가 확인 표시로 쓴다. 사람이 설정하지 않는다 | `bin/upgrade-hobby` |

## Django 앱 (`web`, `worker`, `temporal-django-worker`)

세 서비스가 같은 이미지를 쓰고 같은 설정 모듈(`posthog/settings/`)을 읽는다.
`worker`와 `web`은 `.env.services`와 `docker-compose.base.yml`의 `x-worker_env` 값을 공통으로 받는다.

### compose가 고정해 두는 값

| 변수 | 값 | 서비스 | 의미 | 근거 |
| --- | --- | --- | --- | --- |
| `DEPLOYMENT` | `hobby` | web, worker | 마이그레이션이 hobby 분기를 탄다. `bin/migrate`의 Rust 마이그레이터와 `setup_tasks_oauth`, `schedule_temporal_workflows`가 꺼진다 | `docker-compose.base.yml`, `bin/migrate` |
| `SITE_URL` | `https://$DOMAIN` | web, worker, temporal-django-worker, plugins | 앱의 외부 주소. CSRF 신뢰 출처도 이 값에서 만든다 | `docker-compose.hobby.yml`, `posthog/settings/access.py:CSRF_TRUSTED_ORIGINS` |
| `SECRET_KEY` | `$POSTHOG_SECRET` | 같음 | 위 참조 | 같음 |
| `ENCRYPTION_SALT_KEYS` | `$ENCRYPTION_SALT_KEYS` | web, worker, plugins, ingestion-* | 위 참조 | 같음 |
| `OBJECT_STORAGE_ENABLED` | `true` | web, worker | 코드 기본값은 `DEBUG`일 때만 켜짐이라 hobby에서 명시한다 | `docker-compose.hobby.yml`, `posthog/settings/object_storage.py` |
| `PERSONHOG_ADDR`, `PERSONHOG_ENABLED` | `personhog-router:50052`, `true` | web, worker, temporal-django-worker, ingestion-general | 인물 데이터 접근 경로. `PERSONHOG_ADDR` 코드 기본값은 빈 값 | `docker-compose.hobby.yml`, `posthog/settings/personhog.py` |
| `FEATURE_FLAGS_SERVICE_URL` | `http://feature-flags:3001` | web, worker, temporal-django-worker | 코드 기본값은 `http://localhost:3001`이라 hobby에서 덮는다 | `docker-compose.hobby.yml`, `posthog/settings/data_stores.py:FEATURE_FLAGS_SERVICE_URL` |
| `CDP_API_URL` | `http://plugins:6738` | web, worker | CDP 서비스 주소. 코드 기본값은 빈 값 | `docker-compose.base.yml`, `posthog/settings/data_stores.py:CDP_API_URL` |
| `RECORDING_API_URL` | `http://recording-api:6738` | web, worker, temporal-django-worker | 세션 리플레이 재생 API. 코드 기본값은 빈 값 | `docker-compose.hobby.yml`, `posthog/settings/session_replay_v2.py` |
| `LIVESTREAM_HOST` | `https://$DOMAIN/livestream` | web | 실시간 스트림 주소. 코드 기본값은 빈 값 | `docker-compose.hobby.yml`, `posthog/settings/web.py:LIVESTREAM_HOST` |
| `PERSONS_DB_WRITER_URL`, `PERSONS_DB_READER_URL` | 메인 Postgres | web, worker | hobby는 인물 테이블이 메인 DB에 있다 | `docker-compose.base.yml` |
| `CLICKHOUSE_LOGS_CLUSTER_HOST`, `CLICKHOUSE_LOGS_CLUSTER_SECURE` | `clickhouse`, `false` | web, worker, temporal-django-worker | 로그 제품 전용 ClickHouse 설정. 코드 기본값은 `localhost`와 (운영에서) `true` | `docker-compose.hobby.yml`, `posthog/settings/data_stores.py` |
| `BROWSERLESS_CDP_URL`, `BROWSERLESS_TOKEN`, `HEATMAP_BROWSERLESS_URL`, `HEATMAP_BROWSERLESS_TOKEN` | `browserless` 컨테이너 | worker, temporal-django-worker | 이미지 내보내기·히트맵 스크린샷 렌더링. Django 이미지에는 브라우저가 없다 | `docker-compose.hobby.yml`, `posthog/settings/exports.py` |
| `SESSION_RECORDING_V2_S3_*` | `seaweedfs:8333`, 키 `any` | web, worker | 리플레이 v2 저장소 | `docker-compose.hobby.yml` |
| `OBJECT_STORAGE_*` | `objectstorage:19000`, 키 `object_storage_root_*` | web, worker, plugins | 일반 객체 스토리지 | `docker-compose.hobby.yml`, `.env.services` |
| `OTEL_SDK_DISABLED` | `true` | web, worker | OpenTelemetry를 끈다 | `docker-compose.base.yml` |
| `POSTHOG_SKIP_MIGRATION_CHECKS` | `1` | worker | 시작 시 마이그레이션 확인을 건너뜀 | `docker-compose.hobby.yml`, `bin/migrate-check` |
| `SKIP_ASYNC_MIGRATIONS_SETUP` | `0` | asyncmigrationscheck | 코드 기본값은 `True`(건너뜀). 이 확인 컨테이너만 켠다 | `docker-compose.hobby.yml`, `posthog/settings/async_migrations.py` |
| `API_QUERIES_PER_TEAM` | `{"1": 100}` | web, worker | 팀별 동시 API 쿼리 한도(JSON) | `docker-compose.base.yml` |

### 접근·보안

| 변수 | 필수 | 기본값 | 의미 | 근거 |
| --- | --- | --- | --- | --- |
| `SECRET_KEY` | 예 | 기본값이면 종료 | 위 참조 | `posthog/settings/access.py` |
| `SITE_URL` | 사실상 예 | `http://localhost:8010` | 외부 주소 | `posthog/settings/__init__.py:SITE_URL` |
| `ALLOWED_HOSTS` | 아니오 | `*` | 쉼표 구분 호스트 목록 | `posthog/settings/access.py` |
| `SECURE_COOKIES` | 아니오 | `DEBUG`·`TEST`가 아니면 `true` | 쿠키 `Secure` 플래그와 HTTPS 리다이렉트 | 같음 |
| `DISABLE_SECURE_SSL_REDIRECT` | 아니오 | `false` | HTTPS 리다이렉트 끄기. `.env.services`가 `true`로 준다 | 같음, `.env.services` |
| `IS_BEHIND_PROXY` | 아니오 | `false` | 프록시 뒤에서 `X-Forwarded-*`를 믿음. `.env.services`가 `true`로 준다 | 같음, `.env.services` |
| `TRUSTED_PROXIES`, `TRUST_ALL_PROXIES` | 아니오 | 없음, `false` | 믿을 프록시. `IS_BEHIND_PROXY`가 참인데 둘 다 없으면 경고를 낸다 | `posthog/settings/access.py` |
| `EXTRA_CSRF_TRUSTED_ORIGINS` | 아니오 | 빈 값 | `SITE_URL` 외에 신뢰할 출처 | 같음 |
| `CORS_ALLOWED_ORIGINS` | 아니오 | 없음(모든 출처 허용) | 값을 주면 그 목록만 허용 | 같음 |
| `ALLOWED_IP_BLOCKS` | 아니오 | 빈 값 | 접근 허용 IP 대역 | 같음 |
| `JWT_SIGNING_KEY` | 아니오 | `SECRET_KEY` | 위 참조 | 같음 |
| `OPT_OUT_CAPTURE` | 아니오 | `false` | 서버 텔레메트리를 끈다 | `posthog/settings/base_variables.py` |
| `DEBUG` | 아니오 | `false` | 개발 모드. 인증을 느슨하게 한다. 운영에서 켜지 않는다 | 같음 |
| `E2E_TESTING` | 아니오 | `false` | 켜면 보안 취약점이라는 경고가 뜬다. 테스트 전용 | 같음 |

### 데이터 저장소

| 변수 | 필수 | 기본값 | 의미 | 근거 |
| --- | --- | --- | --- | --- |
| `DATABASE_URL` | 예 (또는 `POSTHOG_DB_NAME`) | 운영 기본값은 빈 값 | Postgres 연결 문자열. 둘 다 없으면 서버가 뜨지 않는다. `.env.services`가 `postgres://posthog:posthog@db:5432/posthog`를 준다 | `posthog/settings/data_stores.py` |
| `POSTHOG_DB_NAME` 외 `POSTHOG_POSTGRES_*` | 아니오 | 호스트 기본 `localhost`, 포트 `5432` | `DATABASE_URL` 대신 쓰는 개별 항목. SSL 옵션 포함 | 같음 |
| `POSTHOG_POSTGRES_READ_HOST` | 아니오 | 없음 | 읽기 복제본. 있으면 DB 라우터가 켜진다 | 같음 |
| `POSTHOG_POSTGRES_DIRECT_HOST` | 아니오 | 없음 | 마이그레이션용 직접 연결(PgBouncer 우회) | 같음, `bin/migrate` |
| `USING_PGBOUNCER` | 아니오 | `false` | 서버 측 커서를 끈다 | 같음 |
| `MIGRATE_LOCK_TIMEOUT` | 아니오 | `20000` | 마이그레이션 연결 `lock_timeout`(ms) | 같음 |
| `REDIS_URL` | 사실상 예 | 운영 기본값은 빈 값 | Redis 주소. `.env.services`가 `redis://redis7:6379/`를 준다 | 같음 |
| `POSTHOG_REDIS_HOST` 외 | 아니오 | 없음 | `REDIS_URL`이 비었을 때 호스트·포트·비밀번호로 조립 | 같음 |
| `CLICKHOUSE_HOST` | 아니오 | `clickhouse` | ClickHouse 호스트 | 같음 |
| `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD` | 아니오 | `default`, 빈 값 | 기본 접속 계정 | 같음 |
| `CLICKHOUSE_API_USER`/`_PASSWORD` 외 `APP`, `BILLING`, `DICT_READER` | 아니오 | `.env.services`가 `api/apipass`, `app/apppass`, `billing/billingpass`, `dict_reader/dictreaderpass`를 준다 | 용도별 ClickHouse 계정 | `.env.services` |
| `CLICKHOUSE_DATABASE` | 아니오 | `default` (`.env.services`는 `posthog`) | 위 "바꾸면 안 되는 값" 참조 | `posthog/settings/data_stores.py` |
| `CLICKHOUSE_CLUSTER` | 아니오 | `posthog` | 클러스터 이름. 위 참조 | 같음 |
| `CLICKHOUSE_SECURE`, `CLICKHOUSE_VERIFY` | 아니오 | 운영 `true`, `true` (`.env.services`는 둘 다 `false`) | TLS 사용·인증서 검증 | 같음, `.env.services` |
| `CLICKHOUSE_PASSWORD_FILE` | 아니오 | 없음 | 비밀번호를 파일에서 읽는다. 회전하는 토큰용. hobby에서는 쓰지 않는다 | 같음 |
| `KAFKA_HOSTS` | 예 | 코드 기본값은 `KAFKA_DEFAULT_HOSTS`를 거쳐 정해진다(미확인) | 카프카 부트스트랩 주소. hobby는 `kafka` 또는 `kafka:9092` | `posthog/settings/kafka.py`, `docker-compose.base.yml` |
| `KAFKA_SECURITY_PROTOCOL`, `KAFKA_SASL_*` | 아니오 | | 카프카 보안 설정 | `posthog/settings/kafka.py` |

카프카는 `KAFKA_<프로필>_*` 이름으로 프로필별 설정을 받는다. 프로필에 값이 없으면 `KAFKA_DEFAULT_*`, 그 다음 `KAFKA_HOSTS` 같은 옛 이름을 쓴다. 근거: `posthog/settings/kafka.py` 머리 주석.

### 객체 스토리지와 세션 리플레이

| 변수 | 필수 | 기본값 | 의미 | 근거 |
| --- | --- | --- | --- | --- |
| `OBJECT_STORAGE_ENABLED` | 아니오 | `DEBUG`일 때만 `true` | 객체 스토리지 기능 전체 | `posthog/settings/object_storage.py` |
| `OBJECT_STORAGE_ENDPOINT` | 켰다면 예 | 운영 기본값은 빈 값 | 내부 S3 호환 주소. hobby는 `http://objectstorage:19000` | 같음 |
| `OBJECT_STORAGE_PUBLIC_ENDPOINT` | 아니오 | `OBJECT_STORAGE_ENDPOINT` | 브라우저에 주는 서명 URL의 주소. hobby는 `https://$DOMAIN`(Caddy의 `/posthog` 경로가 스토리지로 간다) | 같음, `docker-compose.base.yml` (`proxy`) |
| `OBJECT_STORAGE_ACCESS_KEY_ID`, `OBJECT_STORAGE_SECRET_ACCESS_KEY` | 켰다면 예 | 운영 기본값은 없음(AWS 기본 자격 증명) | 접근 키 | 같음 |
| `OBJECT_STORAGE_BUCKET` | 아니오 | `posthog` | 버킷 이름. 위 참조 | 같음 |
| `OBJECT_STORAGE_REGION` | 아니오 | `us-east-1` | 리전 | 같음 |
| `SESSION_RECORDING_V2_S3_ENDPOINT` | 아니오 | 운영 기본값은 빈 값 | 리플레이 v2 저장소. hobby는 `http://seaweedfs:8333` | `posthog/settings/session_replay_v2.py` |
| `SESSION_RECORDING_V2_S3_ACCESS_KEY_ID`, `..._SECRET_ACCESS_KEY` | 아니오 | 운영 기본값 없음 | hobby는 `any` | 같음 |
| `SESSION_RECORDING_V2_S3_BUCKET`, `..._PREFIX`, `..._REGION` | 아니오 | `posthog`, `session_recordings`, `us-east-1` | 위치 | 같음 |
| `RECORDING_API_JWT_SECRET` | 아니오 | 운영 기본값은 빈 값 | `recording-api` 호출 JWT 서명 키. `새키,옛키` 형식으로 교체 | 같음 |
| `REPLAY_PROXY_JWT_SECRET` | 아니오 | 빈 값 | 업스트림의 리플레이 프록시용. 비우면 쓰지 않는다 | 같음 |

SeaweedFS를 쓴다는 점에 유의한다. MinIO는 제거됐다. 근거: `docs/internal/hobby-minio-removal.md`.

### 이메일

이메일은 동적 설정이다. 환경변수는 기본값이고 DB 값이 우선한다. 근거: `posthog/settings/dynamic_settings.py`.

| 변수 | 기본값 | 의미 |
| --- | --- | --- |
| `EMAIL_ENABLED` | `true` | 이메일 서비스 사용 |
| `EMAIL_HOST` | 빈 값 | SMTP 호스트. 비어 있으면 이메일을 보내지 않는다 (`posthog/email.py`가 `EMAIL_HOST` 유무로 판단) |
| `EMAIL_PORT` | `25` | SMTP 포트 |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | 빈 값 | SMTP 계정 |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | `false` | 연결 보안 |
| `EMAIL_DEFAULT_FROM` | `DEFAULT_FROM_EMAIL`, 없으면 `root@localhost` | 보내는 사람 |
| `EMAIL_REPLY_TO` | 빈 값 | 회신 주소 |

SES 설정은 `posthog/settings/ses.py`에 따로 있다(미확인).

### Temporal과 기타

| 변수 | 기본값 | 의미 | 근거 |
| --- | --- | --- | --- |
| `TEMPORAL_HOST`, `TEMPORAL_PORT`, `TEMPORAL_NAMESPACE` | `temporal`, `7233`, `default` | Temporal 서버 주소 | `posthog/settings/temporal.py` |
| `TEMPORAL_TASK_QUEUE` | `general-purpose-task-queue` | 기본 작업 큐 | 같음 |
| `STATSD_HOST`, `STATSD_PORT`, `STATSD_PREFIX` | 없음, `8125`, 빈 값 | StatsD 메트릭 | `posthog/settings/statsd.py` |
| `PROM_PUSHGATEWAY_ADDRESS` | 없음 | 마이그레이션 메트릭 푸시 | `posthog/settings/__init__.py` |
| `GRANIAN_WORKERS` | `4` | 웹 서버 워커 수. ASGI에서는 동시성이 워커 수로만 늘어난다 | `bin/docker-server` |
| `GRANIAN_INTERFACE` | `asgi` | `asgi` 또는 `wsgi` | 같음 |
| `GRANIAN_HOST`, `GRANIAN_LOG_LEVEL`, `GRANIAN_METRICS_ENABLED`, `GRANIAN_METRICS_PORT` | `0.0.0.0`, `warning`, `true`, `9090` | 웹 서버 설정과 내장 메트릭 | 같음 |
| `POSTHOG_GRANIAN_SHARED_SOCKET` | `false` | 워커들이 리슨 소켓 하나를 공유 | 같음 |
| `STATIC_COLLECTION` | `false` | `collectstatic` 빌드 때만 켠다 | `posthog/settings/base_variables.py`, `Dockerfile` |
| `SKIP_SERVICE_VERSION_REQUIREMENTS` | `DEBUG` 등이 아니면 `false` | 서비스 버전 범위 검사 건너뜀. 코드가 "위험하다"고 경고한다 | `posthog/settings/service_requirements.py` |
| `DISABLE_MMDB` | `TEST` | GeoIP 기능 끄기 | `posthog/settings/__init__.py` |
| `GEOIP_PATH` | 코드에 고정 | `BASE_DIR/share`. 환경변수로 바꾸지 못한다 | `posthog/settings/geoip.py` |
| `MULTI_ORG_ENABLED` | `false` | 조직 여러 개 허용. 코드 주석은 프리미엄 라이선스가 필요하다고 적는다. 이 포크에서의 동작은 미확인 | `posthog/settings/__init__.py` |
| `INSTANCE_TAG` | `none` | 인스턴스 식별 태그 | 같음 |

## 노드 서비스 (`plugins`, `ingestion-*`, `recording-api`)

이미지는 `${REGISTRY_URL}-node`다. 기본 설정은 `nodejs/` 코드에 있다. 이 문서는 compose가 넘기는 값만 정리했고 코드의 기본값은 읽지 않았다(미확인).

| 서비스 | compose가 넘기는 값 | 근거 |
| --- | --- | --- |
| `plugins` | `SITE_URL`, `SECRET_KEY`, `OBJECT_STORAGE_*`, `CDP_REDIS_HOST=redis7`, `CDP_VALKEY_HOST=valkey`(없으면 기동 거부), `LOGS_REDIS_*`, `TRACES_REDIS_*`, `ENCRYPTION_SALT_KEYS`, `PERSONS_DATABASE_URL`, `BEHAVIORAL_COHORTS_DATABASE_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT=''`. `./share`를 마운트 | `docker-compose.hobby.yml` |
| `ingestion-general` | `PERSONS_DATABASE_URL`, `BEHAVIORAL_COHORTS_DATABASE_URL`, `ENCRYPTION_SALT_KEYS`, `PERSONHOG_ADDR`, `PERSONHOG_ENABLED` | 같음 |
| `ingestion-sessionreplay` | `SESSION_RECORDING_V2_S3_*`(타임아웃 `120000` 포함), `ENCRYPTION_SALT_KEYS` | 같음 |
| `recording-api` | `SESSION_RECORDING_V2_S3_*`, `ENCRYPTION_SALT_KEYS`, `INTERNAL_API_SECRET`. 리플레이 재생에 필요 | 같음 |
| `ingestion-error-tracking` | `ENCRYPTION_SALT_KEYS`, `ERROR_TRACKING_CYMBAL_BASE_URL=http://cymbal:3302` | 같음 |
| `ingestion-logs`, `ingestion-traces` | `LOGS_REDIS_TLS=false`, `TRACES_REDIS_TLS=false` | 같음 |

## Rust·Go 서비스

이미지는 `ghcr.io/posthog/posthog/<서비스>:master`다. compose가 넘기는 값만 정리했다. 코드의 기본값은 읽지 않았다(미확인).

| 서비스 | 주요 환경변수 | 근거 |
| --- | --- | --- |
| `capture` | `ADDRESS=0.0.0.0:3000`, `KAFKA_TOPIC`/`CAPTURE_OUTPUT_ANALYTICS_MAIN_TOPIC=events_plugin_ingestion`, `KAFKA_HOSTS`, `REDIS_URL`, `CAPTURE_MODE=events` | `docker-compose.base.yml` |
| `replay-capture` | 같은 바이너리, `CAPTURE_MODE=recordings`, 토픽 `session_recording_snapshot_item_events` | 같음 |
| `capture-ai` | `CAPTURE_MODE=ai`, 토픽 `events_plugin_ingestion_ai` | 같음 |
| `capture-logs` | `BIND_PORT=4318`, `KAFKA_TOPIC=logs_ingestion`, `KAFKA_METRICS_TOPIC=metrics_ingestion`, `JWT_SECRET`(기본값 주의) | 같음 |
| `feature-flags` | `WRITE_DATABASE_URL`, `READ_DATABASE_URL`, `PERSONS_*_DATABASE_URL`, `MAXMIND_DB_PATH=/share/GeoLite2-City.mmdb`, `REDIS_URL`, `ADDRESS=0.0.0.0:3001`, `INTERNAL_REQUEST_TOKEN`, `OBJECT_STORAGE_ENDPOINT`와 접근 키(`x-hypercache-s3`) | `docker-compose.base.yml`, `docker-compose.hobby.yml` |
| `hypercache-server` | `x-hypercache-s3` 값. 포트 3002 | 같음 |
| `property-defs-rs`, `property-defs-ai` | `DATABASE_URL`, `KAFKA_HOSTS`, `FILTER_MODE=opt-out`. `property-defs-ai`는 토픽 `clickhouse_ai_events_json`, 그룹 `property-defs-ai` | 같음 |
| `personhog-replica` | `PRIMARY_DATABASE_URL` | `docker-compose.hobby.yml` |
| `personhog-router` | `personhog-replica`에 의존 | 같음 |
| `cymbal` | `KAFKA_HOSTS`, `OBJECT_STORAGE_*`(`seaweedfs:8333`), `DATABASE_URL`, `PERSONS_URL`, `REDIS_URL`, `MAXMIND_DB_PATH`, `CYMBAL_REMOTE_RESOLUTION_HOST=cymbal-resolution`, `INTERNAL_API_SECRET=$POSTHOG_SECRET` | `docker-compose.hobby.yml` |
| `cymbal-resolution` | `CYMBAL_MODE=resolution`, `GRPC_ADDRESS=0.0.0.0:50061`, `OBJECT_STORAGE_*`, `DATABASE_URL`, `INTERNAL_API_SECRET=$POSTHOG_SECRET` | 같음 |
| `livestream` | `LIVESTREAM_JWT_SECRET=${POSTHOG_SECRET}`. 설정 파일 `posthog/docker/livestream/configs-hobby.yml`을 마운트 | 같음 |

`cymbal`과 `cymbal-resolution`은 `INTERNAL_API_SECRET`에 `$POSTHOG_SECRET`을 그대로 넘긴다. Django 쪽은 `${INTERNAL_API_SECRET:-$POSTHOG_SECRET}`이므로 `.env`에 `INTERNAL_API_SECRET`를 따로 두면 cymbal과 값이 갈라진다. 이 경우 cymbal 쪽 compose도 같이 고쳐야 한다. 실제로 갈라졌을 때의 동작은 확인하지 못했다(미확인).

## 인프라 컨테이너

| 서비스 | 이미지 | 설정 | 근거 |
| --- | --- | --- | --- |
| `db` | `postgres:15.12-alpine` | 사용자·DB·비밀번호 모두 `posthog`. 볼륨 `postgres-data`. `docker/postgres-init-scripts`를 초기화 스크립트로 마운트 | `docker-compose.base.yml`, `docker-compose.hobby.yml` |
| `redis7` | `redis:7.2-alpine` | `--maxmemory 200mb`, `allkeys-lru`. 볼륨 `redis7-data` | 같음 |
| `valkey` | `valkey/valkey:8.1-alpine` | `--maxmemory 200mb`, `allkeys-lru`. 볼륨 없음. CDP 서비스의 이중 쓰기 대상 | 같음 |
| `clickhouse` | `clickhouse/clickhouse-server:26.9.13.15` | `posthog/docker/clickhouse/`의 `config.xml`, `users.xml`, `user_defined_function.xml`, `config.d/default.xml`을 마운트. 볼륨 `clickhouse-data` | 같음 |
| `zookeeper` | `zookeeper:3.7.0` | 자동 정리 간격 1, 스냅샷 3개 유지. 볼륨 3개 | `docker-compose.hobby.yml` |
| `kafka` | `redpandadata/redpanda:v25.1.9` | `--smp 2 --memory 3G`, 로그 보존 1시간(`KAFKA_LOG_RETENTION_*`). 볼륨 `kafka-data` | 같음 |
| `objectstorage` | `chrislusf/seaweedfs:4.29` | 포트 `127.0.0.1:19000`. 시작 때 `posthog`, `ai-blobs` 버킷과 `posthog` 신원을 만든다. `anonymous` 신원은 만들지 않는다 | 같음 |
| `seaweedfs` | 같은 이미지 | 포트 `127.0.0.1:8333`, `127.0.0.1:9333`. 볼륨 `seaweedfs` | 같음 |
| `browserless` | `ghcr.io/browserless/chromium:v2.51.2` | `TOKEN=${BROWSERLESS_SECRET:-$POSTHOG_SECRET}` | 같음 |
| `proxy` | `caddy` | `CADDY_HOST`, `CADDY_TLS_BLOCK`. 경로별로 capture, flags, livestream 등에 나눠 보낸다. 포트 80, 443 | `docker-compose.base.yml`, `docker-compose.hobby.yml` |
| `temporal` | `temporalio/auto-setup:1.26.2` | 포트 `127.0.0.1:7233`. `ENABLE_ES=false` | 같음 |
| `temporal-ui` | `temporalio/ui:2.47.2` | 포트 `127.0.0.1:8081` | 같음 |

ClickHouse 이미지 기본값과 서비스 버전 범위가 어긋나 보이는 점은 [런북](runbook.md#서비스-버전-범위)에 적었다.

## 설정 파일 지도

`posthog/settings/__init__.py`가 아래 모듈을 한꺼번에 가져온다. 변수 수는 `getenv`/`get_from_env` 호출 줄을 센 값이다(근사치).

| 파일 | 변수 수 | 내용 |
| --- | --- | --- |
| `base_variables.py` | 약 25 | `DEBUG`, `TEST`, `CLOUD_DEPLOYMENT`, `OPT_OUT_CAPTURE`, `DEMO` 등 기본 스위치 |
| `access.py` | 약 20 | 비밀 키, 프록시, 쿠키, CORS, SSL |
| `data_stores.py` | 약 160 | Postgres, ClickHouse, Redis, 내부 API 비밀, 기능 플래그 서비스 |
| `web.py` | 약 180 | Django 앱 설정, 인증, 소셜 로그인, 레이트 리밋, 기능별 스위치 |
| `kafka.py` | | 프로필별 카프카 설정 |
| `object_storage.py`, `session_replay_v2.py`, `session_replay.py` | | 객체 스토리지, 리플레이, 레이트 리밋 |
| `temporal.py` | 약 100 | Temporal 서버와 큐, 워크플로 설정 |
| `integrations.py` | 약 115 | 외부 연동(Slack, GitHub, OAuth 클라이언트 등). 연동을 켠 팀만 쓴다 |
| `dynamic_settings.py` | 약 65 | 인스턴스 설정. DB가 우선 |
| `ingestion.py`, `feature_flags.py`, `cohorts.py`, `batch_exports.py`, `data_warehouse.py`, `logs.py`, `signals.py` | | 제품별 설정 |
| `personhog.py` | | 인물 데이터 클라이언트 |
| `ses.py`, `email.py` | | 이메일 |
| `ee.py` | | `ee` 패키지가 있을 때만 `EE_AVAILABLE`을 참으로 한다. 이 포크에는 `ee`가 없다 |

찾는 변수가 어느 파일에 있는지는 `grep -rn '"변수명"' posthog/settings`로 확인한다.

호스트에서 개발할 때의 변수 우선순위는 `docs/internal/dev-env-vars.md`에 있다. `.env.development`와 `.env.local.example`은 개발 전용이다.

## 미확인 항목

- `str_to_bool`이 참으로 보는 문자열 목록
- `ENCRYPTION_SALT_KEYS`를 여러 개 줄 때 목록 순서의 의미와 교체 절차
- Node 서비스(`nodejs/`)와 Rust 서비스(`rust/`) 내부의 환경변수 기본값 전체
- `capture-logs`의 `JWT_SECRET`이 쓰이는 곳과 hobby에서 기본값을 그대로 써도 되는지
- `KAFKA_DEFAULT_HOSTS`의 코드 기본값
- `posthog/settings/integrations.py`, `temporal.py`, `web.py`의 개별 변수 의미. 위에서는 hobby에 의미가 있는 것만 다뤘다

Decided in: buzzhog-uxbl
