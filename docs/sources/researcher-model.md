# Codex の調査係のモデルと推論量の根拠

ADR 0020（Codex の調査係を gpt-5.4-mini から gpt-5.6-luna・max に替え、読み切り規則を足す）の出典。
発端は利用者の「Codex 側のサブエージェントが 5.4-mini のままだが、gpt-5.6-luna の max などが良いのでは」という提案（2026-09-14）。

判断の物差しは 3 つ。①5.4-mini がまだ使えるか・公式の置き換え先は何か（一次情報）、②推論量をどう選べと公式が言っているか（一次情報）、
③調査係の型の仕事（長い文字起こしからの抽出）で、モデル×推論量ごとに正答率・トークン・時間がどう変わるか（自分の実測。`bench/results/runs_effort.jsonl`）。

各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、規則を見直すときは再取得して差分を見る。

## 一次情報（OpenAI）

| # | 出典（題名と URL） | 取得日時 | via | ファイル | 何の根拠か |
|---|---|---|---|---|---|
| 1 | Models \| ChatGPT Learn — https://learn.chatgpt.com/codex/models | 2026-09-14T10:22:03+09:00 | jina | [snapshots/20260914_1022_Models_ChatGPT_Learn.md](../snapshots/20260914_1022_Models_ChatGPT_Learn.md) | GPT-5.4 / 5.4 mini は 2026-08-31 に Codex（ChatGPT ログイン）から退役。`gpt-5.4-mini` は `gpt-5.6-luna` に置き換えよ。API キーは無関係。Luna は抽出・分類・変換・構造化要約向け。推論量は「必要な結果が出る最低」。Max は最難問向けで、ほとんどの仕事に要らない |
| 2 | Subagents \| ChatGPT Learn — https://learn.chatgpt.com/docs/agent-configuration/subagents | 2026-09-14T10:21:57+09:00 | jina | [snapshots/20260914_1021_Subagents_ChatGPT_Learn.md](../snapshots/20260914_1021_Subagents_ChatGPT_Learn.md) | `[agents]` の既定で推論量を省くとそのモデルの既定になる（luna は medium）。terra は読む量の多い走査向け、luna は型の決まった高頻度の仕事向け。low は「単純で速さが要るとき」、max / xhigh は「特に重い推論」 |
| 3 | GPT-5.6 Luna Model \| OpenAI API — https://developers.openai.com/api/docs/models/gpt-5.6-luna | 2026-09-14T10:21:29+09:00 | jina | [snapshots/20260914_1021_GPT-5.6_Luna_Model_OpenAI_API.md](../snapshots/20260914_1021_GPT-5.6_Luna_Model_OpenAI_API.md) | $0.20 / $1.20（キャッシュ入力 $0.02）。文脈 1,050,000・出力 128,000。推論量は none / low / medium（既定）/ high / xhigh / max。「以前の nano 段に相当」 |
| 4 | GPT-5.4 Mini Model \| OpenAI API — https://developers.openai.com/api/docs/models/gpt-5.4-mini | 2026-09-14T10:21:33+09:00 | jina | [snapshots/20260914_1021_GPT-5.4_Mini_Model_OpenAI_API.md](../snapshots/20260914_1021_GPT-5.4_Mini_Model_OpenAI_API.md) | API 側は継続（$0.75 / $4.50）。比較対象 |
| 5 | GPT-5.6: Frontier intelligence that scales with your ambition — https://openai.com/index/gpt-5-6/ | 2026-09-14T10:21:37+09:00 | jina | [snapshots/20260914_1021_GPT-5.6_Frontier_intelligence_that_scale.md](../snapshots/20260914_1021_GPT-5.6_Frontier_intelligence_that_scale.md) | Sol / Terra / Luna の 3 段。当初価格 Luna $1 / $6。`max` は ChatGPT ログインの Codex でも使える |
| 6 | Advancing the price-performance frontier with GPT-5.6 — https://openai.com/index/advancing-the-price-performance-frontier-with-gpt-5-6/ | 2026-09-14T10:21:44+09:00 | jina | [snapshots/20260914_1021_Advancing_the_price-performance_frontier.md](../snapshots/20260914_1021_Advancing_the_price-performance_frontier.md) | 7/30 に Luna を 80% 値下げ（$0.20 / $1.20）、Terra は $2 / $12。サブスクの消費量にも同じ比で反映 |
| 7 | Configuration Reference \| ChatGPT Learn — https://learn.chatgpt.com/docs/config-file/config-reference | 2026-09-14T10:21:52+09:00 | jina | [snapshots/20260914_1021_Configuration_Reference_ChatGPT_Learn.md](../snapshots/20260914_1021_Configuration_Reference_ChatGPT_Learn.md) | `agents.default_subagent_model` / `default_subagent_reasoning_effort` の優先順位（明示の spawn 指定が勝つ）。一覧は xhigh までで max が無い（文書のほうが遅れている。M3） |

