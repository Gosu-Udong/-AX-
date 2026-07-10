---
name: verify-textile-labels
description: >-
  무신사(또는 패션 이커머스) 상품 카탈로그의 섬유 혼용률·충전재 표시가 법정 표시기준을
  지키는지 검증할 때 사용한다. 부위별 혼용률 합계가 100%인지, '기타섬유' 합계가 15%
  이하인지, 솜털·깃털 등 충전재 표시값이 시험성적서와 일치하는지, 카테고리별 필수 부위가
  누락되지 않았는지를 결정론적으로 판정한다. 사용자가 상품 CSV/JSON·시험성적서·혼용률·
  충전재·다운·패딩·품질표시 검수를 언급하면 트리거된다. 화장품 광고 표현 검수나
  상품정보고시 필수항목 검수에는 사용하지 않는다(그 경우 lint-beauty-claims /
  check-info-notice 사용).
---

# verify-textile-labels

무신사가 2024-12~2025-03 다운·캐시미어 7,968개를 전수조사해 8.5%(약 677개)의 오기재를 적발하고
브랜드에 5~35일 판매중지 제재를 내린 사건, 그리고 2025-12 노스페이스 패딩 13스타일·28SKU 충전재
오기재(환불 안내 + 판매대행사 벌점) 사건에서 드러난 **섬유 표시 위반**을 배포 전에 자동으로 걸러낸다.

## 사용 시나리오

- 브랜드/판매대행사가 업로드한 상품 카탈로그를 CI 게이트에서 검사해 오기재 상품의 배포를 차단한다.
- MD·안전거래센터가 수천 SKU를 수작업 검수하는 대신 결정론적 리포트로 우선순위를 잡는다.

## 실행 명령

```bash
# 혼용률·기타섬유·필수부위 + 충전재 시험성적서 대조
python3 scripts/verify_textile_labels.py samples/products.json --lab samples/lab_results.csv

# JSON 리포트
python3 scripts/verify_textile_labels.py samples/products.json --lab samples/lab_results.csv --json

# 전부 정상 카탈로그(exit 0 확인)
python3 scripts/verify_textile_labels.py samples/products_pass.json --lab samples/lab_results.csv
```

## 입력 형식

- 상품 카탈로그(JSON): `{"products":[{"sku","name","category","parts":{"겉감":{"면":60,...}}}]}`
  - `category`: `padded_outer`(겉감+충전재 필수) 또는 `default`(겉감 필수).
  - `parts`: 부위명 -> {섬유명: 함유율(%)}.
- 시험성적서(CSV, `--lab`, 선택): 헤더 `sku,part,component,measured_pct`. 충전재 실측값.

## 검증 규칙 (references/textile_rules.json)

1. `MIX_SUM_100` — 부위별 혼용률 합계 = 100%.
2. `ETC_FIBER_MAX_15` — '기타섬유' 합계 <= 15%.
3. `FILLING_LAB_MATCH` — 충전재 성분별 |표시 - 시험| <= 5%p, 성적서 미제출 SKU 별도 표시.
4. `REQUIRED_PARTS` — 카테고리별 필수 부위 누락 검출.
5. `MIX_DESCENDING` — 혼용순서 내림차순(경고, 판정 불포함).

## 출력 해석

- 각 SKU: `PASS` / `FAIL` + 위반 사유(규칙 ID·교정 제안), `~ (경고)`는 exit code에 영향 없음.
- exit code: `0`=전 상품 통과, `1`=위반 존재(CI 차단), `2`=사용 오류.

## references

- `references/textile_rules.json`: 규칙 임계값 + 조문/출처 URL(법령·KATS·무신사 뉴스룸).
