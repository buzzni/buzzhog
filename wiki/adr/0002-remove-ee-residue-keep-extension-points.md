# ADR 0002: ee 잔재를 걷어 내고 확장 지점은 남긴다

확인 기준 커밋: ca37aa9e209

상태: 채택

## 맥락

[ADR 0001](0001-remove-non-foss.md)로 `ee/`가 없어졌지만, 그것을 가져오는 코드가 남아 있었다.
`from ee` import를 쓰는 Python 파일이 264개였고, `Dockerfile`은 없는 `ee`를 복사했다.
`ee` 앱의 마이그레이션이 없어져 마이그레이션 그래프가 끊겼고(`NodeNotFoundError posthog.1345 → ee.0061`), 빈 DB에서 `migrate`가 되지 않았다.
근거: [업스트림](../upstream.md#알려진-부작용-끊어진-ee-import-해소됨), 에픽 `buzzhog-dsv8`의 기록.

포크는 나중에 자체 ee를 만들 계획이다.
그래서 지금은 `ee` 관련 코드를 지우되, 나중에 꽂을 자리는 남긴다.

## 결정

1. `ee` 전용 모듈은 삭제하고 등록도 뺀다.
   삭제한 것: PostHog AI 도구(`max_tools.py`), Salesforce 보강과 billing 워크플로, SCIM 뷰, PostHog AI temporal 워크플로, 구체화 컬럼 관리 Dagster 작업, billing 동기화 관리 명령.
2. FOSS 기능 안의 `ee` 분기는 잘라낸다.
   쿼터는 제한하지 않고, billing 정보는 없고, 구독 발송은 꺼진다.
   `ee.hogai`에 기대던 LLM 기능은 쓸 수 없다.
3. 확장 지점 세 곳은 남긴다.
   - `posthog/settings/ee.py`의 `EE_AVAILABLE`. `ee.apps`를 import할 수 있을 때만 참이다.
   - `posthog/settings/web.py`의 `ee.apps.EnterpriseConfig` 조건부 등록과 `posthog/settings/__init__.py`의 `ee.settings` 조건부 import.
   - `posthog/ee_urls.py`의 `ee_urlpatterns`와 `ee.urls`의 조건부 import.
   근거: 위 파일. `git grep -lE '^\s*(from|import) ee(\.|\s|$)' -- '*.py'`가 이 4개 파일만 보여 준다.
4. 실험의 holdout·saved metric serializer는 `products/experiments/backend/presentation/holdout_serializers.py`에 모델 필드만 쓰는 최소 `ModelSerializer`로 새로 썼다.
   지운 `ee` 코드를 베끼지 않았다.
5. `posthog_ai`, `tasks` 같은 AI 제품은 폴더를 두고 `ee` import만 정리했다.
   제품 삭제는 이 결정에 들지 않고 별도 backlog다.
6. RBAC 모델 다섯 개(`AccessControl`, `Role`, `RoleMembership`, `FeatureFlagRoleAccess`, `OrganizationResourceAccess`)의 앱 레이블을 `ee`에서 `access_control`로 옮겼다.
   - 테이블 이름 `ee_*`는 그대로 둔다. 예: `db_table = "ee_role"`.
   - 테이블을 만드는 마이그레이션은 `products/access_control/backend/migrations/0000_rbac_models.py`와 `0004_featureflagroleaccess.py`로 새로 썼다.
   - `(ee, ...)`에 의존하던 마이그레이션 29개와 `to=ee.*` 참조를 고쳤다. 이력을 고치는 일이므로 안전을 확인했다: 이 포크 코드로 `migrate`한 DB는 없다(사람 확인).
7. 도메인이 다른 SSO를 강제할 때 GitHub·GitLab 같은 소셜 로그인을 거절하는 파이프라인 단계는 `ee`와 함께 사라졌다.
   보안 때문에 FOSS 단계로 다시 썼다(`posthog/api/authentication.py`).
8. `ee`가 정의하던 설정 중 FOSS 코드가 읽는 것은 `posthog/settings/email.py`(Customer.io)와 `posthog/settings/llm.py`(LLM 제공자·게이트웨이)로 옮겨 환경변수로 읽는다. 값이 없으면 빈 문자열이다.
   `ee` 설정만 이 값을 정의하던 탓에 이미지에서 `/login`과 `/preflight`가 500을 냈다.

## 결과

- 빈 DB에서 `migrate`가 끝난다(미적용 0). 이미지가 뜨고 가입 201, 핵심 API 200을 확인했다. 근거: 에픽 `buzzhog-dsv8`의 병합 기록.
- 과금 서비스로 사용량을 보내는 코드는 없어졌다. 클라우드로 가는 사용량 이벤트는 그대로다([외부 호출](../external-calls.md)).
- 나중에 자체 ee를 만들 때는 `ee` 패키지에 `apps.EnterpriseConfig`, `urls`(`urlpatterns`와 `extend_api_router`), `settings`를 두면 위 확장 지점이 자동으로 잡힌다.
  자르기로 한 기능(쿼터, billing, 구독 발송)은 자체 ee가 다시 붙일 자리를 코드로 남기지 않았다. 다시 짜야 한다.
- 결정이 필요한 backlog: 실험 API 동작(`buzzhog-x76a`), `loginas`(`buzzhog-bmih`), `ee` 없이 `AccessControl`을 무시하는 동작(`buzzhog-3dz9`).
- `services/llm-gateway`는 삭제된 `quota_limits` 엔드포인트를 부르고 실패하면 통과시킨다. 코드 동결 중이라 손대지 않았다.
- 알려진 한계: ClickHouse가 없는 호스트에서는 `_readyz`가 503이다([런북](../runbook.md)).

Decided in: buzzhog-dsv8
