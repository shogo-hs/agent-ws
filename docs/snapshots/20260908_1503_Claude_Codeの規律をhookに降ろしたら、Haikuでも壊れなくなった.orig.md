Title: Claude Codeの規律をhookに降ろしたら、Haikuでも壊れなくなった

URL Source: https://zenn.dev/yui/articles/97597aa13b9802

Markdown Content:
前にFable 5の「働き方」をドキュメント化してOpus/Sonnetに引き継がせる話を書きました。

Fable 5とOpus/Sonnetの品質差の大半は知能ではなく**規律・順序・検証**の差なので、それをスキル(working method + チーム別playbook)として明文化し、サブエージェントチーム全体に配る、というものです。これはかなりうまく機能して、Opusでは本来検出できなかったバグが検出できるようになりました。

ただ、しばらく運用して**ルールの置き場所に最適化の余地が残っていた**ことに気がつきました。

**あの仕組みは、ルールを全部プロンプト層に置いている**んです。

## プロンプトのルールは「確率的」である

playbookに「`"use client"`はページ先頭に貼るな、葉に押し下げろ」と書く。エージェント定義に埋める。委譲プロンプトにダイジェストを逐語コピーする。レポートをゲートに照らして差し戻す。──前回やったことは全部、突き詰めると**モデルが読んで従ってくれることに賭ける**構造です。

これ自体は問題ではありません。「境界を手でトレースせよ」「根本原因を確定するまで直すな」のような判断の要るルールは、モデルに読ませて判断させる以外に実現方法がなく、プロンプトに置くのが正解です。

ただし、プロンプトの遵守は確率的で、その確率は一定ではありません。

*   **コンテキストが伸びるほど劣化する。**セッション序盤は完璧に守っていたルールが、20万トークン目のエージェントからはすり抜ける
*   **モデルのランクを下げるほど劣化する。**Opusなら9割守るルールを、Haikuは体感でかなり忘れます
*   **守らせるためのコストが常時かかる。**ルールを確実に届けるには全委譲プロンプトにダイジェストを貼るしかなく、これは違反していようがいまいが毎回トークンを食う

つまり「ルールを増やすほど、1本あたりの遵守率が下がり、トークン代は上がる」というジレンマがあります。

## playbookのルールには2種類ある

改めて自分のplaybookを読み直すと、ルールは2種類に分かれることに気づきました。

**判断が要るルール:**

> Server/Client境界を手でトレースせよ
> 
>  根本原因を確定していない修正は当てずっぽうだ

これはモデルの判断力に頼るしかないため、プロンプトに置くのが正しいです。

**grepで書けるルール:**

> `app/**/page.tsx`の先頭に`"use client"`があったらアウト
> 
> `"use client"`ファイル内の`process.env.XXX`(非`NEXT_PUBLIC_`)はアウト
> 
> `@ts-ignore`は理由なしではアウト

これは**モデルに守らせる必要がありません**。機械的に判定できるルールなので、プロンプトベースではなく、hookで強制すれば良いことに気がつきました。

## Claude Codeのhooksで「編集のたびに自動レビュー」する

