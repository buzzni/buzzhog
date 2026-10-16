# 업스트림 동기화

확인 기준 커밋: a24aeab6d4e

이 페이지는 buzzhog가 PostHog 업스트림을 따라가는 방식과, 포크가 업스트림과 다르게 고친 곳(패치 로그)을 적는다.
근거는 `git log`와 `git show`로 확인한 것만 쓴다.
확인하지 못한 항목은 "미확인", 사람이 정해야 할 항목은 "결정 필요"로 표시한다.

## 현재 상태

### 저장소 관계

- `origin`은 `https://github.com/buzzni/buzzhog.git`이다. 근거: `git remote -v`.
- 로컬 clone에는 `upstream` remote가 없다. 근거: `git remote -v`는 `origin`만 보여 준다.
- 업스트림은 GitHub의 `PostHog:master`로 보인다. 근거: 병합 커밋 `70371e9eb38`의 제목 `Merge branch 'PostHog:master' into master`.
  업스트림 저장소의 정확한 이름(`PostHog/posthog` 또는 FOSS 미러)은 미확인이다.
  아래 "non-FOSS 제거 커밋"의 작성자가 봇이라는 점만 확인했다.

### 동기화 방식

포크는 업스트림 `master`를 포크의 `master`로 병합하는 방식으로 따라간다.
이 병합은 GitHub의 "Sync fork" 동작으로 만든 것으로 보인다(미확인: 병합 커밋 제목이 그 기본 형식이다).

- 병합 커밋 `70371e9eb38`의 부모는 `b068ff99030`(포크 `master`의 이전 끝)과 `e289996cf97`(업스트림 끝)이다. 근거: `git log -1 --format='%p' 70371e9eb38`.
- 이 병합이 가져온 변경은 2464개 파일이다. 근거: `git diff --stat 70371e9eb38^1 70371e9eb38`.
- 포크 쪽 부모 `b068ff99030`도 업스트림이 만든 봇 커밋이다.
  포크 `master`는 지금까지 업스트림 커밋만 쌓였고, 포크가 만든 코드 커밋은 없다.

### non-FOSS 제거 커밋

업스트림 이력에 `posthog-foss-sync[bot]`이 만든 커밋 두 개가 있다. 근거: `git log --author=foss-sync`.

| 커밋 | 날짜 | 제목 |
| --- | --- | --- |
| `b068ff99030` | 2026-10-15 | Sync and remove all non-FOSS parts |
| `e289996cf97` | 2026-10-16 | Sync and remove all non-FOSS parts |

두 커밋 모두 상태가 `D`(삭제) 1016개와 `M`(수정) 1개다.
`e289996cf97`이 지운 범위는 아래와 같다. 근거: `git show --name-status e289996cf97`.

| 경로 | 삭제한 파일 수 | 비고 |
| --- | --- | --- |
| `ee/hogai` | 490 | |
| `ee/api` | 129 | |
| `ee/migrations` | 68 | |
| `ee/billing` | 45 | |
| `ee/clickhouse` | 33 | |
| `ee/partners` | 31 | |
| `ee/tasks` | 21 | |
| `ee/models` | 13 | |
| `ee/` 나머지 | 45 | `vercel`, `management`, `benchmarks`, `support_sidebar_max`, `bin`, `surveys`, `sqs`, `certs`, `admin`, `session_recordings`, `urls.py`, `settings.py`, `middleware.py`, `LICENSE` 등 |
| `.github/workflows` | 140 | CI 워크플로 전부 |
| `.github/dependabot.yml` | 1 | |

수정한 파일은 `LICENSE` 하나다.
"Portions of this software are licensed as follows" 단락과 `ee/` 안내 문구를 지우고 `MIT License` 제목을 붙였다.
라이선스 영향은 [라이선스](licenses.md)와 [ADR 0001](adr/0001-remove-non-foss.md)에서 다룬다.

현재 트리에서 `ee/`는 없다(`git ls-files ee`가 0줄).
`.github/workflows`도 없다(`git ls-files`에서 0건).

### 알려진 부작용: 끊어진 `ee` import

`ee/`를 지웠지만 `from ee...` 또는 `import ee`를 쓰는 Python 파일이 264개 남아 있다.
근거: `git grep -lE '^\s*(from|import) ee(\.|\s|$)' -- '*.py'`. 예: `posthog/admin/admins/conversation_admin.py`, `posthog/admin/admins/oauth_admin.py`.
이 import가 실행 시점에 어떻게 처리되는지는 미확인이다(조건부 import인지, 깨지는지 확인하지 않았다).
영향 조사는 [모듈 지도](modules.md)와 [설정](configuration.md)에서 이어서 다룬다.

