# 무신사(Musinsa) 리서치 — 문제 후보 3개 + 추천

> 이 문서는 플랜모드 제약 때문에 여기에 먼저 작성함.
> 플랜 승인 후 그대로 `/home/user/-AX-/musinsa/research.md` 로 저장할 내용.

## 0. 환경 및 출처 접근성 주의 (정직하게 기록)

- **이 환경에서 WebFetch는 사실상 전 도메인 403**이다. 검증 시도한 URL(모두 403/차단):
  law.go.kr, easylaw.go.kr, 무신사 뉴스룸(newsroom.musinsa.com), SBS Biz, 아시아경제,
  이투데이, 한국섬유신문, 청년일보, 헤럴드경제, 김·장 인사이트, godo 가이드,
  ko/en.wikipedia.org, yna.co.kr. → WebFetch 접근 = **실패(403)** 로 표기.
- 반면 **WebSearch는 정상 동작**하며, 각 URL의 실제 본문을 회수·요약해서 돌려준다.
  아래 출처들의 사실관계(숫자·날짜·조치)는 WebSearch가 회수한 본문 요약으로 교차확인했다.
  즉 URL은 실재하며 공개 접근 가능하나, 이 샌드박스의 WebFetch 게이트웨이만 403을 낸다.
- 규칙상 "AI가 접근·확인 가능한 공개 URL"이 근거여야 하므로, 각 후보에 **복수 언론사 URL**을
  두어 어느 하나가 막혀도 동일 사실을 다른 공개 출처로 확인 가능하게 했다.

---

## 후보 A ⭐(추천) — 섬유 혼용률·충전재 표시 검증 플러그인

### 1) 문제 정의
무신사 입점 브랜드(및 그 판매대행사)가 상품 상세페이지의 **혼용률(섬유 조성비)·충전재
비율**을 잘못 기재하거나 시즌 업데이트 시 갱신하지 않아, "거위털/캐시미어/특정 혼용률"로
표기된 상품이 실제와 다른 사례가 반복적으로 발생한다.
- 고통 주체: ① **무신사 안전거래센터·MD** — 수천~수만 개 카탈로그를 수작업으로 검수해야 함
  (7,968개 전수조사에 100일 소요, 막대한 비용). ② **소비자** — 허위·과장 표기 상품 구매 →
  리콜·환불. ③ **입점 브랜드** — 판매중지(최소 5일~최대 35일) 제재·신뢰도 하락.
- 규제 리스크: 표시·광고법상 허위·과장광고, 전기생활용품안전법 안전기준(섬유제품 표시),
  섬유상품 품질표시 규정 위반.

### 2) 공개 근거 (2개 이상)
- **무신사 다운·캐시미어 7,968개 전수조사, 8.5% 오기재 적발, 5~35일 판매중지** (2024-12-16 착수, 100일):
  - 헤럴드경제 https://biz.heraldcorp.com/article/10449772 — WebFetch 실패(403) / WebSearch 확인 O
  - EBN https://www.ebn.co.kr/news/articleView.html?idxno=1656435 — WebFetch 미시도, WebSearch 확인 O
  - 아시아경제 https://cm.asiae.co.kr/article/2025032516490862001 — WebSearch 확인 O
  - SBS Biz https://biz.sbs.co.kr/article/20000224713 — WebFetch 실패(403) / WebSearch 확인 O
- **노스페이스 패딩 충전재 혼용률 오기재 13스타일·28SKU (2025-12-02~03)** + 무신사 "기타 섬유는
  전기생활용품안전법 안전기준에 따라 15% 이내 합계 표시로 개선":
  - 아시아경제 https://www.asiae.co.kr/article/2025120218030203524 — WebFetch 실패(403)/WebSearch 확인 O
  - 이투데이 https://www.etoday.co.kr/news/view/2531959 — WebFetch 실패(403)/WebSearch 확인 O
  - 뉴시스 https://www.newsis.com/view/NISX20251202_0003424994 — WebSearch 확인 O
  - 한국섬유신문 https://www.ktnews.com/news/articleView.html?idxno=142743 — WebFetch 실패(403)/WebSearch 확인 O
- **법령/표시기준 (규칙의 근거)**:
  - 섬유상품 품질표시에 관한 규정 (혼용률 표시방법·오차: 혼용순서 2% 이내) law.go.kr
    https://www.law.go.kr/lsInfoP.do?lsiSeq=42610 — WebFetch 실패(403)/WebSearch 확인 O
  - 국가기술표준원(KATS) 섬유제품분야 상품별 품질표시기준
    https://www.kats.go.kr/content.do?cmsid=553 — WebSearch 확인 O
