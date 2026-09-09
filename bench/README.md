# bench — agent-ws の有効性を測る

同じ材料・同じ依頼文・同じモデルで、agent-ws の仕組みがある場合と無い場合を headless の Claude Code で走らせ、
処理したトークン・費用・読みに行った範囲・答えの正誤を比べます。python3 の標準ライブラリだけで動きます。

agent-ws を使うだけなら不要です（README の数字の根拠と、AGENTS.md や hooks を変えたときの退行確認のためのもの）。
テンプレートから作った人は `projects/_example/` と同じく消して構いません。
自社向けに規約や hooks を書き換えたとき、読む量や正誤が悪化していないかを同じ手順で測ることはできます。

## 条件（1 つだけ違う）

| 条件 | 中身 | 何と比べるか |
|---|---|---|
| A: agent-ws | リポジトリの現物（AGENTS.md・CLAUDE.md・hooks・skills・scripts・templates）＋ `projects/` | — |
| B: 同じ構造・仕組みなし | 同じ `projects/` ツリーだけ。規約・hooks・skills・scripts・注入が無い | A と比べて「仕組み」の効果 |
| C: 導入前 | tasks/ 階層も index.md も無い。`projects/<案件>/docs/` に資料を平置き、`notes/` にナレッジ、`memo.md` に概要と作業の状況 | A と比べて「導入前後」の差 |

B と C は build 時に A から機械的に派生させるので、`corpus/` を直せば 3 条件が揃って変わります。

## 材料

- `corpus/projects/`: 架空の 3 案件（acme / beta / gamma）。現在のタスクは acme の見積（`projects/acme/tasks/20260906_estimate`・doing）
- 規模 `small` はこれだけ。`large` は `run.py` が生成するノイズ案件 5 件（delta / epsilon / zeta / eta / theta・各 4 タスク）を足し、doing のタスクが 6 になる
- 罠: 見積依頼メールに「提案書の 8 台は使わない」という警告は無い。キックオフの references/ に提案時の旧単価表（ノード 29,000 円/台）がある。PoC 報告会の文字起こしに「10 台で運用でカバーする案」が出て却下されている
- 正解は 12 台 × 新単価で月額 363,400 円・6 ヶ月 2,180,400 円
- `corpus/inbox/`: 引き継ぎ実験（chain）で使う。見積タスクが無い状態のルートに置く 5 ファイル（依頼メール・単価表・無関係な資料 3 件）

## 実験

| exp | 開始状態 | 依頼文 | 見るもの |
|---|---|---|---|
| `trap` | 見積が doing | 「続きをやって。終わったら結果を報告して。」 | 探す工程の量、古い数字を掴むか |
| `chain` | 見積が無い + inbox/ | S1「acme の見積タスクを始めて。依頼メールと単価表は inbox/ にある。前提（ノード数・インスタンス種別・期間）を確認して、今日はそこまで。計算と報告文は次回。終わったら何をどこに残したか報告して。」→ 新セッションで S2「続きをやって。終わったら結果を報告して。」 | S1 が残した状態で S2 が再収集せず正解に届くか |
| `newtask` | 見積が doing | 「acme の案件で、10 月から始まる移行フェーズの進め方の資料を作って。これまでに決まったこと（構成・前提・関係者・PoC で分かったこと）を踏まえて、フェーズ分けと各フェーズでやること、注意点を Markdown で 1 枚にまとめて。終わったらどこに置いたか報告して。」 | 新規タスクでどこまで読みに行くか、古い数字を掴むか |
| `base` | 見積が doing | 「OK とだけ答えて」（1 ターン） | 条件ごとの固定分（1 ターンで必ず送られる分） |

## 手順

