# 업스트림 동기화

확인 기준 커밋: 70371e9eb38

이 페이지는 buzzhog가 PostHog 업스트림을 따라가는 방식과, 포크가 업스트림과 다르게 고친 곳(패치 로그)을 적는다.
근거는 git 명령과 `gh api`로 확인한 것만 쓰고, 각 사실 옆에 그 명령을 적는다.
확인하지 못한 항목은 "미확인", 사람이 정해야 할 항목은 "결정 필요"로 표시한다.

## 현재 상태

### 저장소 관계

- `origin`은 `https://github.com/buzzni/buzzhog.git`이다. 근거: `git remote -v`.
- 로컬 clone에는 `upstream` remote가 없다. 근거: `git remote -v`는 `origin`만 보여 준다.
- 업스트림은 `PostHog/posthog-foss`의 `master`다. 근거: `gh api repos/buzzni/buzzhog`의 `parent`와 `source`가 `PostHog/posthog-foss`다.
  병합 커밋 `70371e9eb38`의 제목 `Merge branch 'PostHog:master' into master`도 이와 맞는다.
- `PostHog/posthog`는 업스트림이 아니다.
  병합한 업스트림 끝 `e289996cf97`은 `posthog-foss-sync[bot]`의 커밋이다.
  그 부모인 `PostHog/posthog` 커밋 `7010e516600`에는 `ee/`와 `.github/workflows`가 있다. 근거: `git ls-tree --name-only 7010e516600 ee .github/workflows`.
- `PostHog/posthog`를 `upstream`으로 등록해 병합하면, merge-base 뒤에 `PostHog/posthog`가 고친 `ee/`와 `.github/workflows` 파일이 modify/delete 충돌로 들어온다.
  고치지 않은 파일은 지운 상태로 남는다.
  근거: 같은 상황을 흉내 낸 `git merge-tree --write-tree --name-only b068ff99030 7010e516600`이 충돌 33건(`.github/workflows` 20개, `ee/` 13개)을 낸다.
  이 33개는 `git diff --name-status 4e824e99423 7010e516600 -- ee .github/workflows`의 `M` 33개와 같다.
  충돌을 `PostHog/posthog` 쪽으로 풀면 그 파일이 다시 들어온다.
  새로 만든 파일이 충돌 없이 들어오는지는 이 범위에 예가 없어 미확인이다.
- 마지막으로 병합한 업스트림 끝은 `e289996cf97`이다. 근거: `git log -1 --format=%h --author=foss-sync HEAD`.
  아래 "패치 로그"는 이 커밋과 비교한다.

### 동기화 방식

포크는 업스트림 `master`를 포크의 `master`로 병합하는 방식으로 따라간다.
이 병합은 GitHub의 "Sync fork" 동작으로 만든 것으로 보인다(미확인: 병합 커밋 제목이 그 기본 형식이다).

- 병합 커밋 `70371e9eb38`의 부모는 `b068ff99030`(포크 `master`의 이전 끝)과 `e289996cf97`(업스트림 끝)이다. 근거: `git log -1 --format='%p' 70371e9eb38`.
- 이 병합이 가져온 변경은 2464개 파일이다. 근거: `git diff --stat 70371e9eb38^1 70371e9eb38`.
- 포크 쪽 부모 `b068ff99030`도 업스트림이 만든 봇 커밋이다.
  포크 `master`는 지금까지 업스트림 커밋만 쌓였고, 포크가 만든 코드 커밋은 없다.
  근거: `git log --format='%h %an' e289996cf97..70371e9eb38`는 `b068ff99030`(봇)과 병합 커밋 `70371e9eb38`만 보여 준다.
