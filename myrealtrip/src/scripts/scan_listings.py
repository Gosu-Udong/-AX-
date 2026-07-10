#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""darkpattern-scan — 여행상품 리스팅 JSON에서 가격표시 다크패턴을 검출.

검출 유형:
  1) 대표가격 오인(misleading_reference_price): 대표가 < 모든 실판매 옵션가,
     또는 대표가가 성인 표준가가 아닌 아동가/쿠폰가와 동일.
  2) 순차공개 가격책정(drip_pricing): 대표가에 미포함된 필수 수수료가 있어
     최종 결제가가 상승.
  3) 거짓 긴급성(false_urgency): 상시 마감/재고 임박(always_on=true).
  4) 특정옵션 사전선택(option_preselection): 유료 부가옵션 기본 선택(default_selected).

각 검출은 공정위/한국소비자원 다크패턴 유형과 출처 URL로 매핑된다.
표준 라이브러리만 사용. 결정론적. exit 0=통과 / 1=위반 / 2=사용오류.
"""
import argparse
import json
import os
import sys

DEFAULT_TYPES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "references", "darkpattern_types.json"
)

CHILD_COUPON_HINTS = ["아동", "소아", "유아", "어린이", "쿠폰", "할인", "밀", "child", "kid", "coupon"]


def _err(msg):
    sys.stderr.write("[사용오류] " + msg + "\n")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _has_hint(label):
    low = str(label).lower()
    return any(h.lower() in low for h in CHILD_COUPON_HINTS)


def evaluate(listings, types):
    pat = types["patterns"]
    results = []
    for lst in listings:
        lid = lst.get("id", "(no-id)")
        name = lst.get("name", "")
        findings = []

        display = lst.get("display_price")
        options = lst.get("options", []) or []
        opt_prices = [o["price"] for o in options if isinstance(o.get("price"), (int, float))]

        # 1) 대표가격 오인
        if display is not None and opt_prices:
            min_opt = min(opt_prices)
            if display < min_opt:
                findings.append(_finding(
                    pat, "misleading_reference_price",
                    "대표가 %g원 < 실판매 최저 옵션가 %g원 (표시가로 구매 불가)" % (display, min_opt)))
            else:
                # 대표가와 동일한 옵션이 아동가/쿠폰가이고, 더 비싼 표준가 옵션이 존재
                same = [o for o in options if o.get("price") == display]
                higher = [o for o in options if isinstance(o.get("price"), (int, float)) and o["price"] > display]
                if same and higher and any(_has_hint(o.get("label", "")) for o in same):
                    lbl = next(o.get("label", "") for o in same if _has_hint(o.get("label", "")))
                    findings.append(_finding(
                        pat, "misleading_reference_price",
                        "대표가 %g원이 표준가가 아닌 '%s' 옵션가와 동일 (상위 표준가 옵션 존재)" % (display, lbl)))

        # 2) 순차공개(숨겨진 필수 수수료)
        fees = lst.get("required_fees", []) or []
        fee_total = sum(f["amount"] for f in fees if isinstance(f.get("amount"), (int, float)))
        if fee_total > 0 and display:
            final = display + fee_total
            ratio = fee_total / float(display) if display else 0
            sev = "HIGH" if ratio >= 0.3 else "MEDIUM"
            names = ", ".join(str(f.get("label", "수수료")) for f in fees)
            findings.append(_finding(
                pat, "drip_pricing",
                "대표가 %g원에 미포함 필수 수수료 %g원(%s) → 최종 %g원(+%.0f%%)"
                % (display, fee_total, names, final, ratio * 100),
                severity=sev))

        # 3) 거짓 긴급성
        urg = lst.get("urgency", {}) or {}
        if urg.get("type") in ("deadline", "stock") and urg.get("always_on") is True:
            findings.append(_finding(
                pat, "false_urgency",
                "상시 긴급성 표시: '%s' (always_on=true)" % urg.get("text", urg.get("type"))))

        # 4) 특정옵션 사전선택
        for a in lst.get("addons", []) or []:
            if a.get("default_selected") is True and (a.get("price", 0) or 0) > 0:
                findings.append(_finding(
                    pat, "option_preselection",
                    "유료 부가옵션 '%s'(%g원) 기본 선택됨" % (a.get("label", ""), a.get("price", 0))))

        results.append({
            "id": lid, "name": name,
            "status": "FAIL" if findings else "PASS",
            "findings": findings,
        })
    return results


def _finding(pat, key, detail, severity=None):
    p = pat[key]
    return {
        "pattern": key,
        "pattern_ko": p["ko"],
        "ftc_type": p["ftc_type"],
        "severity": severity or p.get("severity", "MEDIUM"),
        "detail": detail,
        "remedy": p.get("remedy", ""),
        "source_url": p.get("source_url", ""),
    }


def format_report(results, types):
    lines = []
    lines.append("=" * 68)
    lines.append("darkpattern-scan — 가격표시 다크패턴 검사 리포트")
    lines.append("기준: %s" % types["meta"]["title"])
    lines.append("=" * 68)
    n_pass = n_fail = 0
    for r in results:
        tag = "[FAIL]" if r["status"] == "FAIL" else "[PASS]"
        lines.append("%s %-8s %s" % (tag, r["id"], r["name"]))
        if r["status"] == "FAIL":
            n_fail += 1
            for f in r["findings"]:
                lines.append("        - [%s] %s (%s)"
                             % (f["severity"], f["pattern_ko"], f["detail"]))
                lines.append("          공정위 유형: %s" % f["ftc_type"])
                lines.append("          시정: %s" % f["remedy"])
                lines.append("          출처: %s" % f["source_url"])
        else:
            n_pass += 1
    lines.append("-" * 68)
    lines.append("요약: 총 %d개 | PASS %d | FAIL %d" % (len(results), n_pass, n_fail))
    return "\n".join(lines), n_fail


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="scan_listings",
        description="여행상품 리스팅 JSON에서 가격표시 다크패턴을 검출한다.",
    )
    ap.add_argument("input", help="검사할 상품 리스팅 JSON 경로")
    ap.add_argument("--types", default=DEFAULT_TYPES,
                    help="다크패턴 유형 데이터 경로(기본: references/darkpattern_types.json)")
    ap.add_argument("--json", action="store_true", help="사람용 리포트 대신 JSON 출력")
    args = ap.parse_args(argv)

    try:
        data = load_json(args.input)
        types = load_json(args.types)
    except FileNotFoundError as e:
        _err("파일을 찾을 수 없습니다: %s" % e.filename)
        return 2
    except json.JSONDecodeError as e:
        _err("JSON 파싱 실패: %s" % e)
        return 2

    listings = data.get("listings")
    if not isinstance(listings, list):
        _err("입력 JSON에 'listings' 배열이 필요합니다.")
        return 2

    results = evaluate(listings, types)
    n_fail = sum(1 for r in results if r["status"] == "FAIL")

    if args.json:
        print(json.dumps({
            "tool": "darkpattern-scan",
            "reference": types["meta"]["title"],
            "summary": {
                "total": len(results),
                "pass": sum(1 for r in results if r["status"] == "PASS"),
                "fail": n_fail,
            },
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        report, n_fail = format_report(results, types)
        print(report)

    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
