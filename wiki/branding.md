# 브랜딩·상표 잔존 위치

확인 기준 커밋: 70371e9eb38

이 포크에 남아 있는 PostHog 상표와 브랜딩의 위치다. 법무 검토용 표 형식으로 적었다.
`posthog`라는 단어는 Python 패키지명(`import posthog`), Docker 이미지명, GitHub 조직명으로도 쓰여서 단순 검색 횟수는 브랜딩 사용량이 아니다. 이 문서는 사용자 눈에 보이는 이름·로고·도메인과 그 파일 위치를 가른다.
저작권 고지와 의존성 라이선스는 [licenses.md](licenses.md), 외부로 나가는 호출은 [external-calls.md](external-calls.md)를 본다.

기준: 파일 개수는 `git ls-files`와 `git grep` 결과이며 대소문자를 구분한 `PostHog`(제품명 표기)를 센 곳은 그렇다고 적었다.

## 로고와 아이콘 파일

| 위치 | 파일 | 용도 | 근거 |
| --- | --- | --- | --- |
| `frontend/public/` | `posthog-logo.svg`, `posthog-logo.png`, `posthog-icon.svg` | 앱 로고. 이메일 템플릿이 `posthog-logo.png`를 쓴다 | `posthog/templates/email/base.html` (20행) |
| `frontend/public/icons/` | `favicon.ico`, `favicon-16x16.png`, `favicon-32x32.png`, `favicon-dev.ico`, `apple-touch-icon.png`, `android-chrome-192x192.png`, `android-chrome-512x512.png`, `safari-pinned-tab.svg` (8개) | 파비콘, 홈 화면 아이콘 | `posthog/templates/head.html` (10~22행) |
| `frontend/public/site.webmanifest` | `name`·`short_name`이 `PostHog` | PWA 이름 | `frontend/public/site.webmanifest` |
| `.github/` | `posthog-logo-light.svg`, `posthog-logo-dark.svg` | README 머리 로고 | `README.md` (3~4행) |
| `frontend/public/hedgehog/` | `hog-welder.png`, `self-driving-hog.png` | 헤지호그 마스코트 | `frontend/public/hedgehog/` |
| `frontend/public/` | `not-found-astrohog.png`, `blank-dashboard-hog.png` | 404·빈 화면 일러스트 | |
| `frontend/public/email/` | `invite-email-welcome.png` 외 화살표 아이콘 4개 | 이메일 본문 이미지 | |
| `frontend/public/posthog-ai-onboarding/` | `connect`, `delegate`, `meet`, `skills`, `start`의 `.jpg`와 `.mp4` (10개) | PostHog AI 온보딩 영상·이미지 | |
| `frontend/public/services/` | 제3자 서비스 로고(예: `Google_Sheets.svg`, `Mongodb.svg`) | 이 항목은 PostHog 상표가 아니라 제3자 상표 | |
| `products/desktop/apps/mobile/assets/`, `products/desktop/apps/mobilehog/assets/` | `favicon.png`, `app-icon.png`, `adaptive-icon.png` 등 | 데스크톱·모바일 앱 아이콘 | `products/desktop/apps/mobile/assets/` |

## `@posthog/brand` 패키지

브랜드 자산을 npm 패키지로 가져온다. 이 패키지는 다른 의존성과 성격이 다르다.

| 항목 | 내용 | 근거 |
| --- | --- | --- |
| 의존 선언 | `frontend/package.json`에서 `"@posthog/brand": "catalog:"` | `frontend/package.json:77` |
| 사용 범위 | `.ts`, `.tsx`, `.css`, `.scss`에서 이 패키지를 가져오는 파일이 `frontend/src` 68개, `products/dashboards` 10개, `products/customer_analytics` 10개, `products/workflows` 7개, `products/ai_observability` 7개 등 | `git grep -l '@posthog/brand'` |
| 라이선스 | PolyForm Strict License 1.0.0. 패키지 `LICENSE`가 "소스 공개형이며 오픈소스가 아니다. 상업적 사용, 자기 프로젝트에서의 사용, 배포, 파생물은 허가되지 않는다"고 적고, 헤지호그 일러스트는 PostHog 상표·브랜드 자산이라고 명시한다 | `npm pack @posthog/brand@0.12.3`의 `LICENSE` |
| 영향 | 이 포크가 재배포·상업 운영을 하면 이 패키지는 라이선스 밖에 놓인다. 패키지를 걷어내는 비용은 미확인(소스 파일 수는 위 참고) | [licenses.md](licenses.md) |

헤지호그 UI는 `@posthog/hedgehog-mode`(MIT 선언)가 맡고 `gsap`(비-OSI)을 끌어온다. 이를 가져오는 소스 파일은 12개다(`git grep -l '@posthog/hedgehog-mode'`).

## 제품명 문구