- 무신사 공식(참고, 403이나 실재): https://newsroom.musinsa.com/newsroom-menu/2025-0123-2 ,
  https://newsroom.musinsa.com/newsroom-menu/2025-1202-2

### 3) Codex 플러그인 해법 스케치
- 스킬: `verify-textile-labels` (SKILL.md + `scripts/verify.py`, Python 표준 라이브러리만).
- 입력: 상품 카탈로그 CSV/JSON (부위별 소재 문자열, 예 `겉감: 폴리에스터 80%, 나일론 20% / 충전재: 거위털 90%, 오리털 10%`), 선택적으로 시험성적서 CSV(SKU→실제 조성).
- 결정론적 검증 규칙:
  1. 부위별(겉감/안감/충전재) **혼용률 합계 = 100%** (오차 규칙 반영)
  2. **"기타 섬유" 합계 ≤ 15%** (전기생활용품안전법 안전기준)
  3. 충전재 표기(거위털/오리털/캐시미어) vs 시험성적서 불일치(재활용다운 등) 플래그
  4. 부위별 혼용률 **누락/공란** 탐지, 혼용순서(내림차순) 규칙
  5. 시험성적서 미제출 SKU 별도 표시(무신사 실제 대응 방식 반영)
- 출력: SKU별 PASS/FAIL 표 + 위반 사유 + 교정값 제안. 하나라도 FAIL이면 non-zero exit (CI 친화).
- 유료 API 불필요, 샘플 데이터 동봉 → 심사자 완전 재현 가능.

### 4) 2시간 구현 가능성 = **상**
- 파싱 + 산술 + 규칙표. 데모: Codex CLI에서
  `$verify-textile-labels samples/products.csv --lab samples/lab_results.csv`
  → 예) "1996 눕시 자켓: FAIL — 충전재 합계 95%(≠100%); '거위털' 표기이나 시험결과 재활용다운 → 오기재".
  한 줄 명령으로 결정론적 리포트 확인.

---

## 후보 B — 전자상거래 상품정보제공고시 필수항목 컴플라이언스 체커

### 1) 문제 정의
전자상거래법 하위 **「상품 등의 정보제공에 관한 고시」**는 품목(의류/패션잡화/화장품/구두 등
약 30여 품목)별로 필수 표기항목(의류: 제품소재·색상·치수·제조자·제조국·세탁방법·제조연월·
취급주의·품질보증기준·A/S 책임자 등)을 요구한다. 무신사는 2024-12 입점 브랜드에 "정보고시 미준수
등 위반 시 판매중지·주문취소"를 공지했다. 수만 개 입점 상품에서 **필드 누락·공란·'상품상세 참조'
남용**을 걸러내야 하고, 브랜드는 카테고리별 필수항목을 몰라 누락한다. 위반 시 시정명령+과태료
(최대 5백만원, 허위 제공 시 1천만원).

### 2) 공개 근거
- 무신사 뉴스룸(입점 브랜드 정보고시 위반 조치 안내)
  https://newsroom.musinsa.com/newsroom-menu/2024-1216-musinsa — WebFetch 실패(403)/WebSearch 확인 O
- 국가법령정보센터 「전자상거래 등에서의 상품 등의 정보제공에 관한 고시」
  https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000065929 — WebFetch 실패(403)/WebSearch 확인 O
- 과태료·개정 안내: winselling https://winselling.co.kr/notice/winselling/detail/66 (WebSearch 확인 O),
  김·장 https://www.kimchang.com/ko/insights/detail.kc?sch_section=4&idx=25119 (WebFetch 실패(403))
- 공정위 전자상거래 소비자보호 https://www.ftc.go.kr/www/contents.do?key=703 — WebSearch 확인 O

### 3) Codex 플러그인 해법 스케치
- 스킬 `check-product-info-notice` + `scripts/check.py` + `references/notice_schema.json`
  (품목별 필수항목을 고시 별표 기반으로 코드화).
- 입력 상품 리스팅 JSON → 카테고리별 필수항목 존재/비공란 검증, "상세 참조"류 회피표기 탐지.
- 출력: 누락 항목/공란 항목 리포트 + 해당 고시 근거 문구. non-zero exit 지원.

