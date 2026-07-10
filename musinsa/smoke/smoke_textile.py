#!/usr/bin/env python3
"""[스모크테스트] 무신사 후보 A: 혼용률·충전재 표시 검증 — 개념 증명용 최소 구현.

본 구현 아님. 결정론적 룰 판정이 가능한지만 확인한다.
근거: 섬유제품 품질표시 규정(부위별 혼용률 합계 100%), 무신사 전수조사 사례.
"""
import json, sys

TOLERANCE_PP = 5  # 충전재 표시 vs 시험성적서 허용 오차(%p)

def check(product):
    issues = []
    for part, mix in product.get("parts", {}).items():
        total = sum(mix.values())
        if total != 100:
            issues.append(f"[혼용률] '{part}' 합계 {total}% ≠ 100%")
    f = product.get("filling")
    if f:
        for k, declared in f.get("declared", {}).items():
            lab = f.get("lab", {}).get(k)
            if lab is None:
                issues.append(f"[충전재] '{k}' 시험성적서 값 없음")
            elif abs(declared - lab) > TOLERANCE_PP:
                issues.append(f"[충전재] '{k}' 표시 {declared}% vs 시험 {lab}% (오차 {abs(declared-lab)}%p > {TOLERANCE_PP}%p)")
    return issues

def main():
    data = json.load(open(sys.argv[1], encoding="utf-8"))
    failed = 0
    for p in data["products"]:
        issues = check(p)
        status = "FAIL" if issues else "PASS"
        failed += bool(issues)
        print(f"{status}  {p['sku']}  {p['name']}")
        for i in issues:
            print(f"      - {i}")
    print(f"\n결과: {len(data['products'])}개 중 {failed}개 위반")
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
