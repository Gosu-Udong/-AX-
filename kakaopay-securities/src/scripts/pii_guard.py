#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pii-guard — 코드·로그·설정에서 개인정보(PII) 평문 노출 정적 검사.

개인정보 보호법·신용정보법의 고유식별정보 암호화·마스킹 의무를 근거로
주민등록번호·카드번호(Luhn 검증)·계좌번호·휴대전화·이메일 패턴을 검출하고,
같은 라인의 로그/네트워크 sink 및 제3자·국외 호스트 컨텍스트를 결합해 노출 위험을 승급한다.
(카카오페이 알리페이 개인정보 국외이전 제재 유형에 대응.)

출력 시 원문 PII는 마스킹하여 표기(실제 값 미출력).
exit code: 0=통과, 1=위반, 2=사용오류.
"""
import argparse
import json
import os
import re
import sys

DEFAULT_EXTS = [".py", ".js", ".ts", ".java", ".go", ".rb", ".php", ".kt",
                ".log", ".txt", ".json", ".env", ".yml", ".yaml", ".properties",
                ".sql", ".csv", ".xml", ".ini", ".conf"]
MASKED_RX = re.compile(r"[0-9]{2,}[-\s]?[*Xx•●○]{2,}|[*Xx•●○]{2,}[-\s]?[0-9]{2,}")


def load_rules(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def luhn_ok(number):
    digits = [int(c) for c in re.sub(r"\D", "", number)]
    if len(digits) < 13:
        return False
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def mask_preview(s):
    core = re.sub(r"\s", "", s)
    if len(core) <= 4:
        return core[0] + "*" * (len(core) - 1) if core else ""
    return core[:2] + "*" * (len(core) - 4) + core[-2:]


def discover_files(paths, exts):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for root, _d, names in os.walk(p):
                for name in sorted(names):
                    if os.path.splitext(name)[1].lower() in exts:
                        out.append(os.path.join(root, name))
    return sorted(set(out))


def scan_file(path, rules):
    findings = []
    masked_count = 0
    sinks = rules["sinks"]
    third = rules["third_party_hosts"]
    patterns = rules["patterns"]
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        masked_count += len(MASKED_RX.findall(line))
        # sink / 제3자 컨텍스트 (라인 단위)
        sink_hit = next((s for s in sinks if re.search(s["pattern"], line)), None)
        third_hit = next((t for t in third if re.search(t["pattern"], line, re.IGNORECASE)), None)

        # 후보 수집 (priority = patterns 목록의 순서: 앞쪽이 더 구체적/우선)
        candidates = []
        for prio, rule in enumerate(patterns):
            for m in re.finditer(rule["pattern"], line):
                value = m.group(0)
                if rule.get("luhn") and not luhn_ok(value):
                    continue  # Luhn 실패 → 카드번호 아님(오탐 제거)
                min_digits = rule.get("min_digits")
                if min_digits and len(re.sub(r"\D", "", value)) < min_digits:
                    continue  # 자릿수 미달 → 날짜(YYYY-MM-DD) 등 오탐 제거
                candidates.append((prio, m.start(), m.end(), rule, value))

        # 겹치는 매치는 우선순위 높은(prio 작은) 것만 채택해 이중 계수 방지
        candidates.sort(key=lambda c: (c[0], c[1]))
        claimed = []
        for prio, start, end, rule, value in candidates:
            if any(not (end <= cs or start >= ce) for cs, ce in claimed):
                continue
            claimed.append((start, end))
            severity, context = "medium", "평문 저장/노출"
            if third_hit:
                severity = "critical"
                context = third_hit["kind"] + " (" + (sink_hit["kind"] if sink_hit else "외부 호스트") + ")"
            elif sink_hit:
                severity = "high"
                context = sink_hit["kind"]
            findings.append({
                "severity": severity, "file": path, "line": lineno,
                "type": rule["type"], "rule_id": rule["id"],
                "masked_value": mask_preview(value), "context": context,
                "law": rule["law"], "source_url": rule["source_url"],
            })
    return findings, masked_count


SEV_ORDER = {"critical": 0, "high": 1, "medium": 2}


def print_report(files, findings, masked_total):
    print("[pii-guard] 개인정보(PII) 평문 노출 정적 검사")
    print("근거: 개인정보 보호법·신용정보법(고유식별정보 암호화·마스킹 의무)\n")
    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)
    for path in files:
        fs = by_file.get(path, [])
        if not fs:
            print("PASS  %s" % path)
            continue
        print("%s" % path)
        for f in sorted(fs, key=lambda x: (x["line"], SEV_ORDER[x["severity"]])):
            print("  FAIL L%-4d [%s] %s = %s  (%s)"
                  % (f["line"], f["severity"].upper(), f["type"], f["masked_value"], f["context"]))
            print("       └ 근거: %s" % f["law"])
            print("         출처: %s" % f["source_url"])
    crit = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")
    fail = len(findings) > 0
    print("\n요약: 파일 %d개 · PII 노출 %d건(critical %d · high %d) · 마스킹 처리 %d건 → %s (exit %d)"
          % (len(files), len(findings), crit, high, masked_total, "FAIL" if fail else "PASS", 1 if fail else 0))
    return fail


def main():
    ap = argparse.ArgumentParser(description="코드·로그 PII 평문 노출 정적 검사")
    ap.add_argument("paths", nargs="+", help="검사할 파일 또는 디렉토리")
    ap.add_argument("--rules", default=None, help="룰 JSON 경로(기본: references/pii_rules.json)")
    ap.add_argument("--ext", action="append", help="추가 확장자")
    ap.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = ap.parse_args()

    rules_path = args.rules or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "references", "pii_rules.json")
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
    masked_total = 0
    for path in files:
        fs, masked = scan_file(path, rules)
        all_findings.extend(fs)
        masked_total += masked

    if args.json:
        fail = len(all_findings) > 0
        print(json.dumps({
            "skill": "pii-guard",
            "files_scanned": len(files),
            "exposures": len(all_findings),
            "masked_ok": masked_total,
            "status": "FAIL" if fail else "PASS",
            "findings": all_findings,
        }, ensure_ascii=False, indent=2))
        return 1 if fail else 0

    fail = print_report(files, all_findings, masked_total)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