- 업스트림은 동기화할 때마다 `master`를 다시 쓴다.
  봇은 `PostHog/posthog` 커밋 위에 새 봇 커밋을 하나 얹고, 이전 봇 커밋은 새 끝의 이력에 남기지 않는다.
  근거: `git merge-base --is-ancestor b068ff99030 e289996cf97`이 실패한다. 두 부모의 merge-base는 `b068ff99030`의 부모인 `4e824e99423`이다.
  2026-10-16에 본 업스트림 끝 `e2c6705c4c7`도 `e289996cf97`을 이력에 두지 않는다. 근거: `gh api repos/PostHog/posthog-foss/compare/e289996cf97...e2c6705c4c7`의 `status`가 `diverged`다.
  그래서 `git fetch upstream`은 강제 갱신(forced update)으로 나오고, 지난 봇 커밋은 포크 이력에만 남는다.

### non-FOSS 제거 커밋

포크 이력(`HEAD`)에 `posthog-foss-sync[bot]`이 만든 커밋 두 개가 있다. 근거: `git log --author=foss-sync`.
업스트림 끝 `e289996cf97`의 이력에는 `e289996cf97` 하나만 있다. 근거: `git log --author=foss-sync e289996cf97`.

| 커밋          | 날짜       | 제목                               |
| ------------- | ---------- | ---------------------------------- |
| `b068ff99030` | 2026-10-15 | Sync and remove all non-FOSS parts |
| `e289996cf97` | 2026-10-16 | Sync and remove all non-FOSS parts |

두 커밋 모두 상태가 `D`(삭제) 1016개와 `M`(수정) 1개다.
`e289996cf97`이 지운 범위는 아래와 같다. 근거: `git show --name-status e289996cf97`.