## 패치 로그

포크가 업스트림과 다르게 고친 파일의 기록이다.

### 지금까지의 차이

`master`(`70371e9eb38`)의 트리는 업스트림 끝 커밋 `e289996cf97`의 트리와 같다.
근거: `git diff --stat e289996cf97 70371e9eb38`의 출력이 비어 있다.
따라서 코드 패치는 없다.

현재 위키 브랜치와 업스트림 끝의 차이는 `wiki/` 아래 파일 추가뿐이다. 근거: `git diff --name-status e289996cf97 HEAD`.

| 파일 | 이유 | 커밋 |
| --- | --- | --- |
| (없음) | 코드 패치 없음 | - |

### 이후 기록하는 방법

포크에서 업스트림 파일을 고칠 때마다 위 표에 한 행을 더한다.

1. 커밋 제목에 이유를 쓴다. 예: `fix(scope): ...`.
2. 표에 파일 경로, 이유, 커밋 해시를 적는다. 해시는 `git rev-parse --short`로 얻는다.
3. 다음 동기화에서 충돌이 날 파일을 미리 알 수 있도록, 같은 파일을 두 번 고치면 행을 합치지 말고 따로 둔다.
4. 업스트림이 같은 수정을 가져오면 행을 지우지 말고 "업스트림 반영" 열(추가 예정)에 해시를 적는다.

현재 차이 목록을 다시 만드는 명령:

```bash
git fetch upstream
git diff --name-status upstream/master HEAD -- . ':!wiki'
```

## 동기화 절차 (제안)

아래는 제안이다. 주기와 브랜치 정책은 **결정 필요**다.

### 결정 필요

| 항목 | 제안 | 이유 |
| --- | --- | --- |
| 주기 | 2주에 한 번, 보안 수정은 즉시 | 마지막 병합(`70371e9eb38`)이 327개 커밋을 한 번에 가져왔다. 간격이 길수록 충돌이 커진다. |
| 동기화 브랜치 | `master`에 직접 병합하지 말고 `sync/YYYY-MM-DD`에서 병합한 뒤 PR | 끊어진 `ee` import를 병합 전에 검사할 자리가 생긴다. |
| 병합 방식 | `git merge`(리베이스 안 함) | 지금까지의 방식과 같고 업스트림 해시가 보존된다. |
| `upstream` remote 등록 | 등록한다 | 현재 로컬에 없다. |

### 단계

1. `upstream` remote를 등록하고 가져온다. 주소는 위에서 말한 대로 미확인이므로 확정 후 쓴다.

   ```bash
   git remote add upstream <확정한 주소>
   git fetch upstream
   ```

2. 동기화 브랜치를 만든다.

   ```bash
   git switch -c sync/YYYY-MM-DD master
   ```

3. 업스트림을 병합한다.

   ```bash
   git merge upstream/master
   ```

4. 충돌은 이 순서로 푼다.
   1. 패치 로그 표에 있는 파일: 포크 수정을 유지하면서 업스트림 변경을 받는다.
   2. `LICENSE`: 업스트림 본문이 `MIT License` 단일 본문인지 확인한다. 라이선스 문구가 `ee/`를 말하면 업스트림이 되돌린 것이다.
   3. `ee/`, `.github/workflows`: 아래 "non-FOSS 재유입 확인"으로 처리한다.
   4. 그 밖의 파일: 업스트림 쪽을 택한다.
5. non-FOSS 재유입을 확인한다(아래).
6. `hogli test --changed`로 변경된 파일의 테스트를 돌린다.
7. PR을 만들어 병합한다.
8. **upstream 머지 후 `moai-wiki` sweep을 실행한다.** 위키 페이지의 `확인 기준 커밋`과 근거(`파일:심볼`)를 새 `HEAD`에 맞춰 갱신한다.

### non-FOSS 재유입 확인

병합 뒤 아래 명령의 결과가 모두 비어 있어야 한다.

```bash
git ls-files ee
git ls-files .github/workflows
git diff --name-only HEAD~1 -- ee .github/workflows
```

비어 있지 않으면 업스트림이 해당 경로를 다시 넣은 것이다.
추가한 파일은 지우고, 왜 들어왔는지(업스트림의 FOSS 동기화가 중단됐는지 등)를 [ADR 0001](adr/0001-remove-non-foss.md)에 적는다.

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
- 결정 기록: [ADR 0001: non-FOSS 제거](adr/0001-remove-non-foss.md)
- 용어: [용어집](glossary.md)

Decided in: buzzhog-whby
