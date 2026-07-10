#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refund-policy-lint — 여행상품 취소·환불 정책을 소비자분쟁해결기준 위약금 상한과 대조.

카테고리 분기(국외여행 패키지 / 국내여행 / 숙박 / 항공권)에 따라 올바른 기준을
적용한다. 항공권 등 기준 밖 카테고리는 '기준 미적용(N/A)'으로 명시하여 거짓양성을
방지한다. 상한 초과 구간을 검출하고 시정 제안과 PASS/FAIL 리포트를 낸다.

표준 라이브러리만 사용. 결정론적. exit 0=통과 / 1=위반 / 2=사용오류.
"""
import argparse
import json
import os
import sys

DEFAULT_BASELINE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "references", "krca_refund_baseline.json"
)


def _err(msg):
    sys.stderr.write("[사용오류] " + msg + "\n")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cap_for(days_before, brackets):
    """days_before가 속한 구간의 위약금 상한(%)과 근거 설명을 반환."""
    # min_days_before 내림차순으로 정렬하여 처음 만족하는 구간 채택.
    for b in sorted(brackets, key=lambda x: x["min_days_before"], reverse=True):
        if days_before >= b["min_days_before"]:
            return b["max_penalty_pct"], b["desc"]
    last = sorted(brackets, key=lambda x: x["min_days_before"])[0]
    return last["max_penalty_pct"], last["desc"]


def severity(overage):
    if overage >= 20:
        return "HIGH"
    if overage >= 10:
        return "MEDIUM"
    return "LOW"


def evaluate(products, baseline):
    """상품 리스트를 평가하여 결과 dict 리스트 반환."""
    cats = baseline["categories"]
    results = []
    for p in products:
        pid = p.get("id", "(no-id)")
        name = p.get("name", "")
        category = p.get("category", "")
        cat = cats.get(category)

        if cat is None:
            results.append({
                "id": pid, "name": name, "category": category,
                "category_label": "(정의되지 않은 카테고리)",
                "status": "N/A", "issues": [],
                "note": "기준 데이터에 없는 카테고리 — 기준 미적용(검토 대상)",
            })
            continue

        if not cat.get("applicable", True):
            results.append({
                "id": pid, "name": name, "category": category,
                "category_label": cat.get("label", category),
                "status": "N/A", "issues": [],
                "note": "기준 미적용: " + cat.get("reason", "카테고리 기준 없음"),
                "source_url": cat.get("source_url", ""),
            })
            continue

        brackets = cat["brackets"]
        issues = []
        for tier in p.get("cancellation_policy", []):
            try:
                days = int(tier["days_before"])
                pen = float(tier["penalty_pct"])
            except (KeyError, ValueError, TypeError):
                issues.append({
                    "days_before": tier.get("days_before"),
                    "penalty_pct": tier.get("penalty_pct"),
                    "cap": None, "overage": None, "severity": "HIGH",
                    "basis": "취소 tier 형식 오류(days_before/penalty_pct 필요)",
                    "remedy": "days_before(정수)와 penalty_pct(숫자)를 채운다.",
                })
                continue
            cap, basis = cap_for(days, brackets)
            if pen > cap:
                overage = round(pen - cap, 2)
                issues.append({
                    "days_before": days, "penalty_pct": pen,
                    "cap": cap, "overage": overage,
                    "severity": severity(overage),
                    "basis": basis,
                    "remedy": "위약금을 %g%% 이하로 조정" % cap,
                })
        results.append({
            "id": pid, "name": name, "category": category,
            "category_label": cat.get("label", category),
            "status": "FAIL" if issues else "PASS",
            "issues": issues,
            "source_url": cat.get("source_url", ""),
        })
    return results


def format_report(results, baseline):
    lines = []
    lines.append("=" * 68)
    lines.append("refund-policy-lint — 취소·환불 위약금 상한 검사 리포트")
    lines.append("기준: %s" % baseline["meta"]["title"])
    lines.append("=" * 68)
    n_pass = n_fail = n_na = 0
    for r in results:
        tag = {"PASS": "[PASS]", "FAIL": "[FAIL]", "N/A": "[N/A ]"}[r["status"]]
        head = "%s %-8s %s  (%s)" % (tag, r["id"], r["name"], r["category_label"])
        lines.append(head)
        if r["status"] == "N/A":
            lines.append("        - %s" % r.get("note", ""))
            n_na += 1
        elif r["status"] == "FAIL":
            n_fail += 1
            for it in r["issues"]:
                if it["cap"] is None:
                    lines.append("        - %s" % it["basis"])
                    continue
                lines.append(
                    "        - D-%s 위약금 %g%% > 상한 %g%% (초과 %g%%p · 심각도 %s)"
                    % (it["days_before"], it["penalty_pct"], it["cap"],
                       it["overage"], it["severity"])
                )
                lines.append("          근거: %s" % it["basis"])
                lines.append("          시정: %s" % it["remedy"])
            if r.get("source_url"):
                lines.append("          출처: %s" % r["source_url"])
        else:
            n_pass += 1
    lines.append("-" * 68)
    lines.append("요약: 총 %d개 | PASS %d | FAIL %d | N/A(기준 미적용) %d"
                 % (len(results), n_pass, n_fail, n_na))
    return "\n".join(lines), n_fail


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="lint_refund_policy",
        description="여행상품 취소·환불 정책을 소비자분쟁해결기준 위약금 상한과 대조한다.",
    )
    ap.add_argument("input", help="검사할 상품 취소·환불 정책 JSON 경로")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE,
                    help="기준 데이터 JSON 경로(기본: references/krca_refund_baseline.json)")
    ap.add_argument("--json", action="store_true", help="사람용 리포트 대신 JSON 출력")
    args = ap.parse_args(argv)

    try:
        data = load_json(args.input)
        baseline = load_json(args.baseline)
    except FileNotFoundError as e:
        _err("파일을 찾을 수 없습니다: %s" % e.filename)
        return 2
    except json.JSONDecodeError as e:
        _err("JSON 파싱 실패: %s" % e)
        return 2

    products = data.get("products")
    if not isinstance(products, list):
        _err("입력 JSON에 'products' 배열이 필요합니다.")
        return 2

    results = evaluate(products, baseline)
    n_fail = sum(1 for r in results if r["status"] == "FAIL")

    if args.json:
        print(json.dumps({
            "tool": "refund-policy-lint",
            "baseline": baseline["meta"]["title"],
            "summary": {
                "total": len(results),
                "pass": sum(1 for r in results if r["status"] == "PASS"),
                "fail": n_fail,
                "na": sum(1 for r in results if r["status"] == "N/A"),
            },
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        report, n_fail = format_report(results, baseline)
        print(report)

    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
