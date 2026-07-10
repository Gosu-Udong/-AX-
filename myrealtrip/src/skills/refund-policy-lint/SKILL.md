---
name: refund-policy-lint
description: 여행상품의 취소·환불 정책 JSON을 공정거래위원회 「소비자분쟁해결기준」의 위약금 상한과 대조해 위반을 검출한다. 취소/환불/위약금/캔슬피/refund/cancellation 정책을 릴리스·QA·CI 전에 점검하거나, "이 상품 환불 규정이 법정 기준을 넘는지" 확인할 때 트리거. 카테고리(국외여행 패키지·국내여행·숙박·항공권)별로 올바른 기준을 적용하며, 항공권 등 기준 밖 카테고리는 '기준 미적용'으로 표시한다. 단순 텍스트 요약·법률 자문에는 트리거하지 않는다(구조화 JSON 대상).
---

# refund-policy-lint — 취소·환불 위약금 상한 린터

## 언제 쓰나 (사용 시나리오)
- 상품 카탈로그를 릴리스하기 전 CI/QA 단계에서 취소·환불 위약금이 법정 상한을 초과하지 않는지 결정론적으로 게이트한다.
- 신규/변경 상품의 취소 정책 리뷰, 파트너가 등록한 정책의 자동 1차 검수.
- 소비자분쟁 예방: 「소비자분쟁해결기준」 대비 정량 초과 구간을 근거·출처와 함께 리포트.

## 실행 명령 (플러그인 루트 `src/`에서)
```bash
# 사람용 리포트 (정상 → exit 0, 위반 → exit 1)
python3 scripts/lint_refund_policy.py samples/policy_good.json
python3 scripts/lint_refund_policy.py samples/policy_bad.json

# 기계 판독용 JSON
python3 scripts/lint_refund_policy.py samples/policy_bad.json --json

# 기준 데이터 교체(성수기 숙박 등 별도 baseline 적용 시)
python3 scripts/lint_refund_policy.py <입력> --baseline references/krca_refund_baseline.json
```

## 입력 형식
`{"products": [ ... ]}` 형태의 JSON. 각 product:
- `id` (문자열), `name` (문자열)
- `category` — `overseas_package`(국외여행 패키지) | `domestic_package`(국내여행) | `accommodation`(숙박) | `air_ticket`(항공권)
- `cancellation_policy` — `[{"days_before": 정수, "penalty_pct": 숫자}, ...]`
  - `days_before` = 여행개시일(숙박은 사용예정일)까지 남은 일수
  - `penalty_pct` = 그 시점 취소 시 소비자가 부담하는 위약금(%)

## 처리 방식
1. `references/krca_refund_baseline.json`에서 상품 `category`에 맞는 기준(brackets)을 선택한다. **카테고리 분기가 핵심** — 단일 테이블로 전 카테고리를 재단하면 거짓양성이 나므로, 항공권처럼 `applicable:false`인 카테고리는 검사하지 않고 N/A로 표시한다.
2. 각 취소 tier의 `days_before`가 속한 구간의 `max_penalty_pct`(상한)를 찾아, `penalty_pct`가 상한을 초과하면 위반으로 플래그한다.
3. 초과폭(%p)으로 심각도(HIGH≥20 / MEDIUM≥10 / LOW)를 매기고, 상한 이하로 조정하라는 시정 제안과 근거·출처 URL을 붙인다.

## 출력 해석
- `[PASS]` 모든 구간이 상한 이하. `[FAIL]` 하나 이상 초과(상세 목록·시정·출처 포함). `[N/A ]` 기준 미적용 카테고리(항공권 등).
- 종료코드: `0`=위반 없음, `1`=위반 있음(CI 실패), `2`=사용오류(파일 없음/형식 오류).

## references
- `references/krca_refund_baseline.json` — 카테고리별 위약금 상한 기준과 각 항목의 출처 URL. 판정의 근거를 이 파일로 역추적할 수 있다. 기준 원출처: 「소비자분쟁해결기준」(law.go.kr), 찾기쉬운 생활법령(easylaw.go.kr), 한국여행업협회 여행정보센터(tourinfo.or.kr).
- 주의: 숙박 기준은 성수기/비수기·주중/주말로 세분되며 baseline은 '비수기 주중' 대표값이다. 성수기·주말은 상한이 더 높으므로 해당 baseline을 교체해 적용한다.
