# トークン削減の手段を外部に探した調査の根拠

`docs/adr/0012`（索引・グラフ・出力圧縮のツールを入れない）の根拠にした出典。
「tgrep を組み込むべきか」から始まり、「そもそもトークンを減らす道具は何か」を外に探した。

判断の物差しは agent-ws 自身の実測（`docs/adr/0009`）と、この調査で取った実測。
**処理した入力の大半は毎ターンの会話再送**で、tool 結果の本文はごく一部。だから
「出力を小さくする道具」と「再送そのものを削る手段」を分けて評価している。

各行のファイルに取得日時・引用・原文（`.orig.md`）がある。ページは書き換わるので、
規則を見直すときは再取得して差分を見る。

## 一次情報（Anthropic）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 1 | Tool search tool — https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool | 2026-09-08T22:29:04+09:00 | [snapshots/20260908_2229_Tool_search_tool.md](../snapshots/20260908_2229_Tool_search_tool.md) | ツール定義を毎ターン積まず必要時に展開する仕組み。`defer_loading` とベータ名 |
| 2 | Scale to many tools with tool search（Agent SDK） — https://code.claude.com/docs/en/agent-sdk/tool-search | 2026-09-08T22:29:08+09:00 | [snapshots/20260908_2229_Scale_to_many_tools_with_tool_search_-_C.md](../snapshots/20260908_2229_Scale_to_many_tools_with_tool_search_-_C.md) | Claude Code では既定オン。`ENABLE_TOOL_SEARCH` の値と対応モデル |
| 3 | Introducing advanced tool use — https://www.anthropic.com/engineering/advanced-tool-use | 2026-09-08T22:29:13+09:00 | [snapshots/20260908_2229_Introducing_advanced_tool_use_on_the_Cla.md](../snapshots/20260908_2229_Introducing_advanced_tool_use_on_the_Cla.md) | 5サーバー58ツールで約55Kトークン、50+ MCP ツールで約72K、社内では最適化前に134K |
| 4 | Context editing — https://platform.claude.com/docs/en/build-with-claude/context-editing | 2026-09-08T22:31:05+09:00 | [snapshots/20260908_2231_Context_editing.md](../snapshots/20260908_2231_Context_editing.md) | 古い tool_result をサーバ側で削る仕様。キャッシュ無効化を認めた記述と `clear_at_least` の損益分岐 |
| 5 | How Claude Code uses prompt caching — https://code.claude.com/docs/en/prompt-caching | 2026-09-06T15:51:18+09:00（既存） | [snapshots/20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.md](../snapshots/20260906_1551_How_Claude_Code_uses_prompt_caching_-_Cl.md) | 毎ターン全文脈を再送すること、`/clear` はコスト0、`/rewind` はキャッシュヒットすること |

