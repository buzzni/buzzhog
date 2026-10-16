# 의존성 라이선스

확인 기준 커밋: 70371e9eb38

법무 검토용 요약이다. 집계 명령은 끝의 [집계 방법](#집계-방법)에 그대로 적었다.
브랜딩·상표 자산은 [branding.md](branding.md), 외부로 나가는 호출은 [external-calls.md](external-calls.md)를 본다.

## 저장소 자체 라이선스

| 위치 | 라이선스 | 근거 |
| --- | --- | --- |
| 루트 | MIT, `Copyright (c) 2020-2026 PostHog Inc.` | `LICENSE` |
| `rust/` | MIT, `Copyright (c) 2023 PostHog` | `rust/LICENSE` |
| `packages/quill`, `packages/owners-yaml`, `products/desktop`, `tools/hogli` | MIT, `Copyright (c) 2026 PostHog Inc.` | 각 디렉터리의 `LICENSE` |
| `.github/actions/paths-filter`, `.depot/actions/paths-filter` | 외부 액션 사본. 라이선스 종류 미확인 | `.github/actions/paths-filter/LICENSE` |
| `products/desktop/packages/electron-trpc/src/vendor/unpromise` | 벤더링된 코드. 종류 미확인 | `products/desktop/packages/electron-trpc/src/vendor/unpromise/LICENSE` |

- 루트 `LICENSE`는 순수 MIT 하나뿐이다. `ee/` 디렉터리는 이 포크에 없다(`ls ee` 실패). 비-FOSS 부분을 제거한 결과로 보이며 경위는 [adr/0001-remove-non-foss.md](adr/0001-remove-non-foss.md)를 본다.
- 루트 `package.json`의 `license` 필드는 `MIT`(`package.json:9`). 이 저장소의 Cargo 매니페스트 3개가 `license = "MIT"`를 선언한다.
- 워크스페이스 Rust 크레이트 75개 중 73개는 `license` 필드가 없다(`cargo metadata`의 `source == null` 패키지). 루트 MIT가 적용된다고 보지만, 크레이트별 선언은 없다.

## 집계 요약

| 생태계 | 잠금 파일 | 조회 항목 수 | 허용형(MIT, Apache, BSD, ISC 등) | 약한 카피레프트(MPL, EPL, CDDL) | 강한 또는 라이브러리 카피레프트(GPL, LGPL) |
| --- | --- | --- | --- | --- | --- |
| pip | `uv.lock` | 614(레지스트리 출처) | 약 595 | 약 6 | 약 13 |
| npm | `pnpm-lock.yaml` | 3984 | 약 3938 | 약 30 | 약 16 |
| cargo | `rust/Cargo.lock` | 1200(레지스트리·git 출처) | 약 1189 | 약 10 | 약 1 |

개수는 라이선스 문자열에 `GPL`, `LGPL`, `GNU`, `MPL`, `Mozilla`, `EPL`, `CDDL`이 들어 있는지로 나눈 근사치다. `A OR B`처럼 선택 가능한 표기도 들어 있는 쪽으로 센다. 정확한 판정은 아래 목록을 쓴다.

가장 많은 라이선스(상위):

| 생태계 | 상위 |
| --- | --- |
| pip | `MIT License` 163, `Apache Software License` 112, `BSD License` 78, `MIT`(SPDX) 57, `Apache-2.0` 42 |
| npm | `MIT` 3071, `Apache-2.0` 429, `ISC` 172, `BSD-3-Clause` 86, `MIT-0` 56 |
| cargo | `MIT OR Apache-2.0` 427, `MIT` 287, `Apache-2.0` 143, `Apache-2.0 OR MIT` 86, `MIT/Apache-2.0` 83 |

## 법무 검토가 필요한 항목

### 소스 공개형이지만 오픈소스가 아닌 항목

| 패키지 | 생태계 | 라이선스 | 쓰이는 곳 | 근거 |
| --- | --- | --- | --- | --- |
| `@posthog/brand` 0.12.3 | npm | PolyForm Strict License 1.0.0. 상업적 사용, 자기 프로젝트에서의 사용, 배포, 파생물 모두 허용되지 않는다고 패키지 `LICENSE`가 적는다. 헤지호그 일러스트는 PostHog 상표·브랜드 자산이라고 명시 | `frontend/package.json`과 `products/*/package.json` 다수가 `"@posthog/brand": "catalog:"`로 의존. 이 패키지를 가져오는 소스 파일은 169개 | `frontend/package.json:77`, 패키지 `LICENSE`(`npm pack @posthog/brand@0.12.3`로 확인) |
| `gsap` 3.14.2 | npm | 레지스트리 값이 `Standard 'no charge' license: https://gsap.com/standard-license`. 오픈소스 라이선스가 아님 | `@posthog/hedgehog-mode@0.0.63`의 전이 의존 | `pnpm-lock.yaml`의 `@posthog/hedgehog-mode@0.0.63` 항목 |
| `@posthog/hedgehog-mode` 0.0.63 | npm | MIT 선언. 그러나 위 `gsap`을 끌어온다 | 헤지호그 UI | `pnpm-lock.yaml` |

`@posthog/brand`의 라이선스 파일 전체는 [branding.md](branding.md)의 같은 이름 절에서도 다룬다.
이 패키지가 다른 npm 패키지처럼 허용형이 아니라는 점이 이 목록의 핵심이다.

### 카피레프트 (GPL, LGPL)

| 패키지 | 생태계 | 라이선스 | 비고 |
| --- | --- | --- | --- |
| `ffmpeg-static` 5.3.0 | npm | `GPL-3.0-or-later` | `puppeteer-capture@1.45.0`의 전이 의존(`pnpm-lock.yaml`). 어느 워크스페이스가 `puppeteer-capture`를 쓰는지 미확인 |
| `@img/sharp-libvips-*` 1.2.4 (10개: darwin, linux, linuxmusl 변종) | npm | `LGPL-3.0-or-later` | `sharp`의 플랫폼별 선택 바이너리 |
| `@img/sharp-win32-arm64`, `-ia32`, `-x64`, `@img/sharp-wasm32` 0.34.5 | npm | `Apache-2.0 AND LGPL-3.0-or-later`(wasm32는 `AND MIT` 추가) | 같음 |
| `node-forge` 1.4.0 | npm | `(BSD-3-Clause OR GPL-2.0)` | BSD 쪽을 고를 수 있다 |
| `psycopg` 3.2.10, `psycopg-binary` 3.2.10 | pip | LGPLv3 | PostgreSQL 드라이버 |
| `psycopg2-binary` 2.9.11 | pip | `LGPL with exceptions` | 같음 |
| `paramiko` 3.5.1 | pip | LGPL | |
| `chardet` 5.2.0 | pip | LGPLv2+ | |
| `clickhouse-pool` 0.5.3 | pip | LGPL-3.0-or-later | |
| `jwcrypto` 1.5.7 | pip | LGPL-3.0-or-later | |
| `pymssql` 2.3.8 | pip | LGPL-2.1-or-later | |
| `python-stdnum` 2.2 | pip | LGPLv2+ | |
| `suds-community` 1.2.0 | pip | LGPL | |
| `browser-cookie3` 0.20.1 | pip | `lgpl`(PyPI 원문 소문자) | |
| `text-unidecode` 1.3 | pip | `Artistic License`, GPL, GPLv2+ 분류자가 함께 붙음 | 선택 가능한지 미확인 |
| `tld` 0.13.2 | pip | `MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later` | 선택 가능 |
| `r-efi` 5.3.0 | cargo | `MIT OR Apache-2.0 OR LGPL-2.1-or-later` | 허용형을 고를 수 있다 |

### 약한 카피레프트 (MPL, EPL, CDDL)

| 패키지 | 생태계 | 라이선스 |
| --- | --- | --- |
| `certifi` 2026.1.4, `hypothesis` 6.151.9, `pathspec` 1.0.4, `pytest-rerunfailures` 16.6, `tqdm` 4.67.1(`MPL-2.0 AND MIT`), `orjson` 3.11.9(`MPL-2.0 AND (Apache-2.0 OR MIT)`) | pip | MPL-2.0 |
| `axe-core` 4.5.1, `ip6addr` 0.2.5, `lightningcss-*` 1.31.1·1.32.0(플랫폼별 22개 안팎) | npm | MPL-2.0 |
| `dompurify` 3.2.7, 3.4.0, 3.4.13 | npm | `(MPL-2.0 OR Apache-2.0)` |
| `elkjs` 0.10.0 | npm | EPL-2.0. `frontend/package.json`과 `products/{data_modeling,engineering_analytics,product_analytics}/package.json`이 직접 의존 |
| `brownstone` 3.0.0, `colored` 3.1.1, `fernet` 0.2.2, `indent_write` 2.2.0, `nom-supreme` 0.8.0, `option-ext` 0.2.0, `webpki-roots` 0.25.4 | cargo | MPL-2.0 |
| `smartstring` 1.0.1 | cargo | `MPL-2.0+` |
| `inferno` 0.11.21, 0.12.4 | cargo | CDDL-1.0 |

### 독점 또는 비OSI 라이선스

| 패키지 | 생태계 | 라이선스 | 비고 |
| --- | --- | --- | --- |
| `nvidia-*-cu12` 계열 14개(`nvidia-cublas-cu12`, `-cuda-cupti-`, `-cuda-nvrtc-`, `-cuda-runtime-`, `-cudnn-`, `-cufft-`, `-cufile-`, `-curand-`, `-cusolver-`, `-cusparse-`, `-cusparselt-`, `-nccl-`, `-nvjitlink-`, `-nvshmem-`, `-nvtx-`) | pip | PyPI 분류자 `Other/Proprietary License`. 원문은 `NVIDIA Proprietary Software` 등. `nccl`, `nvshmem`, `nvtx`는 원문이 BSD-3-Clause·Apache 2.0으로 달라 미확인 | `torch`의 CUDA 변종 의존. `pyproject.toml`의 주석에 따르면 `torch`는 CPU wheel 인덱스에서 오고 `inbox-ranking` 그룹에 속한다 |
| `tbb` 2022.3.1, `tcmlib` 1.4.1 | pip | `Intel Simplified Software License` | |
| `linkedin-api-client` 0.3.0 | pip | PyPI 분류자 `Other/Proprietary License`, 원문 `Proprietary` | 광고 연동 소스용으로 보이나 미확인 |
| `ring` 0.16.20 | cargo | `license_file`이 `LICENSE`(ISC·OpenSSL 계열 혼합으로 알려졌으나 미확인) | |
| `libbz2-rs-sys` 0.2.2 | cargo | `bzip2-1.0.6` | 허용형 |

### 허용형이지만 표기가 특이한 항목

| 패키지 | 라이선스 표기 | 비고 |
| --- | --- | --- |
| `caniuse-lite` 1.0.30001690, 1.0.30001777 | `CC-BY-4.0` | 출처 표시 필요 |
| `spdx-exceptions` 2.3.0 | `CC-BY-3.0` | 출처 표시 필요 |
| `@fontsource-variable/inter` 5.2.8 | `OFL-1.1` | 글꼴 |
| `argparse` 2.0.1 | `Python-2.0` | |
| `webpki-root-certs` 1.0.8, `webpki-roots` 1.0.6 | `CDLA-Permissive-2.0` | cargo |
| `temporalio-client`, `-common`, `-common-wasm`, `-protos` 0.5.0 | `license_file`이 `LICENSE.txt` | cargo. 본문 미확인 |

### 라이선스를 레지스트리에서 얻지 못한 항목 (미확인)

| 생태계 | 패키지 |
| --- | --- |
| npm | `@elevenlabs/types` 0.13.0, `@mapbox/jsonlint-lines-primitives` 2.0.2, `@segment/fql-ts` 1.10.1, `heatmap.js` 2.0.5, `khroma` 2.1.0, `union` 0.5.0, `unionfs` 4.6.0 |
| npm (git·tarball 출처, 집계에서 제외) | `uWebSockets.js`: `nodejs/package.json:149`가 GitHub tarball URL로 고정. 레지스트리 조회 대상이 아니라 미확인 |
| pip (PyPI 메타데이터 비어 있음) | `arro3-core` 0.6.5, `autoevals` 0.2.0, `braintrust` 0.2.4, `braintrust-core` 0.0.59, `braintrust-langchain` 0.0.4, `cramjam` 2.12.1, `docker-image-py` 0.1.13, `google-crc32c` 1.8.0, `mistralai` 1.6.0, `mypy-extensions` 1.1.0, `playwright` 1.60.0, `polyleven` 0.11.0 |
| pip (git 출처, 집계에서 제외) | `infi-clickhouse-orm`, `pytest-split`(`pyproject.toml:344`, `pyproject.toml:349`의 `[tool.uv.sources]`) |

pip 항목 중 `license_expression`과 `License ::` 분류자는 비었지만 `license` 원문에만 값이 있는 패키지가 있다(예: `aiohttp`, `celery`, `torch`). 이들은 원문 문자열을 근거로 허용형으로 셌다.

## 집계 방법

세 생태계 모두 잠금 파일에는 라이선스 필드가 없다.
`pnpm-lock.yaml`과 `uv.lock`은 이름·버전만 담으므로, 이름·버전 목록을 뽑아 레지스트리(PyPI, npm)에 조회했다.
Cargo는 `cargo metadata`가 `license` 필드를 바로 준다.
조회는 2026-10-16에 한 번 실행했고, 결과는 그 시점 레지스트리 값이다.
`node_modules`나 가상 환경은 설치하지 않았다.

### Rust (`rust/Cargo.lock`)

`rust/` 안에서 실행한다.
저장소의 Cargo 설정이 오프라인이라 `net.offline=false`를 덮어쓴다.

```bash
cd rust
cargo --config net.offline=false metadata --format-version 1 --locked > cm.json
jq -r '.packages[] | select(.source!=null) | [.name,.version,(.license // .license_file // "UNKNOWN")] | @tsv' cm.json > cargo.tsv
# 워크스페이스 자체 크레이트(source == null)의 license 필드
jq -r '.packages[]|select(.source==null)|[.name,(.license//"UNSET")]|@tsv' cm.json | cut -f2 | sort | uniq -c
# 라이선스별 개수
cut -f3 cargo.tsv | sort | uniq -c | sort -rn
```

### Python (`uv.lock`)

`uv export`는 `inbox-ranking`과 `sentiment` 그룹이 충돌해 `--all-groups`로 실패하므로 쓰지 않았다.
`uv.lock`을 직접 읽어 레지스트리 출처 패키지를 PyPI JSON API에 조회한다.
`info.license_expression`, `License ::` 분류자, `info.license`를 순서대로 적는다.
git 출처 패키지(`infi-clickhouse-orm`, `pytest-split`)와 워크스페이스 멤버는 `source.registry`가 없어 빠진다.

```python
import tomllib, json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
lock = tomllib.load(open(sys.argv[1],'rb'))
pk = [(p['name'], p['version']) for p in lock['package'] if p.get('source',{}).get('registry')]
def get(nv):
    n,v = nv
    try:
        d = json.load(urllib.request.urlopen(f'https://pypi.org/pypi/{n}/{v}/json', timeout=30))['info']
        cl = [c.split(' :: ')[-1] for c in d.get('classifiers',[]) if c.startswith('License ::')]
        lic = d.get('license_expression') or ''
        raw = (d.get('license') or '').strip().replace('\n',' ')[:60]
        return (n,v,lic,';'.join(cl),raw)
    except Exception as e:
        return (n,v,'','','ERR '+str(e)[:40])
with ThreadPoolExecutor(16) as ex:
    for r in ex.map(get, pk): print('\t'.join(r))
```

```bash
python3 pylic.py uv.lock > py.tsv
```

`torch 2.9.1+cpu`는 PyPI에 없는 로컬 버전이라 404가 났다. `torch 2.9.1`의 값(BSD-3-Clause)을 따른다.

### npm (`pnpm-lock.yaml`)

`packages:` 절의 키(`이름@버전`)를 뽑아 `registry.npmjs.org/<이름>/<버전>`의 `license` 필드를 조회한다.

```python
import re
t=open('pnpm-lock.yaml').read()
sec=t.split('\npackages:\n',1)[1].split('\nsnapshots:\n',1)[0]
keys=re.findall(r"^  '?((?:@[^/@']+/)?[^@'\s]+)@([^':\s]+)'?:\s*$",sec,re.M)
open('npmkeys.tsv','w').write('\n'.join('%s\t%s'%k for k in sorted(set(keys))))
```

```python
import json, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
pk=[l.split('\t') for l in open(sys.argv[1]).read().split('\n') if l]
def get(nv):
    n,v=nv
    for _ in range(3):
        try:
            d=json.load(urllib.request.urlopen('https://registry.npmjs.org/%s/%s'%(n.replace('/','%2F'),v),timeout=30))
            l=d.get('license') or d.get('licenses')
            if isinstance(l,dict): l=l.get('type')
            if isinstance(l,list): l=' OR '.join(x.get('type','?') if isinstance(x,dict) else str(x) for x in l)
            return (n,v,str(l) if l else 'UNKNOWN')
        except Exception as e: err=str(e)[:40]
    return (n,v,'ERR '+err)
with ThreadPoolExecutor(32) as ex:
    for r in ex.map(get,pk): print('\t'.join(r))
```

```bash
python3 npmlic.py npmkeys.tsv > npm.tsv
cut -f3 npm.tsv | sort | uniq -c | sort -rn
grep -P 'GPL|UNKNOWN|SEE LICENSE|EPL|CC-BY|OFL|MPL' npm.tsv
```

### 한계

- 잠금 파일 전체를 센다. 개발 도구, 테스트 전용, 선택적 플랫폼 바이너리(`@img/sharp-*`, `lightningcss-*`, `nvidia-*`)도 포함한다. 배포 산출물에 실제로 들어가는지는 미확인.
- 레지스트리가 돌려준 문자열을 그대로 썼다. 패키지 소스의 `LICENSE` 파일과 대조하지 않았다.
- 한 패키지가 `A OR B`로 표기되면 선택할 수 있는 쪽을 고를 수 있다고 본다. 법적 해석은 법무 검토 몫이다.
- 직접 의존과 전이 의존을 구분하지 않았다.

Decided in: buzzhog-gimc
