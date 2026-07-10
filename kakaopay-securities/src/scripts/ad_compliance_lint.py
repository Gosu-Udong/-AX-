#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ad-compliance-lint — 카카오페이증권 마케팅/UI 문구 금융광고 규제 린터.

금융소비자보호법 제22조(광고 관련 준수사항) 및 금융투자협회 광고규정을 근거로
마케팅/UI 문구 리소스(JSON·strings·md·txt 등)에서 다음을 결정론적으로 검출한다.
  1) 원금 보장·확정 수익·손실 없음·무조건 등 오인 소지 금지 표현
  2) 투자성 광고의 투자위험 필수 고지 누락
  3) 협회 광고규정 표시요건 체크리스트(운용실적 면책·심사필 표기·비용 안내)

표준 라이브러리만 사용. 판정 근거(조문/출처 URL)는 references/ad_rules.json에서 로드.
exit code: 0=통과, 1=위반, 2=사용오류.
"""
import argparse
import json
import os
import re
import sys

DEFAULT_EXTS = [".json", ".strings", ".md", ".txt", ".properties", ".html", ".xml", ".yaml", ".yml"]
TEXT_KEYS = ["text", "message", "copy", "body", "title", "desc", "description", "content", "label"]


def load_rules(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def find_line(lines, needle):
    """raw 텍스트 라인 목록에서 needle(문구 앞부분)이 처음 나타나는 1-based 라인 번호."""
    probe = needle.strip()[:24]
    if not probe:
        return 1
    for i, line in enumerate(lines, 1):
        if probe in line:
            return i
    return 1


def discover_files(paths, exts):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    if os.path.splitext(name)[1].lower() in exts:
                        out.append(os.path.join(root, name))
    return sorted(set(out))


def extract_units(path, text, lines):
    """검사 단위(unit) 목록: (label, unit_text, is_investment_ad|None, line_no)."""
    units = []
    if path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        records = None
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
                    records = v
                    break
        if records is not None:
            for idx, rec in enumerate(records):
                if not isinstance(rec, dict):
                    continue
                tv = next((rec[k] for k in TEXT_KEYS if k in rec and isinstance(rec[k], str)), None)
                if tv is None:
                    continue
                label = str(rec.get("id", "item[%d]" % idx))
                inv = rec.get("is_investment_ad", None)
                units.append((label, tv, inv, find_line(lines, tv)))
            if units:
                return units
    # fallback: 파일 전체를 하나의 단위로
    units.append((os.path.basename(path), text, None, 1))
    return units


def is_investment(text, triggers):
    return any(re.search(pat, text) for pat in triggers)


def lint_file(path, rules):
    findings = []
    text = read_text(path)
    lines = text.splitlines()

    # 1) 금지 표현 — 라인 단위 스캔
    for rule in rules["banned_expressions"]:
        rx = re.compile(rule["pattern"])
        for lineno, line in enumerate(lines, 1):
            for m in rx.finditer(line):
                findings.append({
                    "severity": "violation", "file": path, "line": lineno,
                    "kind": "금지표현", "rule_id": rule["id"], "match": m.group(0),
                    "category": rule["category"], "law": rule["law"],
                    "source_url": rule["source_url"], "message": rule["message"],
                })

    # 2) 위험고지 누락 + 3) 체크리스트 — 단위 기준
    triggers = rules["investment_ad_triggers"]
    disc_rules = rules["required_disclosures"]
    for label, utext, inv, lineno in extract_units(path, text, lines):
        investment = inv if inv is not None else is_investment(utext, triggers)
        if not investment:
            continue
        has_disc = any(re.search(d["pattern"], utext) for d in disc_rules)
        if not has_disc:
            d = disc_rules[0]
            findings.append({
                "severity": "violation", "file": path, "line": lineno,
                "kind": "위험고지 누락", "rule_id": d["id"], "match": label,
                "category": "필수 고지 누락", "law": d["law"],
                "source_url": d["source_url"], "message": d["message"],
            })
        for c in rules["display_checklist"]:
            if not re.search(c["trigger_pattern"], utext):
                continue
            if re.search(c["present_pattern"], utext):
                continue
            findings.append({
                "severity": "warning", "file": path, "line": lineno,
                "kind": "표시요건 미충족", "rule_id": c["id"], "match": label,
                "category": c["requirement"], "law": c["law"],
                "source_url": c["source_url"], "message": "협회 광고규정 표시요건 미확인: " + c["requirement"],
            })
    return findings


def print_report(files, findings, strict):
    print("[ad-compliance-lint] 카카오페이증권 광고 문구 컴플라이언스 린트")
    print("근거: 금융소비자보호에 관한 법률 제22조 / 금융투자협회 광고규정\n")
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)
    for path in files:
        fs = by_file.get(path, [])
        if not fs:
            print("PASS  %s" % path)
            continue
        print("%s" % path)
        for f in sorted(fs, key=lambda x: (x["line"], x["rule_id"])):
            tag = "FAIL" if f["severity"] == "violation" else "WARN"
            print("  %-4s L%-4d [%s] %s: '%s'" % (tag, f["line"], f["rule_id"], f["kind"], f["match"]))
            print("       └ %s | 근거: %s" % (f["message"], f["law"]))
            print("         출처: %s" % f["source_url"])
    v = sum(1 for f in findings if f["severity"] == "violation")
    w = sum(1 for f in findings if f["severity"] == "warning")
    fail = v > 0 or (strict and w > 0)
    print("\n요약: 파일 %d개 · 위반 %d건 · 경고 %d건 → %s (exit %d)"
          % (len(files), v, w, "FAIL" if fail else "PASS", 1 if fail else 0))
    return fail


def main():
    ap = argparse.ArgumentParser(description="금소법 §22 광고 문구 컴플라이언스 린터")
    ap.add_argument("paths", nargs="+", help="검사할 파일 또는 디렉토리")
    ap.add_argument("--rules", default=None, help="룰 JSON 경로(기본: references/ad_rules.json)")
    ap.add_argument("--ext", action="append", help="추가 확장자(예: --ext .csv)")
    ap.add_argument("--strict", action="store_true", help="경고도 실패로 처리")
    ap.add_argument("--json", action="store_true", help="JSON 형식으로 출력")
    args = ap.parse_args()

    rules_path = args.rules or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "references", "ad_rules.json")
    try:
        rules = load_rules(rules_path)
    except (OSError, json.JSONDecodeError) as e:
        print("룰 로드 실패: %s" % e, file=sys.stderr)
        return 2

    exts = list(DEFAULT_EXTS) + (args.ext or [])
    files = discover_files(args.paths, exts)
    if not files:
        print("검사 대상 파일 없음: %s" % ", ".join(args.paths), file=sys.stderr)
        return 2

    all_findings = []
    for path in files:
        all_findings.extend(lint_file(path, rules))

    if args.json:
        v = sum(1 for f in all_findings if f["severity"] == "violation")
        w = sum(1 for f in all_findings if f["severity"] == "warning")
        fail = v > 0 or (args.strict and w > 0)
        print(json.dumps({
            "skill": "ad-compliance-lint",
            "files_scanned": len(files),
            "violations": v, "warnings": w,
            "status": "FAIL" if fail else "PASS",
            "findings": all_findings,
        }, ensure_ascii=False, indent=2))
        return 1 if fail else 0

    fail = print_report(files, all_findings, args.strict)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
