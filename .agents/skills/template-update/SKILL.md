---
name: template-update
description: テンプレート（shogo-hs/agent-ws）の更新をこの作業スペースに取り込むとき。「テンプレートの更新を取り込んで」「agent-ws を最新にして」で使う。ローカル運用（テンプレートを clone したまま使う）と fork（自分のリポジトリ）の両方に対応する。
---
# template-update

ゴール: テンプレートの最新の変更が入り、手元の作業（案件・ナレッジ・教訓・書き換えたファイル）が 1 つも失われていない状態。

## 既定の進め方
1. `scripts/ws update` を実行する。ローカル運用か fork かは ws が origin を見て決める（ローカル運用は `git pull --autostash`、fork はリモート `template` のマージ）。ローカル運用なら push 止めもここで入る。
2. 出力の「取り込んだ更新」の一覧（テンプレートの PR のマージ）から、何が変わったかを人に 3 行ほどで伝える。AGENTS.md・スキル・hooks の変更は次のセッションの振る舞いが変わるので必ず挙げる。
3. 「衝突したファイル」が出たら、下の「衝突の直し方」で直す。
4. `python3 -m unittest discover -s tests` と `scripts/ws doctor` を流し、結果を人に伝える。
5. fork は、人が push してと言ったときだけ push する。

## 衝突の直し方
- 衝突の印（`<<<<<<<`・`=======`・`>>>>>>>`）のあるファイルを開き、手元の変更とテンプレートの変更を両方残す形に直す。どちらかを捨てるしかないときは、人に聞く。
- ローカル運用: 印を全部消したら `git reset`（`--hard` を付けない。衝突の状態を解くだけでファイルは変えない）。手元の変更は退避先（`git stash list` の autostash）にも残っている。人が結果を確かめるまで退避先は消さない。
- 手元で消した見本（`scripts/ws init` で消した `projects/_example/`・`knowledges/` の見本）をテンプレートが書き換えた衝突は、消したままにする（ローカル運用はそのファイルを `rm`、fork は `git rm`）。
- fork: 直したら `git add` → `git commit --no-edit`。

## 止まって人に聞くとき
- 「untracked working tree files would be overwritten」: 手元で作ったファイルとテンプレートの新しいファイルの名前がぶつかった。手元のファイルは消さずに人に聞く。
- 「テンプレートと履歴がつながっていない」: GitHub の Use this template で作ったリポジトリ。初回の取り込みはほぼ全ファイルが衝突するので、人に進め方を聞く。

## つまずきどころ
- ローカル運用では、`git push`・push 止め（push の宛先 `no_push`・`.git/hooks/pre-push`）を外す操作・`git reset --hard`・`git checkout`・`git clean`・`git restore` を hook が止める。止められたら回り道（python から git を呼ぶ、別名で同じ操作をする）をせず、理由を人に伝える。作業はコミットされていないので、消したら戻せない。
- 「自分のリポジトリで管理したい」と言われたら、README の「ローカル運用」の移し方を人に案内する（push 止めを外すのは人の操作）。
