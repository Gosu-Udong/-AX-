#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report — refund-policy-lint + darkpattern-scan 결과를 하나의 마크다운 리포트로 통합.

두 스킬을 릴리스 게이트로 한 번에 돌리고, 소비자보호 컴플라이언스 요약을 낸다.
표준 라이브러리만 사용. 결정론적. exit 0=통과 / 1=위반 / 2=사용오류.

예:
  python3 scripts/report.py --policy samples/policy_bad.json --listings samples/listings_bad.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint_refund_policy as refund  # noqa: E402
import scan_listings as dark  # noqa: E402


def _md_refund(results):
    out = ["## 1. 취소·환불 위약금 상한 (refund-policy-lint)", ""]
    out.append("| 상품 | 카테고리 | 결과 | 상세 |")
    out.append("|---|---|---|---|")
    for r in results:
        if r["status"] == "FAIL":
            det = "; ".join(
                "D-%s %g%%>상한%g%%(%s)" % (i["days_before"], i["penalty_pct"], i["cap"], i["severity"])
                for i in r["issues"] if i.get("cap") is not None) or "형식 오류"
        elif r["status"] == "N/A":
            det = r.get("note", "기준 미적용")
        else:
            det = "-"
        out.append("| %s %s | %s | %s | %s |"
                   % (r["id"], r["name"], r["category_label"], r["status"], det))
    return "\n".join(out)


def _md_dark(results):
    out = ["## 2. 가격표시 다크패턴 (darkpattern-scan)", ""]
    out.append("| 상품 | 결과 | 검출 유형 |")
    out.append("|---|---|---|")
    for r in results:
        if r["status"] == "FAIL":
            det = "; ".join("%s(%s)" % (f["pattern_ko"], f["severity"]) for f in r["findings"])
        else:
            det = "-"
        out.append("| %s %s | %s | %s |" % (r["id"], r["name"], r["status"], det))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="report",
        description="refund-policy-lint와 darkpattern-scan 결과를 통합 마크다운 리포트로 생성한다.",
    )
    ap.add_argument("--policy", help="취소·환불 정책 JSON 경로")
    ap.add_argument("--listings", help="상품 리스팅 JSON 경로")
    ap.add_argument("--json", action="store_true", help="마크다운 대신 통합 JSON 출력")
    args = ap.parse_args(argv)

    if not args.policy and not args.listings:
        refund._err("--policy 또는 --listings 중 하나 이상이 필요합니다.")
        return 2

    total_fail = 0
    refund_results = dark_results = None

    try:
        if args.policy:
            baseline = refund.load_json(refund.DEFAULT_BASELINE)
            data = refund.load_json(args.policy)
            if not isinstance(data.get("products"), list):
                refund._err("정책 JSON에 'products' 배열이 필요합니다.")
                return 2
            refund_results = refund.evaluate(data["products"], baseline)
            total_fail += sum(1 for r in refund_results if r["status"] == "FAIL")
        if args.listings:
            types = dark.load_json(dark.DEFAULT_TYPES)
            data = dark.load_json(args.listings)
            if not isinstance(data.get("listings"), list):
                dark._err("리스팅 JSON에 'listings' 배열이 필요합니다.")
                return 2
            dark_results = dark.evaluate(data["listings"], types)
            total_fail += sum(1 for r in dark_results if r["status"] == "FAIL")
    except FileNotFoundError as e:
        refund._err("파일을 찾을 수 없습니다: %s" % e.filename)
        return 2
    except json.JSONDecodeError as e:
        refund._err("JSON 파싱 실패: %s" % e)
        return 2

    if args.json:
        print(json.dumps({
            "tool": "myrealtrip-traveler-guard/report",
            "verdict": "FAIL" if total_fail else "PASS",
            "refund": refund_results,
            "darkpattern": dark_results,
        }, ensure_ascii=False, indent=2))
        return 1 if total_fail else 0

    md = ["# 마이리얼트립 여행자 보호 통합 리포트",
          "",
          "> `myrealtrip-traveler-guard` — 취소·환불 약관과 가격표시 다크패턴 릴리스 전 검사",
          "",
          "**종합 판정: %s** (위반 상품 %d건)" % ("FAIL ❌" if total_fail else "PASS ✅", total_fail),
          ""]
    if refund_results is not None:
        md.append(_md_refund(refund_results))
        md.append("")
    if dark_results is not None:
        md.append(_md_dark(dark_results))
        md.append("")
    md.append("---")
    md.append("근거: 공정거래위원회 「소비자분쟁해결기준」·전자상거래법 다크패턴 규제, 한국소비자원 조사(2024.03). 상세 출처는 references/*.json 참조.")
    print("\n".join(md))
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
