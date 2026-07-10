#!/usr/bin/env bash
# 기업별 submission.zip 빌드
# 사용법: ./scripts/package.sh <musinsa|kakaopay-securities|myrealtrip>
set -euo pipefail

COMPANY="${1:?사용법: ./scripts/package.sh <기업 디렉토리명>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_DIR="$ROOT/$COMPANY"
DIST="$ROOT/dist"

[ -d "$SRC_DIR" ] || { echo "오류: $SRC_DIR 없음"; exit 1; }
[ -f "$SRC_DIR/src/.codex-plugin/plugin.json" ] || { echo "오류: plugin.json 필수"; exit 1; }
[ -f "$SRC_DIR/README.md" ] || { echo "오류: README.md 필수"; exit 1; }
[ -d "$SRC_DIR/logs" ] && [ -n "$(ls -A "$SRC_DIR/logs" 2>/dev/null | grep -v '.gitkeep' || true)" ] \
  || { echo "오류: logs/ 에 원본 대화 로그 필요"; exit 1; }

mkdir -p "$DIST"
OUT="$DIST/${COMPANY}-submission.zip"
rm -f "$OUT"

# 제출 규격: src/ + README.md + logs/ (answers는 사이트 직접 입력이므로 제외 가능하나 참고용 포함)
(cd "$SRC_DIR" && zip -r "$OUT" src README.md logs -x "*/.gitkeep" -x "*/.DS_Store")

echo "생성 완료: $OUT"
unzip -l "$OUT"
