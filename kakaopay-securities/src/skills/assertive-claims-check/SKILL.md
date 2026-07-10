---
name: assertive-claims-check
description: >-
  AI 챗봇 응답·상담 스크립트를 자본시장법 제49조(부당권유 금지) 기준으로 검사한다. 사용자가 AI/챗봇
  답변의 '무조건·반드시 수익·확실히·원금 보장' 등 단정적 판단 표현을 검출하거나, 응답이 실제 사내 근거
  문서(약관·FAQ 지식베이스)에 근거하는지(grounding/환각 여부) 검증하고 근거 파일을 인용하도록 요청할 때
  트리거한다. 임베딩·외부 API 없이 로컬 지식베이스와 토큰 겹침으로 결정론적으로 판정한다. 마케팅 광고
  문구(ad-compliance-lint)나 개인정보(pii-guard)에는 사용하지 않는다.
---

# assertive-claims-check — AI 답변 단정표현 + 근거(grounding) 검증

## 언제 쓰나 (사용 시나리오)
- 금융 챗봇/상담 AI가 생성한 응답을 **고객에게 노출하기 전** 자동 검수할 때.
- 응답이 사내 약관·FAQ에 **근거하지 않는 주장(환각)**을 하거나, **단정적 판단**으로 부당권유 리스크를 만드는지 확인할 때.
- 회사가 지향하는 "정확성과 근거가 검증되는 AI"를 릴리스 파이프라인에서 결정론적으로 강제하고 싶을 때.

## 무엇을 검사하나
1. **단정적 표현 검출**(자본시장법 §49②): 불확실한 사항에 단정적 판단을 제공하거나 확실하다고 오인시키는 표현(무조건, 반드시 수익, 확실히, 원금 보장, 100%/절대 등).
2. **근거 검증(grounding)**: 응답을 문장 단위로 분해 → 각 문장 토큰을 로컬 지식베이스(약관·FAQ 텍스트) 라인과 **겹침 매칭**(조사·어미 차이를 흡수하는 접두 매칭 포함)해 근거 점수를 계산. 임계값(기본 0.5) 미만이면 **미근거(ungrounded)**로 플래그하고, 근거가 있으면 **근거 파일:라인**을 인용한다. 임베딩·외부 API를 쓰지 않아 100% 재현 가능.

## 실행 명령
```bash
# 응답 디렉토리 vs 지식베이스 디렉토리
python3 scripts/assertive_claims_check.py \
  --answer samples/ai_responses --kb samples/knowledge_base

# 임계값 조정(엄격하게) + JSON 출력
python3 scripts/assertive_claims_check.py \
  --answer samples/ai_responses --kb samples/knowledge_base --threshold 0.6 --json
```

## 입력 형식
- `--answer`: AI 응답 파일/디렉토리(`.txt .md`). 한 문장 = 한 판정 단위(문장 종결부호/줄바꿈으로 분리, `#`로 시작하는 줄은 주석으로 무시).
- `--kb`: 지식베이스 디렉토리/파일(`.txt .md .json`). **한 사실을 한 줄**로 작성하면 근거 인용 정밀도가 높다(약관·FAQ 발췌 스타일).

## 출력 해석
- 문장별 `PASS`/`FAIL`. FAIL 사유는 `단정표현`, `미근거` 또는 둘 다.
- 근거 있는 문장: `근거 확인(score=…): <파일>:<라인> "<원문>"`.
- 미근거 문장: `근거 없음(score=…) → 지식베이스 미확인 주장`.
- 단정표현 또는 미근거가 1건이라도 있으면 **exit code 1**, 없으면 exit 0.

## 근거 데이터 / references
- 룰·조문·출처·grounding 파라미터: `references/assertive_rules.json` (assertive_expressions, grounding.default_threshold/stopwords).
- 핵심 조문: 자본시장과 금융투자업에 관한 법률 제49조(부당권유의 금지), 금융위원회 금융분야 AI 가이드라인(정확성·근거).
