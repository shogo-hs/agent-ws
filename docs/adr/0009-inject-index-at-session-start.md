# 0009. SessionStart で現在のタスクの index.md 全文とナレッジの一覧を注入する
- 状態: 採用 / 日付: 2026-09-06

## 状況
エージェントはターンごとに会話全体を再送し、キャッシュ読みでも入力の 0.1x で課金される。bench の agent-ws あり条件で、処理した入力の 93〜95% がこの再送（cache read）で、tool 結果の本文は 5〜7% だった。「続きをやって」では index.md を読むだけのターンが 1 セッション 1.6 回あり、処理した入力の 21% を占めていた。
## 決定
SessionStart hook（startup / resume / clear / compact）が、現在のタスクの `index.md` の全文と案件の `knowledges/index.md` の一覧（`<!-- ws:index -->` の中）を `additionalContext` に入れる。合計 6,000 字まで（Claude Code は hook 出力を 10,000 字で切る）。超える index.md は従来どおりパスと「次の一手」だけ。Codex は `.codex/hooks.json` の `additionalContextLimit: 8000`（既定は約 2,500 トークン）。AGENTS.md に「ターンを減らす」節（複数ファイルは 1 ターンで読む・返答は結論だけ）。
## 理由
注入は `_example` で 1,836 字。1 ターンの再送（32k トークン）より小さく、Read の 1〜2 ターンを省ける。compact 後も SessionStart(compact) が同じ注入を返すので、要約で消えた現在地が戻る。
## 捨てた案
- tool 出力に hook で上限を付ける（PostToolUse の updatedToolOutput）: 天井が 5〜7%。Claude Code 側に Bash 30,000 字・Read のページ分割が既にある。JetBrains は rtk の計測で「圧縮できるのは読む量の 1/5、低 effort では +7.6%」と報告している（第三者の実測）
- 注入を「次の一手」だけに留める（従来）: index.md を読む Read のターンが残る
- AGENTS.md をさらに圧縮する: 固定分の差は 2.9k トークン（1 ターンの 9%）で、60 行を削っても 1〜2k
## 影響
起動時の文脈が 1〜2k トークン増え、以後すべてのターンに乗る。効果は bench で未測定（変更の前後を比べる）。0006 の「Read の出力上限を下げない」は変えない。

根拠: `docs/sources/token-saving.md` #2・#8・#12・#14・#15・README「計測」第 6 弾の表
