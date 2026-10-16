# buzzhog 위키

확인 기준 커밋: 70371e9eb38

buzzhog는 PostHog 포크다.
이 위키는 세 가지를 위해 쓴다.

- 코드베이스를 이해한다.
- 제품화 가능성을 판단한다(라이선스, 외부 호출, 브랜딩).
- 운영한다.

## 읽는 순서

1. [시스템 구성도](architecture.md): 어떤 서비스가 있고 어떻게 이어지는가
2. [데이터 흐름](data-flow.md): 이벤트 하나가 저장되기까지, Kafka 토픽과 테이블
3. [용어집](glossary.md): distinct_id, team, HogQL 같은 용어
4. [모듈 지도](modules.md)
5. [라이선스](licenses.md), [외부 호출](external-calls.md), [브랜딩](branding.md)
6. [업스트림 동기화](upstream.md)
7. [운영 런북](runbook.md), [설정](configuration.md), [테스트](testing.md)
8. [결정 기록](adr/README.md)

## 전체 페이지

| 페이지 | 내용 |
| --- | --- |
| [architecture.md](architecture.md) | 시스템 구성도 |
| [data-flow.md](data-flow.md) | 수집→저장 경로, Kafka 토픽, 테이블 |
| [glossary.md](glossary.md) | 용어집 |
| [modules.md](modules.md) | 모듈 지도 |
| [licenses.md](licenses.md) | 라이선스 |
| [external-calls.md](external-calls.md) | 외부 호출 |
| [branding.md](branding.md) | 브랜딩 |
| [upstream.md](upstream.md) | 업스트림 동기화 |
| [runbook.md](runbook.md) | 운영 런북 |
| [configuration.md](configuration.md) | 설정 |
| [testing.md](testing.md) | 테스트 |
| [adr/README.md](adr/README.md) | 결정 기록 목차 |
| [adr/0001-remove-non-foss.md](adr/0001-remove-non-foss.md) | 비 FOSS 코드 제거 결정 |

아직 작성되지 않은 페이지도 링크해 두었다.
다른 묶음이 작성하면 링크가 살아난다.

## 원문 문서

- [monorepo 배치](../docs/internal/monorepo-layout.md)
- [products README](../products/README.md)
- [products 아키텍처](../products/architecture.md)
- 루트 `AGENTS.md`

## 쓰는 규칙

- 코드에서 확인한 사실만 적고, 확인하지 못한 것은 "미확인"으로 표시한다.
- 고객 데이터, 비밀값, 내부 시스템 정보는 쓰지 않는다. 이 저장소는 공개 포크다.

Decided in: buzzhog-6y7m