## 第三者の実測（効果が出なかった報告を含む）

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 4 | Graphify vs Grep — https://www.kubeblogs.com/graphify-claims-71-5x-fewer-tokens-we-tested-it-on-real-production-work/ | 2026-09-08T22:21:30+09:00 | [snapshots/20260908_2221_Graphify_vs_Grep_Claude_Code_Performance.md](../snapshots/20260908_2221_Graphify_vs_Grep_Claude_Code_Performance.md) | コードグラフ索引の「71.5倍」を KubeNine が独立検証し、節約が出なかったとする報告 |
| 5 | Benchmark: grepai vs grep on Claude Code — https://yoanbernabeu.github.io/grepai/blog/benchmark-grepai-vs-grep-claude-code/ | 2026-09-08T22:23:15+09:00 | [snapshots/20260908_2223_Benchmark_grepai_vs_grep_on_Claude_Code_.md](../snapshots/20260908_2223_Benchmark_grepai_vs_grep_on_Claude_Code_.md) | 新規入力を97%減らしても費用は27.5%しか下がらない（cache read が総消費を支配）。ベンチのホストは作者側 |
| 6 | The Subagent Tax, Measured — https://theinfinity.dev/articles/subagent-cost-measured | 2026-09-08T22:20:40+09:00 | [snapshots/20260908_2220_The_Subagent_Tax,_Measured_23,747_Turns_.md](../snapshots/20260908_2220_The_Subagent_Tax,_Measured_23,747_Turns_.md) | 23,747課金ターンの実運用ログからの集計。Systima の「サブエージェント税」への解釈上の反論（対照実験ではない） |
| 7 | token-savior — https://github.com/mibayy/token-savior | 2026-09-08T22:20:45+09:00 | [snapshots/20260908_2220_GitHub_-_Mibayy_token-savior_MCP_server_.md](../snapshots/20260908_2220_GitHub_-_Mibayy_token-savior_MCP_server_.md) | 著者自身によるベンチの撤回。deferred tool loading でツールが143セッション中1回しか呼ばれていなかった |
| 8 | Subagent context budget blown by eagerly loaded tools（issue #60141） — https://github.com/anthropics/claude-code/issues/60141 | 2026-09-08T22:21:34+09:00 | [snapshots/20260908_2221_Subagent_context_budget_blown_by_eagerly.md](../snapshots/20260908_2221_Subagent_context_budget_blown_by_eagerly.md) | サブエージェントは親の遅延読み込みを継承せず起動時点で140〜180kを食うという報告（Closed as not planned） |
| 11 | The Context Tax: When to Compact — https://langwatch.ai/blog/context-tax-when-to-compact | 2026-09-08T22:31:00+09:00 | [snapshots/20260908_2231_The_Context_Tax_When_to_Compact_Your_Cod.md](../snapshots/20260908_2231_The_Context_Tax_When_to_Compact_Your_Cod.md) | LangWatch の Rogerio Chaves が 2,451セッション・287,748APIコールを集計。累積トークンは context size の2.55乗（R² 0.994）、キャッシュ読みが95%、コスト最小は220,000トークン、110k を切ると再発見が上回る、compact 直後の訂正率 17.7%→41.9% |
| 12 | RepoGraph（ICLR 2025・arXiv 2410.14684） — https://arxiv.org/html/2410.14684v1 | 2026-09-08T22:32:14+09:00 | [snapshots/20260908_2232_RepoGraph_Enhancing_AI_Software_Engineer.md](../snapshots/20260908_2232_RepoGraph_Enhancing_AI_Software_Engineer.md) | コードグラフでターンは 21.47→19.12（−11%）に減ったがトークンは 245,008→262,512（+7%）に増えた。査読付きで「ターン削減≠トークン削減」を示した唯一の測定 |
| 13 | I made TS compiler graph MCP — https://dev.to/samchon/i-made-ts-compiler-graph-mcp-10x-fewer-tokens-in-claude-code-1aea | 2026-09-08T22:32:20+09:00 | [snapshots/20260908_2232_I_made_TS_compiler_graph_MCP_10x_fewer_t.md](../snapshots/20260908_2232_I_made_TS_compiler_graph_MCP_10x_fewer_t.md) | 8リポジトリ×4モデル。no-MCP 比で serena +93%、CodeGraph +22〜47%、codebase-memory-mcp +66%。**著者は競合ツールの作者**なので割り引いて読む |

## ツール本体

| # | 出典（題名と URL） | 取得日時 | ファイル | 何の根拠か |
|---|---|---|---|---|
| 9 | mcp-compressor（Atlassian Labs） — https://github.com/atlassian-labs/mcp-compressor | 2026-09-08T22:21:40+09:00 | [snapshots/20260908_2221_GitHub_-_atlassian-labs_mcp-compressor_A.md](../snapshots/20260908_2221_GitHub_-_atlassian-labs_mcp-compressor_A.md) | MCP のツール定義を70〜97%圧縮するプロキシ。tool search が既定オンの環境では役目が重複する |
| 10 | headroom — https://github.com/headroomlabs-ai/headroom | 2026-09-08T22:23:22+09:00 | [snapshots/20260908_2223_GitHub_-_headroomlabs-ai_headroom_Compre.md](../snapshots/20260908_2223_GitHub_-_headroomlabs-ai_headroom_Compre.md) | 会話履歴側を圧縮すると謳う数少ないツール。凍結済みプレフィックスはバイト同一に保つ設計 |

## 既にある台帳

トークン節約の規則そのものの根拠は [token-saving.md](token-saving.md)。
JetBrains の rtk 実測（#15）と Systima のサブエージェント税（#16）はそちらにある。

## 再取得の手順

`WS_ROOT=$PWD uv run python3 scripts/ws ref add <URL> --dir docs/snapshots --summary "<1文>"` で
該当行の URL を撮り直し、上の表のファイル欄を新しいファイル名に差し替える。
