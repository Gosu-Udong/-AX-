#!/usr/bin/env python3
"""[스모크테스트] 카카오페이증권 후보 1: 금융광고 문구 금소법 §22 린터 — 개념 증명용 최소 구현.

본 구현 아님. 금지 표현 사전 + 필수 위험고지 검사가 결정론적으로 가능한지만 확인한다.
근거: 금융소비자보호법 제22조(광고 관련 준수사항).
"""
import json, re, sys

BANNED = [  # (패턴, 근거)
    (r"원금\s*(?:100%\s*)?보장", "금소법 §22 — 손실보전 오인 표현"),
    (r"확정\s*수익", "금소법 §22 — 이익보장 오인 표현"),
    (r"손실\s*없이", "금소법 §22 — 손실보전 오인 표현"),
    (r"무조건", "금소법 §22 — 단정적 표현"),
]
RISK_DISCLOSURE = re.compile(r"(원금\s*손실|투자\s*위험)")

def main():
    items = json.load(open(sys.argv[1], encoding="utf-8"))["banners"]
    violations = 0
    for it in items:
        found = [(m, why) for pat, why in BANNED for m in re.findall(pat, it["text"])]
        needs_risk = it.get("is_investment_ad", True) and not RISK_DISCLOSURE.search(it["text"])
        status = "FAIL" if (found or needs_risk) else "PASS"
        violations += bool(found or needs_risk)
        print(f"{status}  {it['id']}  \"{it['text'][:40]}...\"" if len(it['text']) > 40 else f"{status}  {it['id']}  \"{it['text']}\"")
        for m, why in found:
            print(f"      - 금지 표현 '{m}' ({why})")
        if needs_risk:
            print("      - 투자위험 필수 고지 누락 (금소법 §22 및 협회 광고 규정)")
    print(f"\n결과: {len(items)}건 중 {violations}건 위반")
    sys.exit(1 if violations else 0)

if __name__ == "__main__":
    main()
