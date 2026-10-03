# 0032. テンプレートを clone したまま使う運用（ローカル運用）を受け入れ、push を 3 段で止める。更新の取り込みは scripts/ws update
- 状態: 採用 / 日付: 2026-10-03

## 状況
導入手順は「Use this template（または fork）→ clone」の 1 通りだけだった。実際には、テンプレートを clone して自分の作業をコミットせずに使う人もいる（ローカル運用）。この場合 origin はテンプレート本体のままで、テンプレートに書き込める人（作者・共同作業者）のエージェントが push すると、案件や教訓が公開テンプレートに載る。テンプレートの更新を取り込む手順も、fork を含めて書かれていなかった（エージェントがその都度リモートを足してマージしていた）。

## 決定
- `scripts/ws update` で取り込む。origin がテンプレート本体ならローカル運用として `git pull --autostash --no-rebase origin main`（未コミットの変更を退避 → 最新に進める → 戻す）。それ以外は fork として、リモート `template` が無ければ足し、`git merge --autostash --no-ff` でマージする。衝突したファイルは一覧で出し、直し方は template-update スキルに書く。前回の衝突が残っていれば取り込まない
- ローカル運用の push は 3 段で止める。`scripts/ws init` と `update` が、origin がテンプレート本体のときだけ 1 と 2 を入れる
  1. push の宛先を `no_push`（存在しない宛先）にする。fetch はテンプレートのまま
  2. `.git/hooks/pre-push` を置き、push をすべて失敗させる（URL を直接書いた push も止まる）
  3. PreToolUse hook が、push・1 と 2 を外す操作（`remote set-url`・`git config` での pushurl / hooksPath / insteadOf の変更・`--no-verify`・`.git/hooks` と `.git/config` への書き込み）・未コミットの作業を消す操作（`reset --hard`・`checkout`・`clean`・`restore`・`stash drop`）を止める。`repos/`（案件のコードを置く別リポジトリ）での操作は通す
- ローカル運用かどうかは、origin の URL ではなく 1 の印（`pushurl = no_push`）で決める

## 理由
- 1 だけだと、URL を直接書いた push と宛先を戻すコマンドで 1 行で回り込める。2 は URL に関係なく git 自身が止めるが、`--no-verify` とフックの削除で外れる。3 はエージェントの操作を見て 1 と 2 を外す操作を止める。3 段を重ねると、うっかりの push は通らない
- ローカル運用には正当な push が無いので、push を一律で止めてよい。自分のリポジトリへ移すときは人が 1 と 2 を外す
- URL で決めると、テンプレートを開発する人の clone（origin がテンプレート本体）の push まで止まる。開発する人は `init` を実行しないので、印で決めれば影響しない
- 未コミットの作業は、消えると戻す手段が無い。fork は作業がコミットされているので、`reset --hard` などは止めない
- 2026-10-03 に、テンプレートの 3 つ前の版（177525d）を clone して `ws init`・`LESSONS.md` への追記・`project new` をコミットせずに行い、`git pull --autostash` で最新（4ab843c）に上げた。3 つとも残った

## 捨てた案
- `.git` を消して使う人向けに、取り込みを ws で自作する（どの版を元にしたかを記録し、ファイルごとに元の版・手元・最新版を比べる）: git の 3-way マージを作り直すことになる。ローカル運用でも `.git` を残せば git がそのままやる
- push の宛先を無効にするだけ: 上のとおり 1 行で回り込める
- GitHub 側で止める（テンプレートに書き込める認証情報を置かない・ruleset で push を禁じる）: これだけが回り道まで止めるが、作者のマシンには作者の認証が要り、ruleset は作者の開発も止める

## 影響
hook が止めるのは「うっかり」までで、python から文字列を組み立てて git を呼ぶような回り道は止めない（他の hook と同じ限界）。ローカル運用から自分のリポジトリへ移すときは、人が `git remote set-url --push origin <URL>` と `.git/hooks/pre-push` の削除を行う。GitHub の Use this template で作ったリポジトリはテンプレートと履歴がつながっていないので、`update` は初回の取り込みを人に任せて止まる。

根拠: `tests/test_update.py`