| 위치 | 내용 | 규모 | 근거 |
| --- | --- | --- | --- |
| `frontend/src/` | 사용자에게 보이는 `PostHog` 문자열 | 882개 파일에 `PostHog`가 있음. 이 중 코드 식별자·주석 비율은 가르지 않았다 | `git grep -l 'PostHog' -- frontend/src` |
| `frontend/src/` | `hedgehog` 언급 | 168개 파일(대소문자 무시) | `git grep -l -i hedgehog -- frontend/src` |
| `frontend/src/layout.html` | `<title>PostHog</title>` | 1 | `frontend/src/layout.html:6` |
| `frontend/src/index.html` | 콘솔 인사말(`PostHog — In data we trust`, 채용 링크 `https://posthog.com/careers`)과 구형 브라우저 안내문 | 2곳 | `frontend/src/index.html:59`, `:62`, `:78` |
| `posthog/templates/head.html` | 기본 페이지 제목 `page_title|default:"PostHog"` | 1 | `posthog/templates/head.html:1` |
| `posthog/templates/` | `PostHog`가 들어 있는 템플릿 | 47개 파일(전체 145개 중) | `git grep -l 'PostHog' -- posthog/templates` |
| `posthog/templates/email/` | 이메일 템플릿 | 74개 중 38개가 `PostHog` 포함. 기본 틀 `base.html`이 로고(`alt="PostHog"`)를 넣는다 | `posthog/templates/email/base.html` |
| `frontend/public/` | `PostHog`가 들어 있는 파일 | 2개(`site.webmanifest` 포함) | `git grep -l 'PostHog' -- frontend/public` |

## 도메인

코드에서 센 `*.posthog.com` 계열 문자열이다. 테스트, 문서, 마이그레이션, 잠금 파일, `.md`를 뺐다. 값은 반올림 없는 그대로이며 같은 줄의 중복을 포함한다.

| 도메인 | 횟수 | 성격 |
| --- | --- | --- |
| `posthog.com` (하위 도메인 없음) | 3628 | 문서·가이드 링크가 대부분으로 추정(미확인) |
| `app-static-prod.posthog.com` | 683 | 정적 자산 CDN(CSP `font-src`에 포함). 대부분 스냅샷·고정 데이터에서 나온다고 보이나 미확인 |
| `app-static.eu.posthog.com` | 459 | EU 정적 자산 CDN |
| `internal-j.posthog.com` | 457 | `frontend/src` 2개, `rust/cymbal` 1개, `posthog/test` 1개 파일에서 나온다. 많은 횟수는 파일 하나에 몰려 있다고 추정 |
| `us.posthog.com` | 333 | 리전 앱 호스트 |
| `us.i.posthog.com` | 105 | 수집(ingest) 호스트 |
| `app.posthog.com` | 93 | 구 앱 호스트 |
| `eu.posthog.com` | 81 | EU 앱 호스트 |
| `mcp.posthog.com`, `oauth.posthog.com`, `code.posthog.com`, `gateway.us.posthog.com` | 15, 9, 9, 6 | 서비스별 호스트 |
| `eu.i.posthog.com` | 15 | EU 수집 호스트 |
| `mmdbcdn.posthog.net` | 12 | GeoIP 파일 CDN |
| `*.dev.posthog.dev`, `posthog.dev` | 6 이상, 9 | 개발·내부 환경 호스트 |
| `releases.posthog.com` | 8 | CLI 릴리스 |
| `posthog.org` | 6 | |

호출 의미와 끄는 방법은 [external-calls.md](external-calls.md)에 둔다. 이메일 주소는 `@posthog.com`이 `posthog/`, `frontend/src`, `nodejs/src`, `products`(테스트·마이그레이션 제외)에서 212개 파일 634회 나온다.
발신자 주소의 기본값은 `root@localhost`이다(`posthog/settings/dynamic_settings.py:169~170`의 `EMAIL_DEFAULT_FROM`). `PostHog` 이름으로 보내는 하드코딩 발신자는 찾지 않았다(미확인).

## 디렉터리별 `posthog` 문자열 (참고)

`git grep -I -i posthog` 결과다. 패키지명과 import 구문이 대부분이라 브랜딩 사용량은 아니다.

| 디렉터리 | 파일 수 | 줄 수 |
| --- | --- | --- |
| `products/` | 17119 | 104211 |
| `posthog/` | 5035 | 81479 |
| `frontend/src/` | 3247 | 14134 |
| `rust/` | 614 | 8659 |
| `services/` | 783 | 7063 |
| `packages/` | 482 | 5156 |
| `docs/` | 320 | 3367 |
| `nodejs/src/` | 552 | 2673 |
| `tools/` | 206 | 2371 |
| `bin/` | 112 | 783 |
| `cli/` | 63 | 653 |
| `common/` | 81 | 267 |
| `docker/` | 18 | 159 |

## 저작권 고지

| 위치 | 내용 |
| --- | --- |
| `LICENSE` | `Copyright (c) 2020-2026 PostHog Inc.` (MIT) |
| `rust/LICENSE` | `Copyright (c) 2023 PostHog` |
| `packages/quill/LICENSE`, `packages/owners-yaml/LICENSE`, `products/desktop/LICENSE`, `tools/hogli/LICENSE` | `Copyright (c) 2026 PostHog Inc.` |

MIT는 저작권 고지와 허가 문구의 보존을 요구한다. 상표 사용은 MIT가 허가하지 않는다(법적 해석은 법무 몫).

## 미확인

- `docs/`, `README.md` 등 마크다운 본문의 브랜딩은 이 조사에서 제외했다.
- `products/` 아래 제품별 브랜딩 자산(로고 외)의 전수 목록은 만들지 않았다.
- 각 도메인 횟수의 출처 파일 분포는 `internal-j.posthog.com`만 확인했다.

Decided in: buzzhog-gimc