| 경로                     | 삭제한 파일 수 | 비고                                                                                                                                                                                  |
| ------------------------ | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ee/hogai`               | 490            |                                                                                                                                                                                       |
| `ee/api`                 | 129            |                                                                                                                                                                                       |
| `ee/migrations`          | 68             |                                                                                                                                                                                       |
| `ee/billing`             | 45             |                                                                                                                                                                                       |
| `ee/clickhouse`          | 33             |                                                                                                                                                                                       |
| `ee/partners`            | 31             |                                                                                                                                                                                       |
| `ee/tasks`               | 21             |                                                                                                                                                                                       |
| `ee/models`              | 13             |                                                                                                                                                                                       |
| `ee/` 나머지             | 45             | `vercel`, `management`, `benchmarks`, `support_sidebar_max`, `bin`, `surveys`, `sqs`, `certs`, `admin`, `session_recordings`, `urls.py`, `settings.py`, `middleware.py`, `LICENSE` 등 |
| `.github/workflows`      | 140            | CI 워크플로 전부                                                                                                                                                                      |
| `.github/dependabot.yml` | 1              |                                                                                                                                                                                       |

수정한 파일은 `LICENSE` 하나다.
"Portions of this software are licensed as follows" 단락과 그 아래 항목 세 개를 지웠다.
세 항목은 `ee/` 안내 문구, 제3자 구성 요소는 원래 라이선스를 따른다는 문구, 나머지는 "MIT Expat"이라는 문구다.
그리고 `MIT License` 제목을 맨 위에 붙이고, `Copyright (c) 2020-2026 PostHog Inc.` 줄을 그 아래로 옮겼다. 근거: `git show e289996cf97 -- LICENSE`.
라이선스 영향은 [라이선스](licenses.md)와 [ADR 0001](adr/0001-remove-non-foss.md)에서 다룬다.

현재 트리에서 `ee/`는 없다(`git ls-files ee`가 0줄).
`.github/workflows`도 없다(`git ls-files .github/workflows`가 0줄).

### 알려진 부작용: 끊어진 `ee` import (해소됨)

`ee/`를 지운 직후에는 `from ee...` 또는 `import ee`를 쓰는 Python 파일이 264개 남아 있었다.
에픽 `buzzhog-dsv8`(병합 `ca37aa9e209`)이 이를 정리했다.
지금 남은 파일은 4개이고 모두 `ee`가 없어도 되도록 감싼 확장 지점이다.
근거: `git grep -lE '^\s*(from|import) ee(\.|\s|$)' -- '*.py'`가 `posthog/ee_urls.py`, `posthog/settings/__init__.py`, `posthog/settings/ee.py`, `posthog/settings/web.py`만 보여 준다.
어떤 기능을 자르고 어떤 자리를 남겼는지는 [ADR 0002](adr/0002-remove-ee-residue-keep-extension-points.md)에 적었다.

업스트림을 다시 병합하면 업스트림이 새로 넣은 `from ee` import가 들어올 수 있다.
위 명령으로 병합 뒤에 확인한다.

## 패치 로그

포크가 업스트림과 다르게 고친 파일의 기록이다.

### 지금까지의 차이

`master`(`70371e9eb38`)의 트리는 업스트림 끝 커밋 `e289996cf97`의 트리와 같았다.
근거: `git diff --stat e289996cf97 70371e9eb38`의 출력이 비어 있다.
그 뒤 에픽 `buzzhog-dsv8`이 `ee` 잔재를 걷어 내면서 코드 패치가 처음 생겼다.
이 패치는 마일스톤 브랜치 `milestone/buzzhog-tfjd`에 병합 커밋 `ca37aa9e209`로 들어 있다.
근거: `git log --oneline e289996cf97..ca37aa9e209 -- . ':!wiki'`.

업스트림 끝 `e289996cf97`과 비교한 차이는 `wiki/`를 뺀 파일 503개다(추가 7, 삭제 147, 수정 349).
근거: `git diff --name-status e289996cf97 ca37aa9e209 -- . ':!wiki'`.
이 수는 `ca37aa9e209`에서 센 값이다. 이후 커밋이 들어오면 위 명령으로 다시 센다.

같은 파일을 여러 번 고친 경우가 있으므로, 파일별 행 대신 영역별로 묶어 적는다.
다음 동기화에서 충돌이 나면 영역의 커밋으로 `git log --oneline e289996cf97..HEAD -- <파일>`을 돌려 포크 수정을 찾는다.

| 영역                                 | 파일                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | 이유                                                                                                                                                                                                                | 커밋                                                                      | 업스트림 반영 |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------- |
| `ee` import 정리, `posthog/`         | 모듈 수십 개. 예: `posthog/api/rest_router.py`, `posthog/tasks/usage_report.py`, `posthog/tasks/scheduled.py`                                                                                                                                                                                                                                                                                                                                                                                                      | 지운 `ee/`를 가져오는 import를 없애거나 조건부로 바꿨다. SCIM, billing, 쿼터 제한, 라이선스, Vercel, 구체화 컬럼 관리, PostHog AI temporal 워크플로, Salesforce 보강을 삭제했다                                     | `1ab1a2084d5`, `7589e6af6ab`                                              | 없음          |
| `ee` import 정리, `products/`        | 34개 제품 모듈. `max_tools.py`를 삭제한 제품이 많다                                                                                                                                                                                                                                                                                                                                                                                                                                                                | 쿼터는 제한 없음, billing 정보 없음, 구독 발송은 꺼짐으로 자른다. 실험의 holdout·saved metric serializer를 `products/experiments/backend/presentation/holdout_serializers.py`로 새로 썼다                           | `486af9263a3`                                                             | 없음          |
| RBAC 모델의 앱 레이블                | `products/access_control/backend/models/`, `products/access_control/backend/migrations/0000_rbac_models.py`, `0004_featureflagroleaccess.py`, 의존을 고친 마이그레이션 29개                                                                                                                                                                                                                                                                                                                                        | `Role`, `RoleMembership`, `AccessControl`, `FeatureFlagRoleAccess`, `OrganizationResourceAccess`가 `ee` 앱에 있어 마이그레이션 그래프가 끊겼다. 앱 레이블을 `access_control`로 옮기고 테이블 이름 `ee_*`는 유지했다 | `84dbc958ac3`                                                             | 없음          |
| 설정                                 | `posthog/settings/email.py`, `posthog/settings/llm.py`(새 파일), `posthog/settings/__init__.py`                                                                                                                                                                                                                                                                                                                                                                                                                    | 지운 `ee` 설정만 정의하던 Customer.io와 LLM 제공자 설정 14개를 환경변수로 읽게 했다                                                                                                                                 | `772ab459cce`                                                             | 없음          |
| 도구 설정                            | `tach.toml`, mypy·ruff·import-linter 설정, 소유자 파일                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `ee`를 목록에서 뺐다                                                                                                                                                                                                | `cfb59cf0e3b`                                                             | 없음          |
| 이미지                               | `Dockerfile`, `Dockerfile.llm-analytics`, `.dockerignore`                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `ee` 복사와 `compileall` 대상을 뺐다                                                                                                                                                                                | `0ac1ea3a6a1`                                                             | 없음          |
| 리뷰 수정                            | `posthog/api/authentication.py`, `bin/start-backend`, `services/agent-proxy/` 등 17개                                                                                                                                                                                                                                                                                                                                                                                                                              | 도메인이 다른 SSO를 강제할 때 GitHub·GitLab 로그인을 거절하는 단계를 FOSS로 새로 넣었다. 테스트가 쓰던 이름을 고쳤다                                                                                                | `abcf3ec53fa`, `accf3d0501a`                                              | 없음          |
| 지운 라우트의 프런트 호출부, billing | `frontend/src/scenes/billing/billingReads.ts`, `paymentEntryLogic.ts`, `billingUsageLogic.ts`, `billingSpendLogic.ts`, `BillingUsage.tsx`, `BillingSpendView.tsx`와 그 테스트                                                                                                                                                                                                                                                                                                                                      | 재생성된 billing 클라이언트에 없는 함수를 가져와 프런트 빌드가 깨졌다. 사용량·지출 읽기와 결제 단계는 API를 부르지 않고 "이 버전에서는 쓸 수 없음"으로 끝난다                                                       | `83c159fbcc8`, `be7dec8258e`, `07ae0bbf0e2`, `7590400ca28`, `6ae3f52633c` | 없음          |
| 지운 라우트의 프런트 호출부, 그 밖   | `frontend/src/scenes/max/`(대화 삭제), `frontend/src/scenes/settings/environment/usageMetricsConfigLogic.ts`·`UsageMetricsConfig.tsx`, `frontend/src/scenes/notebooks/Nodes/NotebookNodeUsageMetrics.tsx`, 속성 정의 편집 모달과 `queryDatabaseLogic.tsx`, `products/business_intelligence/frontend/biPropertyFields*.ts`, `frontend/src/scenes/experiments/holdoutsLogic.tsx`, `products/experiments/frontend/scenes/ExperimentsHoldoutsScene.tsx`, `frontend/src/scenes/authentication/vercel/VercelConnect.tsx` | 같은 이유다. 대화 삭제, 사용량 지표 추가, holdout 만들기는 이유를 단 비활성 버튼이 되었다. 속성 정의 편집에서 설명·상태 필드를 뺐다. Vercel 연결 화면은 안내만 보여 준다                                            | `696eedb6ae5`, `eecb551e376`, `79b95d49310`, `180e226c05a`, `be7dec8258e` | 없음          |

### 이후 기록하는 방법

포크에서 업스트림 파일을 고칠 때마다 위 표에 한 행을 더한다.

1. 커밋 제목에 이유를 쓴다. 예: `fix(scope): ...`.
2. 표에 파일 경로, 이유, 커밋 해시를 적는다. 해시는 `git rev-parse --short`로 얻는다.
3. 다음 동기화에서 충돌이 날 파일을 미리 알 수 있도록, 새로 고치는 파일은 파일 경로를 적은 행으로 따로 둔다. 같은 파일을 두 번 고쳐도 행을 합치지 않는다. 에픽 하나가 수십 개 파일을 같은 이유로 고친 경우만 위 표처럼 영역 행으로 묶고, 커밋 해시로 파일을 다시 찾는다.
4. 업스트림이 같은 수정을 가져오면 행을 지우지 말고 "업스트림 반영" 열에 해시를 적는다.

현재 차이 목록을 다시 만드는 명령:

```bash
LAST_UPSTREAM=$(git log -1 --format=%H --author=foss-sync HEAD)
git diff --name-status "$LAST_UPSTREAM" HEAD -- . ':!wiki'
```

`LAST_UPSTREAM`은 마지막으로 병합한 업스트림 끝, 곧 `HEAD` 이력에서 가장 최근 봇 커밋이다.
git 이력에서 구하므로 손으로 갱신하지 않는다.
업스트림 끝이 봇 커밋일 때만 병합한다는 아래 "동기화 전에 확인할 것"을 지켜야 이 값이 맞다.

`upstream/master`와 바로 비교하지 않는다.
업스트림이 앞서 나가면 아직 병합하지 않은 업스트림 변경이 모두 포크의 차이로 나온다.
`upstream/master...HEAD`(merge-base 기준)도 쓰지 않는다.
업스트림이 이력을 다시 쓰므로 merge-base가 `ee/`가 있는 `PostHog/posthog` 커밋이 되고, 봇이 지운 파일과 `LICENSE` 수정이 포크의 차이로 나온다.
근거: 지금의 merge-base 자리인 `7010e516600`과 비교한 `git diff --name-status 7010e516600 HEAD -- . ':!wiki'`가 `D` 1016개와 `M` 1개(`LICENSE`)를 낸다.

## 동기화 절차 (제안)

아래는 제안이다. 주기와 브랜치 정책은 **결정 필요**다.

### 결정 필요

| 항목                   | 제안                                                             | 이유                                                                                                                                                                                                                             |
| ---------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 주기                   | 2주에 한 번, 보안 수정은 즉시                                    | 마지막 병합(`70371e9eb38`)은 약 23시간 동안 쌓인 커밋 327개를 가져왔다(`4e824e99423` 2026-10-15 05:35 UTC부터 `7010e516600` 2026-10-16 04:13 UTC까지, 봇 커밋 포함). 같은 속도라면 2주에 수천 개다. 간격이 길수록 충돌이 커진다. |
| 동기화 브랜치          | `master`에 직접 병합하지 말고 `sync/YYYY-MM-DD`에서 병합한 뒤 PR | 끊어진 `ee` import를 병합 전에 검사할 자리가 생긴다.                                                                                                                                                                             |
| 병합 방식              | `git merge`(리베이스 안 함)                                      | 지금까지의 방식과 같고 업스트림 해시가 보존된다.                                                                                                                                                                                 |
| `upstream` remote 등록 | 등록한다                                                         | 현재 로컬에 없다.                                                                                                                                                                                                                |

### 단계

1. `upstream` remote를 등록하고 가져온다.
   가져온 뒤, 병합하기 전에 아래 "동기화 전에 확인할 것"을 먼저 본다.

   ```bash
   git remote add upstream https://github.com/PostHog/posthog-foss.git
   git fetch upstream
   git log -1 --format='%an %s' upstream/master
   ```

2. 최신 `origin/master`에서 동기화 브랜치를 만든다.
   로컬 `master`는 뒤처져 있을 수 있다.

   ```bash
   git fetch origin
   git switch -c sync/YYYY-MM-DD origin/master
   ```

3. 업스트림을 병합한다.

   ```bash
   git merge upstream/master
   ```

4. 충돌은 이 순서로 푼다.
   1. 패치 로그 표에 있는 파일: 포크 수정을 유지하면서 업스트림 변경을 받는다.
   2. `LICENSE`: 업스트림 본문이 `MIT License` 단일 본문인지 확인한다. 라이선스 문구가 `ee/`를 말하면 업스트림이 되돌린 것이다.
   3. `ee/`, `.github/workflows`, `.github/dependabot.yml`: 아래 "non-FOSS 재유입 확인"으로 처리한다.
   4. 그 밖의 파일: 충돌은 양쪽이 모두 고친 파일에서만 난다.
      패치 로그 표에 없는 파일에서 충돌이 나면 표에 적지 않은 포크 수정이 있다는 뜻이다.
      `git log --oneline "$LAST_UPSTREAM"..HEAD -- <파일>`로 포크 커밋을 찾아 표에 더한 뒤 1과 같이 푼다.
      `LAST_UPSTREAM`은 위 "현재 차이 목록을 다시 만드는 명령"에서 구한다.
      병합 중에는 `HEAD`가 병합 전 커밋이라 지난번 업스트림 끝이 나온다.
      업스트림 쪽을 그대로 택하면 그 포크 수정이 사라진다.
5. non-FOSS 재유입을 확인한다(아래).
6. `hogli test --changed`로 변경된 파일의 테스트를 돌린다.
   끊어진 `ee` import 때문에 병합 전부터 실패하는 테스트가 있을 수 있다(미확인).
   실패가 나면 같은 테스트를 `origin/master`에서 돌려, 병합 전부터 실패했는지 비교한다.
7. PR을 만들어 병합한다.
   GitHub에서는 "Create a merge commit"으로 병합한다. 근거: `gh api repos/buzzni/buzzhog`의 `allow_merge_commit`이 `true`다.
   squash나 rebase로 병합하지 않는다.
   squash나 rebase로 병합하면 업스트림 커밋이 포크 `master`의 조상이 되지 않는다.
   그러면 다음 동기화의 merge-base가 앞으로 나가지 않아, 이미 받은 업스트림 변경을 다시 병합하게 되고 포크가 고친 파일에서 충돌이 쌓인다.
8. **upstream 머지 후 `moai-wiki` sweep을 실행한다.** 위키 페이지의 `확인 기준 커밋`과 근거(`파일:심볼`)를 새 `HEAD`에 맞춰 갱신한다.
   이 페이지의 "마지막으로 병합한 업스트림 끝"도 병합한 `upstream/master` 해시로 바꾼다.

### non-FOSS 재유입 확인

병합 뒤 아래 두 명령의 결과가 모두 비어 있어야 한다.
`git ls-files`는 인덱스를 보므로 충돌을 푸는 중에도 쓸 수 있다.

```bash
git ls-files ee .github/workflows .github/dependabot.yml
grep -n 'ee/' LICENSE
```

`git ls-files`의 결과가 비어 있지 않으면 업스트림이 해당 경로를 다시 넣은 것이다.
다시 들어온 파일은 지우고, 왜 들어왔는지(업스트림의 FOSS 동기화가 중단됐는지 등)를 동기화 PR 설명에 적는다.
non-FOSS 파일을 받아들이는 등 [ADR 0001](adr/0001-remove-non-foss.md)의 결정을 바꾸면 새 ADR을 쓰고, ADR 0001의 상태를 `대체됨(ADR NNNN)`으로 바꾼다.
`NNNN`은 새 ADR의 번호다.
채택한 ADR 본문은 [고치지 않는다](adr/README.md#작성법).

`grep`의 결과가 비어 있지 않으면 업스트림이 `LICENSE`의 `ee/` 단락을 되돌린 것이다.
그리고 `LICENSE`가 `MIT License`로 시작하는지 본다.

```bash
head -1 LICENSE
```

### 동기화 전에 확인할 것

- 업스트림 끝이 봇 커밋(`Sync and remove all non-FOSS parts`)인지 확인한다. 봇 커밋이 아닌 끝을 병합하면 `ee/`가 들어올 수 있다.
  확인 명령: `git log -1 --format='%an %s' upstream/master`.
- 업스트림 끝이 봇 커밋이 아닐 때 어떻게 할지(다음 봇 커밋까지 기다릴지)는 **결정 필요**다.

## 관련 문서

- 레이아웃 원문: [monorepo-layout.md](../docs/internal/monorepo-layout.md)
- 라이선스 영향: [라이선스](licenses.md)
- 결정 기록: [ADR 0001: non-FOSS 제거](adr/0001-remove-non-foss.md), [ADR 0002: ee 잔재 제거와 확장 지점](adr/0002-remove-ee-residue-keep-extension-points.md)
- 용어: [용어집](glossary.md)

Decided in: buzzhog-whby, buzzhog-dsv8, buzzhog-miju
