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

<!-- generated:scope:begin -->
Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml` — Do not edit by hand.

`git ls-files | grep -E '(^|/)(uv\.lock|pnpm-lock\.yaml|package-lock\.json|yarn\.lock|Cargo\.lock|go\.mod|go\.sum|requirements[^/]*\.txt)$'`는 32개 파일을 낸다. `yarn.lock`은 없다.

| 파일 | 생태계 | 처리 | 비고 |
| --- | --- | --- | --- |
| `uv.lock` | pip | 집계 | 메인 Django 앱 |
| `services/llm-gateway/uv.lock` | pip | 집계 | |
| `services/stripe-mock/uv.lock` | pip | 집계 | |
| `common/ingestion/acceptance_tests/requirements.txt` | pip | 집계 | `==`로 고정한 직접 의존만. 전이 의존은 잠금 파일이 없어 세지 않았다 |
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
| `rust/batch-import-worker/scripts/package-lock.json` | npm | 집계 | |
| `rust/Cargo.lock` | cargo | 집계 | Rust 서비스 워크스페이스 |
| `cli/Cargo.lock` | cargo | 집계 | `posthog-cli` 바이너리 |
| `funnel-udf/Cargo.lock` | cargo | 집계 | 크레이트 이름 `funnels` |
| `rust/common/hogvm/node/Cargo.lock` | cargo | 집계 | |
| `livestream/go.mod` | go | 집계 | |
| `bin/hobby-installer/go.mod` | go | 집계 | |
| `tools/phrocs/go.mod` | go | 집계 | |
| `clickhouse-udfs/util/go.mod` | go | 집계 | |
| `services/hogql-language-service/go.mod` | go | 집계 | |
| `packages/agent/agent-shadow/go.mod` | go | 집계 | `require`가 없다 |
| `bin/hobby-installer/go.sum`, `clickhouse-udfs/util/go.sum`, `livestream/go.sum`, `services/hogql-language-service/go.sum`, `tools/phrocs/go.sum` | go | 제외 | 같은 디렉터리의 `go.mod` `require` 목록을 대신 썼다. `go.sum`은 검증용 해시 목록이고, 빌드에 들어가지 않는 모듈(`/go.mod` 줄)까지 담는다 |

합계: 집계 25개, 제외 7개(`requirements.txt` 2개, `go.sum` 5개).
<!-- generated:scope:end -->

## 집계 요약

잠금 파일마다 항목을 `license-policy.toml`로 판정한 수다. 열의 뜻은 [분류 규칙](#분류-규칙)에 있다.
`review`와 `deny`가 `--check`를 실패시킨다. "승인된 예외"는 `status = "approved"`인 `[[package]]`·`[[path]]` 항목이 통과시킨 것이다. "review 면제"는 `[scope]`의 `development`가 면제한 `review`다.

<!-- generated:summary:begin -->
Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml` — Do not edit by hand.

| 파일 | 생태계 | 항목 수 | allow | 승인된 예외 | review 면제(development) | review | deny |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `uv.lock` | pip | 614 | 568 | 0 | 0 | 46 | 0 |
| `services/llm-gateway/uv.lock` | pip | 98 | 96 | 0 | 0 | 2 | 0 |
| `services/stripe-mock/uv.lock` | pip | 32 | 32 | 0 | 0 | 0 | 0 |
| `common/ingestion/acceptance_tests/requirements.txt` | pip | 9 | 9 | 0 | 0 | 0 | 0 |
| `pnpm-lock.yaml` | npm | 3984 | 3958 | 0 | 0 | 25 | 1 |
| `products/desktop/pnpm-lock.yaml` | npm | 3097 | 3078 | 0 | 0 | 18 | 1 |
| `packages/agent/pnpm-lock.yaml` | npm | 600 | 591 | 0 | 0 | 9 | 0 |
| `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml` | npm | 567 | 553 | 0 | 0 | 14 | 0 |
| `frontend/@posthog/lemon-ui/pnpm-lock.yaml` | npm | 110 | 110 | 0 | 0 | 0 | 0 |
| `tools/hedgebox-dummy/pnpm-lock.yaml` | npm | 450 | 435 | 0 | 0 | 15 | 0 |
| `products/canvas/packages/canvas_builder/package-lock.json` | npm | 226 | 226 | 0 | 0 | 0 | 0 |
| `products/visual_review/cli/package-lock.json` | npm | 157 | 143 | 0 | 0 | 14 | 0 |
| `.github/actions/paths-filter/package-lock.json` | npm | 550 | 550 | 0 | 0 | 0 | 0 |
| `.depot/actions/paths-filter/package-lock.json` | npm | 550 | 550 | 0 | 0 | 0 | 0 |
| `rust/batch-import-worker/scripts/package-lock.json` | npm | 4 | 4 | 0 | 0 | 0 | 0 |
| `rust/Cargo.lock` | cargo | 1200 | 1192 | 0 | 0 | 8 | 0 |
| `cli/Cargo.lock` | cargo | 446 | 446 | 0 | 0 | 0 | 0 |
| `funnel-udf/Cargo.lock` | cargo | 61 | 61 | 0 | 0 | 0 | 0 |
| `rust/common/hogvm/node/Cargo.lock` | cargo | 111 | 111 | 0 | 0 | 0 | 0 |
| `livestream/go.mod` | go | 86 | 85 | 0 | 0 | 1 | 0 |
| `bin/hobby-installer/go.mod` | go | 25 | 24 | 0 | 0 | 1 | 0 |
| `tools/phrocs/go.mod` | go | 30 | 30 | 0 | 0 | 0 | 0 |
| `clickhouse-udfs/util/go.mod` | go | 7 | 7 | 0 | 0 | 0 | 0 |
| `services/hogql-language-service/go.mod` | go | 1 | 1 | 0 | 0 | 0 | 0 |
| `packages/agent/agent-shadow/go.mod` | go | 0 | 0 | 0 | 0 | 0 | 0 |
| 잠금 파일 밖 파일(`[[path]]` 항목) | path | 14 | 0 | 0 | 0 | 13 | 1 |
<!-- generated:summary:end -->

- 항목은 잠금 파일의 `이름@버전` 하나다. 잠금 파일끼리 겹치는 항목은 파일마다 따로 센다.
- pip 항목 수는 레지스트리 출처 패키지만이다. git 출처(`infi-clickhouse-orm`, `pytest-split`, `pyproject.toml:344`, `:349`)와 워크스페이스 멤버는 빠진다.
- cargo 항목 수는 `source != null`인 외부 크레이트다. go 항목 수는 `go.mod`의 `require` 줄(직접과 `// indirect` 모두)이다.

### 위반 목록

