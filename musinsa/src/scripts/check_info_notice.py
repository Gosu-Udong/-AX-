#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check-info-notice — 전자상거래 상품정보제공고시 필수항목 컴플라이언스 체커.

「전자상거래 등에서의 상품 등의 정보제공에 관한 고시」 별표의 품목별 필수항목이
(1) 누락되었는지, (2) 공란인지, (3) '상세페이지 참조' 류 회피표기로 채워졌는지를
결정론적으로 검출한다. (references/info_notice_schema.json 근거)

exit code: 0=전 상품 통과, 1=위반 존재, 2=사용 오류.
입력: 리스팅 JSON ({"listings":[{"sku","name","category","info":{...}}]}).
표준 라이브러리만 사용.
"""
import argparse
import json
import os
import sys

DEFAULT_SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "info_notice_schema.json")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def is_detail_ref(value, phrases):
    v = value.replace(" ", "")
    return any(p.replace(" ", "") in v for p in phrases)


def check_listing(listing, schema, category_override):
    violations = []
    category = category_override or listing.get("category", "")
    cat_def = schema["categories"].get(category)
    if cat_def is None:
        return [f"[카테고리 미지원] '{category}' 카테고리 스키마 없음 (지원: {', '.join(schema['categories'])})"]

    info = listing.get("info", {}) or {}
    phrases = schema["detail_ref_phrases"]
    for field in cat_def["required_fields"]:
        key, label = field["key"], field["label"]
        raw = info.get(key)
        if raw is None:
            violations.append(f"[누락] '{label}'({key}) 항목 자체가 없음")
            continue
        value = str(raw).strip()
        if value == "":
            violations.append(f"[공란] '{label}'({key}) 값이 비어 있음")
            continue
        if not field.get("allow_detail_ref", False) and is_detail_ref(value, phrases):
            violations.append(
                f"[상세참조 회피] '{label}'({key}) = '{value}' -> 이 항목은 상세페이지 참조로 갈음 불가, 실제 값 표기 필요"
            )
    return violations


def build_report(listings, schema, category_override):
    results = []
    for l in listings:
        violations = check_listing(l, schema, category_override)
        results.append({
            "sku": l.get("sku", "?"),
            "name": l.get("name", ""),
            "category": category_override or l.get("category", ""),
            "status": "FAIL" if violations else "PASS",
            "violations": violations,
        })
    return results


def print_text(results):
    failed = 0
    for r in results:
        print(f"{r['status']}  {r['sku']}  [{r['category']}]  {r['name']}")
        for v in r["violations"]:
            print(f"      - {v}")
        if r["status"] == "FAIL":
            failed += 1
    print(f"\n결과: 리스팅 {len(results)}개 중 위반 {failed}개")
    return failed


def main(argv=None):
    ap = argparse.ArgumentParser(description="전자상거래 상품정보제공고시 필수항목 체커")
    ap.add_argument("listings", help="리스팅 JSON 경로 ({\"listings\":[...]})")
    ap.add_argument("--category", help="모든 리스팅에 적용할 카테고리(예: 의류, 화장품)")
    ap.add_argument("--schema", default=DEFAULT_SCHEMA, help="스키마 JSON 경로(기본: references/info_notice_schema.json)")
    ap.add_argument("--json", action="store_true", help="JSON 리포트로 출력")
    args = ap.parse_args(argv)

    try:
        schema = load_json(args.schema)
        data = load_json(args.listings)
        listings = data["listings"] if isinstance(data, dict) else data
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[사용오류] 입력을 읽지 못했습니다: {exc}", file=sys.stderr)
        return 2

    results = build_report(listings, schema, args.category)
    failed = sum(1 for r in results if r["status"] == "FAIL")

    if args.json:
        print(json.dumps({
            "tool": "check-info-notice",
            "total": len(results),
            "failed": failed,
            "results": results,
        }, ensure_ascii=False, indent=2))
    else:
        print_text(results)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
