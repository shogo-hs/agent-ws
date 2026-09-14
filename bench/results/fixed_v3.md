# 固定分（1 ターンで必ず送られる分）の内訳と、設定で落とせる量

`claude -p "OK とだけ答えて"`（1 ターン）を bench の A 条件（large・doing）で 2 回ずつ走らせ、
2 回目の `input + cache_creation + cache_read` を固定分とした（1 回目は書き込み、2 回目は全部 cache read になる）。
Claude Code 2.1.26x・Sonnet 5・`--setting-sources project --strict-mcp-config --allowedTools "Read,Grep,Glob,Bash,Write,Edit"`。
測定スクリプトは `bench/run_fixed.py`。

## セッション開始時に書く分と、他のセッションと共有して読む分

| 条件 | 固定分 | 1 回目の cache 作成（このセッションで書く） | 1 回目の cache 読み（1 時間以内の別セッションと共有） |
|---|---:|---:|---:|
| 空のディレクトリ（CLAUDE.md も hooks も無し） | 29,489 | 9,250 | 20,237 |
| B（同じ projects/、agent-ws なし） | 29,489 | 9,250 | 20,237 |
| C（導入前の構成） | 29,489 | 9,250 | 20,237 |
| **A（agent-ws）** | **35,105** | **14,866** | 20,237 |

- agent-ws が足している固定分は **5,616 トークン**（AGENTS.md・SessionStart の注入・skills と researcher の説明）。全部「セッションごとに書く側」に乗る
- 書く側の単価は読む側の 20 倍（1h TTL: $4 対 $0.20 / MTok）。**1 セッション開始のたびに 14,866 × $4/M ≒ $0.06** が掛かり、trap（6 ターン・$0.14）ではこれが費用の 4 割

## 設定・フラグで落とせる量（A 条件）

| 変種 | 固定分 | 差 | 何が起きたか |
|---|---:|---:|---|
| 既定 | 35,105 | — | |
| `--effort low` / `high` | 35,105 | 0 | effort は固定分を変えない（出力側に効く） |
| `permissions.deny: [ListAgents, ReportFindings, ScheduleWakeup, Workflow]`（settings.json） | 30,221 | **−4,884（−14%）** | agent-ws の仕事で使わない常時ロードの 4 本の定義が外れる |
| 同 + `Agent, Skill` | 22,954 | −12,151（−35%） | researcher（Agent）とスキル（Skill）も外れる。agent-ws では使えない |
| `disableWorkflows: true` | 33,064 | −2,041 | Workflow だけ外れる（上の deny に含まれる） |
| `--tools "Read,Grep,Glob,Bash,Write,Edit"` | 22,113 | −12,992 | deny 6 本と同じ。Agent 3,820・Skill 3,447 |
| `--tools` 6 本 + Agent + Skill | 29,380 | −5,725 | deny 4 本とほぼ同じ |
| `--disallowedTools ToolSearch` | 51,136 | **+16,031** | tool search が切れて遅延ロードのツールが全部載る。書かないこと |
| `--disallowedTools` に TodoWrite を含める | 34,068 | −1,037 | task-tracking のツール名を書くとその一群が opt-in されて相殺する（CLI reference）。書かないこと |
| `--model haiku` | 27,263 | −7,842 | システムプロンプトがモデルで違う |
| `--model haiku --tools` 6 本 | 17,566 | −17,539 | researcher の固定分の下限 |

`--bare` は hooks・CLAUDE.md・skills を読まないので agent-ws では使えない（ログイン情報も別扱いで、この計測では未ログイン扱いになった）。
