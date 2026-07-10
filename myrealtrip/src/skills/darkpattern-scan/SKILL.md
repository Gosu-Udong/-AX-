---
name: darkpattern-scan
description: 여행상품 리스팅 JSON에서 가격표시 다크패턴을 검출한다. 대표가격 오인(대표가가 실판매 옵션가보다 낮거나 아동가/쿠폰가), 숨겨진 필수 수수료(순차공개 가격책정/drip pricing), 거짓 긴급성(상시 마감임박), 유료옵션 사전선택을 공정위·한국소비자원 다크패턴 유형에 매핑해 리포트한다. 상품 리스팅/가격표시/대표가/다크패턴/darkpattern/가격 오인을 릴리스·QA·CI 전에 점검할 때 트리거. 취소·환불 약관 검사는 refund-policy-lint를 쓴다.
---

# darkpattern-scan — 가격표시 다크패턴 스캐너

## 언제 쓰나 (사용 시나리오)
- 상품 리스팅을 노출하기 전 대표가격·수수료·긴급성·옵션 기본선택을 릴리스 게이트로 자동 검사한다.
- 한국소비자원이 2024.03 지적한 '대표가를 아동가/밀쿠폰가로 표시'(마이리얼트립 등, 2023.12 개선완료) 같은 유형이 재발하지 않도록 상시 감시한다.
- 전자상거래법 다크패턴 규제 대응: 순차공개 가격책정·특정옵션 사전선택 등 위험 항목을 근거·출처와 함께 리포트.

## 실행 명령 (플러그인 루트 `src/`에서)
```bash
# 사람용 리포트 (정상 → exit 0, 위반 → exit 1)
python3 scripts/scan_listings.py samples/listings_good.json
python3 scripts/scan_listings.py samples/listings_bad.json

# 기계 판독용 JSON
python3 scripts/scan_listings.py samples/listings_bad.json --json
```

## 입력 형식
`{"listings": [ ... ]}` 형태의 JSON. 각 listing:
- `id`, `name`
- `display_price` (대표가격, 숫자), `display_price_label` (표기 라벨)
- `options` — `[{"label": "성인", "price": 62000}, ...]` 실판매 옵션가
- `required_fees` — `[{"label": "시설이용료", "amount": 15000}, ...]` 대표가에 미포함된 필수 수수료
- `urgency` — `{"type": "deadline"|"stock"|"none", "always_on": true|false, "text": "..."}`
- `addons` — `[{"label": "여행자보험", "price": 12000, "default_selected": true|false}, ...]` 유료 부가옵션

## 처리 방식 (검출 룰)
1. **대표가격 오인**: `display_price` < 모든 옵션가(표시가로 구매 불가), 또는 대표가가 성인 표준가가 아닌 아동가/쿠폰가와 동일한데 더 비싼 표준 옵션이 존재.
2. **순차공개 가격책정(drip pricing)**: `required_fees` 합계가 있어 최종가 = 대표가 + 필수수수료로 상승(수수료 비율 ≥30%면 HIGH).
3. **거짓 긴급성**: `urgency.always_on == true`인 상시 마감/재고 임박 표시.
4. **특정옵션 사전선택**: 유료 `addons` 중 `default_selected == true`.

## 출력 해석
- `[FAIL]` 검출 항목마다 심각도·상세·공정위 유형·시정 제안·출처 URL을 출력. `[PASS]` 검출 없음.
- 종료코드: `0`=검출 없음, `1`=검출 있음(CI 실패), `2`=사용오류.

## references
- `references/darkpattern_types.json` — 4개 검출 유형과 공정위/한국소비자원 다크패턴 유형·출처 URL 매핑. 판정 근거를 이 파일로 역추적한다. 원출처: 공정위 온라인 다크패턴 규제(전자상거래법), 한국소비자원 2024.03 조사(khan.co.kr), 상품정보제공고시(law.go.kr).

## 통합 리포트
두 스킬 결과를 한 번에 보려면: `python3 scripts/report.py --policy <정책> --listings <리스팅>` (마크다운, `--json` 지원).