`license-policy.toml`이 실패로 세는 항목이다. `--check`가 같은 판정에서 한 줄씩 낸다. 이 표는 이름·버전·라이선스·규칙이 같은 항목을 잠금 파일끼리 묶는다.
규칙 열은 판정을 정한 자리다. `[deny]`·`[review]`는 정책의 목록, `[[package]]`·`[[path]]`는 항목별 결정이다. `not an SPDX expression`은 찾은 문자열이 SPDX식이 아니라는 뜻이다.

<!-- generated:violations:begin -->
Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml` — Do not edit by hand.

`--check`가 실패로 세는 항목: 잠금 파일별 169건, 아래 표 111줄.

| 판정 | 생태계 | 이름 | 버전 | 찾은 라이선스 | 잠금 파일 | 규칙 |
| --- | --- | --- | --- | --- | --- | --- |
| deny | npm | `@posthog/brand` | 0.11.0, 0.12.3 | `SEE LICENSE IN LICENSE` | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | [[package]] `@posthog/brand` status=rejected |
| deny | path | `frontend/src/lib/components/Hogfetti/hogs/*.png` |  | `LicenseRef-PolyForm-Strict-1.0.0` | 추적 파일 15개 | [[path]] `frontend/src/lib/components/Hogfetti/hogs/*.png` status=rejected |
| review | cargo | `aws-lc-sys` | 0.37.1 | `ISC AND (Apache-2.0 OR ISC) AND OpenSSL` | `rust/Cargo.lock` | [review] licenses `OpenSSL` |
| review | cargo | `inferno` | 0.11.21, 0.12.4 | `CDDL-1.0` | `rust/Cargo.lock` | [review] licenses `CDDL-1.0` |
| review | cargo | `ring` | 0.16.20 | `FILE:LICENSE` | `rust/Cargo.lock` | [[package]] `ring` 0.16.20 status=proposed |
| review | cargo | `temporalio-client` | 0.5.0 | `FILE:LICENSE.txt` | `rust/Cargo.lock` | [[package]] `temporalio-client` status=proposed |
| review | cargo | `temporalio-common` | 0.5.0 | `FILE:LICENSE.txt` | `rust/Cargo.lock` | [[package]] `temporalio-common` status=proposed |
| review | cargo | `temporalio-common-wasm` | 0.5.0 | `FILE:LICENSE.txt` | `rust/Cargo.lock` | [[package]] `temporalio-common-wasm` status=proposed |
| review | cargo | `temporalio-protos` | 0.5.0 | `FILE:LICENSE.txt` | `rust/Cargo.lock` | [[package]] `temporalio-protos` status=proposed |
| review | go | `github.com/mattn/go-localereader` | v0.0.1 | `NO-LICENSE-FILE` | `bin/hobby-installer/go.mod`, `livestream/go.mod` | [[package]] `github.com/mattn/go-localereader` status=proposed |
| review | npm | `@anthropic-ai/claude-agent-sdk` | 0.3.280 | `SEE LICENSE IN README.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | [[package]] `@anthropic-ai/claude-agent-sdk` status=proposed |
| review | npm | `@anthropic-ai/claude-agent-sdk-darwin-arm64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-darwin-x64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-linux-arm64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-linux-arm64-musl` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-linux-x64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-linux-x64-musl` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-win32-arm64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@anthropic-ai/claude-agent-sdk-win32-x64` | 0.3.280 | `SEE LICENSE IN LICENSE.md` | `packages/agent/pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `@elevenlabs/types` | 0.13.0 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `@img/sharp-libvips-darwin-arm64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-darwin-x64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-arm` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-arm64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-ppc64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-riscv64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-s390x` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linux-x64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linuxmusl-arm64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-libvips-linuxmusl-x64` | 1.2.4, 1.3.2 | `LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `@img/sharp-libvips-*` status=proposed |
| review | npm | `@img/sharp-wasm32` | 0.34.5, 0.35.3 | `Apache-2.0 AND LGPL-3.0-or-later AND MIT` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [review] licenses `LGPL-3.0-or-later` |
| review | npm | `@img/sharp-win32-arm64` | 0.34.5, 0.35.3 | `Apache-2.0 AND LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [review] licenses `LGPL-3.0-or-later` |
| review | npm | `@img/sharp-win32-ia32` | 0.34.5, 0.35.3 | `Apache-2.0 AND LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [review] licenses `LGPL-3.0-or-later` |
| review | npm | `@img/sharp-win32-x64` | 0.34.5, 0.35.3 | `Apache-2.0 AND LGPL-3.0-or-later` | `nodejs/.../ml-mirror-image-scrub-sidecar/pnpm-lock.yaml`, `pnpm-lock.yaml`, `products/visual_review/cli/package-lock.json`, `tools/hedgebox-dummy/pnpm-lock.yaml` | [review] licenses `LGPL-3.0-or-later` |
| review | npm | `@mapbox/jsonlint-lines-primitives` | 2.0.2 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `@react-grab/cli` | 0.2.0 | `UNKNOWN` | `products/desktop/pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `@segment/fql-ts` | 1.10.1 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `elkjs` | 0.10.0 | `EPL-2.0` | `pnpm-lock.yaml` | [review] licenses `EPL-2.0` |
| review | npm | `exif-parser` | 0.1.12 | `UNKNOWN` | `products/desktop/pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `ffmpeg-static` | 5.3.0 | `GPL-3.0-or-later` | `pnpm-lock.yaml` | [[package]] `ffmpeg-static` status=proposed |
| review | npm | `gsap` | 3.14.2 | `Standard 'no charge' license: https://gsap.com/standard-license.` | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | [[package]] `gsap` status=proposed |
| review | npm | `heatmap.js` | 2.0.5 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `khroma` | 2.1.0 | `UNKNOWN` | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `oxlint-plugin-react-doctor` | 0.9.18 | `SEE LICENSE IN LICENSE` | `products/desktop/pnpm-lock.yaml` | not an SPDX expression |
| review | npm | `pastable` | 2.2.1 | `UNKNOWN` | `products/desktop/pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `posthog-js` | 1.438.8 | `(Apache-2.0 AND MIT)` | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | [[package]] `posthog-js` status=proposed |
| review | npm | `posthog-js` | 1.376.2 | `SEE LICENSE IN LICENSE` | `tools/hedgebox-dummy/pnpm-lock.yaml` | [[package]] `posthog-js` status=proposed |
| review | npm | `react-doctor` | 0.9.18 | `SEE LICENSE IN LICENSE` | `products/desktop/pnpm-lock.yaml` | [[package]] `react-doctor` status=proposed |
| review | npm | `typed-openapi` | 2.2.7 | `UNKNOWN` | `products/desktop/pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `union` | 0.5.0 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | npm | `unionfs` | 4.6.0 | `UNKNOWN` | `pnpm-lock.yaml` | `UNKNOWN` is in no list |
| review | path | `.github/scripts/signal-fanout` |  | `MIT` | 추적 파일 1개 | [[path]] `.github/scripts/signal-fanout` status=proposed |
| review | path | `frontend/public/Inter.{woff,woff2}` |  | `OFL-1.1` | 추적 파일 2개 | [[path]] `frontend/public/Inter.{woff,woff2}` status=proposed |
| review | path | `frontend/public/fonts/TwemojiCountryFlags.woff2` |  | `CC-BY-4.0` | 추적 파일 1개 | [[path]] `frontend/public/fonts/TwemojiCountryFlags.woff2` status=proposed |
| review | path | `frontend/public/fonts/cmunti-webfont.woff` |  | `OFL-1.1` | 추적 파일 1개 | [[path]] `frontend/public/fonts/cmunti-webfont.woff` status=proposed |
| review | path | `frontend/public/fonts/fairytale_serif-webfont.{woff,woff2}` |  | `LicenseRef-Unknown` | 추적 파일 2개 | [[path]] `frontend/public/fonts/fairytale_serif-webfont.{woff,woff2}` status=proposed |
| review | path | `frontend/src/scenes/terminal/assets/buildroot-bzimage.bin` |  | `GPL-2.0-only` | 추적 파일 1개 | [[path]] `frontend/src/scenes/terminal/assets/buildroot-bzimage.bin` status=proposed |
| review | path | `frontend/src/scenes/terminal/assets/jq-linux-i386.bin` |  | `MIT AND BSD-2-Clause AND LGPL-2.1-only` | 추적 파일 1개 | [[path]] `frontend/src/scenes/terminal/assets/jq-linux-i386.bin` status=proposed |
| review | path | `frontend/src/scenes/terminal/assets/tools-linux-i386.tar.gz.bin` |  | `GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT` | 추적 파일 1개 | [[path]] `frontend/src/scenes/terminal/assets/tools-linux-i386.tar.gz.bin` status=proposed |
| review | path | `frontend/src/scenes/terminal/assets/{seabios,vgabios}.bin` |  | `LGPL-3.0-only AND GPL-3.0-only` | 추적 파일 2개 | [[path]] `frontend/src/scenes/terminal/assets/{seabios,vgabios}.bin` status=proposed |
| review | path | `products/desktop/**/OpenRunde/*` |  | `LicenseRef-Unknown` | 추적 파일 12개 | [[path]] `products/desktop/**/OpenRunde/*` status=proposed |
| review | path | `products/desktop/apps/mobilehog/assets/fonts/RoundHog*.ttf` |  | `OFL-1.1` | 추적 파일 5개 | [[path]] `products/desktop/apps/mobilehog/assets/fonts/RoundHog*.ttf` status=proposed |
| review | path | `products/desktop/apps/{mobile,mobilehog}/assets/fonts/JetBrainsMono*` |  | `OFL-1.1` | 추적 파일 18개 | [[path]] `products/desktop/apps/{mobile,mobilehog}/assets/fonts/JetBrainsMono*` status=proposed |
| review | path | `products/desktop/packages/electron-trpc/**` |  | `MIT` | 추적 파일 29개 | [[path]] `products/desktop/packages/electron-trpc/**` status=proposed |
| review | pip | `arro3-core` | 0.6.5 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `autoevals` | 0.2.0 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `braintrust` | 0.2.4 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `braintrust-core` | 0.0.59 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `braintrust-langchain` | 0.0.4 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `browser-cookie3` | 0.20.1 | `R:lgpl` | `uv.lock` | `lgpl` is in no list |
| review | pip | `chardet` | 5.2.0 | `C:GNU Lesser General Public License v2 or later (LGPLv2+)` | `uv.lock` | [review] licenses `LGPL-2.0-or-later` |
| review | pip | `clickhouse-pool` | 0.5.3 | `C:GNU Lesser General Public License v3 or later (LGPLv3+)` | `uv.lock` | [review] licenses `LGPL-3.0-or-later` |
| review | pip | `cramjam` | 2.12.1 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `docker-image-py` | 0.1.13 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `google-crc32c` | 1.8.0 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `jwcrypto` | 1.5.7 | `E:LGPL-3.0-or-later` | `uv.lock` | [review] licenses `LGPL-3.0-or-later` |
| review | pip | `linkedin-api-client` | 0.3.0 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `linkedin-api-client` status=proposed |
| review | pip | `lupa` | 2.7 | `R:MIT style` | `uv.lock` | not an SPDX expression |
| review | pip | `mistralai` | 1.6.0 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `mypy-extensions` | 1.1.0 | `R:` | `services/llm-gateway/uv.lock`, `uv.lock` | not an SPDX expression |
| review | pip | `nvidia-cublas-cu12` | 12.8.4.1 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cuda-cupti-cu12` | 12.8.90 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cuda-nvrtc-cu12` | 12.8.93 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cuda-runtime-cu12` | 12.8.90 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cudnn-cu12` | 9.10.2.21 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cufft-cu12` | 11.3.3.83 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cufile-cu12` | 1.13.1.3 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-curand-cu12` | 10.3.9.90 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cusolver-cu12` | 11.7.3.90 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cusparse-cu12` | 12.5.8.93 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-cusparselt-cu12` | 0.7.1 | `R:NVIDIA Proprietary Software` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-nccl-cu12` | 2.27.5 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-nvjitlink-cu12` | 12.8.93 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-nvshmem-cu12` | 3.3.20 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `nvidia-nvtx-cu12` | 12.8.90 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `nvidia-*-cu12` status=proposed |
| review | pip | `paramiko` | 3.5.1 | `C:GNU Library or Lesser General Public License (LGPL)` | `uv.lock` | [[package]] `paramiko` status=proposed |
| review | pip | `playwright` | 1.60.0 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `polyleven` | 0.11.0 | `R:` | `uv.lock` | not an SPDX expression |
| review | pip | `prometheus-fastapi-instrumentator` | 7.1.0 | `C:OSI Approved` | `services/llm-gateway/uv.lock` | not an SPDX expression |
| review | pip | `psycopg` | 3.2.10 | `C:GNU Lesser General Public License v3 (LGPLv3)` | `uv.lock` | [[package]] `psycopg` status=proposed |
| review | pip | `psycopg-binary` | 3.2.10 | `C:GNU Lesser General Public License v3 (LGPLv3)` | `uv.lock` | [review] licenses `LGPL-3.0-only` |
| review | pip | `psycopg2-binary` | 2.9.11 | `C:GNU Library or Lesser General Public License (LGPL)` | `uv.lock` | not an SPDX expression |
| review | pip | `pymssql` | 2.3.8 | `E:LGPL-2.1-or-later` | `uv.lock` | [review] licenses `LGPL-2.1-or-later` |
| review | pip | `python-stdnum` | 2.2 | `C:GNU Lesser General Public License v2 or later (LGPLv2+)` | `uv.lock` | [review] licenses `LGPL-2.0-or-later` |
| review | pip | `suds-community` | 1.2.0 | `C:GNU Library or Lesser General Public License (LGPL)` | `uv.lock` | not an SPDX expression |
| review | pip | `tbb` | 2022.3.1 | `C:Other/Proprietary License` | `uv.lock` | [[package]] `tbb` status=proposed |
| review | pip | `tcmlib` | 1.4.1 | `C:Other/Proprietary License` | `uv.lock` | not an SPDX expression |
| review | pip | `text-unidecode` | 1.3 | `C:Artistic License;GNU General Public License (GPL);GNU General Public License v2 or later (GPLv2+)` | `uv.lock` | not an SPDX expression |
| review | pip | `tld` | 0.13.2 | `E:MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later` | `uv.lock` | [review] licenses `MPL-1.1` |
| review | pip | `umap-learn` | 0.5.7 | `C:OSI Approved` | `uv.lock` | not an SPDX expression |
| review | pip | `uritemplate` | 4.2.0 | `R:BSD 3-Clause OR Apache-2.0` | `uv.lock` | not an SPDX expression |
<!-- generated:violations:end -->

가장 많은 라이선스(루트 잠금 파일 기준):

<!-- generated:top:begin -->
Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml` — Do not edit by hand.

| 생태계 | 상위 5개 | 기준 |
| --- | --- | --- |
| pip(`uv.lock`) | 분류자 `MIT License` 163, 분류자 `Apache Software License` 112, 분류자 `BSD License` 78, SPDX식 `MIT` 57, SPDX식 `Apache-2.0` 42 | 패키지마다 `license_expression`(SPDX식), `License ::` 분류자, `license` 원문 중 처음으로 비어 있지 않은 값 하나 |
| npm(`pnpm-lock.yaml`) | `MIT` 3071, `Apache-2.0` 429, `ISC` 172, `BSD-3-Clause` 86, `MIT-0` 56 | 레지스트리 `license` 필드 |
| cargo(`rust/Cargo.lock`) | `MIT OR Apache-2.0` 427, `MIT` 287, `Apache-2.0` 143, `Apache-2.0 OR MIT` 86, `MIT/Apache-2.0` 83 | `Cargo.toml`의 `license` 필드 |
| go(6개 `go.mod` 합계 149줄) | `MIT` 89, `BSD-3-Clause` 26, `Apache-2.0` 23, `ISC` 3, `BSD-2-Clause` 3 | 모듈 zip의 최상위 `LICENSE`·`COPYING` 본문 판별 |
<!-- generated:top:end -->

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
| `gsap` 3.14.2 | `pnpm-lock.yaml`, `products/desktop/pnpm-lock.yaml` | 전이(`@posthog/hedgehog-mode` 0.0.63·0.0.53의 `dependencies`가 `gsap ^3.12.7`) | 레지스트리 `Standard 'no charge' license: https://gsap.com/standard-license.` 패키지 안에는 라이선스 본문이 없고, `README.md:62`는 "100% FREE including ... commercial use", `:90~91`은 위 주소를 가리킨다. 웹 페이지 본문(2026-10-16 확인, "Effective date: April 30, 2025"): Webflow가 "Permitted Uses"에 한해 비독점 라이선스를 준다. Webflow와 경쟁하는 노코드 시각 애니메이션 도구에서의 사용, 그런 제품을 위한 역공학, 독점 고지 제거를 금지한다. Webflow는 위반 시 해지할 수 있고 약관을 고칠 수 있다. "end users are not charged a fee"를 조건으로 적은 옛 "Plain English Summary"는 페이지 HTML 소스의 주석(`<!-- … -->`) 안에만 남아 있고 화면에는 보이지 않는다(`curl`로 받은 원문에서 주석을 지우면 이 문구가 0회 나온다) | 헤지호그 UI(아래 `@posthog/hedgehog-mode`) | https://gsap.com/standard-license | 표시되는 본문의 금지·해지·변경 조항이 이 포크의 상업 운영에 걸리는지 |
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

`OR`의 한쪽이 `allow`이면 `allow`로 센다(분류 규칙 5). 그래서 이 표에 두지 않은 이중 라이선스가 있다: `node-forge` 1.4.0(`(BSD-3-Clause OR GPL-2.0)`), `r-efi` 5.3.0(`MIT OR Apache-2.0 OR LGPL-2.1-or-later`), `dompurify`(`(MPL-2.0 OR Apache-2.0)`). 어느 쪽을 고르는지는 법무 검토 몫이다.

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
| `elkjs` 0.10.0 | `pnpm-lock.yaml` | 직접(`frontend`, `products/{data_modeling,engineering_analytics,product_analytics,workflows}`의 `package.json`) | EPL-2.0 |
| `brownstone` 3.0.0, `fernet` 0.2.2, `indent_write` 2.2.0, `nom-supreme` 0.8.0, `option-ext` 0.2.0, `webpki-roots` 0.25.4, `colored` 3.1.1 | `rust/Cargo.lock` | 전이 | MPL-2.0 |
| `smartstring` 1.0.1 | `rust/Cargo.lock` | 전이 | `MPL-2.0+` |
| `inferno` 0.11.21, 0.12.4 | `rust/Cargo.lock` | 전이 | CDDL-1.0 |
| `brownstone` 3.0.0, `colored` 3.0.0, `indent_write` 2.2.0, `nom-supreme` 0.8.0, `option-ext` 0.2.0 | `cli/Cargo.lock` | 전이 | MPL-2.0 |
| `github.com/hashicorp/golang-lru/v2` v2.0.7 | `livestream/go.mod:14`(직접), `bin/hobby-installer/go.mod:21`(`// indirect`) | 직접·전이 | MPL-2.0. 모듈 zip의 `LICENSE` 첫 줄 `Copyright (c) 2014 HashiCorp, Inc.`, 다음 줄 `Mozilla Public License, version 2.0` |

### 허용형이지만 표기가 특이한 항목

아래는 2026-10-16 집계에서 "비OSI·독점·미확인"으로 센 것 가운데 본문을 확인해 보니 허용형인 것이다. 지금의 요약 표에서는 정책 판정에 따라 `allow`나 `review`다. 고지나 출처 표시 의무가 붙는다.

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
| `products/logs/backend/vendor/drain3/drain.py`, `masking.py` | IBM Drain3 0.9.11 | MIT | `Copyright (c) 2020-2022 International Business Machines`(파일 머리 주석에 전문) | 각 파일 1~28행(MIT 전문은 4~25행), `__init__.py:1~3` |
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
| `frontend/public/Inter.woff`, `Inter.woff2` | Inter | `Copyright 2020 The Inter Project Authors (https://github.com/rsms/inter)`. 13번(라이선스) 필드는 비어 있고 14번이 OFL 안내 주소 `http://scripts.sil.org/OFL`다. 판 번호는 메타데이터에 없다 | 없다 | 앱 기본 글꼴이다. `frontend/src/styles/fonts.scss:7~8`, `:20~21`, `:34~35`가 쓴다 |
| `products/desktop/packages/ui/src/assets/fonts/JetBrainsMono/`, `products/desktop/apps/mobile/assets/fonts/`, `products/desktop/apps/mobilehog/assets/fonts/`의 JetBrains Mono | JetBrains Mono | `Copyright 2020 The JetBrains Mono Project Authors`, SIL OFL 1.1 | `packages/ui/src/assets/fonts/JetBrainsMono/OFL.txt`만 있다 | 모바일 앱 두 곳에는 사본이 없다 |
| `products/desktop/packages/ui/src/assets/fonts/OpenRunde/`, `products/desktop/apps/mobile/assets/fonts/OpenRunde/` | Open Runde | `Copyright 2023 Laurids Kern`, 라이선스 필드 비어 있음 | 없다 | 라이선스 미확인 |
| `products/desktop/apps/mobilehog/assets/fonts/RoundHog*.ttf`, `@posthog/brand`의 `dist/fonts/RoundHog*.woff2` | RoundHog(PostHog 브랜드 글꼴) | "RoundHog derived from Inter (Rasmus Andersson); rounded after Open Runde (Laurids Kern). SIL OFL 1.1." | 없다 | 글꼴 메타데이터는 OFL 1.1, 담긴 패키지 `@posthog/brand`의 `LICENSE`는 PolyForm Strict다. 어느 쪽이 걸리는지 법무 확인. 프런트엔드는 `frontend/src/styles/fonts.scss:47~110`에서 이 글꼴 8종을 쓴다 |
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
| `Copyright 2020 The Inter Project Authors`(SIL OFL) | `frontend/public/Inter.woff`, `Inter.woff2` | 글꼴 메타데이터에 저작권과 OFL URL만 있음. `OFL.txt` 없음 |
| JetBrains Mono OFL | 모바일 앱 글꼴 디렉터리 두 곳 | 메타데이터에 라이선스 문장만 있음. `OFL.txt` 없음 |
| 터미널 바이너리의 GPL·LGPL 본문 | `frontend/public/terminal/*.txt`, `tools-linux-i386.tar.gz.bin` 안 `licenses/` | 커널(GPL-2.0) 본문만 없음 |

브랜딩 쪽 저작권 고지 요약은 [branding.md](branding.md)에도 있다.

## 정책 파일

저장소 루트의 `license-policy.toml`이 어느 라이선스를 허용하고 막을지 적는 정책 원본이다.
2026-10-16에 레이븐이 채택했다(`status = "adopted"`, buzzhog-djp9).
`wiki/_tools/gen_licenses.py --check`와 PR 게이트(`.github/workflows/license-gate.yml`, [PR 게이트](#pr-게이트))가 이 파일을 읽는다([집계 방법](#집계-방법)). 저장소 전체 스캔은 아직 읽지 않는다. buzzhog-djp9.fai에서 붙인다.
이 결정은 법률 자문이 아니다. 판매 전 법무 검토는 따로 받는다.

- 판정은 `allow`, `review`, `deny` 세 가지다. `review`는 사람이 보고 결정을 적기 전까지 검사 실패로 센다. 어느 목록에도 없는 식별자, `UNKNOWN`, `SEE LICENSE IN ...`, 조회 오류, `license_file`만 있는 크레이트는 `review`다.
- 식별자는 SPDX다. SPDX에 없는 것(PolyForm Strict, GSAP, 독점)은 `LicenseRef-`를 붙였다.
- `A OR B`는 더 좋은 쪽, `A AND B`는 더 나쁜 쪽, `X WITH 예외`는 `X`로 판정하되 예외가 deny 목록에 걸리면 `deny`다(`Apache-2.0 WITH Commons-Clause`). [분류 규칙](#분류-규칙)이 그 구현이다. 정확히 맞는 식별자가 접두사보다 먼저이고, 접두사끼리는 `deny`가 `review`보다 먼저다.

### 결정한 목록

| 구분 | 라이선스 | 비고 |
| --- | --- | --- |
| allow | MIT, BSD, Apache-2.0, ISC, 0BSD, Zlib, BSL-1.0, Unlicense, CC0, PSF, BlueOak, Unicode 등 33개 | 고지(저작권·라이선스 본문)를 싣는다 |
| allow | `MPL-2.0` | 파일 단위 카피레프트. 수정하지 않고 쓸 때만 허용한다. 수정하면 그 파일을 MPL-2.0으로 공개해야 한다 |
| allow | `WTFPL` | 본문이 비격식이지만 허용형이다 |
| allow + 고지 | `OFL-1.1`, `CC-BY-3.0`, `CC-BY-4.0` | `[allow] notice` 목록. 저작권·라이선스 본문에 더해 글꼴의 OFL 사본, 출처 표시를 산출물이나 NOTICE에 싣는다 |
| review | GPL, LGPL, `MPL-1.1`, EPL, CDDL, `CC-BY-SA-*`, Artistic, `OpenSSL`, `BSD-4-Clause`, EUPL, OSL, CPAL | 패키지·경로마다 사람이 한 번 보고 결정을 적는다 |
| deny | AGPL, SSPL, BUSL, Elastic-2.0, Commons Clause, PolyForm, `CC-BY-NC`, 독점 | 예외는 제거·대체 작업으로 푼다 |

`gen_licenses.py`의 허용 목록은 이 파일의 `[allow]`다. 스크립트에 따로 적은 목록은 없다.

### 범위와 승인

- 항목의 `scope`는 `distributed`(기본) 또는 `development`다. 개발·테스트·CI 전용 의존(uv `dev` 그룹, devDependencies, `.github/actions`·`.depot/actions`)은 `development`다. `deny`는 두 범위에 똑같이 걸리고, `review`는 `development`에서 면제한다.
- 검사는 범위를 두 곳에서만 읽는다. `.github/actions/`·`.depot/actions/` 아래 잠금 파일의 항목은 `development`다. 나머지는 `distributed`다. `approved` 항목의 `scope`는 그 항목이 `verdict = "review"`를 적었을 때만 차이를 낸다. 다른 `approved` 항목은 `deny`가 아니면 이미 "승인된 예외"로 통과하고, `deny`는 두 범위에 똑같이 걸리기 때문이다. uv `dev` 그룹과 devDependencies는 잠금 파일에서 읽지 않는다. 프런트엔드는 devDependencies도 번들에 넣으므로, 개발 전용 패키지도 사람이 패키지마다 승인해야 통과한다. `proposed` 항목의 `scope`도 `license`·`verdict`처럼 적용하지 않는다.
- `[[package]]`는 패키지별 결정이다. 레지스트리 값이 비어 있는 패키지의 라이선스를 본문으로 바로잡거나(`license`), 정책 판정을 덮어쓴다(`verdict`). `license`와 `verdict`는 `status`가 `approved`인 항목에만 적용한다. `proposed` 항목에 걸리면 `license`·`verdict`와 상관없이 `review`로 센다(찾은 라이선스가 `deny`면 `deny`). 그래서 라이선스가 `allow`여도 `proposed`는 검사 실패다. `rejected`는 제거·대체가 결정된 것이고, 걸리면 `deny`로 센다.
- `approved` 항목은 `version`을 고정하거나 `review_by`를 적어야 한다. 둘 다 없으면 검사가 거부한다. 그런 항목과 `review_by`가 지난 항목은 `proposed`처럼 센다. `[[path]]`는 glob으로만 맞추므로 `version`이 아무것도 고정하지 않는다. 그래서 `approved` `[[path]]`는 `review_by`가 있어야 한다. `review_by`는 `YYYY-MM-DD`다.
- `approved` 항목은 `verdict`가 있으면 그것을, 없으면 `license`를, 그것도 없으면 찾은 라이선스를 판정한다. 결과가 `deny`가 아니면 "승인된 예외"로 통과한다. `deny` 라이선스를 통과시키려면 `verdict = "allow"`를 적는다.
- `[[path]]`는 잠금 파일 밖 파일(터미널 바이너리, 글꼴, 복사한 이미지, 벤더링한 코드)에 같은 결정을 적는 자리다.

### 이미 들어 있는 deny·review 대상

- `@posthog/brand`와 복사본 Hogfetti PNG: `rejected`. 상업 사용이 허가되지 않아 제거·대체가 결정됐다. 대체 작업은 buzzhog-9ies다. RoundHog 글꼴 항목은 OFL과 PolyForm 중 어느 쪽이 걸리는지 정하지 않았으므로 `proposed`로 두고, 같은 작업에서 바꾼다.
- `@anthropic-ai/claude-agent-sdk`, `react-doctor`, `linkedin-api-client`, `tbb`(`deny`), 터미널 GPL 바이너리, `nvidia-*`, `gsap`(`review`): `proposed`다. 항목별 조사(buzzhog-wrap, buzzhog-2txv, buzzhog-ra0l, buzzhog-auf6, buzzhog-nhi6)에서 예외로 둘지 제거할지 정한다.
- 나머지 `[[package]]`·`[[path]]` 항목도 `proposed`다. 위 "법무 검토가 필요한 항목"과 "잠금 파일 밖 제3자 구성요소" 표에서 옮겼다. `OFL-1.1`·`CC-BY` 글꼴·데이터 항목의 `review`는 라이선스가 아니라 고지 파일이 없어서 남은 것이다. `proposed`라서 라이선스가 `allow`여도 고지 파일을 넣고 `approved`로 닫기 전까지 검사 실패다.

### PR 게이트

`.github/workflows/license-gate.yml`이 `pull_request`와 `develop`로의 push, 수동 실행(`workflow_dispatch`)에서 돈다. 이 포크의 다른 CI는 `.depot/workflows/`에 있고 `.github/workflows/`에는 이 파일 하나뿐이다.
작업은 셋이다.

| 작업 | 하는 일 | 실행 시점 |
| --- | --- | --- |
| `Dependency review` | GitHub `actions/dependency-review-action`(v4.9.0)이 PR이 더하거나 바꾼 의존성의 라이선스를 본다. 정책의 deny 목록에 걸리면 실패한다 | `pull_request`만 |
| `Policy check` | `python3 -I wiki/_tools/gen_licenses.py --check`. 잠금 파일 전체와 `[[path]]` 항목을 정책으로 판정한다 | 항상 |
| `License gate pass` | 위 둘의 결과를 모아 한 개의 상태 검사로 낸다. 브랜치 보호에서 필수 검사로 고를 이름이다 | 항상 |

- **보고만 한다(report-only).** 지금 트리에는 알려진 위반이 169건(deny 3, review 166)이라 켜 두면 모든 PR이 막힌다. 저장소 변수 `LICENSE_GATE_ENFORCE`가 `true`가 아니면 두 검사는 돌고 결과를 작업 요약(job summary)과 경고 주석으로 보이되 작업은 성공으로 끝난다. 켜는 것은 코드 변경이 아니라 GitHub 설정(Settings, Variables)에서 이 변수를 `true`로 두는 일이다. 켜기 전에 위반 169건을 먼저 줄이거나 `[[package]]`·`[[path]]`로 닫는다.
- **머지를 막는 것은 별개 설정이다.** 워크플로가 실패해도 브랜치 보호에서 `License gate pass`를 필수 상태 검사로 지정하지 않으면 머지는 막히지 않는다. 그것은 사람이 GitHub에서 하는 설정이다.
- **`deny-licenses`를 골랐다.** 이 액션은 `allow-licenses`와 `deny-licenses`를 같이 받지 못한다. `allow-licenses`는 목록에 없는 모든 라이선스를 실패로 세므로 review 목록(GPL, LGPL, MPL 등)과 알 수 없는 라이선스까지 기계가 막게 된다. 정책은 그것을 사람이 정하게 둔다. 확정된 거부인 deny 목록만 diff에 대한 기계 판정이 될 수 있다.
- **deny 목록은 `license-policy.toml`의 `[deny]`에서 실행할 때마다 만든다.** 액션은 정확한 SPDX 식별자만 맞추고 번들된 SPDX 목록에 없는 식별자는 설정 오류로 끝난다. 그래서 `licenses`는 그대로 쓰고(`LicenseRef-*`는 GitHub 의존성 그래프가 내지 않으므로 뺀다), `prefixes`는 워크플로 안의 표(`PREFIX_IDS`)로 식별자로 풀어 쓴다. 정책에 표에 없는 접두사를 더하면 이 단계가 실패하므로 워크플로의 표를 같이 고친다.
- **한계.** `Dependency review`는 PR이 바꾼 것만 본다. 이미 트리에 있는 것과 GitHub가 라이선스를 못 찾은 패키지는 잡지 못하므로 `Policy check`가 필요하다. 이 액션은 GitHub 의존성 그래프를 쓴다. 비공개 저장소에서는 GitHub Advanced Security가 필요하고, 없으면 이 작업이 실패한다(미확인: 이 저장소의 설정). pnpm·uv·Cargo·Go 잠금 파일을 그래프가 읽는지는 PR을 실제로 열어 봐야 안다(미확인). 저장소 안 바이너리·글꼴·이미지는 어느 쪽도 보지 않는다.
- **`Policy check`가 러너에서 도는 조건.** PyPI, npm 레지스트리, Go 모듈 프록시, crates.io에 닿는 공개 네트워크와 `ubuntu-24.04` 이미지에 든 `cargo`면 된다. 인증이 필요한 레지스트리는 쓰지 않는다. 2026-10-21에 캐시 없이 돌려 약 100초가 걸렸고, 위반 169건(deny 3, review 166)과 종료 코드 1이 나왔다. GitHub 러너에서 돌려 본 것은 아니다(미확인).
- 정책 파일을 PR이 바꾸면 그 PR의 검사는 바뀐 정책으로 돈다. 정책 변경은 사람의 검토로 막는다.
- 액션은 전체 커밋 SHA로 고정했다. 다음 버전은 Renovate나 사람이 올린다.

## 집계 방법

요약 표, 위반 목록, 범위 표, 상위 라이선스 표, 허용 목록은 `wiki/_tools/gen_licenses.py`가 만든다. 이 페이지의 `generated:` 구역이 그 결과다. 구역 밖은 손으로 쓴 글이고, 스크립트는 건드리지 않는다.
스크립트는 저장소 루트에서 돌린다. 레지스트리와 `cargo`가 필요하다.

```bash
python3 -I wiki/_tools/gen_licenses.py                              # 구역을 다시 쓴다
python3 -I wiki/_tools/gen_licenses.py --check                      # 정책 위반이 있거나 페이지가 낡았으면 종료 코드 1
python3 -I wiki/_tools/gen_licenses.py --cache-dir /tmp/lic-cache   # 레지스트리 답을 저장소 밖에 보관한다
python3 -I wiki/_tools/gen_licenses.py --list                       # allow가 아닌 항목을 TSV로 낸다. 페이지는 쓰지 않는다
python3 -I wiki/_tools/test_gen_licenses.py                         # 판정 규칙의 테스트. 네트워크가 필요 없다
```

- 스크립트는 `wiki/licenses.md` 말고는 저장소에 아무것도 쓰지 않는다. 임시 파일은 시스템 임시 디렉터리에만 둔다. `--cache-dir`이 저장소 안이면 거부한다.
- 범위 표의 비고 열은 `wiki/_tools/licenses-notes.tsv`에서 온다. 잠금 파일이 늘면 스크립트가 "no notes row" 경고를 낸다. 그 파일에 한 줄을 더한다.
- 실패한 조회가 하나라도 있으면 스크립트는 실패한 패키지 수와 앞쪽 10개를 오류로 내고, `licenses.md`를 쓰지 않은 채 0이 아닌 코드로 끝난다(2026-10-16 실행에서는 실패가 없었다).
- 레지스트리 답은 시간이 지나면 바뀐다. 저장소가 그대로여도 `--check`가 낡았다고 말할 수 있다.
- `--cache-dir`에 든 답은 다시 조회하지 않는다. 레지스트리 쪽 변화를 보려면 캐시 없이 돌리거나 캐시 디렉터리를 비운다. 조회 코드(`fetch_*`)가 바뀌면 스크립트가 그 캐시를 버린다.
- `--check`는 위반마다 한 줄을 표준 출력에 낸다. 여섯 열(판정, 잠금 파일, 이름, 버전, 라이선스, 규칙)를 탭으로 나눈다. `[[path]]` 항목은 잠금 파일 열에 "추적 파일 N개"를 적는다. 위반 수는 표준 오류에 낸다. 정책이 `status = "draft"`이면 위반을 내도 실패하지 않는다.
- `--list`는 `allow`가 아닌 모든 항목(승인된 예외, review 면제 포함)을 `--check`와 같은 열로 낸다.
- 페이지와 `--check`는 한 번의 판정을 함께 쓴다. 그래서 요약 표, 위반 목록, 검사 결과가 어긋나지 않는다.
- 잠금 파일에는 라이선스 필드가 없다(cargo는 `cargo metadata`가 바로 준다). 그래서 이름·버전을 뽑아 레지스트리에 조회한다. `node_modules`나 가상 환경은 설치하지 않는다.

### 분류 규칙

스크립트의 `Policy`가 `license-policy.toml`을 읽어 정한다. 정책 파일이 스크립트가 구현하지 않은 값(`[expression]`의 다른 해석, 모르는 `status`·`scope`, `[[package]]`·`[[path]]`의 모르는 필드, `YYYY-MM-DD`가 아닌 `review_by`)을 적으면 스크립트는 판정하지 않고 끝난다.

1. 찾은 문자열을 SPDX식으로 바꾼다. npm, cargo, go와 pip의 `license_expression`은 그대로 쓴다. pip 분류자는 표(`PIP_CLASSIFIERS`)로 SPDX 식별자로 바꾸고 `AND`로 잇는다. `OSI Approved`, `DFSG approved`는 뺀다. 표에 없는 분류자(`Other/Proprietary License`, `GNU Library or Lesser General Public License (LGPL)` 등)가 하나라도 있으면 SPDX식이 없는 것으로 본다. pip 원문은 `MIT License`, MIT 라이선스 URL, `Apache License 2.0`류, `3-Clause BSD`로 시작하면 그 식별자로 읽고, 아니면 원문을 SPDX식으로 읽어 본다. 다만 원문에 `proprietary`, `Commons Clause`, `non-commercial`이 있으면 시작 부분으로 읽지 않는다(`Apache License 2.0 with Commons Clause`는 `review`다).
2. SPDX식이 아니면 `review`다. `UNKNOWN`, `SEE LICENSE IN ...`, `license_file`만 있는 크레이트, `NO-LICENSE-FILE`, 빈 값이 여기에 든다.
3. 식별자는 대소문자를 가리지 않는다. 끝의 `+`를 먼저 떼고, `[expression.alias]`로 바꾼다. 정확한 목록(`allow`, `deny`, `review`)이 먼저이고, 다음이 `deny` 접두사, 그다음이 `review` 접두사다. 어디에도 없으면 `review`다.
4. SPDX에 없는 맨 식별자(`Proprietary`, `Commons-Clause`)는 `LicenseRef-`를 붙인 이름으로도 정확한 목록과 `deny` 접두사에 맞춰 본다. 그래서 `Commons-Clause`는 `LicenseRef-Commons-Clause`(`deny`)다.
5. `A OR B`는 더 좋은 쪽, `A AND B`는 더 나쁜 쪽이다(`allow` > `review` > `deny`). `/`는 `OR`다. `X WITH 예외`는 `X`의 판정이고, 예외가 3·4로 `deny`이면 `deny`다.
6. 판정 뒤에 `[[package]]`·`[[path]]` 항목과 범위를 적용한다([범위와 승인](#범위와-승인)). `[[package]]`는 생태계와 이름(`*` 글롭)으로 맞추고, 버전을 고정한 항목이 먼저, 그다음 정확한 이름이 먼저다. pip 이름은 양쪽 다 PEP 503 형태(소문자, `-`·`_`·`.`의 연속은 `-` 하나)로 바꿔 맞춘다. 어느 의존성에도 적용되지 않는 `[[package]]` 항목은 경고만 낸다. `[[path]]` 글롭은 `git ls-files` 목록에 맞춘다. `**/`는 디렉터리 여러 개, `*`는 한 디렉터리 안, `{a,b}`는 둘 중 하나다. 맞는 파일이 없는 항목은 경고만 낸다.

<!-- generated:allow:begin -->
Generated from `wiki/_tools/gen_licenses.py`, `wiki/_tools/licenses-notes.tsv` and `license-policy.toml` — Do not edit by hand.

허용 목록(`license-policy.toml`의 `[allow]`): `MIT`, `MIT-0`, `MIT-CMU`, `X11`, `NCSA`, `Apache-2.0`, `BSD-1-Clause`, `BSD-2-Clause`, `BSD-2-Clause-Patent`, `BSD-3-Clause`, `BSD-3-Clause-Clear`, `0BSD`, `ISC`, `Zlib`, `Libpng`, `libpng-2.0`, `BSL-1.0`, `PostgreSQL`, `HPND`, `UPL-1.0`, `W3C`, `Unlicense`, `CC0-1.0`, `Python-2.0`, `PSF-2.0`, `CNRI-Python`, `BlueOak-1.0.0`, `Unicode-3.0`, `Unicode-DFS-2016`, `AFL-2.1`, `AFL-3.0`, `MPL-2.0`, `WTFPL`, `OFL-1.1`, `CC-BY-3.0`, `CC-BY-4.0`, `CDLA-Permissive-2.0`, `bzip2-1.0.6`.
<!-- generated:allow:end -->

### 조회 방식

| 생태계 | 항목을 뽑는 곳 | 라이선스를 얻는 곳 |
| --- | --- | --- |
| pip(`uv.lock`) | 레지스트리 출처 패키지(`source.registry`). git 출처와 워크스페이스 멤버는 뺀다. `uv export`는 `inbox-ranking`과 `sentiment` 그룹이 충돌해(`pyproject.toml:330`의 `conflicts`) `--all-groups`로 실패하므로 쓰지 않는다 | PyPI JSON API(`license_expression`, `License ::` 분류자, `license` 원문 순). 로컬 버전(`torch` 2.9.1+cpu처럼 `+`가 붙은 다른 인덱스의 빌드)은 `+` 앞의 공개 버전으로 조회한다 |
| pip(`requirements.txt`) | `==`로 고정한 줄만 | 위와 같음 |
| npm(`pnpm-lock.yaml` 형식 9.0과 5.4, `package-lock.json`) | pnpm은 `packages:` 절 키, `package-lock.json`은 `packages` 항목. 버전이 숫자로 시작하지 않는 항목(git·tarball 출처)과 링크는 뺀다 | `registry.npmjs.org`의 `license`(없으면 `licenses`) |
| cargo(`Cargo.lock`) | `cargo metadata --locked`가 주는 `source`가 있는 패키지. 임시 디렉터리에서 돌리고 `--manifest-path`로 매니페스트를 가리킨다 | `Cargo.toml`의 `license`. 없으면 `license_file`만 있는 크레이트로 센다 |
| go(`go.mod`) | `require` 줄(직접과 `// indirect` 모두). `go` 명령은 쓰지 않는다 | `proxy.golang.org` 모듈 zip의 최상위 `LICENSE*`·`LICENCE*`·`COPYING*` 본문을 정해진 문구로 판별한다. MPL 본문이 GNU 라이선스를 언급하므로 MPL을 먼저 본다 |

