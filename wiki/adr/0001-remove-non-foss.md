# ADR 0001: non-FOSS 부분 제거를 따라간다

확인 기준 커밋: 79b3714e131

상태: 채택

## 맥락

`PostHog/posthog`의 `LICENSE`는 `ee/` 디렉터리에 별도 Enterprise 라이선스를 걸고, 그 밖의 코드는 "MIT Expat"으로 둔다.
근거: 커밋 `e289996cf97^`(`7010e516600`)의 `LICENSE`(`ee/` 아래 내용은 `ee/LICENSE`를 따른다는 문구).
`ee/LICENSE`는 운영 환경에서 쓰려면 PostHog 구독 약관(또는 별도 합의)에 동의하고 유효한 Enterprise 라이선스도 있어야 한다고 적는다. 근거: `git show e289996cf97^:ee/LICENSE`.
이 포크의 업스트림은 `PostHog/posthog-foss`다. 근거: [업스트림](../upstream.md).
포크 이력에는 `posthog-foss-sync[bot]`이 만든 커밋이 두 개 있고, 둘 다 제목이 `Sync and remove all non-FOSS parts`다.
`b068ff99030`(2026-10-15)과 `e289996cf97`(2026-10-16)이다. 근거: `git log --author=foss-sync --format='%h %ad %s' --date=short`.

## 결정

업스트림 `posthog-foss`의 non-FOSS 제거를 그대로 받아들이고, 포크에서 `ee/`를 되살리지 않는다.
포크는 병합 커밋 `70371e9eb38`(제목 `Merge branch 'PostHog:master' into master`)에서 `e289996cf97`을 병합했다.
근거: `git log -1 --format='%p %s' 70371e9eb38`의 두 번째 부모가 `e289996cf97`이다.

`e289996cf97`이 지운 것은 파일 1016개다. 근거: `git show --name-status e289996cf97`.
`b068ff99030`도 같은 파일 1016개를 지우고 `LICENSE`를 같은 본문으로 바꿨다.
근거: 두 커밋의 `git show --name-status` 출력이 같고, `git diff b068ff99030 e289996cf97 -- LICENSE`가 비어 있다.

| 위치 | 삭제 파일 수 |
| --- | --- |
| `ee/` 전체 | 875 (`ee/hogai` 490, `ee/api` 129, `ee/migrations` 68, `ee/billing` 45, `ee/clickhouse` 33, `ee/partners` 31, 나머지) |
| `.github/workflows` | 140 |
| `.github/dependabot.yml` | 1 |

`LICENSE`는 수정됐다.
`ee/` 안내와 제3자 구성 요소 문구를 뺀 `MIT License` 단일 본문이 됐다. 근거: `git diff e289996cf97^ e289996cf97 -- LICENSE`.
`ee/LICENSE`도 함께 지워졌다.

왜 이 방식을 택했는지 포크 쪽 의사결정자의 기록은 저장소에서 찾지 못했다.
라이선스 정리가 목적으로 보이나 **미확인**이다.
확인한 근거는 위 `LICENSE` 변경뿐이다.

## 결과

- 루트 라이선스는 MIT 하나다. `ee/`는 없다. 근거: [라이선스](../licenses.md#저장소-자체-라이선스).
- 지운 `ee/`를 가져오는 Python 파일이 남아 있다([업스트림](../upstream.md#알려진-부작용-끊어진-ee-import)).
  실행 시점 영향은 한 곳만 확인했고, 나머지는 미확인이다.
  `posthog/settings/web.py`는 `from ee.apps import EnterpriseConfig`를 `try/except ImportError`로 감싸, `ee`가 없으면 `INSTALLED_APPS`에 넣지 않는다.
- `.github/workflows`가 없어 GitHub Actions 워크플로 정의가 포크에 없다.
  `.depot/workflows`에는 Depot CI 워크플로 4개(`ci-backend.yml` 등)가 남아 있다. 근거: `git ls-files .depot/workflows`.
  이 워크플로가 포크에서 돌아가는지는 미확인이다.
- 포크가 `PostHog/posthog`를 직접 병합하면, `PostHog/posthog`가 그사이 고친 `ee/`와 `.github/workflows` 파일이 modify/delete 충돌로 나온다.
  근거: [업스트림](../upstream.md#저장소-관계). 병합 절차는 [업스트림](../upstream.md)을 따른다.
- 업스트림이 이 방침을 되돌리면 이 ADR을 `대체됨`으로 바꾸고 새 ADR을 쓴다.

Decided in: buzzhog-a4ho