### 4) 2시간 구현 = **상**
- 데모: `$check-product-info-notice samples/listing.json --category 의류`
  → "누락: 제조국, 세탁방법 / 공란: 품질보증기준".

---

## 후보 C — 화장품(뷰티) 표시·광고 부당표현 린터 (무신사 뷰티 확장 연계)

### 1) 문제 정의
무신사는 2026년 뷰티를 핵심 전략으로 대확장(성수 메가스토어 약 2,000평, **직매입 400여 브랜드·
매장 500+ 브랜드**). 신진·인디 브랜드 상세페이지 카피에는 **화장품법 제13조 부당 표시·광고**
(의약품 오인 표현: 여드름 치료/재생/염증완화, 기능성 오인: 미백·주름개선을 심사 없이 표기,
실증 없는 효능·최상급 표현) 위반 리스크가 크다. 식약처 온라인 점검에서 **화장품법 위반 83건**이
적발됐고 그중 의약품 오인 광고가 64%였다. 무신사 뷰티 MD가 수동 검수하기엔 물량이 급증한다.

### 2) 공개 근거
- 화장품법 제13조(부당한 표시·광고 금지) law.go.kr
  https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=205691 — WebFetch 실패(403)/WebSearch 확인 O
- 화장품 표시·광고 실증에 관한 규정 / 찾기쉬운 생활법령(실증)
  https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=1301&ccfNo=4&cciNo=2&cnpClsNo=2 — WebFetch 실패(403)/WebSearch 확인 O
- 식약처 화장품 표시·광고 위반 83건 적발(의약품 오인 64%):
  메디컬투데이 https://www.mdtoday.co.kr/news/view/1065598151615045 — WebSearch 확인 O,
  코스인코리아 https://www.cosinkorea.com/news/article.html?no=55334 — WebSearch 확인 O
- 무신사 뷰티 확장(400여 직매입·500+ 브랜드·성수):
  뉴스웨이 https://newsway.co.kr/news/view?ud=2026062315435953666 — WebSearch 확인 O,
  아시아경제 https://www.asiae.co.kr/article/2026022707401658893 — WebSearch 확인 O

### 3) Codex 플러그인 해법 스케치
- 스킬 `lint-cosmetic-claims` + `scripts/lint.py` + `references/banned_terms.json`
  (의약품적/기능성 오인/절대·최상급 표현 사전, 각 항목에 근거 법조문 매핑).
- 상품명·상세 텍스트를 스캔 → 위반 후보 표현 하이라이트 + 근거 조문 + "실증자료 필요" 표시.
- 순수 사전+정규식, 유료 API 불필요.

### 4) 2시간 구현 = **상**
- 데모: `$lint-cosmetic-claims samples/beauty_detail.md`
  → "'피부 재생' → 의약품 오인 우려(화장품법 §13); '미백' → 기능성 심사 표기 필요".

---

## 최종 추천: **후보 A (섬유 혼용률·충전재 표시 검증 플러그인)**

이유:
1. **문제 실재성 최강**: 무신사 스스로 7,968개 전수조사·8.5% 오기재·5~35일 판매중지·리콜을
   공개했고(2024-12~2025-03), 2025-12 노스페이스 패딩 13스타일·28SKU 오기재로 **반복 발생**함이
   입증된다. 다수 주요 언론 + 법령(섬유상품 품질표시 규정, 전기생활용품안전법 15% 규칙)으로 다중 확인.
2. **결정론적 스크립트에 완벽 적합**: 합계 100% 검증, 기타섬유 ≤15%, 충전재 claim–시험결과 일치는
   순수 산술·규칙 판정 → 유료 API·LLM 판단 없이 재현 가능(심사자 재현성 최상). 무신사 공개 메시지
   ("AI를 의도대로 통제해 결과를 만든다")와 정확히 부합.
3. **개발/데이터 워크플로에 자연 결합**: 상품 카탈로그를 CI에서 검증하는 개발자 도구 = Codex 플러그인의
   전형적 유스케이스. 샘플 CSV + 한 줄 명령 + 명확한 PASS/FAIL로 로그·플러그인·질문지 정합성 확보 쉬움.

(후보 B는 범용성 좋으나 "고시 별표 코드화" 분량이 있고, 후보 C는 뷰티 확장 서사와 좋게 맞으나
표현 사전의 주관성 때문에 결정론성/재현성에서 A보다 약간 불리. 총감독이 뷰티 서사를 원하면 C를
2순위로.)
