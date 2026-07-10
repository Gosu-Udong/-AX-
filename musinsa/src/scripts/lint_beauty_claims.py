#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lint-beauty-claims — 화장품법 제13조 부당 표시·광고 표현 사전 기반 스캐너.

상품명·상세페이지 텍스트를 스캔하여 의약품 오인/기능성 오인/실증 필요/최상급 표현을
결정론적으로 검출하고, 각 위반 후보에 근거 조문·URL·교정 제안을 매핑한다.
(references/beauty_banned_terms.json 근거)

exit code: 0=위반 없음, 1=위반 존재, 2=사용 오류.
입력: .md/.txt 텍스트 파일(문서 전체 스캔) 또는 .json({"listings":[{"sku","name","text"}]}).
표준 라이브러리만 사용.
"""
import argparse
import json
import os
import sys

DEFAULT_TERMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "beauty_banned_terms.json")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def scan_text(text, categories):
    """텍스트에서 위반 후보 표현을 라인 단위로 검출. hits 리스트 반환."""
    hits = []
    lines = text.splitlines() or [text]
    for lineno, line in enumerate(lines, start=1):
        for cat in categories:
            for term in cat["terms"]:
                start = 0
                while True:
                    idx = line.find(term, start)
                    if idx == -1:
                        break
                    hits.append({
                        "line": lineno,
                        "term": term,
                        "category": cat["label"],
                        "category_id": cat["id"],
                        "severity": cat["severity"],
                        "law": cat["law"],
                        "law_url": cat["law_url"],
                        "advice": cat["advice"],
                        "context": line.strip()[:80],
                    })
                    start = idx + len(term)
    return hits


def print_text(units):
    total_hits = 0
    for unit in units:
        header = unit["label"]
        hits = unit["hits"]
        status = "FAIL" if hits else "PASS"
        print(f"{status}  {header}  (위반 후보 {len(hits)}건)")
        for h in hits:
            print(f"      - L{h['line']} [{h['category']}] '{h['term']}'  근거: {h['law']}")
            print(f"        교정: {h['advice']}")
            print(f"        조문 URL: {h['law_url']}")
        total_hits += len(hits)
    fails = sum(1 for u in units if u["hits"])
    print(f"\n결과: 대상 {len(units)}건 중 위반 {fails}건 (표현 {total_hits}개)")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description="화장품 부당 표시·광고 표현 린터")
    ap.add_argument("input", help="스캔할 .md/.txt 파일 또는 .json 리스팅 파일")
    ap.add_argument("--terms", default=DEFAULT_TERMS, help="표현 사전 JSON(기본: references/beauty_banned_terms.json)")
    ap.add_argument("--json", action="store_true", help="JSON 리포트로 출력")
    args = ap.parse_args(argv)

    try:
        categories = load_json(args.terms)["categories"]
        if args.input.lower().endswith(".json"):
            data = load_json(args.input)
            listings = data["listings"] if isinstance(data, dict) else data
            units = []
            for l in listings:
                text = "\n".join(str(x) for x in [l.get("name", ""), l.get("text", "")])
                units.append({
                    "id": l.get("sku", "?"),
                    "label": f"{l.get('sku', '?')}  {l.get('name', '')}",
                    "hits": scan_text(text, categories),
                })
        else:
            with open(args.input, encoding="utf-8") as fh:
                text = fh.read()
            units = [{
                "id": os.path.basename(args.input),
                "label": os.path.basename(args.input),
                "hits": scan_text(text, categories),
            }]
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[사용오류] 입력을 읽지 못했습니다: {exc}", file=sys.stderr)
        return 2

    fails = sum(1 for u in units if u["hits"])

    if args.json:
        print(json.dumps({
            "tool": "lint-beauty-claims",
            "total": len(units),
            "failed": fails,
            "results": units,
        }, ensure_ascii=False, indent=2))
    else:
        print_text(units)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
