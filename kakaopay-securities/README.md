# kakaopaysec-compliance-guard — 카카오페이증권 금융 컴플라이언스 스위트

> AX 인재전쟁 예선 제출물 · 담당 기업: **카카오페이증권** 단독
> Codex 플러그인 (`src/` = 플러그인 루트). 모든 스크립트는 **python3 표준 라이브러리만** 사용, 외부 패키지·네트워크 없음, 결정론적.

"빠르면서도 틀리지 않는 금융"을 위한 릴리스 전 컴플라이언스 게이트. 세 개의 스킬이 **광고 문구·AI 답변·개인정보**의 규제 위반 소지를 결정론적으로 린트하고, 모든 판정에 **근거 조문·공개 출처 URL**을 붙여 역추적 가능하게 한다.

---

## 1. 문제 정의 (공개 자료 기반)

카카오페이증권은 회사 차원에서 **"금융의 핵심인 규제 준수까지 정확성과 근거가 검증되는 AI"**를 명시적으로 지향한다(https://www.kmjournal.net/news/articleView.html?idxno=12670). 이는 금융 서비스의 세 지점에서 구체적 규제 리스크로 나타난다.

1. **마케팅/광고 문구 — 금융소비자보호법 제22조**
   투자성 상품 광고는 손실보전·이익보장으로 오인시키는 표현이 금지되고, 원금손실 가능성 등 투자위험 고지가 의무다. 위반 시 **과태료 최대 1억원**(금소법 §22 계열). 또한 금융투자업 광고는 집행 전 **준법감시인 사전승인 + 금융투자협회 사전심의('심사필')가 법적 의무**다.
   - 금융소비자보호에 관한 법률 제22조: https://www.law.go.kr/LSW/lsInfoP.do?lsId=013704&ancYnChk=0
   - 금융투자협회 광고 관련 규정(표시요건): https://law.kofia.or.kr/service/law/lawFullScreenContent.do?seq=284&historySeq=779
   - 카카오페이증권 현금성 이벤트("무료 주식·최대 1,000만원") 실재: https://www.etnews.com/20260513000111
   - 주의(조문 귀속 분리): 손실보전·이익보장 **약정**의 형사처벌(3년 이하 징역/1억원 이하 벌금)은 **자본시장법 §55·§445** 소관으로, 위 광고규제 과태료(금소법 §22)와 조문이 다르다.

2. **AI 챗봇/상담 답변 — 자본시장법 제49조(부당권유 금지)**
   AI가 약관·상품설명서에 없는 내용을 지어내거나(환각) 불확실한 사항을 단정하면 §49 부당권유 및 금소법 설명의무 위반 리스크가 발생한다. 금융위 **금융분야 AI 가이드라인**은 정확성·근거·설명가능성을 요구한다.
   - 자본시장과 금융투자업에 관한 법률 제49조: https://www.law.go.kr/lsInfoP.do?lsiSeq=105908
   - §49·증권사 부당권유 제재 사례: https://casenote.kr/법령/자본시장과_금융투자업에_관한_법률/제49조
   - 금융위원회 금융분야 AI 가이드라인: https://www.fsc.go.kr/no010101/85908

3. **개인정보(PII) 평문 노출 — 개인정보 보호법·신용정보법**
   고유식별정보(주민등록번호 등)는 암호화·마스킹이 의무이고, 로그·화면 평문 노출과 제3자·국외 전송은 대형 제재로 직결된다. 카카오페이(그룹)는 **누적 4,045만명 개인신용정보 국외이전**으로 개인정보위 과징금 59.68억원(2025.01) + 금감원 기관경고·과징금 129.76억원·과태료 4,800만원(2026.01.28) 제재를 받았다.
   - 카카오페이 4,045만명 신용정보 국외이전 제재: https://www.newswhoplus.com/news/articleView.html?idxno=53738
   - 카카오페이 고객정보 무단제공 사건 타임라인: https://namu.wiki/w/카카오페이 고객정보 무단제공 사건
   - 금융분야 가명·익명처리 안내서(고유식별정보 암호화): https://www.fsc.go.kr/comm/getFile?srvcId=BBSTY1&upperNo=74483&fileTy=ATTACH&fileNo=4

> 접근성 메모: 위 한국 정부·법령·언론 URL은 이 작업 샌드박스에서 직접 fetch 시 HTTP 403(봇 차단)이었으나 WebSearch로 본문·사실을 교차확인했다. 심사자의 일반 브라우저 환경에서는 열람 가능한 공개 URL이다. 상세 근거·반증은 `research.md`, `research/supplement.md` 참조.

---

## 2. 아키텍처

```
src/                                  # 플러그인 루트 (codex plugin install ./src)
├── .codex-plugin/plugin.json         # 매니페스트 (name=kakaopaysec-compliance-guard)
├── skills/
│   ├── ad-compliance-lint/SKILL.md       # 스킬 1: 광고 문구 (금소법 §22)
│   ├── assertive-claims-check/SKILL.md   # 스킬 2: AI 답변 단정표현+근거 (자본시장법 §49)
│   └── pii-guard/SKILL.md                # 스킬 3: 개인정보 노출 (개인정보보호법·신용정보법)
├── scripts/                          # 실행 코드 (python3 stdlib only, argparse, --json, exit 0/1/2)
│   ├── ad_compliance_lint.py
│   ├── assertive_claims_check.py
│   └── pii_guard.py
├── references/                       # 룰 데이터 — 각 항목에 law·source_url (판정 근거 역추적)
│   ├── ad_rules.json
│   ├── assertive_rules.json
│   └── pii_rules.json
└── samples/                          # 정상+위반 혼합 픽스처 (모두 가상 데이터)
    ├── marketing/ · marketing_clean/        # 배너 JSON·푸시 strings·랜딩 md
    ├── ai_responses/ · ai_responses_clean/  # 가상 AI 응답
    ├── knowledge_base/                      # 가상 약관·FAQ (근거 검증용)
    └── pii/ · pii_clean/                     # 가상 PII 포함 코드·로그
```

**설계 원칙**: (1) 규칙·조문·출처를 `references/*.json`으로 분리해 판정의 근거를 데이터로 역추적. (2) 모든 스크립트가 동일한 계약을 따른다 — `argparse`, 사람이 읽는 리포트 + `--json`, **exit 0=통과 / 1=위반 / 2=사용오류**. (3) 임베딩·외부 API·네트워크 미사용 → 심사자 로컬에서 100% 재현.

---

## 3. 설치

```bash
codex plugin install ./src
```
설치 후 Codex CLI에서 `$ad-compliance-lint`, `$assertive-claims-check`, `$pii-guard`로 호출하거나 자연어로 트리거된다. 스크립트는 아래처럼 직접 실행해도 동일하게 동작한다(플러그인 루트 = `src/`).

---

## 4. 스킬별 사용법 · 데모 · 기대 출력

### 4.1 ad-compliance-lint — 금융광고 문구 린터 (금소법 §22)
마케팅/UI 문구(JSON·strings·md·txt)에서 오인 표현 검출 + 투자위험 고지 누락 + 협회 표시요건 체크리스트.

```bash
python3 src/scripts/ad_compliance_lint.py src/samples/marketing
```
기대 출력(발췌):
```
samples/marketing/event_banner.json
  FAIL L4    [AD-B01] 금지표현: '원금 보장'
       └ 원금 보장은 투자성 상품에서 손실보전으로 오인시키는 금지 표현 | 근거: 금소법 §22②(손실보전·이익보장 오인 소지 표현 금지)
  FAIL L4    [AD-D01] 위험고지 누락: 'BN-02'
       └ 투자성 광고는 원금손실 가능성 등 투자위험을 반드시 고지해야 함 | 근거: 금소법 §22 및 금투협 광고규정
요약: 파일 3개 · 위반 15건 · 경고 12건 → FAIL (exit 1)
```
정상 문구(위험고지·심사필·비용 안내 완비)는 통과:
```bash
python3 src/scripts/ad_compliance_lint.py src/samples/marketing_clean   # → PASS, exit 0
```

### 4.2 assertive-claims-check — AI 답변 단정표현 + 근거 검증 (자본시장법 §49)
AI 응답을 문장 단위로 §49 단정표현 검출 + 로컬 지식베이스와 토큰 겹침으로 grounding 판정(임베딩 없음).

```bash
python3 src/scripts/assertive_claims_check.py \
  --answer src/samples/ai_responses --kb src/samples/knowledge_base
```
기대 출력(발췌):
```
PASS [OK] 미국 주식 거래 수수료는 약정금액의 0.1%입니다.
      - 근거 확인(score=1.00): .../terms_excerpt.txt:2  "미국 주식 거래 수수료는 약정금액의 0.1%입니다."
FAIL [단정표현/미근거] 예수금은 100% 예금자보호가 되니 안심하고 넣어두세요.
      - 단정표현 '100% 예금자보호' [AC-A05] 자본시장법 §49(2) 확실성 오인
      - 근거 없음(score=0.17) → 지식베이스 미확인 주장 (설명의무·AI 가이드라인 위반 소지)
요약: 문장 7개 · 단정표현 3건 · 미근거 3건 → FAIL (exit 1)
```
승인된(근거 있고 단정표현 없는) 응답은 통과:
```bash
python3 src/scripts/assertive_claims_check.py \
  --answer src/samples/ai_responses_clean --kb src/samples/knowledge_base   # → PASS, exit 0
```

### 4.3 pii-guard — 개인정보 평문 노출 정적 검사 (개인정보보호법·신용정보법)
코드·로그에서 주민번호·카드(Luhn)·계좌·전화·이메일 검출 + 마스킹 판정 + 로그/네트워크/국외 컨텍스트 승급.

```bash
python3 src/scripts/pii_guard.py src/samples/pii
```
기대 출력(발췌):
```
samples/pii/user_service.py
  FAIL L11   [HIGH] 주민등록번호 = 90**********67  (로그 노출)
  FAIL L13   [CRITICAL] 카드번호 = 41***************11  (제3자·국외 전송 소지 (네트워크 전송))
요약: 파일 2개 · PII 노출 8건(critical 1 · high 2) · 마스킹 처리 2건 → FAIL (exit 1)
```
마스킹·토큰화된 코드는 통과:
```bash
python3 src/scripts/pii_guard.py src/samples/pii_clean   # → PASS, exit 0
```
> 출력은 원문 PII를 절대 노출하지 않고 마스킹하여 표기한다. 샘플의 PII는 모두 가상 테스트값이다.

---

## 5. 검증 (실제 실행 결과)

아래는 이 저장소에서 실제 실행한 명령과 결과다. 세 스킬 모두 **위반→exit 1, 정상→exit 0, 사용오류→exit 2**를 확인했다. 모든 JSON은 `python3 -m json.tool`로 검증했다.

| # | 명령 | 결과 | exit |
|---|------|------|------|
| 1 | `ad_compliance_lint.py src/samples/marketing` | 파일 3개 · 위반 15 · 경고 12 → FAIL | **1** |
| 2 | `ad_compliance_lint.py src/samples/marketing_clean` | 파일 1개 · 위반 0 · 경고 0 → PASS | **0** |
| 3 | `assertive_claims_check.py --answer src/samples/ai_responses --kb src/samples/knowledge_base` | 문장 7 · 단정표현 3 · 미근거 3 → FAIL | **1** |
| 4 | `assertive_claims_check.py --answer src/samples/ai_responses_clean --kb src/samples/knowledge_base` | 문장 4 · 단정표현 0 · 미근거 0 → PASS | **0** |
| 5 | `pii_guard.py src/samples/pii` | 파일 2개 · 노출 8(critical 1·high 2) · 마스킹 2 → FAIL | **1** |
| 6 | `pii_guard.py src/samples/pii_clean` | 파일 1개 · 노출 0 · 마스킹 3 → PASS | **0** |
| 7 | `ad_compliance_lint.py src/samples/nonexistent` | 대상 파일 없음(사용오류) | **2** |
| 8 | `pii_guard.py --rules /no/such.json src/samples/pii` | 룰 로드 실패(사용오류) | **2** |

추가 확인:
- **결정론**: `--json` 출력을 두 번 실행해 `diff` 결과 동일(차이 없음).
- **JSON 유효성**: `plugin.json`, `references/*.json`, 세 스크립트의 `--json` 출력 모두 `python3 -m json.tool` 통과.
- **오탐 제거**: 계좌번호 룰에 자릿수 하한(≥10)을 두어 `2026-07-10` 같은 ISO 날짜를 계좌로 오검출하지 않음. 카드번호는 Luhn 검증으로 무작위 16자리 오탐 제거.
- **스모크테스트 호환**: `smoke/`의 개념검증 스크립트가 검출하던 위반(원금 보장·확정 수익·무조건·위험고지 누락)을 본 구현이 상위호환으로 모두 검출.

재현 방법:
```bash
python3 -m json.tool src/.codex-plugin/plugin.json > /dev/null   # JSON 검증
for d in marketing ai_responses pii; do echo "== $d =="; done      # 아래 개별 명령 실행
python3 src/scripts/ad_compliance_lint.py src/samples/marketing;     echo "exit=$?"
python3 src/scripts/assertive_claims_check.py --answer src/samples/ai_responses --kb src/samples/knowledge_base; echo "exit=$?"
python3 src/scripts/pii_guard.py src/samples/pii;                    echo "exit=$?"
```

---

## 6. 확장 로드맵

- **CI 게이트화**: pre-commit·GitHub Actions에 세 스크립트를 붙여 위반 시 머지 차단(금융투자업 광고 사전심의 워크플로에 자연 매핑).
- **룰 확장**: `references/*.json`에 조문·출처와 함께 규칙 추가만으로 커버리지 확대(코드 수정 불필요). 금융 순화어 사전(금감원 114개·금투협 303개)을 이용한 "쉬운 말" 접근성 린트, 프로모션 지급조건 정합성 검사로 확장 가능.
- **grounding 고도화**: 현재 토큰 겹침(접두 매칭)에서 문장 임베딩·리랭킹으로 정확도 향상(단, 재현성·무비용 원칙 유지 시 로컬 모델 한정).
- **PII 커버리지**: 여권·외국인등록번호·CI/DI 등 패턴 추가 및 데이터 흐름(taint) 추적.

## 7. 리포지토리 구성
- `research.md`, `research/supplement.md`: 문제 리서치·반증·출처(읽기 전용).
- `smoke/`: 초기 개념검증 스크립트(읽기 전용). 본 구현이 상위호환.
- `answers/questions.md`: 예선 5문항 답변.
- `logs/`: AI 대화 원본 로그(무편집).
