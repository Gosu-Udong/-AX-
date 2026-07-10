# AX 인재전쟁 — 예선 과제 (해커톤 제출 모노레포)

프라이머 × 조코딩AX파트너스 주최 **AX 인재전쟁** 예선 과제 제출물 개발 저장소.

- 과제 페이지: https://hack.primer.kr/rounds/10
- 마감: **2026-07-10 23:59:59 (KST)**
- 과제: 선택한 기업(또는 그 산업·고객)이 겪는 실제 문제를 **공개 자료로 입증**하고,
  이를 해결하는 **Codex 플러그인**을 개발해 제출

## 대상 기업 (3개사 각각 별도 제출)

| 디렉토리 | 기업 | 문제 방향 (공개 인터뷰 기반) |
|---|---|---|
| `musinsa/` | 무신사 | 패션·뷰티를 데이터와 AI로 확장 |
| `kakaopay-securities/` | 카카오페이증권 | 빠르면서도 틀리지 않는 금융 — 규제 준수·정확성·근거 검증 |
| `myrealtrip/` | 마이리얼트립 | 진짜 여행자의 문제 해결 |

## 저장소 구조

각 기업 디렉토리는 제출 규격(`submission.zip`)과 동일한 구조를 가진다:

```
<기업>/
├── src/                        # 플러그인 루트
│   ├── .codex-plugin/
│   │   └── plugin.json         # 필수 매니페스트
│   ├── skills/<이름>/SKILL.md  # 스킬 (핵심 실행 요소)
│   └── ...                     # 그 밖의 실행 코드·설정
├── README.md                   # 플러그인 소개·실행 방법
├── logs/                       # AI 대화 원본 로그 (무편집)
└── answers/questions.md        # 예선 5문항 답변 (각 800자, 사이트 입력용)
```

공통 자료:

- `docs/hackathon-rules.md` — 과제 본문·제출 규칙 원문 정리
- `docs/codex-plugin-spec.md` — Codex 플러그인/스킬 공식 스펙 노트
- `docs/company-briefs.md` — 기업별 공개 자료 브리프
- `scripts/package.sh` — 기업별 `submission.zip` 빌드 스크립트

## 작업 방식 (오케스트레이션)

- 메인 세션(Fable)이 설계 총감독·오케스트레이션을 담당
- 기업별 리서치·개발은 **기업당 1개의 Opus 4.8 서브에이전트**로 분리해
  컨텍스트 오염 방지
- 모든 근거는 AI가 검증 가능한 **공개 자료**만 사용 (내부 정보·출처 없는 숫자 금지)
- AI와의 대화 로그는 편집 없이 원본 그대로 `logs/`에 포함 (편집·발췌·삭제 시 실격)

## 패키징

```bash
./scripts/package.sh musinsa            # → dist/musinsa-submission.zip
./scripts/package.sh kakaopay-securities
./scripts/package.sh myrealtrip
```
