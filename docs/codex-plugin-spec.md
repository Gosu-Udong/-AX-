# Codex 플러그인 / 스킬 스펙 노트

출처: OpenAI 공식 문서 (developers.openai.com/codex — Context7 문서 미러로 확보)

## 플러그인 구조

```
my-plugin/                 # = 제출물의 src/
  .codex-plugin/
    plugin.json            # 필수: 플러그인 매니페스트
  skills/                  # 선택: 패키징된 스킬들
  hooks/                   # 선택: 라이프사이클 훅
  .app.json                # 선택: 앱/커넥터 매핑
  .mcp.json                # 선택: MCP 서버 설정
  assets/                  # 선택: 아이콘·로고·스크린샷
```

## plugin.json 매니페스트

최소 형태 (`name`은 **kebab-case** — Codex가 플러그인 식별자로 사용):

```json
{
  "name": "my-first-plugin",
  "version": "1.0.0",
  "description": "Reusable greeting workflow",
  "skills": "./skills/"
}
```

전체 필드: `name`, `version`, `description`, `author{name,email,url}`,
`homepage`, `repository`, `license`, `keywords[]`,
`skills`(경로), `mcpServers`(.mcp.json 경로), `apps`, `hooks`,
`interface{displayName, shortDescription, longDescription, ...}`.
모든 경로는 플러그인 루트 기준 상대경로.

## 스킬 (SKILL.md)

스킬 디렉토리 구조:

```
skills/<skill-name>/
  SKILL.md       # 필수: 지시문 + 메타데이터
  scripts/       # 선택: 실행 코드
  references/    # 선택: 참고 문서
  assets/        # 선택: 템플릿·리소스
```

SKILL.md 형식:

```md
---
name: skill-name
description: 이 스킬이 언제 트리거되어야 하고 언제 아닌지 정확히 설명.
---

Codex가 따를 스킬 지시문.
```

- 사용자 입력에서 `$<skill-name>`으로 명시 호출 가능하며,
  description 매칭으로 자동 트리거도 됨
- `scripts/`의 실행 코드를 지시문에서 호출하도록 쓰면 재현 가능한 동작 확보

## 실행/테스트

- 플러그인 설치: `codex plugin install <path|url>` (로컬 경로 설치 지원)
- 스킬 확인: Codex CLI에서 `$skill-name` 호출 또는 자연어로 트리거
- 이 저장소에서는 각 기업 디렉토리의 `src/`가 플러그인 루트
