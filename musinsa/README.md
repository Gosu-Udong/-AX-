# musinsa-listing-guard

무신사 상품 리스팅의 **법정 표시 위반**을 배포 전에 결정론적으로 걸러내는 Codex 플러그인(컴플라이언스 스위트).
섬유 혼용률·충전재 표시, 전자상거래 상품정보제공고시 필수항목, 화장품 표시·광고 3개 축을
**python3 표준 라이브러리만**으로 판정한다. 유료 API·LLM 판단·네트워크 없이 심사자가 완전히 재현할 수 있다.

> AX 인재전쟁 예선 제출물(무신사). 모든 주장·수치에 공개 출처 URL을 병기했다.

---

## 1. 문제 정의 (공개 자료 기반)

무신사는 입점 브랜드·판매대행사가 올린 상품 정보의 **표시 오류**로 반복적인 리콜·제재·PR 리스크를 겪고 있다.
세 가지가 대표적이며, 각각을 스킬 1개로 커버한다.

### (A) 섬유 혼용률·충전재 오기재
- 무신사는 2024-12-16 다운·캐시미어 **7,968개**를 전수조사(약 100일)해 **8.5%가 오기재**임을 적발하고,
  위반 브랜드에 **최소 5일~최대 35일 판매중지** 제재를 내렸다.
  - 무신사 뉴스룸 https://newsroom.musinsa.com/newsroom-menu/2025-0325
  - SBS Biz https://biz.sbs.co.kr/article/20000224713 · 아시아경제 https://cm.asiae.co.kr/article/2025032516490862001
- 2025-12에는 노스페이스 패딩 **13스타일·28SKU**의 충전재('거위털' 등)가 실제와 다르게 표기된 사건이 재발했고,
  조치는 판매중지가 아니라 **환불 안내 + 판매대행사 벌점 부과**였다(전수조사 사건의 판매중지와 구분).
  - 무신사 뉴스룸 https://newsroom.musinsa.com/newsroom-menu/2025-1202-2
- 근거 기준: 섬유제품의 품질표시에 관한 규정(부위별 혼용률 합계·혼용순서) https://www.law.go.kr/lsInfoP.do?lsiSeq=42610 ,
  '기타섬유'는 전기생활용품안전법 안전기준에 따라 **15% 이내 합계 표시**로 개선.

### (B) 전자상거래 상품정보제공고시 필수항목 누락
- 「전자상거래 등에서의 상품 등의 정보제공에 관한 고시」는 품목별 필수 표기항목(의류: 소재·색상·치수·제조자·제조국·
  세탁방법·제조연월·품질보증기준·A/S연락처 등)을 요구한다. https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000065929
- 무신사는 2024-12-16 입점 브랜드에 "상품정보 표시의무 등 위반 시 **판매중지·주문취소·리콜·퇴점**"을 공지했다.
  https://newsroom.musinsa.com/newsroom-menu/2024-1216-musinsa
- 현장 이슈: 필수항목 누락·공란, '상세페이지 참조'로 필수값을 갈음하는 회피표기.

### (C) 화장품(뷰티) 부당 표시·광고
- 무신사는 2026년 뷰티를 핵심 전략으로 확장 중이며 신진·인디 브랜드 상세페이지가 급증한다.
- 식약처 온라인 점검에서 화장품 부당광고 **83건**이 적발됐고 그중 **의약품 오인 광고가 64%**였다.
  - 뉴시스 https://www.newsis.com/view/NISX20250806_0003280269 · 한국의약통신 https://www.kpanews.co.kr/article/show.asp?idx=261845
- 근거: 화장품법 제13조(부당한 표시·광고 금지) https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=205691 ,
  화장품 표시·광고 실증에 관한 규정 https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=1301&ccfNo=4&cciNo=2&cnpClsNo=2

---

## 2. 아키텍처

```
src/                                  # 플러그인 루트
├── .codex-plugin/plugin.json         # 매니페스트 (name: musinsa-listing-guard)
├── skills/
│   ├── verify-textile-labels/SKILL.md   # (A) 섬유 혼용률·충전재
│   ├── check-info-notice/SKILL.md       # (B) 상품정보제공고시 필수항목
│   └── lint-beauty-claims/SKILL.md      # (C) 화장품 표시·광고
├── scripts/                          # 결정론적 실행 코드(표준 라이브러리만)
│   ├── verify_textile_labels.py
│   ├── check_info_notice.py
│   └── lint_beauty_claims.py
├── references/                       # 룰 데이터(조문·출처 URL 필드 포함)
│   ├── textile_rules.json
│   ├── info_notice_schema.json
│   └── beauty_banned_terms.json
└── samples/                          # 정상+위반 혼합 (가상 브랜드)
    ├── products.json · products_pass.json · lab_results.csv
    ├── listings.json · listings_pass.json
    └── beauty_detail.md · beauty_clean.md
```

설계 원칙: **판정 근거 역추적 가능**(모든 룰이 references JSON의 조문/URL을 참조), **CI 친화**(위반 시 exit 1),
**재현성**(고정 룰 + 샘플 동봉, LLM·네트워크 없음).

---

## 3. 설치

```bash
codex plugin install ./src
```

설치 후 Codex CLI에서 `$verify-textile-labels`, `$check-info-notice`, `$lint-beauty-claims`로 명시 호출하거나
자연어(예: "이 카탈로그 혼용률 검수해줘")로 트리거된다. 스크립트는 아래처럼 단독 실행도 가능하다(심사자 재현용).