## 第三者（手がかりにだけ使った。帰属）

| # | 出典（題名と URL） | 取得日時 | via | ファイル | 何の手がかりか |
|---|---|---|---|---|---|
| 8 | The Ultra Mode Trade-Off（codex.danielvaughan.com） — https://codex.danielvaughan.com/2026/07/24/codex-cli-ultra-mode-trade-off-reasoning-budgets-subagent-cost-task-routing/ | 2026-09-14T10:22:08+09:00 | jina | [snapshots/20260914_1022_The_Ultra_Mode_Trade-Off_When_Bigger_Rea.md](../snapshots/20260914_1022_The_Ultra_Mode_Trade-Off_When_Bigger_Rea.md) | max は 1 エージェントの思考を長くするだけで、型の決まった仕事には効かないという見立て。相対コストの数字は著者の見積で使っていない |

## 自分の実測（Codex CLI 0.153.4、ChatGPT ログイン、2026-09-14）

| # | 何を | どこに | 要点 |
|---|---|---|---|
| M1 | `codex exec -m gpt-5.4-mini "Reply with exactly: OK"` | `docs/adr/0020` | 400 `The 'gpt-5.4-mini' model is not supported when using Codex with a ChatGPT account`。`~/.codex/models_cache.json` の一覧は gpt-6-astra / gpt-5.6-sol / terra / luna / gpt-5.5 で 5.4 系は無い |
| M2 | `codex exec -m gpt-5.6-terra -c 'agents.default_subagent_model="gpt-5.6-luna"'` で子を 1 体 spawn させ、セッションログを読む | `docs/adr/0020` | 親が `spawn_agent` を呼び、子の `thread_settings_applied` に `model: gpt-5.6-luna`。developer message に「`fork_turns` 省略か `"all"` は親のモデルと推論量を継承し上書きを受け付けない。`model` / `reasoning_effort` を指定するときは `fork_turns` を `"none"` か正の整数にする」 |
| M3 | `codex exec -m gpt-5.6-luna -c model_reasoning_effort='"max"'` | `docs/adr/0020` | 受理される（`--ephemeral` では collab spawn が `no thread with id` で失敗するので、spawn の確認は ephemeral なしで行った） |
| M4 | 架空の文字起こし（1,134 行・69 KB）から決定 20・宿題 15 を抽出し却下 12 を混ぜない正答率を、luna の low / medium / high / xhigh / max と terra low で各 n=3（素の依頼文）、読み切り規則つきで luna low を n=8、medium / max を各 n=4 | `bench/results/runs_effort.jsonl`・`bench/researcher_effort.py` | 結果と解釈は `docs/adr/0020`。失敗した run は `sed -n '1,520p'` までしか読まずに書き始めるか、全範囲を読んだ後 grep の当たりだけで書いて「決まりました」型の決定 8 件を落としていた（run ディレクトリの `stdout.jsonl`） |
| M5 | M2 と同じ spawn を `agents.default_subagent_reasoning_effort="max"` で | `docs/adr/0020` | 子の thread は gpt-5.6-luna で起動する（既定の effort に max を置いても拒否されない） |

## 再取得の手順

`WS_ROOT=$PWD uv run python scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
実測は `bench/README.md` の「調査係のモデルと推論量」の手順で取り直す。
