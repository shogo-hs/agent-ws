# 0013. InsForge 型の「backend context engineering」は取り込まない。同等物が既にある
- 状態: 採用 / 日付: 2026-09-08

## 状況
X の記事「How to cut Claude Code costs by 3x」（2026-04-21）が、Supabase を InsForge に替えると Claude Code のセッションが 10.4M → 3.7M トークン（2.8 倍）になったと報告した。InsForge は BaaS（Postgres・auth・storage・edge functions・model gateway）で、減った理由として 4 つの仕組みを挙げる: ①用途ごとに狭く切った skills（4 本。名前と説明だけ先に載る）②MCP の代わりに `--json` と終了コードを返す CLI ③`metadata` 1 回（約 500 トークン）でバックエンドの全状態を返す ④どこで失敗したか分かる構造化エラー。agent-ws に取り込めるか調べた。

## 決定
取り込まない。製品（InsForge）は agent-ws の仕事に当てはまらず、4 つの仕組みは agent-ws に同等物が既にあり、bench の実測に効く余地が残っていない。

## 理由
- 製品: agent-ws は案件とタスクの文書を扱う作業スペースで、バックエンドを持たない。記事の削減は「バックエンドを操作する仕事」の話で、その大半は Supabase 側で 8 回繰り返した認証エラーのデバッグループ（著者自身が P.S. で注記。各 1 セッションの比較で、比べているのは製品の差）
- ①skills: `.agents/skills/` の 5 本は 1.7〜3.8KB、説明は 1〜2 文で用途ごとに分かれている。Claude Code の skills は元から名前と説明だけ先に載る仕組み
- ②CLI: `scripts/ws` が唯一の道具で MCP は 0 本。Scalekit の「MCP は CLI の 4〜32 倍」は GitHub MCP の 43 ツール定義が毎ターン注入されることが原因で、積んでいないものは減らせない（0012）
- ③metadata 1 回: SessionStart で現在のタスクの index.md 全文とナレッジ一覧を注入している（0009）。役目が同じ
- ④構造化エラー: hook の拒否文は代わりに読む場所を含む（0001）。bench の A 条件 45 セッションで拒否は 3 回（42 セッションは 0 回）で、再試行のループは起きていない
- 第三者ベンチ: MCPMark v2（Sonnet 4.6・Postgres 21 タスク × 4 走・7.3M 対 17.9M で 2.4 倍）は InsForge 自身の計測で、比較対象は Supabase MCP。バックエンド MCP 同士の比較で、MCP を持たない agent-ws には当てはまらない

## 捨てた案
- `scripts/ws` の出力を `--json` にする: tool 結果の本文は総消費の 0.2〜3.1%（0012）。出力の形を変えても効く範囲が無い
- hook の拒否文を書き換える: 拒否がほぼ起きていないので効く対象が無い

## 影響
新しい仕組みは入れない。バックエンドを持つ案件を agent-ws で扱うときは、その側の道具を選ぶ基準として記事の 4 点（狭い skills・`--json` の CLI・1 回で全状態・場所の分かるエラー）は有効なので、そのときに再読する。

根拠: `docs/sources/token-reduction-tools.md` #14〜#19・`bench/results/runs_ts8.jsonl`（A 条件の denied 列）