Claude Codeには[hooks](https://docs.anthropic.com/en/docs/claude-code/hooks)という仕組みがあります。ツール実行の前後などに任意のコマンドを走らせられて、今回使うのは**PostToolUse**: エージェントが`Edit`/`Write`するたびに発火します。

重要なのは、**exit 2で終了すると、stderrの内容がそのままエージェントにフィードバックされる**ということです。つまり人間には何も通知されず、編集した本人(エージェント)にだけ「ここがダメ」と返ります。これが編集のたびの自動レビューとして機能します。

[ccteams](https://www.npmjs.com/package/ccteams)のv0.3.0で、これを**スタック固有の全チーム**(next-ts / go-api / python-fastapi / rails / django / react-native / frontend)に同梱しました。各チームのplaybookのfailure catalogから「grepで書けるルール」を抜き出してチェックスクリプトに落としています。

| チーム | チェック内容(抜粋) |
| --- | --- |
| `next-ts` | routeレベルの`"use client"`、clientでの非`NEXT_PUBLIC_` env参照、`useEffect`+`fetch`、cache指定なし`fetch`、`@ts-ignore`/`as any` |
| `go-api` | `http.Error`の後に`return`がない、`%w`でなく`%v`でのエラーラップ、`_`でのエラー握りつぶし、リクエスト中の`context.Background()` |
| `python-fastapi` | 裸の`except:`、Pydantic v1 API(`@validator`/`.dict()`)、ミュータブルなデフォルト引数、async内のブロッキング呼び出し |
| `rails` | `where("#{}")`のSQLインジェクション、`update_column`/`save(validate: false)`、`default_scope`、params直渡し、`Time.now` |
| `django` | naiveな`datetime.now()`、`fields = '__all__'`、injectionになりうる`.raw()`/`.extra()`、`post_save`シグナル |
| `react-native` | `ScrollView`内の`.map`、indexをkeyに使う、DOM API(`localStorage`など)、`Platform`分岐なしの`behavior="padding"` |
| `frontend` | `div`への`onClick`、`alt`なし`<img>`、`:focus-visible`なしの`outline: none`、z-indexエスカレーション |

[前回の記事](https://zenn.dev/yui/articles/e4f8268ab5c6c1)で「Opus/Sonnetの失敗は決まった形式」として挙げたリストのうち、**機械判定できるものがそのままhookになっています**。前回Go playbookの例として挙げた「`http.Error`を呼んでそのまま処理を続ける」も、プロンプトの注意書きから決定的チェックに昇格しました。

例としてnext-tsチームで、エージェントが違反コードを書くとその場でこう返ります。

```
ccteams next-ts check — app/dashboard/page.tsx:
  - route-level "use client": this page and its entire import tree now render
    client-side. Push "use client" down to the smallest interactive leaf component instead.
  - client file reads process.env.API_SECRET: non-NEXT_PUBLIC_ env vars are undefined
    in the browser (or a secret leak if inlined). Read it on the server or rename it
    NEXT_PUBLIC_ only if it is truly public.
Fix these now, or state in your report why each is intentional.
```

エージェントはこれを見て**同じターン内で**修正します。人間は何もする必要はありません。

## 結果的に何が嬉しいのか

### 1. 発火率100%。コンテキストの長さにもモデルのランクにも依存しない

プロンプトのルールは「読まれて、覚えられていて、その瞬間に想起される」ことが条件となっています。hookはgrepなので、セッションが50万トークン目だろうが、軽量モデルだろうが必ず発火します。**規律のうち機械化できる部分が、モデルの状態と無関係になった**のが最大の変化です。

### 2. トークンの払い方が「常時課金」から「違反時のみ課金」に変わる

プロンプトにルールを置くと、守られていても毎回そのトークンを払います。hookは逆で、**違反しなければ0トークン**です。フィードバックの数行がコンテキストに入るのは違反したときだけです。ルールの置き場所を確率層から決定層に移すことは、そのままトークン最適化でもあります。

### 3. 差し戻しループが減る

差し戻しは予防よりコストが高いです。builderのミスをreviewerが捕まえる構造は機能しますが、builderの実装→reviewerのレビュー→差し戻し→builderの再修正、と1往復あたりの課金が重い。hookは**ミスが書かれた瞬間、reviewerに届く前**に潰すので、この往復自体が発生しません。reviewerは境界トレースやビルド実行のような、本当に判断が要るレビューに集中できます。

## そして、モデルを下げられるようになる

ここまでがhooksの話ですが、v0.3.0にはもう1つ、セットで意味を持つ機能を入れました。**モデルプロファイル**です。

ccteamsのエージェントは、実行係(builder)= `sonnet`、判断係(reviewer/architect)= `opus`という2層で出荷されています。これを適用時にまとめてリマップできるようにしました。

```
ccteams use next-ts --profile budget    # builder: haiku / reviewer: sonnet
ccteams use next-ts                     # builder: sonnet / reviewer: opus(デフォルト)
ccteams use next-ts --profile max       # 全員 opus
```

| プロファイル | 実行係 | 判断係 | 使いどころ |
| --- | --- | --- | --- |
| `budget` | haiku | sonnet | 定型作業を大量に回すとき。検証ゲート付きの最安構成 |
| `balanced` | sonnet | opus | デフォルト。ほとんどの作業はこれ |
| `max` | opus | opus | builderの質がコストより重要な難所 |

今までもagentファイルのfrontmatterを手で編集すればモデルは変えられましたが、`ccteams use`のたびに上書きされて戻ってしまう問題がありました。プロファイルは適用時の変換なので、切り替えはコマンド1発で、`ccteams current`でいつでも確認できます。

モデルを下げるほどhookの恩恵が大きくなるため、今回の変更と共に入れることにしました。Haikuにplaybookを100%守らせるのはプロンプトだけでは無理がありますが、hookはHaikuが書いたコードにも同じ精度で発火します。決定的なチェックが下から支えているから、`--profile budget`が「安かろう悪かろう」ではなく実用構成になります。

## 壊さないための設計

`.claude/settings.json`はユーザーの持ち物なので、hooksの管理はかなり慎重に設計しています。

*   ccteamsが置くhookスクリプトは必ず`.claude/hooks/ccteams-*`という名前で、settings.json内のエントリもこのパスを参照します。**チーム切替時はこのマーカーを持つエントリだけを除去する**ので、あなたが自分で書いたhookには一切触れません
*   チーム切替でスクリプトも消え、再適用しても重複登録されません
*   チェックスクリプト自体は「内部エラーが起きたら黙ってexit 0」で書いてあり、hookのバグがセッションを壊すことはありません

## 使い方

```
npm install -g ccteams@latest
ccteams use go-api --profile budget   # next-ts, rails, django, python-fastapi など。profile は balanced / max も
# Claude Code を再起動(hooks もエージェントもセッション開始時にロードされます)
```

これだけで、そのスタックのチーム + playbook + 学習ループ + 決定的チェックhook + お好みのコスト構成が入ります。チームを切り替えればhookも一緒に入れ替わり、自分で書いたhookには触れません。

もしこの設定で少しでも手間が省けましたら、[リポジトリ](https://github.com/toffyui/ccteams)にスターをいただけると励みになります。issueや使ってみた感想も大歓迎です!

## あとがき

hookで強制できるのは、あくまで「grepで書けるルール」だけです。Server/Client境界を手でトレースする、`next build`を実際に走らせて出力を引用する、根本原因の因果を言語化する──こうした判断の要るゲートは今もreviewerとplaybookの仕事で、ここをhookに置き換えるつもりはありません。境界線はシンプルで、**偽陽性なく機械判定できるならプロンプトからhookへ降ろす、判断が要るならプロンプトに残す**です。

なお、hookを同梱していないチームが3つあります(generalist / debug / research)。これは、スタック非依存のチームにはgrepすべき固定パターンがそもそも存在しないためです。debugチームの「因果を言えるまでfixに進むな」のような規律は判断そのものなので、プロンプト側に置くのが正しいと考えました。**機械判定できるものはhookへ、判断が要るものはプロンプトへ**という境界線を、チーム構成にもそのまま適用した形です。

少しでも参考になれば嬉しいです。
