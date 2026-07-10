#!/usr/bin/env python3
"""[스모크테스트] 마이리얼트립 후보 A: 취소·환불 위약금 상한 검증 — 개념 증명용 최소 구현.

본 구현 아님. 소비자분쟁해결기준(국외여행) 시점별 배상 상한과의 대조가
결정론적으로 가능한지만 확인한다.
"""
import json, sys

# 국외여행 소비자분쟁해결기준: (여행개시 D-일 이상, 위약금 상한 %)
CAPS = [(30, 0), (20, 10), (10, 15), (8, 20), (1, 30), (0, 50)]

def cap_for(days_before):
    for d, cap in CAPS:
        if days_before >= d:
            return cap
    return 50

def main():
    products = json.load(open(sys.argv[1], encoding="utf-8"))["products"]
    violations = 0
    for p in products:
        issues = []
        for tier in p["cancellation_policy"]:
            cap = cap_for(tier["days_before"])
            if tier["penalty_pct"] > cap:
                issues.append(f"D-{tier['days_before']} 위약금 {tier['penalty_pct']}% > 법정 상한 {cap}% (시정: {cap}% 이하)")
        status = "FAIL" if issues else "PASS"
        violations += bool(issues)
        print(f"{status}  {p['id']}  {p['name']}")
        for i in issues:
            print(f"      - {i}")
    print(f"\n결과: {len(products)}개 중 {violations}개 위반")
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()
