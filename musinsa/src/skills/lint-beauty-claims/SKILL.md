---
name: lint-beauty-claims
description: >-
  무신사 뷰티(또는 화장품 이커머스) 상품명·상세페이지 카피가 화장품법 제13조 부당 표시·광고에
  해당하는 표현을 담고 있는지 검사할 때 사용한다. 의약품 오인(치료·재생·염증완화), 기능성 오인
  (미백·주름개선 심사 필요), 실증 필요 표현(즉각·임상적으로 입증·부작용 없음), 절대·최상급
  (최고·1위·100%) 표현을 사전 기반으로 스캔하고 근거 조문을 매핑한다. 사용자가 화장품·뷰티 카피·
  광고 문구·부당광고·의약품 오인·기능성 표현 검수를 언급하면 트리거된다. 섬유 혼용률 검증이나
  상품정보고시 필수항목 검수에는 사용하지 않는다(verify-textile-labels / check-info-notice 사용).
---

# lint-beauty-claims

무신사가 2026년 뷰티를 핵심 전략으로 확장하며 신진·인디 브랜드 상세페이지가 급증하는 가운데,
식약처 점검에서 화장품 부당광고 83건 중 의약품 오인이 64%를 차지했다. 이 스킬은 배포 전에
**화장품법 제13조 위반 후보 표현**을 조문과 함께 표시해 MD 검수를 돕는다.

## 사용 시나리오

- 뷰티 상세페이지/상품명을 CI 게이트에서 사전 스캔해 위반 표현이 있으면 게시를 차단한다.
- 각 표현에 근거 조문·교정 제안을 붙여 브랜드가 카피를 수정하도록 돕는다.

## 실행 명령

```bash
# 텍스트/마크다운 상세페이지 스캔
python3 scripts/lint_beauty_claims.py samples/beauty_detail.md

# JSON 리포트 / 정상 카피(exit 0)
python3 scripts/lint_beauty_claims.py samples/beauty_detail.md --json
python3 scripts/lint_beauty_claims.py samples/beauty_clean.md
```

## 입력 형식

- `.md`/`.txt`: 문서 전체를 라인 단위로 스캔.
- `.json`: `{"listings":[{"sku","name","text"}]}` — 상품별 스캔.

## 검증 카테고리 (references/beauty_banned_terms.json)

- `medicinal` — 의약품 오인 표현(화장품법 §13①1).
- `functional` — 기능성 오인, 심사·보고 필요(화장품법 §13①2, §4).
- `substantiation` — 실증 자료 필요 표현(화장품법 §14).
- `superlative` — 절대·최상급 표현(화장품법 §13①4).

## 출력 해석

- 대상별 `PASS`/`FAIL` + 위반: `L<라인> [카테고리] '표현'`, 근거 조문·URL·교정 제안.
- 이 스킬은 위반 '후보'를 표시하는 사전 스크리너이며, 실증자료 보유·심사 여부는 사람이 확정한다.
- exit code: `0`=위반 없음, `1`=위반 존재, `2`=사용 오류.

## references

- `references/beauty_banned_terms.json`: 표현 사전 + 카테고리별 근거 조문/출처 URL.