```
python3 bench/run.py build --cond A --scale large --state doing --out /tmp/x   # 中身を見たいとき
bench/run_all.sh v2                                                           # 設計どおりの順で全部（2 並列）
python3 bench/run.py run --exp trap --scale large --model sonnet -n 5 --tag v2 # 1 実験だけ
python3 bench/run.py summary                                                  # results/summary.md と summary.json
python3 bench/run.py fig                                                      # results/fig_*.svg
```

`--delegate` を付けると、本線 sonnet が researcher（haiku）に委譲できる条件になります
（`--allowedTools` に `Agent` を足すだけ。B/C には `.claude/agents/` が無いので何も起きません）。
委譲なしと同じ tag で走らせて比べてください。

実行ディレクトリは `WS_BENCH_RUNS`（既定 `/var/tmp/agent-ws-bench/runs`）の下に 1 セッション 1 つ組みます。
作業スペースの中に置くと親の CLAUDE.md が読まれて条件が汚れるので、外に置いてください。
起動は次のとおりで、グローバルの hooks・プラグイン・MCP を外し、プロジェクトの `.claude/settings.json`（A の hooks）と CLAUDE.md だけを載せます。

```
env -u CLAUDECODE claude -p "<依頼文>" --model sonnet|haiku --output-format json \
  --setting-sources project --strict-mcp-config --max-turns 30 --allowedTools "Read,Grep,Glob,Bash,Write,Edit"
```

結果は `results/runs.jsonl`（朝の 99 セッション。`summary.md` の元）、`results/runs_ts7.jsonl`（PR #8 の部品分解。tag ts7-*）、`results/runs_ts8.jsonl`（PR #8 を A にした A/B/C の取り直し。tag ts8）に 1 行 1 セッション（最終応答・使ったツールとパス・書き換えたファイル付き）で追記されます。

## 数える値

| 値 | 定義 | 出所 |
|---|---|---|
| in_total | Σ（新規入力 + キャッシュ作成 + キャッシュ読み）。同じ message.id の usage は 1 回だけ数える | transcript jsonl（`~/.claude/projects/*/<session_id>.jsonl`） |
| ctx_final | 最後のターンの入力合計（最終文脈サイズ） | 同上 |
| cost_usd | Claude Code が定価で計算した費用 | 結果 JSON の total_cost_usd |
| turns / reads / searches | assistant メッセージ数 / Read と cat・sed / Grep・Glob と grep・find・ls | transcript の tool_use |
| other_task | 現在のタスク以外の tasks/ 配下を読んだ回数。C は現在のタスクの資料 2 件と notes/ 以外の docs/。newtask は tasks/ の references/（C は docs/）全部。chain は元からあった tasks/（C は docs/）全部 | 同上 |
| inbox_reads | inbox/ を読んだ回数（chain の S2 で 0 なら再収集していない） | 同上 |
| denied | A の hook が拒否した回数 | tool_result の `[agent-ws]` |
| delegates | Agent ツール（サブエージェントへの委譲）を呼んだ回数。`--delegate` を付けていない実行では常に 0 | transcript の tool_use |
| verdict | 見積: correct / wrong8 / wrong10 / wrongOld12 / wrongOld8 / mixed / none（最終応答と書き換えたファイルの数字で判定）。newtask: 必須 8 項目の充足数と混入 3 項目の出現（文脈付き。混入は目視で確認する） | 最終応答 + 差分 |
| left_behind / doc_location | 作成・変更したファイル。newtask は資料の置き場所（current_task / new_task / project_dir / elsewhere / response_only） | 実行前後のツリー差分 |

集計は条件ごとに中央値（最小〜最大）。A/B と A/C の各対に 5 対 5 の並べ替え検定（252 通り・両側）の p 値を付けます。5 回なので p は目安です。

## 測っていないもの

- 「1 時間空いたあとの 1 通目を止める」hook の節約（計算で出せる）
- 文字起こしの用語集正規化（置換は決定的で、効果は前処理側にある）
- compact 後の再注入（headless で多ターンの往復を再現しにくい）
- Opus・GPT 系のモデル