직접/전이는 `pyproject.toml`의 `[project] dependencies`와 `[dependency-groups]`에 이름이 있는지로 갈랐다. 전이 의존을 끌어온 패키지는 `uv.lock`의 각 패키지 `dependencies`를 거꾸로 찾아 적었다. 이 구분은 스크립트가 하지 않는다. 위 "법무 검토가 필요한 항목" 표를 `--list` 출력에서 손으로 옮겨 쓸 때 한 것이다.

`SEE LICENSE IN ...`인 패키지는 레지스트리 `dist.tarball`을 받아 각자 새 빈 디렉터리에 풀고 라이선스 파일만 읽었다. 이것도 손으로 한 일이다.

```bash
n=@anthropic-ai/claude-agent-sdk; v=0.3.280; d=$(mktemp -d)
curl -s -o $d/pkg.tgz "$(curl -s https://registry.npmjs.org/${n/\//%2F}/$v | jq -r .dist.tarball)"
mkdir $d/x && tar -xzf $d/pkg.tgz -C $d/x --no-same-owner && cat $d/x/package/LICENSE*
```

`license_file`만 있는 크레이트는 `~/.cargo/registry/src/index.crates.io-*/<이름>-<버전>/`에서 본문을 읽었다.
`UNKNOWN`·`ERR`·`NO-LICENSE-FILE`로 나온 항목은 `--list` 출력에서 골라 "라이선스를 레지스트리에서 얻지 못한 항목" 표에 손으로 옮겼다.

워크스페이스 크레이트(`source == null`)의 `license` 필드 수([저장소 자체 라이선스](#저장소-자체-라이선스)의 "75개 중 73개" 등)도 스크립트가 세지 않는다. 저장소 루트에서 이렇게 셌다.

```bash
for m in rust cli funnel-udf rust/common/hogvm/node; do
  (cd "$(mktemp -d)" && cargo metadata --manifest-path "$OLDPWD/$m/Cargo.toml" --format-version 1 --locked) |
    jq -r '.packages[] | select(.source==null) | (.license // "UNSET")' | sort | uniq -c
done
```

### `@posthog/brand` 사용 파일 수

저장소 루트에서 돌린다.

```bash
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
