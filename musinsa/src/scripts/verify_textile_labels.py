#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify-textile-labels — 무신사 상품 리스팅의 섬유 혼용률·충전재 표시 결정론적 검증기.

검사 규칙(references/textile_rules.json 근거):
  1. 부위별 혼용률 합계 = 100%            (섬유제품 품질표시 규정)
  2. '기타섬유' 합계 <= 15%              (전기생활용품안전법 안전기준)
  3. 충전재 표시값 vs 시험성적서 대조(5%p) (허위·과장광고 금지 / 무신사 안전거래정책)
  4. 카테고리별 필수 부위 누락            (섬유제품 품질표시기준)
  + 혼용순서 내림차순(경고, 판정 불포함)

exit code: 0=전 상품 통과, 1=위반 존재, 2=사용 오류.
표준 라이브러리만 사용. 입력 상품=JSON, 시험성적서=CSV(--lab).
"""
import argparse
import csv
import json
import os
import sys

DEFAULT_RULES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "textile_rules.json")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_lab(path):
    """시험성적서 CSV -> {(sku, part, component): measured_pct}. 헤더: sku,part,component,measured_pct"""
    lab = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"sku", "part", "component", "measured_pct"}
        if reader.fieldnames is None or not required.issubset({c.strip() for c in reader.fieldnames}):
            raise ValueError("시험성적서 CSV 헤더는 sku,part,component,measured_pct 여야 합니다.")
        for row in reader:
            key = (row["sku"].strip(), row["part"].strip(), row["component"].strip())
            lab[key] = float(row["measured_pct"])
    return lab


def is_etc_fiber(name, etc_labels):
    return any(lbl in name for lbl in etc_labels)


def check_product(product, rules, lab):
    """단일 상품 검증. (violations, warnings) 반환."""
    violations = []
    warnings = []
    sku = product.get("sku", "?")
    parts = product.get("parts", {})

    # 4. 필수 부위 누락
    rp = rules["required_parts"]
    category = product.get("category", "default")
    required = rp["by_category"].get(category, rp["by_category"]["default"])
    for part_name in required:
        if part_name not in parts or not parts[part_name]:
            violations.append(f"[필수부위 누락:{rp['id']}] '{part_name}' 부위 혼용률 정보 없음")

    etc_labels = rules["etc_fiber_cap"]["labels"]
    etc_max = rules["etc_fiber_cap"]["max_total_pct"]
    target = rules["mix_sum"]["target_pct"]
    tol = rules["mix_sum"]["tolerance_pp"]

    for part_name, mix in parts.items():
        if not isinstance(mix, dict) or not mix:
            violations.append(f"[혼용률 공란:{rules['mix_sum']['id']}] '{part_name}' 성분이 비어 있음")
            continue
        # 1. 합계 100%
        total = round(sum(mix.values()), 3)
        if abs(total - target) > tol:
            violations.append(
                f"[혼용률 합계:{rules['mix_sum']['id']}] '{part_name}' 합계 {total:g}% (목표 {target}%) "
                f"-> 교정: 합계가 {target}%가 되도록 성분비 조정"
            )
        # 2. 기타섬유 <= 15%
        etc_total = round(sum(v for k, v in mix.items() if is_etc_fiber(k, etc_labels)), 3)
        if etc_total > etc_max:
            violations.append(
                f"[기타섬유 초과:{rules['etc_fiber_cap']['id']}] '{part_name}' 기타섬유 합계 {etc_total:g}% > {etc_max}% "
                f"-> 교정: {etc_max}% 초과 섬유는 개별 섬유명으로 표기"
            )
        # 혼용순서 내림차순(경고)
        values = list(mix.values())
        if values != sorted(values, reverse=True):
            warnings.append(f"[혼용순서:{rules['descending_order']['id']}] '{part_name}' 함유량 내림차순 아님")

    # 3. 충전재 표시 vs 시험성적서
    flm = rules["filling_lab_match"]
    ctol = flm["component_tolerance_pp"]
    for part_name, mix in parts.items():
        if not any(lbl in part_name for lbl in flm["part_labels"]):
            continue
        if not isinstance(mix, dict):
            continue
        for component, declared in mix.items():
            if lab is None:
                warnings.append(f"[시험성적서 미제출:{flm['id']}] '{part_name}/{component}' 대조 불가(--lab 미지정)")
                continue
            key = (sku, part_name, component)
            measured = lab.get(key)
            if measured is None:
                violations.append(
                    f"[시험성적서 미제출:{flm['id']}] '{part_name}/{component}' 성적서 값 없음 "
                    f"-> 교정: 공인기관 시험성적서 제출 필요"
                )
            elif abs(declared - measured) > ctol:
                violations.append(
                    f"[충전재 불일치:{flm['id']}] '{part_name}/{component}' 표시 {declared:g}% vs 시험 {measured:g}% "
                    f"(오차 {abs(declared - measured):g}%p > {ctol}%p) -> 교정: 표시값을 시험값 {measured:g}%로 정정"
                )
    return violations, warnings


def build_report(products, rules, lab):
    results = []
    for p in products:
        violations, warnings = check_product(p, rules, lab)
        results.append({
            "sku": p.get("sku", "?"),
            "name": p.get("name", ""),
            "status": "FAIL" if violations else "PASS",
            "violations": violations,
            "warnings": warnings,
        })
    return results


def print_text(results):
    failed = 0
    for r in results:
        print(f"{r['status']}  {r['sku']}  {r['name']}")
        for v in r["violations"]:
            print(f"      - {v}")
        for w in r["warnings"]:
            print(f"      ~ (경고) {w}")
        if r["status"] == "FAIL":
            failed += 1
    print(f"\n결과: 상품 {len(results)}개 중 위반 {failed}개")
    return failed


def main(argv=None):
    ap = argparse.ArgumentParser(description="무신사 섬유 혼용률·충전재 표시 검증기")
    ap.add_argument("products", help="상품 카탈로그 JSON 경로 ({\"products\":[...]})")
    ap.add_argument("--lab", help="시험성적서 CSV 경로(sku,part,component,measured_pct)")
    ap.add_argument("--rules", default=DEFAULT_RULES, help="규칙 JSON 경로(기본: references/textile_rules.json)")
    ap.add_argument("--json", action="store_true", help="JSON 리포트로 출력")
    args = ap.parse_args(argv)

    try:
        rules = load_json(args.rules)["rules"]
        data = load_json(args.products)
        products = data["products"] if isinstance(data, dict) else data
        lab = load_lab(args.lab) if args.lab else None
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[사용오류] 입력을 읽지 못했습니다: {exc}", file=sys.stderr)
        return 2

    results = build_report(products, rules, lab)
    failed = sum(1 for r in results if r["status"] == "FAIL")

    if args.json:
        print(json.dumps({
            "tool": "verify-textile-labels",
            "total": len(results),
            "failed": failed,
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        print_text(results)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