---

## 4. 스킬별 사용법·데모·기대 출력

모든 명령은 `src/`에서 실행. 공통 옵션: `--json`(JSON 리포트), exit code `0`=통과 / `1`=위반 / `2`=사용 오류.

### (A) verify-textile-labels — 섬유 혼용률·충전재

```bash
python3 scripts/verify_textile_labels.py samples/products.json --lab samples/lab_results.csv
```
검사: ①부위별 혼용률 합계=100% ②'기타섬유' 합계≤15% ③충전재 표시값 vs 시험성적서(5%p) ④필수 부위 누락 (+혼용순서 경고).
기대 출력(발췌):
```
FAIL  MU-1002  [노르딕폴라] 울 블렌드 코트 (합계 오류)
      - [혼용률 합계:MIX_SUM_100] '겉감' 합계 95% (목표 100%) -> 교정: 합계가 100%가 되도록 성분비 조정
FAIL  MU-1003  [노르딕폴라] 구스다운 롱패딩 (충전재 불일치)
      - [충전재 불일치:FILLING_LAB_MATCH] '충전재/솜털' 표시 80% vs 시험 68% (오차 12%p > 5%p) -> 교정: 표시값을 시험값 68%로 정정
결과: 상품 7개 중 위반 4개   (exit 1)
```

### (B) check-info-notice — 상품정보제공고시 필수항목

```bash
python3 scripts/check_info_notice.py samples/listings.json
```
검사: 필수항목 누락·공란·'상세페이지 참조' 회피표기(치수 등 일부 항목은 상세참조 허용). 기대 출력(발췌):
```
FAIL  MU-2002  [의류]  [노르딕폴라] 패딩 (필수항목 누락)
      - [누락] '제조국'(제조국) 항목 자체가 없음
FAIL  MU-2003  [의류]  [그레이스톤] 자켓 (상세참조 회피)
      - [상세참조 회피] '제품 소재(섬유의 조성 또는 함류율)'(제품소재) = '상세페이지 참조' -> 실제 값 표기 필요
결과: 리스팅 4개 중 위반 2개   (exit 1)
```

### (C) lint-beauty-claims — 화장품 표시·광고

```bash
python3 scripts/lint_beauty_claims.py samples/beauty_detail.md
```
검사: 의약품 오인·기능성 오인·실증 필요·최상급 표현을 라인 단위로 스캔 + 조문 매핑. 기대 출력(발췌):
```
FAIL  beauty_detail.md  (위반 후보 17건)
      - L3 [의약품 오인 표현] '여드름 치료'  근거: 화장품법 제13조제1항제1호...
        교정: 질병의 예방·치료·완화를 암시하는 표현은 화장품에 사용할 수 없습니다...
결과: 대상 1건 중 위반 1건 (표현 17개)   (exit 1)
```

정상 샘플(`products_pass.json`, `listings_pass.json`, `beauty_clean.md`)로 실행하면 위반 0건 · exit 0을 확인할 수 있다.

---

## 5. 검증 (실제 실행 결과)

`python3 3.11.15`, 표준 라이브러리만으로 아래를 실행해 확인했다.

### 5-1. JSON 유효성 (`python3 -m json.tool`)
```
OK  .codex-plugin/plugin.json
OK  references/beauty_banned_terms.json
OK  references/info_notice_schema.json
OK  references/textile_rules.json
OK  samples/listings.json · listings_pass.json · products.json · products_pass.json
```
`--json` 출력도 세 스크립트 모두 `json.tool` 파이프 통과.

### 5-2. 스크립트 실행 (명령 · exit code)
| 스킬 | 명령 | 결과 | exit |
|---|---|---|---|
| textile | `verify_textile_labels.py samples/products.json --lab samples/lab_results.csv` | 7개 중 위반 4개 | **1** |
| textile | `verify_textile_labels.py samples/products_pass.json --lab samples/lab_results.csv` | 위반 0개 | **0** |
| info | `check_info_notice.py samples/listings.json` | 4개 중 위반 2개 | **1** |
| info | `check_info_notice.py samples/listings_pass.json` | 위반 0개 | **0** |
| beauty | `lint_beauty_claims.py samples/beauty_detail.md` | 위반 후보 17건 | **1** |
| beauty | `lint_beauty_claims.py samples/beauty_clean.md` | 위반 0건 | **0** |
| 오류 | `verify_textile_labels.py samples/does_not_exist.json` | 사용오류 메시지 | **2** |

→ 위반은 exit 1, 정상은 exit 0, 사용오류는 exit 2로 **CI 게이트에 그대로 연결 가능**함을 확인했다.

---

## 6. 확장 로드맵

- **룰 확대**: 카테고리(신발·가방·화장품)별 정보고시 필수항목·섬유 부위 스키마 추가.
- **가격 오등록 가드**: 2026-02 가격 오등록 강제환불 사건 대응(자릿수/할인율 임계치) 스킬 추가.
- **KC 안전인증 표시 검증**: 인증번호 형식·필수표기 검증(전기생활용품안전법 5개 제재영역 중 하나).
- **실측 사이즈 정합성**: 사이즈표 단조성·이상치 검증(반품 1순위 사유 대응).
- **CI 통합 예시**: pre-commit / GitHub Actions에서 exit code 기반 배포 차단 워크플로 문서화.

## 로그

`logs/` — AI와의 대화 원본 로그(무편집). 리서치 근거는 `research.md`, `research/supplement.md` 참조.
