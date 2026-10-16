# 의존성 라이선스

확인 기준 커밋: 70371e9eb38
재확인은 2026-10-16에 했다. `milestone/buzzhog-vltl`의 제품 코드는 이 커밋과 같다(`git diff --stat 70371e9eb38 milestone/buzzhog-vltl -- . ':!wiki' ':!.moai'`가 비어 있다).
레지스트리(PyPI, npm, Go 모듈 프록시) 조회와 tarball·웹 페이지 확인도 모두 2026-10-16에 했다.

법무 검토용 요약이다. 표를 먼저 두고, 집계 명령은 끝의 [집계 방법](#집계-방법)에 그대로 적었다.
브랜딩·상표 자산은 [branding.md](branding.md), 외부로 나가는 호출은 [external-calls.md](external-calls.md), `ee/` 제거 결정은 [adr/0001-remove-non-foss.md](adr/0001-remove-non-foss.md)를 본다.
"미확인"은 이 페이지를 쓰면서 직접 확인하지 못한 사실이다.

## 저장소 자체 라이선스

| 위치 | 라이선스 | 저작권자 | 근거 |
| --- | --- | --- | --- |
| 루트 | MIT | `Copyright (c) 2020-2026 PostHog Inc.` | `LICENSE` |
| `rust/` | MIT | `Copyright (c) 2023 PostHog` | `rust/LICENSE` |
| `packages/quill`, `packages/owners-yaml`, `products/desktop`, `tools/hogli` | MIT | `Copyright (c) 2026 PostHog Inc.` | 각 디렉터리의 `LICENSE` |
| `.github/actions/paths-filter`, `.depot/actions/paths-filter` | MIT(제3자 사본) | `Copyright (c) 2020 Michal Dorner and contributors` | 두 `LICENSE`는 같은 파일이다(`cmp` 결과 같음) |
| `products/desktop/packages/electron-trpc/src/vendor/unpromise` | MIT(제3자 사본) | `Copyright 2023 Cefn Hoile` | 같은 디렉터리의 `LICENSE`, 출처는 `ATTRIBUTION.txt`(`cefn/watchable`) |

- 루트 `LICENSE`는 MIT 본문 하나다. 이 본문은 `posthog-foss-sync[bot]`의 커밋 `b068ff99030`(2026-10-15)과 `e289996cf97`(2026-10-16)이 만들었다. 두 커밋의 제목은 모두 `Sync and remove all non-FOSS parts`다. 근거: `git log --author=posthog-foss-sync --format='%h %an %s'`.
- 이 포크의 `70371e9eb38`은 `e289996cf97`을 병합한 커밋이다. 부모는 `b068ff99030`과 `e289996cf97`이다. 근거: `git log -1 --format='%P' 70371e9eb38`. `e289996cf97`과 `70371e9eb38`의 `LICENSE`는 같다(`git diff e289996cf97 70371e9eb38 -- LICENSE`가 비어 있다).
- 봇 커밋이 지운 머리말은 아래와 같다. 근거: `git diff e289996cf97^ e289996cf97 -- LICENSE`.

  ```text
  Portions of this software are licensed as follows:

  * All content that resides under the "ee/" directory of this repository, if that directory exists, is licensed under the license defined in "ee/LICENSE".
  * All third party components incorporated into the PostHog Software are licensed under the original license provided by the owner of the applicable component.
  * Content outside of the above mentioned directories or restrictions above is available under the "MIT Expat" license as defined below.
  ```

- 같은 커밋이 `ee/` 전체와 `ee/LICENSE`도 지웠다. 이 포크에는 `ee/`가 없다(`ls ee` 실패). 경위와 결정은 [adr/0001-remove-non-foss.md](adr/0001-remove-non-foss.md)를 본다.
- 제3자 구성요소 문장은 지워졌지만, 그 내용은 법적으로 그대로 적용된다. 루트 MIT는 PostHog Inc.가 권리를 가진 코드에만 걸린다. 아래 표의 제3자 코드·바이너리·글꼴은 각자의 원 라이선스를 따른다.
- 루트 `package.json`의 `license` 필드는 `MIT`(`package.json:9`)다. Cargo 매니페스트 3개가 `license = "MIT"`를 선언한다(`cli/Cargo.toml:15`, `rust/common/symbol_data/Cargo.toml:11`, `rust/replay-anonymizer/Cargo.toml:6`).
- `rust/` 워크스페이스 크레이트 75개 중 73개는 `license` 필드가 없다(`cargo metadata`의 `source == null` 패키지). 루트 MIT가 적용된다고 보지만, 크레이트별 선언은 없다. `funnel-udf`(1개)와 `rust/common/hogvm/node`(2개)의 크레이트도 `license` 필드가 없다.

## 범위

`git ls-files | grep -E '(^|/)(uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock|Cargo\.lock|go\.mod|go\.sum|requirements[^/]*\.txt)$'`는 32개 파일을 낸다. `yarn.lock`은 없다.

| 파일 | 생태계 | 처리 | 비고 |
| --- | --- | --- | --- |
| `uv.lock` | pip | 집계 | 메인 Django 앱 |
| `services/llm-gateway/uv.lock` | pip | 집계 | |
| `services/stripe-mock/uv.lock` | pip | 집계 | |
| `common/ingestion/acceptance_tests/requirements.txt` | pip | 집계 | `==`로 고정한 직접 의존 9개만. 전이 의존은 잠금 파일이 없어 세지 않았다 |
| `services/llm-gateway/benchmarks/requirements.txt` | pip | 제외 | 버전 없는 이름 3개(`openai`, `anthropic`, `python-dotenv`). 벤치마크 스크립트용 |
| `tools/infra-scripts/clitools/requirements.txt` | pip | 제외 | `-c constraints.txt`와 `posthog>=7.67.1` 한 줄. 고정 버전이 없다 |
| `pnpm-lock.yaml` | npm | 집계 | 루트 워크스페이스(`frontend`, `nodejs`, `products/*` 등) |
| `products/desktop/pnpm-lock.yaml` | npm | 집계 | 독립 워크스페이스. 루트 `pnpm-workspace.yaml:20~22`가 `'!products/desktop'`로 뺀다. Electron 앱과 모바일 앱 |
| `packages/agent/pnpm-lock.yaml` | npm | 집계 | 에이전트 런타임(`packages/agent/package.json`의 설명 "The PostHog agent runtime and the packages it bundles") |
| `nodejs/src/ingestion/pipelines/sessionreplay/ml-mirror-image-scrub-sidecar/pnpm-lock.yaml` | npm | 집계 | 세션 리플레이 이미지 가림 처리 사이드카(`package.json`의 `description`) |
| `frontend/@posthog/lemon-ui/pnpm-lock.yaml` | npm | 집계 | 잠금 파일 형식 5.4 |
| `tools/hedgebox-dummy/pnpm-lock.yaml` | npm | 집계 | 데모 데이터용 Hedgebox 앱(`tools/hedgebox-dummy/README.md:3`) |
| `products/canvas/packages/canvas_builder/package-lock.json` | npm | 집계 | |
| `products/visual_review/cli/package-lock.json` | npm | 집계 | |
| `.github/actions/paths-filter/package-lock.json` | npm | 집계 | CI 액션 |
| `.depot/actions/paths-filter/package-lock.json` | npm | 집계 | 위와 같은 액션의 사본 |
| `rust/batch-import-worker/scripts/package-lock.json` | npm | 집계 | 패키지 4개 |
| `rust/Cargo.lock` | cargo | 집계 | Rust 서비스 워크스페이스 |
| `cli/Cargo.lock` | cargo | 집계 | `posthog-cli` 바이너리 |
| `funnel-udf/Cargo.lock` | cargo | 집계 | 크레이트 이름 `funnels` |
| `rust/common/hogvm/node/Cargo.lock` | cargo | 집계 | |
| `livestream/go.mod` | go | 집계 | |
| `bin/hobby-installer/go.mod` | go | 집계 | |
| `tools/phrocs/go.mod` | go | 집계 | |
| `clickhouse-udfs/util/go.mod` | go | 집계 | |
| `services/hogql-language-service/go.mod` | go | 집계 | 외부 모듈 1개 |
| `packages/agent/agent-shadow/go.mod` | go | 집계 | `require`가 없다(외부 모듈 0개) |
| `livestream/go.sum`, `bin/hobby-installer/go.sum`, `tools/phrocs/go.sum`, `clickhouse-udfs/util/go.sum`, `services/hogql-language-service/go.sum` | go | 제외 | 같은 디렉터리의 `go.mod` `require` 목록을 대신 썼다. `go.sum`은 검증용 해시 목록이고, 빌드에 들어가지 않는 모듈(`/go.mod` 줄)까지 담는다 |

합계: 집계 25개, 제외 7개(`requirements.txt` 2개, `go.sum` 5개).

## 집계 요약

열의 뜻은 [분류 규칙](#분류-규칙)에 있다. "허용형"은 허용 목록에 든 라이선스만으로 만족되는 항목만 센다. 나머지는 모두 "비OSI·독점·미확인"으로 간다.

| 파일 | 생태계 | 항목 수 | 허용형 | 약한 카피레프트(MPL, EPL, CDDL) | 강한·라이브러리 카피레프트(GPL, LGPL) | 비OSI·독점·미확인 |
| --- | --- | --- | --- | --- | --- | --- |
| `uv.lock` | pip | 614 | 563 | 6 | 13 | 32 |
| `services/llm-gateway/uv.lock` | pip | 98 | 92 | 4 | 0 | 2 |
| `services/stripe-mock/uv.lock` | pip | 32 | 31 | 1 | 0 | 0 |
| `common/ingestion/acceptance_tests/requirements.txt` | pip | 9 | 9 | 0 | 0 | 0 |
| `pnpm-lock.yaml` | npm | 3984 | 3925 | 30 | 16 | 13 |
| `products/desktop/pnpm-lock.yaml` | npm | 3097 | 3038 | 37 | 1 | 21 |
| `packages/agent/pnpm-lock.yaml` | npm | 600 | 579 | 12 | 0 | 9 |
| `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml` | npm | 567 | 552 | 0 | 14 | 1 |
| `frontend/@posthog/lemon-ui/pnpm-lock.yaml` | npm | 110 | 110 | 0 | 0 | 0 |
| `tools/hedgebox-dummy/pnpm-lock.yaml` | npm | 450 | 432 | 2 | 14 | 2 |
| `products/canvas/packages/canvas_builder/package-lock.json` | npm | 226 | 226 | 0 | 0 | 0 |
| `products/visual_review/cli/package-lock.json` | npm | 157 | 131 | 12 | 14 | 0 |
| `.github/actions/paths-filter/package-lock.json` | npm | 550 | 548 | 1 | 0 | 1 |
| `.depot/actions/paths-filter/package-lock.json` | npm | 550 | 548 | 1 | 0 | 1 |
| `rust/batch-import-worker/scripts/package-lock.json` | npm | 4 | 4 | 0 | 0 | 0 |
| `rust/Cargo.lock` | cargo | 1200 | 1180 | 10 | 1 | 9 |
| `cli/Cargo.lock` | cargo | 446 | 438 | 5 | 1 | 2 |
| `funnel-udf/Cargo.lock` | cargo | 61 | 60 | 0 | 1 | 0 |
| `rust/common/hogvm/node/Cargo.lock` | cargo | 111 | 110 | 0 | 1 | 0 |
| `livestream/go.mod` | go | 86 | 84 | 1 | 0 | 1 |
| `bin/hobby-installer/go.mod` | go | 25 | 23 | 1 | 0 | 1 |
| `tools/phrocs/go.mod` | go | 30 | 30 | 0 | 0 | 0 |
| `clickhouse-udfs/util/go.mod` | go | 7 | 7 | 0 | 0 | 0 |
| `services/hogql-language-service/go.mod` | go | 1 | 1 | 0 | 0 | 0 |
| `packages/agent/agent-shadow/go.mod` | go | 0 | 0 | 0 | 0 | 0 |

- 항목은 잠금 파일의 `이름@버전` 하나다. 잠금 파일끼리 겹치는 항목은 파일마다 따로 센다.
- pip 항목 수는 레지스트리 출처 패키지만이다. git 출처(`infi-clickhouse-orm`, `pytest-split`, `pyproject.toml:344`, `:349`)와 워크스페이스 멤버는 빠진다.
- cargo 항목 수는 `source != null`인 외부 크레이트다. go 항목 수는 `go.mod`의 `require` 줄(직접과 `// indirect` 모두)이다.

가장 많은 라이선스(루트 잠금 파일 기준):

| 생태계 | 상위 5개 | 기준 |
| --- | --- | --- |
| pip(`uv.lock`) | 분류자 `MIT License` 163, 분류자 `Apache Software License` 112, 분류자 `BSD License` 78, SPDX식 `MIT` 57, SPDX식 `Apache-2.0` 42 | 패키지마다 `license_expression`(SPDX식), `License ::` 분류자, `license` 원문 중 처음으로 비어 있지 않은 값 하나 |
| npm(`pnpm-lock.yaml`) | `MIT` 3071, `Apache-2.0` 429, `ISC` 172, `BSD-3-Clause` 86, `MIT-0` 56 | 레지스트리 `license` 필드 |
| cargo(`rust/Cargo.lock`) | `MIT OR Apache-2.0` 427, `MIT` 287, `Apache-2.0` 143, `Apache-2.0 OR MIT` 86, `MIT/Apache-2.0` 83 | `Cargo.toml`의 `license` 필드 |
| go(6개 `go.mod` 합계 149줄) | `MIT` 89, `BSD-3-Clause` 26, `Apache-2.0` 23, `ISC` 3, `BSD-2-Clause` 3 | 모듈 zip의 최상위 `LICENSE`·`COPYING` 본문 판별 |

## 법무 검토가 필요한 항목

"직접"은 저장소의 매니페스트(`pyproject.toml`, `package.json`, `go.mod`의 `// indirect` 없는 줄)가 이름을 적은 것이다. "전이"는 다른 패키지가 끌어온 것이다.

### 독점 또는 소스 공개형(오픈소스 아님)

| 패키지 | 잠금 파일 | 직접/전이 | 라이선스 원문 | 쓰이는 곳 | 근거 | 법무 확인 |
| --- | --- | --- | --- | --- | --- | --- |
| `@anthropic-ai/claude-agent-sdk` 0.3.280 | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | 직접 | 레지스트리 `SEE LICENSE IN README.md`. tarball `LICENSE.md` 전문: "© Anthropic PBC. All rights reserved. Use is subject to the Legal Agreements outlined here: https://code.claude.com/docs/en/legal-and-compliance." `README.md:64`는 Anthropic Commercial Terms of Service를 가리킨다 | 에이전트 런타임 `@posthog/agent`(`packages/agent/packages/agent/package.json:181`, `publishConfig.access`가 `public`), desktop `@posthog/workspace-server`(`products/desktop/packages/workspace-server/package.json:22`) | tarball(`registry.npmjs.org`의 `dist.tarball`) | 재배포 가능 여부. desktop 빌드가 SDK의 네이티브 실행 파일을 앱에 복사하고 서명한다(`products/desktop/apps/code/vite.main.config.mts:168`의 `copyClaudeExecutable`) |
| `@anthropic-ai/claude-agent-sdk-{darwin-arm64,darwin-x64,linux-arm64,linux-arm64-musl,linux-x64,linux-x64-musl,win32-arm64,win32-x64}` 0.3.280(8개) | 위와 같음 | 전이(SDK의 `optionalDependencies`) | 레지스트리 `SEE LICENSE IN LICENSE.md`. `linux-x64` tarball의 `LICENSE.md`는 위와 같은 한 줄 | 플랫폼별 `claude` 실행 파일 | `linux-x64` tarball만 열어 봤다. 나머지 7개 본문은 미확인 | 위와 같음 |
| `@posthog/brand` 0.12.3 | `pnpm-lock.yaml` | 직접(`frontend/package.json:77`의 `catalog:`, 버전은 `pnpm-workspace.yaml:153`) | PolyForm Strict License 1.0.0. 머리말: "source-available, not open source: you may view it, but commercial use, use in your own projects, distribution, and derivative works are not licensed. The PostHog hedgehog illustrations are PostHog trademarks and brand assets." | 프런트엔드와 `products/*`. 이 이름을 적은 소스 파일 173개(desktop 5개), 그중 import·`@import`·`require` 문이 있는 파일 163개(desktop 3개). 명령은 [집계 방법](#posthogbrand-사용-파일-수) | tarball `LICENSE` | 이 포크의 재배포·상업 운영이 라이선스 밖이 되는지 |
| `@posthog/brand` 0.11.0 | `products/desktop/pnpm-lock.yaml` | 직접(`products/desktop/pnpm-workspace.yaml:16`, `packages/shared`, `apps/mobilehog`, `tools/announcements-admin`의 `package.json`) | 0.12.3과 같은 `LICENSE`(두 tarball 파일을 `diff`로 비교해 같음) | desktop·모바일 앱 | tarball `LICENSE` | 위와 같음 |
| `@posthog/brand`에서 복사한 이미지 | (잠금 파일 밖) | 저장소에 복사 | 위 PolyForm Strict 패키지에서 왔다고 주석이 적는다 | `frontend/src/lib/components/Hogfetti/hogs/*.png` 15개. `Hogfetti.tsx:21` 주석 "Confetti hogs are vendored from @posthog/brand" | `git ls-files frontend/src/lib/components/Hogfetti/hogs` | 패키지 라이선스가 복사본에도 걸리는지 |
| `gsap` 3.14.2 | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | 전이(`@posthog/hedgehog-mode` 0.0.63·0.0.53의 `dependencies`가 `gsap ^3.12.7`) | 레지스트리 `Standard 'no charge' license: https://gsap.com/standard-license.` 패키지 안에는 라이선스 본문이 없고, `README.md:62`는 "100% FREE including ... commercial use", `:90~91`은 위 주소를 가리킨다. 웹 페이지 본문(2026-10-16 확인, "Effective date: April 30, 2025"): Webflow가 "Permitted Uses"에 한해 비독점 라이선스를 준다. Webflow와 경쟁하는 노코드 시각 애니메이션 도구에서의 사용, 그런 제품을 위한 역공학, 독점 고지 제거를 금지한다. Webflow는 위반 시 해지할 수 있고 약관을 고칠 수 있다. 같은 페이지의 "Plain English Summary"는 아직 "end users are not charged a fee"를 조건으로 적어 본문과 다르다 | 헤지호그 UI(아래 `@posthog/hedgehog-mode`) | https://gsap.com/standard-license | 본문과 요약 중 어느 쪽이 적용되는지, 상업 운영에 걸리는지 |
| `react-doctor` 0.9.18, `oxlint-plugin-react-doctor` 0.9.18 | `products/desktop/pnpm-lock.yaml` | 전이(`products/desktop/apps/code/package.json:137`의 `react-scan`이 끌어옴) | 레지스트리 `SEE LICENSE IN LICENSE`. 두 tarball의 `LICENSE`는 같고 제목이 "Modified MIT License", `Copyright (c) 2026 Million Software, Inc.`다. MIT 본문 뒤에 두 가지 사용은 저작권자의 사전 서면 허가가 필요하다고 덧붙인다. (1) 소프트웨어를 머신러닝·AI의 학습·미세조정·평가 데이터로 쓰는 것, (2) 소프트웨어를 팔거나, 가치의 전부 또는 대부분이 이 소프트웨어에서 나오는 유료·호스팅·관리형 제품이나 서비스로 제3자에게 제공하는 것 | desktop 앱 `apps/code`의 `react-scan` 의존 | tarball `LICENSE` | 배포되는 앱에 들어가는지(미확인), 제한 조항이 이 포크의 사용에 걸리는지 |
| `nvidia-*-cu12` 15개(`cublas`, `cuda-cupti`, `cuda-nvrtc`, `cuda-runtime`, `cudnn`, `cufft`, `cufile`, `curand`, `cusolver`, `cusparse`, `cusparselt`, `nccl`, `nvjitlink`, `nvshmem`, `nvtx`) | `uv.lock` | 전이(`torch`) | 14개는 분류자 `Other/Proprietary License`, `cusparselt`는 분류자 없이 원문 `NVIDIA Proprietary Software`. `nccl`·`nvshmem`의 원문은 `BSD-3-Clause`, `nvtx`의 원문은 `Apache 2.0`이라 분류자와 다르다 | `torch`의 CUDA 빌드. `pyproject.toml:329` 주석: "sentiment takes torch from PyPI with the CUDA libraries, inbox-ranking takes the CPU-only build." `torch`는 `sentiment`(`:303`)와 `inbox-ranking`(`:310`) 그룹의 직접 의존 | PyPI JSON API | `sentiment` 그룹이 어느 이미지에 설치되는지(미확인) |
| `tbb` 2022.3.1 | `uv.lock` | 직접(`pyproject.toml:161`, linux x86_64 한정) | 분류자 `Other/Proprietary License`, 원문 `Intel Simplified Software License` | 쓰는 코드는 찾지 않았다(미확인) | PyPI JSON API | 본문 미확인 |
| `tcmlib` 1.4.1 | `uv.lock` | 전이(`tbb`) | 위와 같음 | `tbb`의 의존 | PyPI JSON API | 본문 미확인 |
| `linkedin-api-client` 0.3.0 | `uv.lock` | 직접(`pyproject.toml:193`) | 분류자 `Other/Proprietary License`, 원문 `Proprietary` | LinkedIn Ads 데이터 웨어하우스 소스. `products/warehouse_sources/backend/temporal/data_imports/sources/linkedin_ads/client.py:9`가 `linkedin_api.clients.restli.client`를 import한다 | PyPI JSON API | 본문 미확인 |

`@posthog/brand`와 헤지호그 상표의 요약은 [branding.md](branding.md)에 있다.

### 카피레프트 (GPL, LGPL)

| 패키지 | 잠금 파일 | 직접/전이 | 라이선스 | 비고 |
| --- | --- | --- | --- | --- |
| `ffmpeg-static` 5.3.0 | `pnpm-lock.yaml` | 전이(`puppeteer-capture`의 `optionalDependencies`, `pnpm-lock.yaml:43041~43042`) | `GPL-3.0-or-later` | `puppeteer-capture`는 `nodejs/package.json:142`의 직접 의존이고, 세션 리플레이 녹화 래스터라이저(`nodejs/src/session-replay/recording-rasterizer/capture/browser-pool.ts:2`)가 쓴다. 이 서비스의 이미지(`Dockerfile.recording-rasterizer:114`)는 Debian `ffmpeg` 패키지를 따로 설치한다. 이미지 안에 `ffmpeg-static` 바이너리가 실제로 받아지는지는 미확인 |
| `@img/sharp-libvips-*` 1.2.4(10개: darwin 2, linux 6, linuxmusl 2) | `pnpm-lock.yaml`, `tools/hedgebox-dummy/pnpm-lock.yaml` | 전이(`sharp` 0.34.5) | `LGPL-3.0-or-later` | `sharp`의 플랫폼별 선택 바이너리 |
| `@img/sharp-win32-{arm64,ia32,x64}`, `@img/sharp-wasm32` 0.34.5 | 위와 같음 | 전이 | `Apache-2.0 AND LGPL-3.0-or-later`(wasm32는 `AND MIT` 추가) | 같음 |
| `@img/sharp-libvips-*` 1.3.2(10개), `@img/sharp-win32-*`·`@img/sharp-wasm32` 0.35.3(4개) | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json` | 전이(두 `package.json`이 `sharp`를 직접 의존) | 위와 같은 표기 | 사이드카 이미지와 시각 회귀 CLI |
| `node-forge` 1.4.0 | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | 전이(루트 `overrides`가 `>=1.4.0`으로 고정, `pnpm-lock.yaml:124`·`:134`) | `(BSD-3-Clause OR GPL-2.0)` | BSD 쪽을 고를 수 있다 |
| `psycopg` 3.2.10 | `uv.lock` | 직접(`pyproject.toml:111`, `psycopg[binary]`) | 분류자 LGPLv3 | PostgreSQL 드라이버 |
| `psycopg-binary` 3.2.10 | `uv.lock` | 전이(`psycopg[binary]`) | 분류자 LGPLv3 | 같음 |
| `psycopg2-binary` 2.9.11 | `uv.lock` | 직접(`pyproject.toml:110`) | 분류자 LGPL | 같음 |
| `paramiko` 3.5.1 | `uv.lock` | 직접(`pyproject.toml:105`) | 분류자 LGPL | `sshtunnel`도 끌어온다 |
| `clickhouse-pool` 0.5.3 | `uv.lock` | 직접(`pyproject.toml:26`) | 분류자 LGPLv3+ | |
| `pymssql` 2.3.8 | `uv.lock` | 직접(`pyproject.toml:117`) | `LGPL-2.1-or-later` | |
| `browser-cookie3` 0.20.1 | `uv.lock` | 직접(`pyproject.toml:228`, `dev` 그룹) | 원문 `lgpl`(PyPI 원문이 소문자) | 개발 의존 |
| `chardet` 5.2.0 | `uv.lock` | 전이(`prance`, `shrinkray`) | 분류자 LGPLv2+ | |
| `jwcrypto` 1.5.7 | `uv.lock` | 전이(`django-oauth-toolkit`) | `LGPL-3.0-or-later` | |
| `python-stdnum` 2.2 | `uv.lock` | 전이(`scrubadub`) | 분류자 LGPLv2+ | |
| `suds-community` 1.2.0 | `uv.lock` | 전이(`bingads`) | 분류자 LGPL | |
| `text-unidecode` 1.3 | `uv.lock` | 전이(`python-slugify`) | 분류자 `Artistic License`, GPL, GPLv2+가 함께 붙음 | 선택 가능한지 미확인 |
| `tld` 0.13.2 | `uv.lock` | 전이(`courlan`) | `MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later` | 선택 가능 |
| `r-efi` 5.3.0 | `rust/Cargo.lock`, `cli/Cargo.lock`, `funnel-udf/Cargo.lock`, `rust/common/hogvm/node/Cargo.lock` | 전이 | `MIT OR Apache-2.0 OR LGPL-2.1-or-later` | 허용형을 고를 수 있다 |

### 약한 카피레프트 (MPL, EPL, CDDL)

| 패키지 | 잠금 파일 | 직접/전이 | 라이선스 |
| --- | --- | --- | --- |
| `certifi` 2026.1.4 | `uv.lock` | 직접(`pyproject.toml:23`) | MPL-2.0 |
| `orjson` 3.11.9 | `uv.lock` | 직접(`pyproject.toml:102`) | `MPL-2.0 AND (Apache-2.0 OR MIT)` |
| `hypothesis` 6.151.9, `pytest-rerunfailures` 16.6 | `uv.lock` | 직접(`pyproject.toml:245`, `:248`, `dev` 그룹) | MPL-2.0 |
| `pathspec` 1.0.4, `tqdm` 4.67.1(`MIT`와 MPL 2.0 분류자) | `uv.lock` | 전이 | MPL-2.0 |
| `certifi` 2025.11.12, `pathspec` 0.12.1, `pytest-rerunfailures` 16.1, `tqdm` 4.67.1 | `services/llm-gateway/uv.lock` | 미확인(이 서비스의 매니페스트는 대조하지 않았다) | MPL-2.0 |
| `certifi` 2026.2.25 | `services/stripe-mock/uv.lock` | 미확인 | MPL-2.0 |
| `axe-core` 4.5.1(루트), 4.11.1(desktop), 4.11.4(hedgebox-dummy), 4.12.1(paths-filter 2개) | 여러 npm 잠금 파일 | 전이 | MPL-2.0 |
| `ip6addr` 0.2.5 | `pnpm-lock.yaml` | 전이 | MPL-2.0 |
| `lightningcss`와 플랫폼별 바이너리 | 루트 24개(1.31.1과 1.32.0 각 12개), desktop 35개, agent 12개, visual_review CLI 12개 | 전이 | MPL-2.0 |
| `dompurify` 3.2.7, 3.4.0, 3.4.13(루트), 3.4.13(desktop), 3.4.7(hedgebox-dummy) | 여러 npm 잠금 파일 | 루트는 직접(`frontend/package.json`), 나머지는 전이 | `(MPL-2.0 OR Apache-2.0)` |
| `elkjs` 0.10.0 | `pnpm-lock.yaml` | 직접(`frontend`, `products/{data_modeling,engineering_analytics,product_analytics,workflows}`의 `package.json`) | EPL-2.0 |
| `brownstone` 3.0.0, `fernet` 0.2.2, `indent_write` 2.2.0, `nom-supreme` 0.8.0, `option-ext` 0.2.0, `webpki-roots` 0.25.4, `colored` 3.1.1 | `rust/Cargo.lock` | 전이 | MPL-2.0 |
| `smartstring` 1.0.1 | `rust/Cargo.lock` | 전이 | `MPL-2.0+` |
| `inferno` 0.11.21, 0.12.4 | `rust/Cargo.lock` | 전이 | CDDL-1.0 |
| `brownstone` 3.0.0, `colored` 3.0.0, `indent_write` 2.2.0, `nom-supreme` 0.8.0, `option-ext` 0.2.0 | `cli/Cargo.lock` | 전이 | MPL-2.0 |
| `github.com/hashicorp/golang-lru/v2` v2.0.7 | `livestream/go.mod:14`(직접), `bin/hobby-installer/go.mod:21`(`// indirect`) | 직접·전이 | MPL-2.0. 모듈 zip의 `LICENSE` 첫 줄 `Copyright (c) 2014 HashiCorp, Inc.`, 다음 줄 `Mozilla Public License, version 2.0` |

### 허용형이지만 표기가 특이한 항목

아래는 분류 규칙상 "비OSI·독점·미확인" 열로 들어가지만, 본문을 확인해 보니 허용형인 것이다. 고지나 출처 표시 의무가 붙는다.

| 패키지 | 잠금 파일 | 라이선스 표기 | 확인한 본문 |
| --- | --- | --- | --- |
| `ring` 0.16.20 | `rust/Cargo.lock` | `license_file = "LICENSE"` | ISC 계열(새 코드), OpenSSL License, Original SSLeay License를 함께 담는다. 두 BSD 계열 라이선스에 광고 고지 조항이 있다("All advertising materials mentioning features or use of this software must display the following acknowledgment", `LICENSE:66~69`, `:137~140`). 출처: `~/.cargo/registry/src/index.crates.io-*/ring-0.16.20/LICENSE` |
| `aws-lc-sys` 0.37.1 | `rust/Cargo.lock` | `ISC AND (Apache-2.0 OR ISC) AND OpenSSL` | `LICENSE` 첫 줄이 같은 SPDX식이다. BoringSSL·OpenSSL에서 온 부분은 OpenSSL License와 SSLeay License(광고 고지 조항 포함)를 따른다 |
| `libbz2-rs-sys` 0.2.2 | `rust/Cargo.lock` | `bzip2-1.0.6` | BSD 계열 4개 조항(고지 유지, 출처 오인 금지, 수정본 표시, 이름 사용 금지). `Copyright (C) 1996-2021 Julian R Seward` 외, Rust 번역은 `Trifecta Tech Foundation and contributors` |
| `temporalio-client`, `temporalio-common`, `temporalio-common-wasm`, `temporalio-protos` 0.5.0 | `rust/Cargo.lock` | `license_file = "LICENSE.txt"` | 네 개 모두 "The MIT License", `Copyright (c) 2021 Temporal Technologies, Inc.` |
| `webpki-root-certs` 1.0.8, `webpki-roots` 1.0.6 | `rust/Cargo.lock` | `CDLA-Permissive-2.0` | 데이터 라이선스. 본문 미확인. `cli/Cargo.lock`에는 `webpki-root-certs` 1.0.8, `webpki-roots` 1.0.4 |
| `caniuse-lite`(루트 1.0.30001690·1.0.30001777, 그 밖의 잠금 파일에 5개 버전) | 여러 npm 잠금 파일 | `CC-BY-4.0` | 출처 표시 필요. `frontend/package.json`이 직접 의존 |
| `spdx-exceptions` 2.3.0 | `pnpm-lock.yaml` | `CC-BY-3.0` | 출처 표시 필요 |
| `esbuild-plugin-less` 1.3.17 | `pnpm-lock.yaml` | `WTFPL` | `common/esbuilder/package.json` 직접 의존. 빌드 도구 |
| `truncate-utf8-bytes` 1.0.2 | `products/desktop/pnpm-lock.yaml` | `WTFPL` | 전이 |
| `@fontsource-variable/inter` 5.2.8 | `pnpm-lock.yaml` | `OFL-1.1` | 글꼴. `packages/quill/apps/storybook/package.json` 직접 의존. 허용 목록에 들어 있어 "허용형"으로 셌다 |
| `argparse` 2.0.1 | `pnpm-lock.yaml` | `Python-2.0` | 허용 목록에 들어 있어 "허용형"으로 셌다 |
| `posthog-js` 1.376.2 | `tools/hedgebox-dummy/pnpm-lock.yaml` | `SEE LICENSE IN LICENSE` | tarball `LICENSE`는 Apache-2.0, `Copyright 2020 Posthog / Hiberly, Inc.`, `Copyright 2015 Mixpanel, Inc.` |

### 라이선스를 레지스트리에서 얻지 못한 항목 (미확인)

| 생태계 | 패키지 |
| --- | --- |
| npm(`pnpm-lock.yaml`) | `@elevenlabs/types` 0.13.0, `@mapbox/jsonlint-lines-primitives` 2.0.2, `@segment/fql-ts` 1.10.1, `heatmap.js` 2.0.5(`frontend/package.json` 직접 의존), `khroma` 2.1.0, `union` 0.5.0, `unionfs` 4.6.0 |
| npm(`products/desktop/pnpm-lock.yaml`) | `@react-grab/cli` 0.2.0, `exif-parser` 0.1.12, `khroma` 2.1.0, `pastable` 2.2.1, `typed-openapi` 2.2.7(`products/desktop/packages/api-client/package.json` 직접 의존) |
| npm(git·tarball 출처, 집계에서 빠짐) | `uWebSockets.js`: `nodejs/package.json:149`가 GitHub tarball URL로 고정. 레지스트리 조회 대상이 아니다 |
| pip(`uv.lock`, PyPI 메타데이터 비어 있음) | `arro3-core` 0.6.5, `autoevals` 0.2.0, `braintrust` 0.2.4, `braintrust-core` 0.0.59, `braintrust-langchain` 0.0.4, `cramjam` 2.12.1, `docker-image-py` 0.1.13, `google-crc32c` 1.8.0, `mistralai` 1.6.0, `mypy-extensions` 1.1.0, `playwright` 1.60.0, `polyleven` 0.11.0 |
| pip(`uv.lock`, 분류자가 `OSI Approved`뿐) | `umap-learn` 0.5.7(원문은 `BSD`) |
| pip(`uv.lock`, PyPI 404) | `torch` 2.9.1+cpu. PyPI에 없는 로컬 버전이다. `torch` 2.9.1의 원문은 `BSD-3-Clause` |
| pip(`services/llm-gateway/uv.lock`) | `mypy-extensions` 1.1.0(메타데이터 비어 있음), `prometheus-fastapi-instrumentator` 7.1.0(분류자 `OSI Approved`뿐) |
| pip(git 출처, 집계에서 빠짐) | `infi-clickhouse-orm`, `pytest-split`(`pyproject.toml:344`, `:349`의 `[tool.uv.sources]`) |
| go | `github.com/mattn/go-localereader` v0.0.1(`livestream/go.mod:58`, `bin/hobby-installer/go.mod:25`, 둘 다 `// indirect`). 모듈 zip에 `LICENSE` 파일이 없다. `README.md`만 "License: MIT"라고 적는다 |

## 잠금 파일 밖 제3자 구성요소

### 터미널 기능의 바이너리

`frontend/src/scenes/terminal/`은 브라우저 안에서 `v86`(npm, `BSD-2-Clause`, `frontend/package.json:302`) 에뮬레이터로 i386 리눅스를 띄운다.
`terminalRuntime.ts:3~8`이 아래 파일을 `?url`로 가져오고, esbuild 설정이 `.bin`을 `file` 로더로 빌드 산출물에 복사한다(`common/esbuilder/utils.mjs:340`).
즉 이 바이너리는 프런트엔드와 함께 브라우저로 배포된다.
메뉴 노출은 `FEATURE_FLAGS.POSTHOG_TERMINAL`(`frontend/src/lib/constants.tsx:180`, `'posthog-terminal'`)이 가리지만, 경로는 플래그와 상관없이 `frontend/src/scenes/scenes.ts:916`에 등록되어 있다.

| 파일 | 내용 | 라이선스 | 저장소 안의 라이선스 사본·출처 표시 | 법무 확인 |
| --- | --- | --- | --- | --- |
| `frontend/src/scenes/terminal/assets/buildroot-bzimage.bin`(4.8MB) | Linux 커널 bzImage. 문자열 `5.6.15 (posthog@posthog) #1` | GPL-2.0(Linux 커널) | 없다. 커널 소스·설정·빌드 방법을 가리키는 파일을 저장소에서 찾지 못했다(`git grep -i buildroot`) | GPL-2.0 대응 소스 제공 의무 |
| `frontend/src/scenes/terminal/assets/seabios.bin`, `vgabios.bin` | SeaBIOS 1.16.2 | `seabios-COPYING.LESSER.txt`(LGPL-3.0), `seabios-COPYING.txt`(GPL-3.0) | `frontend/public/terminal/firmware-manifest.json`이 소스(`coreboot/seabios` `rel-1.16.2`)와 빌드 스크립트(`copy/v86`)를 가리킨다 | LGPL·GPL 대응 소스 제공 방식이 충분한지 |
| `frontend/src/scenes/terminal/assets/tools-linux-i386.tar.gz.bin`(7.9MB) | Alpine 3.22 패키지 24개(`bash`, `readline`, `nano`, `mc`, `ncdu`, `glib`, `musl`, `ncurses`, `libssh2`, `libcrypto3`, `util-linux` 라이브러리 등) | 패키지마다 다르다. 동봉 사본 기준으로 GNU GPL 본문이 붙은 것은 `bash`, `readline`, `nano`, `mc`, `slang`, `tree`, `gpm`이고, `gettext`(libintl)는 LGPL이다. `glib`, `util-linux`, `e2fsprogs`는 여러 라이선스를 함께 담는다. 나머지(`musl`, `ncurses`, `ncdu`, `libffi`, `libeconf`, `libssh2`, `pcre2`, `zlib`, `openssl`)는 허용형 본문이다 | `frontend/public/terminal/tools-manifest.json`의 `sources` 20개가 원본 tarball URL, sha512, Alpine 빌드 레시피, 라이선스 파일 경로를 적는다. tarball 안 `opt/posthog-tools/licenses/`에 라이선스 사본 20개가 있다(`tar -tzf`로 확인) | GPL 대응 소스 제공 의무. 원본 URL만 적는 방식이 충분한지 |
| `frontend/src/scenes/terminal/assets/jq-linux-i386.bin` | jq 1.8.2(`posthogFilesystem.ts:176`) | jq는 MIT(`jq-COPYING.txt`). 저장소가 jq 옆에 Oniguruma(BSD 계열)와 glibc(LGPL-2.1) 사본도 둔다. 두 라이브러리가 바이너리에 실제로 들어 있는지는 미확인 | `frontend/public/terminal/jq-COPYING.txt`, `oniguruma-COPYING.txt`, `glibc-COPYING.LIB.txt` | glibc가 정적 링크인지(미확인), LGPL 조건 충족 여부 |

### 터미널 기능이 실행 중 받는 패키지

`frontend/src/scenes/terminal/terminal-packages.json`은 `https://raw.githubusercontent.com/PostHog/terminal-assets/<커밋>`에서 아래 압축 파일을 받는다.
기본 `baseUrl`은 `:104`, 패키지별 `baseUrl`은 `:20`(pi), `:33`(Doom), `:101`(Neovim)이다.
저장소 밖 파일이라 라이선스 본문은 모두 미확인이다.

| 패키지 | 버전 | 라이선스 |
| --- | --- | --- |
| Node.js | 22.23.2 | 미확인 |
| `pi` | 0.87.1 | 미확인 |
| Doom (Freedoom) | 0.13.0-4 | 미확인 |
| `sl` | 5.02-r1 | 미확인 |
| `cmatrix` | 2.0-r2 | 미확인 |
| `figlet` | 2.2.5-r3 | 미확인 |
| `nyancat` | 1.5.2-r1 | 미확인 |
| Neovim | 0.11.1-r1 | 미확인 |
| 커널 이미지 `images/linux-fb-bzimage.bin`(`:105~108`) | | Linux 커널이면 GPL-2.0. 파일은 열어 보지 않았다 |

### 벤더링한 코드

| 위치 | 원본 | 라이선스 | 저작권 고지 | 근거 |
| --- | --- | --- | --- | --- |
| `products/logs/backend/vendor/drain3/drain.py`, `masking.py` | IBM Drain3 0.9.11 | MIT | `Copyright (c) 2020-2022 International Business Machines`(파일 머리 주석에 전문) | 각 파일 1~6행, `__init__.py:1~3` |
| `products/logs/backend/vendor/drain3/simple_profiler.py` | David Ohana의 SimpleProfiler(drain3 경유) | Apache-2.0 | `SPDX-License-Identifier: Apache-2.0`. 본문은 URL로만 가리킨다 | 파일 1~7행 |
| `frontend/src/toolbar/vendor/finder/index.ts` | `@medv/finder` 4.0.2 | MIT | `Copyright (c) 2018 Anton Medvedev` | 파일 머리 주석 |
| `frontend/src/vendor/bintrees/index.ts` | `bintrees` 1.0.2 | MIT | `Copyright (C) 2011 by Vadim Graboys` | 파일 머리 주석 |
| `products/desktop/packages/electron-trpc/src/vendor/unpromise/` | `cefn/watchable`의 `unpromise` | MIT | `Copyright 2023 Cefn Hoile` | 같은 디렉터리의 `LICENSE`, `ATTRIBUTION.txt` |
| `.github/actions/paths-filter/`, `.depot/actions/paths-filter/` | `dorny/paths-filter`의 포크(`action.yml`의 `description`이 "Vendored fork of dorny/paths-filter"라고 적는다) | MIT | `Copyright (c) 2020 Michal Dorner and contributors` | 각 `LICENSE` |
| `products/desktop/packages/electron-trpc/` | `package.json`의 `description`이 "Electron support for tRPC (forked with HMR fix)"라고 적는다. npm의 `electron-trpc`는 `MIT`, 작성자 Jason Nall | MIT(원본 레지스트리 값) | 디렉터리에 원본의 `LICENSE`나 저작권 고지가 없다. `package.json`의 `license`도 없다 | `jq .license`가 `null`. 원본 대조는 미확인 |
| `.github/scripts/signal-fanout` | `dimikot/signal-fanout` @ `585118209dec` | GitHub API가 원본 저장소를 MIT로 표시 | 파일에 라이선스·저작권 고지가 없다 | 파일 2~3행. CI 스크립트라 제품과 함께 배포되지 않는다 |

### 글꼴과 이미지

글꼴 메타데이터는 `fontTools`로 `name` 표의 0번(저작권), 13번(라이선스), 14번(라이선스 URL)을 읽었다. 명령은 [집계 방법](#글꼴-메타데이터)에 있다.

| 위치 | 글꼴·자산 | 메타데이터의 저작권·라이선스 | 라이선스 사본 | 비고 |
| --- | --- | --- | --- | --- |
| `frontend/public/fonts/TwemojiCountryFlags.woff2` | Twemoji 국기 부분집합 | 메타데이터 비어 있음 | 없다 | npm `country-flag-emoji-polyfill` 0.1.8의 `dist/TwemojiCountryFlags.woff2`와 바이트가 같다(`cmp`). 그 패키지의 `LICENSE.md`: 코드는 MIT(`Copyright (c) 2022 TalkJS`), 이모지 그림은 Twemoji의 CC-BY-4.0. 출처 표시 필요 |
| `frontend/public/fonts/cmunti-webfont.woff` | CMU Serif | "Converted by Andrey V. Panov from TeX fonts", SIL OFL 1.1 | 없다(메타데이터는 `OFL.txt`를 함께 둔다고 적는다) | `products/legal_documents/frontend/components/base/LegalDocumentsPreview.scss:15`가 쓴다 |
| `frontend/public/fonts/fairytale_serif-webfont.woff`, `.woff2` | 이름 `.` | 메타데이터 비어 있음 | 없다 | 출처·라이선스 미확인. `LegalDocumentsPreview.scss:6~7`이 쓴다 |
| `products/desktop/packages/ui/src/assets/fonts/JetBrainsMono/`, `products/desktop/apps/mobile/assets/fonts/`, `products/desktop/apps/mobilehog/assets/fonts/`의 JetBrains Mono | JetBrains Mono | `Copyright 2020 The JetBrains Mono Project Authors`, SIL OFL 1.1 | `packages/ui/src/assets/fonts/JetBrainsMono/OFL.txt`만 있다 | 모바일 앱 두 곳에는 사본이 없다 |
| `products/desktop/packages/ui/src/assets/fonts/OpenRunde/`, `products/desktop/apps/mobile/assets/fonts/OpenRunde/` | Open Runde | `Copyright 2023 Laurids Kern`, 라이선스 필드 비어 있음 | 없다 | 라이선스 미확인 |
| `products/desktop/apps/mobilehog/assets/fonts/RoundHog*.ttf`, `@posthog/brand`의 `dist/fonts/RoundHog*.woff2` | RoundHog(PostHog 브랜드 글꼴) | "RoundHog derived from Inter (Rasmus Andersson); rounded after Open Runde (Laurids Kern). SIL OFL 1.1." | 없다 | 글꼴 메타데이터는 OFL 1.1, 담긴 패키지 `@posthog/brand`의 `LICENSE`는 PolyForm Strict다. 어느 쪽이 걸리는지 법무 확인. 프런트엔드는 `frontend/src/styles/fonts.scss:47~83`에서 이 글꼴을 쓴다 |
| `@posthog/hedgehog-mode` 0.0.63(루트, `frontend/package.json:80`), 0.0.53(desktop, `products/desktop/apps/code/package.json:97`) | 헤지호그 스프라이트 `assets/sprites.png`, `assets/sprites.json` | 레지스트리 `MIT`. tarball에 `LICENSE` 파일이 없다 | 없다 | MIT는 저작권만 다루고 상표는 다루지 않는다. 헤지호그 상표는 [branding.md](branding.md)를 본다. `gsap`을 끌어온다(위 독점 표) |

## 보존해야 할 제3자 저작권 고지

MIT·BSD·Apache·OFL·CC-BY는 배포할 때 원 저작권 고지와 라이선스 문구를 함께 실어야 한다.
PostHog Inc.의 고지(루트 `LICENSE`)와 함께 아래 고지도 보존해야 한다.

| 고지 | 있는 곳 | 현재 상태 |
| --- | --- | --- |
| `Copyright (c) 2020 Michal Dorner and contributors`(MIT) | `.github/actions/paths-filter/LICENSE`, `.depot/actions/paths-filter/LICENSE` | 사본 있음 |
| `Copyright 2023 Cefn Hoile`(MIT) | `products/desktop/packages/electron-trpc/src/vendor/unpromise/LICENSE` | 사본 있음 |
| `Copyright (c) 2020-2022 International Business Machines`(MIT), SimpleProfiler(Apache-2.0) | `products/logs/backend/vendor/drain3/*.py` 머리 주석 | 주석에 있음. Apache-2.0 본문은 URL로만 |
| `Copyright (c) 2018 Anton Medvedev`(MIT) | `frontend/src/toolbar/vendor/finder/index.ts` 머리 주석 | 주석에 있음. 번들 산출물에 주석이 남는지는 미확인 |
| `Copyright (C) 2011 by Vadim Graboys`(MIT) | `frontend/src/vendor/bintrees/index.ts` 머리 주석 | 같음 |
| 원본 `electron-trpc`의 고지 | `products/desktop/packages/electron-trpc/` | 없음 |
| Twemoji CC-BY-4.0 출처 표시 | `frontend/public/fonts/TwemojiCountryFlags.woff2` | 없음 |
| JetBrains Mono OFL | 모바일 앱 글꼴 디렉터리 두 곳 | 메타데이터에 라이선스 문장만 있음. `OFL.txt` 없음 |
| 터미널 바이너리의 GPL·LGPL 본문 | `frontend/public/terminal/*.txt`, `tools-linux-i386.tar.gz.bin` 안 `licenses/` | 커널(GPL-2.0) 본문만 없음 |

브랜딩 쪽 저작권 고지 요약은 [branding.md](branding.md)에도 있다.

## 집계 방법

모든 명령은 임시 디렉터리에서 돌리고, 결과 파일도 그 디렉터리에만 쓴다. 저장소 안에는 아무것도 쓰지 않는다.
스크립트 파일은 임시 디렉터리 밖의 다른 디렉터리에 두고 `S`로 가리킨다. 내려받은 파일을 읽는 Python은 `-I`로 돌린다.
잠금 파일에는 라이선스 필드가 없다(cargo는 `cargo metadata`가 바로 준다). 그래서 이름·버전을 뽑아 레지스트리에 조회했다.
`node_modules`나 가상 환경은 설치하지 않았다.

```bash
W=/path/to/checkout          # 저장소 루트
S=/path/to/lic-scripts       # 아래 스크립트 6개를 둔 디렉터리
cd "$(mktemp -d)"
```

### 분류 규칙

`classify.py`가 정한다. 순서대로 먼저 맞는 것을 쓴다.

1. 문자열에 `gpl` 또는 `gnu`가 있으면(대소문자 무시) 강한·라이브러리 카피레프트다. `A OR B`로 고를 수 있어도 이쪽으로 센다.
2. `mpl`, `mozilla`, `epl`, `eclipse public`, `cddl`이 있으면 약한 카피레프트다.
3. SPDX식(npm, cargo, go, pip의 `license_expression`)은 `OR`는 하나라도, `AND`는 모두 허용 목록에 있으면 허용형이다. `/`는 `OR`로, `WITH 예외`는 앞의 라이선스로 읽는다.
4. pip 분류자는 `OSI Approved`, `DFSG approved`를 뺀 나머지가 모두 허용형 분류자(`MIT License`, `Apache Software License`, `BSD License`, `ISC License (ISCL)`, `Python Software Foundation License`, `Public Domain`, `The Unlicense (Unlicense)`)면 허용형이다.
5. pip 원문은 `mit`, `apache`, `bsd`, `3-clause bsd`, `isc`, `cc0`, MIT 라이선스 URL로 시작하고 `proprietary`가 없으면 허용형이다.
6. 나머지는 모두 비OSI·독점·미확인이다. `UNKNOWN`, `SEE LICENSE IN ...`, 조회 오류, `license_file`만 있는 크레이트, `CC-BY-*`, `WTFPL`, `CDLA-Permissive-2.0`, `bzip2-1.0.6`, `OpenSSL`이 여기에 든다.

허용 목록: `MIT`, `MIT-0`, `MIT-CMU`, `X11`, `NCSA`, `Apache-2.0`, `BSD`, `BSD-2-Clause`, `BSD-3-Clause`, `0BSD`, `ISC`, `Zlib`, `BSL-1.0`, `Unlicense`, `CC0-1.0`, `Python-2.0`, `PSF-2.0`, `CNRI-Python`, `BlueOak-1.0.0`, `Unicode-3.0`, `Unicode-DFS-2016`, `OFL-1.1`, `AFL-2.1`.

`classify.py`:

```python
# usage: classify.py npm|cargo|go|pip FILE.tsv  -> prints "category<TAB>name<TAB>version<TAB>license"
import re, sys
ALLOW = {x.lower() for x in '''MIT MIT-0 MIT-CMU X11 NCSA Apache-2.0 BSD BSD-2-Clause BSD-3-Clause 0BSD ISC Zlib BSL-1.0
  Unlicense CC0-1.0 Python-2.0 PSF-2.0 CNRI-Python BlueOak-1.0.0 Unicode-3.0 Unicode-DFS-2016 OFL-1.1 AFL-2.1'''.split()}
PIP_SYN = {'mit license': 'MIT', 'apache software license': 'Apache-2.0', 'bsd license': 'BSD', 'isc license (iscl)': 'ISC',
           'python software foundation license': 'PSF-2.0', 'public domain': 'CC0-1.0', 'the unlicense (unlicense)': 'Unlicense'}
PIP_RAW = re.compile(r'^(mit|apache|bsd|3-clause bsd|isc|cc0|http://www\.opensource\.org/licenses/mit)', re.I)
def spdx_ok(expr):
    toks = re.findall(r'\(|\)|[^\s()]+', expr.replace('/', ' OR '))
    pos = 0
    def atom():
        nonlocal pos
        if pos < len(toks) and toks[pos] == '(':
            pos += 1; v = orx(); pos += 1; return v
        v = pos < len(toks) and toks[pos].lower() in ALLOW; pos += 1
        if pos < len(toks) and toks[pos].upper() == 'WITH': pos += 2
        return v
    def andx():
        nonlocal pos
        v = atom()
        while pos < len(toks) and toks[pos].upper() == 'AND': pos += 1; v = atom() and v
        return v
    def orx():
        nonlocal pos
        v = andx()
        while pos < len(toks) and toks[pos].upper() == 'OR': pos += 1; v = andx() or v
        return v
    return bool(toks) and orx() and pos >= len(toks)
def classify(eco, lic):
    if re.search(r'gpl|gnu', lic, re.I): return 'copyleft'
    if re.search(r'\bmpl|mozilla|\bepl\b|eclipse public|cddl', lic, re.I): return 'weak'
    if eco != 'pip': return 'permissive' if spdx_ok(lic) else 'other'
    kind, _, val = lic.partition(':')
    if kind == 'E': return 'permissive' if spdx_ok(val) else 'other'
    if kind == 'C':
        parts = [p for p in val.split(';') if p not in ('OSI Approved', 'DFSG approved')]
        return 'permissive' if parts and all(PIP_SYN.get(p.lower()) for p in parts) else 'other'
    return 'permissive' if PIP_RAW.match(val) and 'proprietary' not in val.lower() else 'other'
eco = sys.argv[1]
for line in open(sys.argv[2]).read().split('\n'):
    if not line: continue
    f = line.split('\t')
    if eco == 'pip':
        lic = 'E:' + f[2] if f[2] else 'C:' + f[3] if f[3] else 'R:' + f[4]
    else:
        lic = f[3] if eco == 'go' else f[2]
    print('\t'.join((classify(eco, lic), f[0], f[1], lic)))
```

각 생태계 결과에 같은 방식으로 돌린다.

```bash
python3 -I $S/classify.py pip py.tsv > py.cls      # npm, cargo, go도 같다
cut -f1 py.cls | sort | uniq -c                    # 요약 표의 열
grep -v '^permissive' py.cls                       # 검토 표의 원본
cut -f4 py.cls | sort | uniq -c | sort -rn | head -5   # 상위 라이선스
```

### Python (`uv.lock`)

`uv export`는 `inbox-ranking`과 `sentiment` 그룹이 충돌해(`pyproject.toml:330`의 `conflicts`) `--all-groups`로 실패하므로 쓰지 않았다.
`uv.lock`을 직접 읽어 레지스트리 출처 패키지를 PyPI JSON API에 조회한다.

`pylic.py`:

```python
import tomllib, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
lock = tomllib.load(open(sys.argv[1], 'rb'))
pk = [(p['name'], p['version']) for p in lock['package'] if p.get('source', {}).get('registry')]
def get(nv):
    n, v = nv
    try:
        d = json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{n}/{v}/json', timeout=30))['info']
        cl = [c.split(' :: ')[-1] for c in d.get('classifiers', []) if c.startswith('License ::')]
        raw = ' '.join((d.get('license') or '').split())[:80]
        return (n, v, d.get('license_expression') or '', ';'.join(cl), raw)
    except Exception as e:
        return (n, v, '', '', 'ERR ' + str(e)[:40])
with ThreadPoolExecutor(16) as ex:
    for r in ex.map(get, pk):
        print('\t'.join(r))
```

```bash
python3 -I $S/pylic.py $W/uv.lock > py.tsv
python3 -I $S/pylic.py $W/services/llm-gateway/uv.lock > py-llm.tsv
python3 -I $S/pylic.py $W/services/stripe-mock/uv.lock > py-stripe.tsv
# requirements.txt의 고정 버전(== 줄)만, 같은 열 순서로
grep '==' $W/common/ingestion/acceptance_tests/requirements.txt | while IFS='=' read n _ v; do
  printf '%s\t%s\t%s\n' "$n" "$v" "$(curl -s https://pypi.org/pypi/$n/$v/json | jq -r '.info | [(.license_expression // ""), ([.classifiers[]|select(startswith("License ::"))|split(" :: ")|last]|join(";")), ((.license // "")|gsub("\\s+";" ")|.[0:80])] | @tsv')"
done > py-acc.tsv
```

직접/전이는 `pyproject.toml`의 `[project] dependencies`와 `[dependency-groups]`에 이름이 있는지로 갈랐다. 전이 의존을 끌어온 패키지는 `uv.lock`의 각 패키지 `dependencies`를 거꾸로 찾아 적었다.

### npm (`pnpm-lock.yaml`, `package-lock.json`)

`npmkeys.py`는 pnpm 잠금 파일(형식 9.0과 5.4)의 `packages:` 절 키와 `package-lock.json`의 `packages` 항목에서 `이름<TAB>버전`을 뽑는다. 버전이 숫자로 시작하지 않는 항목(git·tarball 출처)은 빠진다.

`npmkeys.py`:

```python
import json, re, sys
p = sys.argv[1]
t = open(p).read()
if p.endswith('.json'):
    keys = {(k.rsplit('node_modules/', 1)[1], v['version'])
            for k, v in json.loads(t)['packages'].items()
            if 'node_modules/' in k and 'version' in v and not v.get('link')}
else:
    sec = t.split('\npackages:\n', 1)[1].split('\nsnapshots:\n', 1)[0]
    keys = set(re.findall(r"^  '?/?((?:@[^/@']+/)?[^@/'\s]+)[@/]([0-9][^':\s_(]*)[^:]*'?:\s*$", sec, re.M))
for k in sorted(keys):
    print('%s\t%s' % k)
```

`npmlic.py`:

```python
import json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
pk = [l.split('\t') for l in open(sys.argv[1]).read().split('\n') if l]
def get(nv):
    n, v = nv
    err = ''
    for _ in range(3):
        try:
            d = json.load(urllib.request.urlopen('https://registry.npmjs.org/%s/%s' % (n.replace('/', '%2F'), v), timeout=30))
            l = d.get('license') or d.get('licenses')
            if isinstance(l, dict): l = l.get('type')
            if isinstance(l, list): l = ' OR '.join(x.get('type', '?') if isinstance(x, dict) else str(x) for x in l)
            return (n, v, str(l) if l else 'UNKNOWN')
        except Exception as e:
            err = str(e)[:40]
    return (n, v, 'ERR ' + err)
with ThreadPoolExecutor(32) as ex:
    for r in ex.map(get, pk):
        print('\t'.join(r))
```

```bash
for f in $(git -C $W ls-files '*pnpm-lock.yaml' '*package-lock.json'); do
  python3 -I $S/npmkeys.py $W/$f > "keys-$(echo $f | tr / _).tsv"
done
cat keys-*.tsv | sort -u > keys-all.tsv
python3 -I $S/npmlic.py keys-all.tsv > npm-all.tsv
# 잠금 파일별 결과: 키 목록과 조회 결과를 이름·버전으로 잇는다
awk -F'\t' 'NR==FNR{a[$1"\t"$2]=1;next} ($1"\t"$2) in a' keys-pnpm-lock.yaml.tsv npm-all.tsv > npm.tsv
```

`SEE LICENSE IN ...`인 패키지는 레지스트리 `dist.tarball`을 받아 각자 새 빈 디렉터리에 풀고 라이선스 파일만 읽었다.

```bash
n=@anthropic-ai/claude-agent-sdk; v=0.3.280; d=$(mktemp -d)
curl -s -o $d/pkg.tgz "$(curl -s https://registry.npmjs.org/${n/\//%2F}/$v | jq -r .dist.tarball)"
mkdir $d/x && tar -xzf $d/pkg.tgz -C $d/x --no-same-owner && cat $d/x/package/LICENSE*
```

### Rust (`Cargo.lock`)

`--manifest-path`로 잠금 파일을 지정하고 임시 디렉터리에서 돌린다. 그러면 `cm.json`이 저장소 밖에 생긴다.
`--locked`라서 `Cargo.lock`이 맞지 않으면 고치지 않고 실패한다. `net.offline` 같은 설정은 덮어쓰지 않는다. 저장소의 `rust/.cargo/config.toml`에는 `net.offline`이 없다(이 파일은 `rustflags`와 `SQLX_OFFLINE` 등 `[env]` 값만 둔다).

```bash
for m in rust cli funnel-udf rust/common/hogvm/node; do
  n=$(echo $m | tr / _)
  cargo metadata --manifest-path $W/$m/Cargo.toml --format-version 1 --locked > cm-$n.json
  jq -r '.packages[] | select(.source!=null) | [.name,.version,(.license // ("FILE:"+(.license_file//"")))] | @tsv' cm-$n.json > cargo-$n.tsv
  jq -r '.packages[] | select(.source==null) | (.license // "UNSET")' cm-$n.json | sort | uniq -c   # 워크스페이스 크레이트
done
```

`license_file`만 있는 크레이트는 `~/.cargo/registry/src/index.crates.io-*/<이름>-<버전>/`에서 본문을 읽었다.

### Go (`go.mod`)

`go` 명령은 쓰지 않았다. `golic.py`가 `go.mod`의 `require` 줄을 읽고, 모듈마다 `proxy.golang.org`의 zip을 메모리로 받아 압축을 풀지 않고 최상위 `LICENSE*`·`LICENCE*`·`COPYING*` 파일만 읽는다.
본문 판별은 정해진 문구로 한다. MPL 본문이 GNU 라이선스를 언급하므로 MPL을 먼저 본다.

`golic.py`:

```python
import io, re, sys, urllib.request, zipfile
from concurrent.futures import ThreadPoolExecutor
t = open(sys.argv[1]).read()
reqs = re.findall(r'^\s*(?:require\s+)?([\w.\-/~]+\.[\w.\-/~]+)\s+(v[\w.\-+]+)(\s*//\s*indirect)?\s*$', t, re.M)
SIG = [('MPL-2.0', r'Mozilla Public License,? (v\. |version )?2\.0'), ('GPL', r'GNU (LESSER |LIBRARY )?GENERAL PUBLIC'),
       ('Apache-2.0', r'Apache License,?\s+Version 2\.0'), ('MIT', r'Permission is hereby granted, free of charge'),
       ('BSD-3-Clause', r'Neither the name|names of (its|the copyright holder|their) contributors'),
       ('BSD-2-Clause', r'Redistribution and use in source and binary forms'),
       ('ISC', r'Permission to use, copy, modify, and(/or)? distribute this software for any'),
       ('Unlicense', r'free and unencumbered software'), ('CC0-1.0', r'CC0 1\.0')]
def esc(s): return re.sub(r'[A-Z]', lambda m: '!' + m.group(0).lower(), s)
def get(r):
    m, v, ind = r
    try:
        z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(f'https://proxy.golang.org/{esc(m)}/@v/{esc(v)}.zip', timeout=120).read()))
        root = f'{m}@{v}/'
        files = [n for n in z.namelist() if n.startswith(root) and '/' not in n[len(root):] and re.match(r'(LICEN[CS]E|COPYING)', n[len(root):], re.I)]
        found = []
        for f in files:
            txt = z.read(f).decode('utf-8', 'replace')
            for name, pat in SIG:
                if re.search(pat, txt, re.I):
                    found.append(name); break
            else:
                found.append('UNKNOWN(' + f[len(root):] + ')')
        lic = ' AND '.join(sorted(set(found))) or 'NO-LICENSE-FILE'
    except Exception as e:
        lic = 'ERR ' + str(e)[:40]
    return (m, v, 'indirect' if ind else 'direct', lic)
with ThreadPoolExecutor(8) as ex:
    for row in ex.map(get, reqs):
        print('\t'.join(row))
```

```bash
for f in $(git -C $W ls-files '*go.mod'); do
  python3 -I $S/golic.py $W/$f > "go-$(echo $f | tr / _).tsv"
done
```

### `@posthog/brand` 사용 파일 수

```bash
cd $W
git grep -l '@posthog/brand' -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.mjs' '*.css' '*.scss' | wc -l          # 173
git grep -l '@posthog/brand' -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.mjs' '*.css' '*.scss' | grep -c '^products/desktop/'   # 5
git grep -l -E "(from|import|@import|@use|require\(|import\() *['\"]@posthog/brand" -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.mjs' '*.css' '*.scss' | wc -l   # 163, desktop 3
```

두 수의 차이 10개는 주석·설정·`url(...)` 경로로만 이름이 나오는 파일이다(예: `frontend/src/styles/fonts.scss`, `Hogfetti.tsx`, `common/esbuilder/utils.mjs`).

### 글꼴 메타데이터

`fontTools`와 `brotli`는 저장소 밖 가상 환경에 설치했다(`uv venv`, `uv pip install fonttools brotli`).

`fontnames.py`:

```python
import sys
from fontTools.ttLib import TTFont
for p in sys.argv[1:]:
    n = TTFont(p, lazy=True)['name']
    get = lambda i: (n.getDebugName(i) or '').replace('\n', ' ')[:160]
    print(f'{p}\t{get(1)}\tC={get(0)}\tL={get(13)}\tU={get(14)}')
```

### 한계

- 잠금 파일 전체를 센다. 개발 도구, 테스트 전용, 선택적 플랫폼 바이너리(`@img/sharp-*`, `lightningcss-*`, `nvidia-*`, `@anthropic-ai/claude-agent-sdk-*`)도 들어간다. 배포 산출물에 실제로 들어가는지는 항목마다 따로 적은 곳 말고는 미확인이다.
- 레지스트리가 돌려준 문자열을 그대로 썼다. 패키지 소스의 `LICENSE` 파일과 대조한 것은 이 페이지에 "tarball", "본문"이라고 적은 항목뿐이다.
- `A OR B` 표기는 선택할 수 있는 쪽을 고를 수 있다고 본다. 법적 해석은 법무 검토 몫이다.
- Go는 모듈 최상위 라이선스 파일 하나의 첫 판별 결과만 쓴다. 하위 디렉터리의 다른 라이선스는 보지 않았다.
- Docker 이미지 안의 것은 세지 않았다. 베이스 이미지(`Dockerfile`의 `FROM`: `node:24.13.0-bookworm-slim`, `python:3.14.7-slim-bookworm` 등), apt 패키지(`Dockerfile.recording-rasterizer:114`의 `ffmpeg` 등), `Dockerfile.recording-rasterizer:148`이 받는 `chrome-headless-shell`, `Dockerfile:279~289`가 받는 GeoLite2-City DB(MaxMind 라이선스, 본문 미확인)가 여기에 든다.
- 터미널 기능이 실행 중 받는 패키지(`terminal-packages.json`)와 desktop 앱의 빌드 산출물은 열어 보지 않았다.

Decided in: buzzhog-gimc
