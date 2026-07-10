# myrealtrip-traveler-guard — 여행상품 소비자보호 릴리스 린트 스위트

> AX 인재전쟁 예선 제출물 · 담당 기업: 마이리얼트립(MyRealTrip)
> Codex 플러그인 `myrealtrip-traveler-guard` — 여행상품 **약관·가격 표시의 소비자보호 기준 위반**을 릴리스 전에 결정론적으로 검사한다.

---

## 1. 문제 정의 (공개 자료 기반)

여행 플랫폼은 매일 수많은 상품 약관·가격을 노출하지만, 그중 일부는 **법정 소비자보호 기준을 초과**하거나 **가격을 오인시키는 다크패턴**을 담는다. 수기 검수로는 대규모 카탈로그를 걸러낼 수 없어 분쟁·규제 리스크가 반복된다. 실제 공개 근거:

- **취소·환불 위약금 상한 초과 / 환불 분쟁**: 한국소비자원 집계상 숙박서비스 관련 분쟁 중 '계약해제·해지'가 **최근 3년(2023~2025) 누적 4,079건(전체의 65.5%)**, **2024 단년 1,919건**으로 최다다. 온라인 플랫폼 경유 피해가 다수를 차지한다. (출처: 한국소비자원 웹진 https://www.kca.go.kr/webzine/board/view?menuId=MENU00307&linkId=334 , https://www.ebn.co.kr/news/articleView.html?idxno=1713234 )
- 마이리얼트립과 관련해서는, 소비자가 숙소 예약(712,897원)을 실수로 취소한 뒤 소비자분쟁조정위원회의 전액환불 결정을 사업자가 수용하지 않자 대표를 형사고소했다는 **소송으로 비화한 분쟁 사례가 한 매체에 보도**됐다. (단일 원출처, 고소의 결과·판결은 확인되지 않음. 출처: 트래블아이 https://traveli.net/news/view.php?no=10700 ) — 조정결정 불수용 자체는 법적으로 허용된 행위이므로 위법으로 단정하지 않으며, **견고한 판정 근거는 공정위 「소비자분쟁해결기준」 대비 위약금 상한의 정량 초과**다.
- 취소·환불 기준은 **현재진행형 규제 이슈**다: 공정위는 2024.12 「소비자분쟁해결기준」을 개정해 **숙박 예약 후 24시간 내 취소 시 위약금 면제**를 도입했다. (출처: https://news.nate.com/view/20241227n13342 )
- **가격표시 다크패턴**: 한국소비자원은 2024.03 조사에서 해외 테마파크 입장권 44개 상품 중 **16개(36.4%)** 가 대표가격을 아동가/밀쿠폰가로 표시한 '숨겨진 정보' 다크패턴이라고 지적했고, 여기에 **마이리얼트립**이 포함됐다(마이리얼트립은 2023.12 개선 완료, 트리플·인터파크투어도 개선). 전자상거래법 다크패턴 규제는 상시 유효하다. (출처: 경향신문 https://www.khan.co.kr/article/202403121354001 , 시사저널 https://www.sisajournal.com/news/articleView.html?idxno=285321 , 공정위 규제 https://news.seoul.go.kr/economy/archives/566114 )

기준 원출처:
- 「소비자분쟁해결기준」(국가법령정보센터) https://www.law.go.kr/행정규칙/소비자분쟁해결기준
- 국외여행 취소 위약금(찾기쉬운 생활법령) https://easylaw.go.kr/CSP/CnpClsMain.laf?ccfNo=2&cciNo=3&cnpClsNo=3&csmSeq=894&popMenu=ov
- 한국여행업협회 여행정보센터 http://www.tourinfo.or.kr/v2/info/resolution_02.asp

> 사실관계 주의: 위 대표 고소 사건은 단일 매체 보도이며 결과 미확인이다. 소비자원 통계 수치는 KCA 실제 통계이나 '최근 3년 누적/2024 단년'을 구분해 표기했다. 마이리얼트립의 다크패턴 지적은 '2023.12 개선완료'를 포함해 정직하게 서술한다.

## 2. 해결책 개요 — 두 개의 결정론 린터 + 통합 리포트

`myrealtrip-traveler-guard`는 **네트워크·외부 패키지 없이 python3 표준 라이브러리만으로** 동작하는 릴리스 게이트다. 심사자는 API 키 없이 로컬 샘플로 완전 재현할 수 있다.

| 스킬 | 검사 대상 | 근거 |
|---|---|---|
| `refund-policy-lint` | 취소·환불 위약금 상한 초과 | 공정위 「소비자분쟁해결기준」(카테고리 분기) |
| `darkpattern-scan` | 가격표시 다크패턴 4유형 | 공정위 다크패턴 규제 / KCA 2024.03 조사 |

핵심 설계 — **카테고리 분기(거짓양성 방지)**: 소비자분쟁해결기준의 위약금 상한은 원칙적으로 여행사 주최 패키지 기준이며, 항공권은 항공사 운임규정이 우선한다. 단일 테이블로 전 카테고리를 재단하면 거짓양성이 나므로, 린터는 `overseas_package`/`domestic_package`/`accommodation`에는 각 기준을 적용하고 `air_ticket`은 **'기준 미적용(N/A)'** 으로 명시한다.

## 3. 아키텍처

```
src/                                  # Codex 플러그인 루트
├── .codex-plugin/plugin.json         # 매니페스트 (name: myrealtrip-traveler-guard)
├── skills/
│   ├── refund-policy-lint/SKILL.md   # 취소·환불 위약금 상한 린터
│   └── darkpattern-scan/SKILL.md     # 가격표시 다크패턴 스캐너
├── scripts/
│   ├── lint_refund_policy.py         # 표준 라이브러리, argparse, --json, exit 0/1/2
│   ├── scan_listings.py              # 표준 라이브러리, argparse, --json, exit 0/1/2
│   └── report.py                     # 두 스킬 통합 마크다운 리포트(--report 상당)
├── references/
│   ├── krca_refund_baseline.json     # 카테고리별 위약금 상한 + 출처 URL (근거 역추적)
│   └── darkpattern_types.json        # 다크패턴 유형↔공정위/KCA 매핑 + 출처 URL
└── samples/
    ├── policy_good.json / policy_bad.json      # 정상+위반 혼합(가상 상품)
    └── listings_good.json / listings_bad.json  # 정상+위반 혼합(가상 상품)
```

설계 원칙: 결정론(동일 입력→동일 출력), 근거 역추적(모든 판정에 기준·출처 URL), 무네트워크·무외부패키지, 표준 종료코드(`0`=통과 / `1`=위반 / `2`=사용오류).

## 4. 설치

```bash
codex plugin install ./src
```

설치 후 Codex CLI에서 `$refund-policy-lint`, `$darkpattern-scan`으로 호출하거나 자연어로 트리거한다. 스크립트는 플러그인 루트 `src/`에서 직접 실행할 수도 있다(아래 예시).

## 5. 스킬별 사용법 · 데모 · 기대 출력

### 5-1. refund-policy-lint

```bash
python3 scripts/lint_refund_policy.py samples/policy_good.json   # 기대: exit 0
python3 scripts/lint_refund_policy.py samples/policy_bad.json    # 기대: exit 1
python3 scripts/lint_refund_policy.py samples/policy_bad.json --json
```

정상 샘플 출력(발췌):
```
[PASS] OVS-100  가상 발리 5일 자유패키지  (국외여행 (여행사 주최 패키지))
[PASS] DOM-110  가상 강원 2일 국내여행  (국내여행 (여행사 주최, 숙박 포함))
[PASS] ACC-120  가상 제주 리조트 1박 (비수기 주중)  (숙박 (비수기 주중 대표 기준))
[N/A ] AIR-130  가상 인천-도쿄 왕복 항공권  (항공권 (개별 항공권))
        - 기준 미적용: 항공권 취소·환불은 항공사 운임규정 ... 우선 적용 ...
요약: 총 4개 | PASS 3 | FAIL 0 | N/A(기준 미적용) 1
```

위반 샘플 출력(발췌):
```
[FAIL] OVS-200  가상 로마 4일 패키지 (상한 초과)  (국외여행 (여행사 주최 패키지))
        - D-25 위약금 30% > 상한 10% (초과 20%p · 심각도 HIGH)
          근거: 20일 전까지 통보: 여행요금의 10%
          시정: 위약금을 10% 이하로 조정
          출처: https://easylaw.go.kr/CSP/CnpClsMain.laf?...
요약: 총 5개 | PASS 1 | FAIL 3 | N/A(기준 미적용) 1
```
주목: 위반 샘플의 항공권(AIR-230)은 위약금 100%지만 항공사 운임규정 우선이므로 **N/A로 처리**되어 FAIL로 잡히지 않는다(거짓양성 방지).

### 5-2. darkpattern-scan

```bash
python3 scripts/scan_listings.py samples/listings_good.json     # 기대: exit 0
python3 scripts/scan_listings.py samples/listings_bad.json      # 기대: exit 1
python3 scripts/scan_listings.py samples/listings_bad.json --json
```

위반 샘플 출력(발췌):
```
[FAIL] TKT-200  가상 테마파크 입장권 (대표가=아동가)
        - [HIGH] 대표가격 오인 표시 (대표가 48000원이 표준가가 아닌 '아동' 옵션가와 동일 ...)
          공정위 유형: 눈속임 설계 / 숨겨진 정보 ...
          출처: https://www.khan.co.kr/article/202403121354001
[FAIL] TKT-210  가상 스노클링 투어 (숨겨진 필수 수수료)
        - [HIGH] 순차공개 가격책정 ... 최종 84000원(+71%)
요약: 총 5개 | PASS 0 | FAIL 5
```
검출 4유형: 대표가격 오인 / 순차공개 가격책정(drip pricing) / 거짓 긴급성 / 특정옵션 사전선택.

### 5-3. 통합 리포트 (report.py)

```bash
python3 scripts/report.py --policy samples/policy_bad.json --listings samples/listings_bad.json
python3 scripts/report.py --policy samples/policy_bad.json --listings samples/listings_bad.json --json
```
두 스킬 결과를 하나의 마크다운(종합 판정 PASS/FAIL + 상품별 표)으로 통합한다. 위반이 하나라도 있으면 exit 1.

## 6. 검증 (실제 실행 결과)

아래는 `src/`에서 실제로 실행한 명령과 종료코드다. JSON은 `python3 -m json.tool`로 전수 검증했다.

```text
$ for f in .codex-plugin/plugin.json references/*.json samples/*.json; do python3 -m json.tool "$f" >/dev/null && echo "OK  $f"; done
OK  .codex-plugin/plugin.json
OK  references/darkpattern_types.json
OK  references/krca_refund_baseline.json
OK  samples/listings_bad.json
OK  samples/listings_good.json
OK  samples/policy_bad.json
OK  samples/policy_good.json

$ python3 scripts/lint_refund_policy.py samples/policy_good.json   ; echo exit=$?
요약: 총 4개 | PASS 3 | FAIL 0 | N/A(기준 미적용) 1
exit=0

$ python3 scripts/lint_refund_policy.py samples/policy_bad.json    ; echo exit=$?
요약: 총 5개 | PASS 1 | FAIL 3 | N/A(기준 미적용) 1
exit=1

$ python3 scripts/scan_listings.py samples/listings_good.json      ; echo exit=$?
요약: 총 2개 | PASS 2 | FAIL 0
exit=0

$ python3 scripts/scan_listings.py samples/listings_bad.json       ; echo exit=$?
요약: 총 5개 | PASS 0 | FAIL 5
exit=1

$ python3 scripts/report.py --policy samples/policy_bad.json --listings samples/listings_bad.json ; echo exit=$?
종합 판정: FAIL ❌ (위반 상품 8건)
exit=1

# 사용오류(exit 2) 확인
$ python3 scripts/lint_refund_policy.py samples/nope.json          → [사용오류] 파일을 찾을 수 없습니다  exit=2
$ python3 scripts/report.py                                        → [사용오류] --policy 또는 --listings 필요  exit=2
```

결론: 위반 샘플은 exit 1, 정상 샘플은 exit 0, 사용오류는 exit 2로 결정론적으로 판정된다.

## 7. 확장 로드맵

- **숙박 성수기/주말 기준**: `references/krca_refund_baseline.json`에 성수기·주말 brackets를 추가하고 상품의 season/day_type에 따라 선택.
- **항공 수수료 투명성 린트**: air_ticket을 N/A로 두는 대신 발권·취급·환불 수수료 표기 완전성·비자발취소 환급규정 검사로 심화(별도 스킬).
- **AI 여행플래너 그라운딩 검증**: LLM 생성 일정을 상품 카탈로그·좌표·영업시간과 대조해 환각 장소·불가능 동선을 게이트(회사의 AI 네이티브 전환과 정합).
- **다국어 리스팅 정합성**: 언어별 가격·취소정책·필수고지 불일치 검출(인바운드 확장 대응).
- **CI 연동**: pre-release 훅에서 `report.py`를 실행해 FAIL(exit 1) 시 배포 차단.

## 8. 로그 · 답변

- `logs/` — AI와의 대화 원본 로그(무편집).
- `answers/questions.md` — 예선 5문항 답변(문항당 800자 이내).
- `research.md`, `research/supplement.md` — 문제 발굴·검증 리서치(출처 URL 병기).
