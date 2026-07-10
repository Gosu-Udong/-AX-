#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assertive-claims-check — AI 챗봇 응답 단정표현 검출 + 근거(grounding) 검증.

자본시장과 금융투자업에 관한 법률 제49조(부당권유의 금지)를 근거로 AI 상담 응답에서
'무조건/반드시 수익/확실히/원금 보장' 등 단정적 판단 표현을 검출하고,
각 응답 문장이 로컬 지식베이스(약관·FAQ 텍스트)에 근거하는지 토큰 겹침(접두 매칭 포함)으로
결정론적으로 판정한다(임베딩·외부 API 미사용). 근거 문장은 파일:라인으로 인용.

exit code: 0=통과, 1=위반(단정표현 또는 미근거 문장), 2=사용오류.
"""
import argparse
import json
import os
import re
import sys

SENT_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")
TOKEN_RX = re.compile(r"[가-힣A-Za-z0-9]+")


def load_rules(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def tokenize(text, stopwords):
    toks = [t.lower() for t in TOKEN_RX.findall(text)]
    return [t for t in toks if t not in stopwords and len(t) >= 2]


def token_match(a, b, prefix_min):
    """두 토큰이 동일하거나, 접두사가 일치(조사·어미 차이 흡수)하면 매칭."""
    if a == b:
        return True
    if len(a) >= prefix_min and len(b) >= prefix_min:
        if a.startswith(b[:prefix_min]) or b.startswith(a[:prefix_min]):
            return True
    return False


def build_kb_index(kb_paths, stopwords):
    """지식베이스: (파일, 라인번호, 원문, 토큰집합) 목록."""
    index = []
    files = []
    for p in kb_paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, _d, names in os.walk(p):
                for name in sorted(names):
                    if os.path.splitext(name)[1].lower() in (".txt", ".md", ".json"):
                        files.append(os.path.join(root, name))
    for path in sorted(set(files)):
        for lineno, raw in enumerate(read_text(path).splitlines(), 1):
            line = raw.strip()
            if not line:
                continue
            toks = set(tokenize(line, stopwords))
            if toks:
                index.append({"file": path, "line": lineno, "text": line, "tokens": toks})
    return index, sorted(set(files))


def best_grounding(sent_tokens, index, prefix_min):
    """응답 문장 토큰과 가장 잘 겹치는 KB 라인 + 점수(문장 토큰 중 근거된 비율)."""
    best = None
    best_score = 0.0
    if not sent_tokens:
        return None, 0.0
    for entry in index:
        matched = 0
        for s in sent_tokens:
            if any(token_match(s, k, prefix_min) for k in entry["tokens"]):
                matched += 1
        score = matched / len(sent_tokens)
        if score > best_score:
            best_score = score
            best = entry
    return best, best_score


def split_sentences(text):
    out = []
    for chunk in SENT_SPLIT.split(text):
        s = chunk.strip()
        if s and not s.startswith("#"):
            out.append(s)
    return out


def check_answer(path, rules, index, threshold):
    stopwords = set(rules["grounding"].get("stopwords", []))
    prefix_min = rules["grounding"].get("token_prefix_min_len", 3)
    findings = []
    text = read_text(path)
    lines = text.splitlines()
    for sent in split_sentences(text):
        # 원문 라인 번호(참고용)
        lineno = 1
        for i, ln in enumerate(lines, 1):
            if sent[:20] in ln:
                lineno = i
                break
        # 1) 단정적 표현
        assertive_hits = []
        for rule in rules["assertive_expressions"]:
            m = re.search(rule["pattern"], sent)
            if m:
                assertive_hits.append((m.group(0), rule))
        # 2) 근거 검증
        stoks = tokenize(sent, stopwords)
        entry, score = best_grounding(stoks, index, prefix_min)
        grounded = score >= threshold
        rec = {
            "file": path, "line": lineno, "sentence": sent,
            "grounded": grounded, "grounding_score": round(score, 3),
            "evidence": None, "assertive": [],
        }
        if grounded and entry is not None:
            rec["evidence"] = {"file": entry["file"], "line": entry["line"], "text": entry["text"]}
        for match_text, rule in assertive_hits:
            rec["assertive"].append({
                "match": match_text, "rule_id": rule["id"],
                "law": rule["law"], "source_url": rule["source_url"], "message": rule["message"],
            })
        findings.append(rec)
    return findings


def discover_answer_files(paths):
    out = []
    for p in paths:
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            for root, _d, names in os.walk(p):
                for name in sorted(names):
                    if os.path.splitext(name)[1].lower() in (".txt", ".md"):
                        out.append(os.path.join(root, name))
    return sorted(set(out))


def print_report(records, kb_files, threshold):
    print("[assertive-claims-check] AI 응답 단정표현 + 근거 검증")
    print("근거: 자본시장과 금융투자업에 관한 법률 제49조(부당권유의 금지)")
    print("지식베이스: %s (임계값 %.2f)\n" % (", ".join(kb_files) if kb_files else "(없음)", threshold))
    v_assertive = 0
    v_ungrounded = 0
    for r in records:
        flags = []
        if r["assertive"]:
            flags.append("단정표현")
        if not r["grounded"]:
            flags.append("미근거")
        tag = "FAIL" if flags else "PASS"
        print("%-4s [%s] %s" % (tag, "/".join(flags) if flags else "OK", r["sentence"]))
        for a in r["assertive"]:
            v_assertive += 1
            print("      - 단정표현 '%s' [%s] %s" % (a["match"], a["rule_id"], a["law"]))
            print("        출처: %s" % a["source_url"])
        if r["grounded"]:
            ev = r["evidence"]
            print("      - 근거 확인(score=%.2f): %s:%d  \"%s\"" % (r["grounding_score"], ev["file"], ev["line"], ev["text"][:50]))
        else:
            v_ungrounded += 1
            print("      - 근거 없음(score=%.2f) → 지식베이스 미확인 주장 (설명의무·AI 가이드라인 위반 소지)" % r["grounding_score"])
    fail = (v_assertive + v_ungrounded) > 0
    print("\n요약: 문장 %d개 · 단정표현 %d건 · 미근거 %d건 → %s (exit %d)"
          % (len(records), v_assertive, v_ungrounded, "FAIL" if fail else "PASS", 1 if fail else 0))
    return fail


def main():
    ap = argparse.ArgumentParser(description="자본시장법 §49 단정표현 검출 + 근거 검증")
    ap.add_argument("--answer", "-a", nargs="+", required=True, help="AI 응답 파일/디렉토리")
    ap.add_argument("--kb", "-k", nargs="+", required=True, help="지식베이스 디렉토리/파일(약관·FAQ)")
    ap.add_argument("--rules", default=None, help="룰 JSON 경로(기본: references/assertive_rules.json)")
    ap.add_argument("--threshold", type=float, default=None, help="근거 판정 임계값(기본 0.5)")
    ap.add_argument("--json", action="store_true", help="JSON 형식 출력")
    args = ap.parse_args()

    rules_path = args.rules or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            "..", "references", "assertive_rules.json")
    try:
        rules = load_rules(rules_path)
    except (OSError, json.JSONDecodeError) as e:
        print("룰 로드 실패: %s" % e, file=sys.stderr)
        return 2

    threshold = args.threshold if args.threshold is not None else rules["grounding"].get("default_threshold", 0.5)
    stopwords = set(rules["grounding"].get("stopwords", []))

    index, kb_files = build_kb_index(args.kb, stopwords)
    if not index:
        print("지식베이스가 비어있음: %s" % ", ".join(args.kb), file=sys.stderr)
        return 2

    answer_files = discover_answer_files(args.answer)
    if not answer_files:
        print("응답 파일 없음: %s" % ", ".join(args.answer), file=sys.stderr)
        return 2

    records = []
    for path in answer_files:
        records.extend(check_answer(path, rules, index, threshold))

    if args.json:
        v_assertive = sum(len(r["assertive"]) for r in records)
        v_ungrounded = sum(1 for r in records if not r["grounded"])
        fail = (v_assertive + v_ungrounded) > 0
        print(json.dumps({
            "skill": "assertive-claims-check",
            "kb_files": kb_files, "threshold": threshold,
            "sentences": len(records),
            "assertive_hits": v_assertive, "ungrounded": v_ungrounded,
            "status": "FAIL" if fail else "PASS",
            "records": records,
        }, ensure_ascii=False, indent=2))
        return 1 if fail else 0

    fail = print_report(records, kb_files, threshold)
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
