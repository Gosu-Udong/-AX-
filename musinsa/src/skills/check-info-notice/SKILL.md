---
name: check-info-notice
description: >-
  무신사(또는 이커머스) 상품 리스팅이 「전자상거래 등에서의 상품 등의 정보제공에 관한 고시」의
  품목별 필수 표기항목을 갖췄는지 검증할 때 사용한다. 의류·화장품 필수항목(소재·색상·치수·
  제조자·제조국·세탁방법·제조연월·품질보증기준·A/S연락처 등)의 누락·공란, 그리고
  '상세페이지 참조' 류 회피표기 남용을 결정론적으로 검출한다. 사용자가 상품정보고시·정보고시·
  필수항목·표시의무·상세페이지 참조 검수를 언급하면 트리거된다. 섬유 혼용률 수치 검증이나
  화장품 광고 표현 검수에는 사용하지 않는다(verify-textile-labels / lint-beauty-claims 사용).
---

# check-info-notice

전자상거래법 하위 상품정보제공고시는 품목별 필수 표기항목을 요구하며, 무신사는 2024-12-16
입점 브랜드에 "상품정보 표시의무 등 위반 시 판매중지·주문취소·리콜·퇴점"을 공지했다.
이 스킬은 수만 개 리스팅에서 **필수항목 누락·공란·'상세 참조' 남용**을 자동으로 걸러낸다.

## 사용 시나리오

- 입점 상품 등록/수정 시 CI 게이트에서 필수항목 미비 리스팅의 게시를 차단한다.
- 카테고리(의류/화장품)별 필수항목을 몰라 누락하는 브랜드에 구체적 누락 목록을 돌려준다.

## 실행 명령

```bash
# 리스팅 자체 category 필드 사용
python3 scripts/check_info_notice.py samples/listings.json

# 모든 리스팅을 특정 카테고리로 강제
python3 scripts/check_info_notice.py samples/listings.json --category 의류

# JSON 리포트 / 정상 데모(exit 0)
python3 scripts/check_info_notice.py samples/listings.json --json
python3 scripts/check_info_notice.py samples/listings_pass.json
```

## 입력 형식

- 리스팅(JSON): `{"listings":[{"sku","name","category","info":{"제품소재":"...","제조국":"..."}}]}`
  - `category`: `의류` 또는 `화장품`(스키마에 정의된 품목). `--category`로 일괄 지정 가능.
  - `info`: 필수항목 key -> 값 문자열.

## 검증 규칙 (references/info_notice_schema.json)

- 누락: 필수 key 자체가 없음.
- 공란: 값이 빈 문자열.
- 상세참조 회피: `allow_detail_ref=false` 항목이 '상세페이지 참조' 등 회피표기로 채워짐
  (치수 등 일부 항목은 상세참조 허용).

## 출력 해석

- 각 리스팅: `PASS` / `FAIL` + 위반 유형([누락]/[공란]/[상세참조 회피])과 항목명.
- exit code: `0`=전 리스팅 통과, `1`=위반 존재, `2`=사용 오류.

## references

- `references/info_notice_schema.json`: 품목별 필수항목 + 상세참조 허용 여부 + 고시/공정위 URL.
