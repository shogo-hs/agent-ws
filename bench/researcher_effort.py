"""調査係のモデルと推論量を決めるための実測（ADR 0020）。

架空の会議文字起こし（1,134 行・69 KB。決定 20・宿題 15・却下や検討中の案 12 を雑談に埋めた）から
決定事項と宿題を out.md に抜かせ、正解の語が正しい節にあるか・却下案が混ざっていないかを数える。
`codex exec` をモデル×推論量ごとに走らせ、正答率・トークン・秒を `bench/results/runs_effort.jsonl` に残す。
python3 の標準ライブラリだけで動く。材料は `WS_BENCH_RUNS`（既定 /var/tmp/agent-ws-bench）の下に置く。

  bench/researcher_effort.py gen                                          # 材料を作る（乱数固定）
  bench/researcher_effort.py run 3 bare gpt-5.6-luna:low,gpt-5.6-luna:max # 素の依頼文で各 3 回
  bench/researcher_effort.py run 4 rule gpt-5.6-luna:low                  # 「末尾まで読み切る」規則を足した依頼文で
  bench/researcher_effort.py summary                                      # モデル×推論量×規則ごとの中央値
"""
import json, os, random, re, shutil, statistics, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

E = os.path.join(os.environ.get("WS_BENCH_RUNS", "/var/tmp/agent-ws-bench"), "effort")
RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "runs_effort.jsonl")

DEC = [("監視基盤は Grafana Cloud に統一する", "Grafana Cloud"), ("本番 DB は PostgreSQL 16 にする", "PostgreSQL 16"),
       ("リリースは毎週木曜 14 時に固定する", "木曜 14 時"), ("ログの保持期間は 90 日にする", "90 日"), ("CI は GitHub Actions に寄せる", "GitHub Actions"),
       ("キャッシュは Valkey 8 を使う", "Valkey 8"), ("バッチの実行時刻は 深夜 2 時 15 分 に変更する", "2 時 15 分"), ("検証環境の台数は 7 台にする", "7 台"),
       ("障害連絡は Slack の #ops-alert に一本化する", "#ops-alert"), ("契約更新は 2027 年 3 月末 とする", "2027 年 3 月末"),
       ("言語は Go 1.24 で書き直す", "Go 1.24"), ("画像は WebP に統一する", "WebP"), ("認証は Keycloak を採用する", "Keycloak"),
       ("定例は 隔週火曜 に減らす", "隔週火曜"), ("ドメインは example-crm.jp に決める", "example-crm.jp"), ("予算上限は 月額 480 万円 とする", "480 万円"),
       ("コードレビューは 2 名承認 を必須にする", "2 名承認"), ("ストレージは S3 互換の MinIO を使う", "MinIO"), ("SLA は 99.95% で合意する", "99.95%"),
       ("移行の順番は 顧客マスタ → 受注 → 請求 とする", "顧客マスタ")]
HW = [("佐藤", "9 月 20 日", "ログ保持のコスト試算"), ("田中", "9 月 25 日", "Keycloak の PoC 手順書"), ("鈴木", "10 月 1 日", "移行手順のレビュー依頼"),
      ("高橋", "9 月 18 日", "SLA 文言の法務確認"), ("伊藤", "9 月 30 日", "MinIO のバックアップ設計"), ("渡辺", "10 月 3 日", "負荷試験のシナリオ作成"),
      ("山本", "9 月 22 日", "Grafana のダッシュボード雛形"), ("中村", "9 月 26 日", "WebP 変換の互換性調査"), ("小林", "10 月 7 日", "予算の再見積"),
      ("加藤", "9 月 19 日", "Valkey の永続化設定"), ("吉田", "9 月 29 日", "GitHub Actions の runner 台数見積"), ("山田", "10 月 2 日", "顧客マスタの項目定義"),
      ("松本", "9 月 24 日", "障害訓練の日程調整"), ("井上", "10 月 6 日", "Go 移行の工数見積"), ("木村", "9 月 27 日", "契約書ドラフト")]
# 宿題は言い回しが変わる（「互換性調査」→「互換性を調査する」）ので、採点はこの 1 語で当てる
HW_KEY = ["ログ保持", "PoC 手順書", "移行手順", "法務", "バックアップ", "負荷試験", "ダッシュボード", "互換性", "再見積", "永続化", "runner", "項目定義", "障害訓練", "工数", "契約書"]
DIS = [("Datadog への移行", "Datadog", "却下"), ("MySQL 8 の採用", "MySQL 8", "却下"), ("Redis Enterprise の契約", "Redis Enterprise", "却下"),
       ("Auth0 の利用", "Auth0", "却下"), ("台数を 12 台 に増やす案", "12 台", "却下"), ("AVIF への統一", "AVIF", "却下"),
       ("Rust への書き直し", "Rust", "検討中"), ("SLA 99.99% の要求", "99.99%", "検討中"), ("CircleCI の継続", "CircleCI", "却下"),
       ("月額 600 万円 の予算案", "600 万円", "却下"), ("定例を 毎週月曜 にする案", "毎週月曜", "検討中"), ("Cloudflare R2 の利用", "Cloudflare R2", "検討中")]
SP = ["佐藤", "田中", "鈴木", "高橋", "伊藤", "渡辺", "山本", "中村", "小林", "加藤", "吉田", "山田", "松本", "井上", "木村", "司会"]
FILL = ["そこは前回の議事録にもありましたね。", "ちょっと待ってください、画面共有します。", "音声が途切れていませんか。大丈夫ですか。",
        "先週の障害の件は別途振り返りをやりましょう。", "この資料の 3 ページ目を見てもらえますか。", "ここは持ち帰りでもいいかもしれません。",
        "すみません、少し遅れて入りました。", "前提として、現行の構成は変えない想定です。", "それは営業側の意見も聞いてからですね。",
        "ざっくりで良いので数字の感覚を共有したいです。", "一旦、話を戻します。", "この辺りは詳細設計で詰めましょう。",
        "議事録は後で共有します。", "質問いいですか。それは本番だけの話ですか。", "はい、検証環境も同じ想定です。",
        "そこはまだ決めていません。", "なるほど、理解しました。", "時間が押しているので次に進みます。", "先ほどの点、補足すると運用チームの負荷も見ています。",
        "この件は来週の定例で続きをやります。", "昼休みを挟むので 13 時に再開します。", "ありがとうございます。では次の議題です。",
        "リスクとしては要員の確保ですね。", "他に意見のある方はいますか。", "特にありません。", "私も同意見です。"]
DP = ["では {x} で決定ですね。", "{x} で行きましょう。異論なければこれで確定します。", "{x} とすることに決まりました。", "はい、{x} で確定でお願いします。"]
HP = ["{w}さん、{d}までに{x}をお願いします。", "はい、{x}は私、{w}が{d}までにやります。", "{x}は {w} さん担当で期限は {d} ですね。"]
RP = {"却下": ["{x}という案も出ましたが、今回は見送りです。", "{x}はコスト面で不採用になりました。", "{x}は検討しましたが採用しません。"],
      "検討中": ["{x}も候補ですが、まだ決めません。要検討です。", "{x}については持ち帰って次回また相談します。"]}

PROMPT = """あなたは調査係。カレントディレクトリの transcript.md（会議の文字起こし）を読み、決定事項と宿題を抽出して out.md に書いてください。
形式:
## 決定事項
- （1 行 1 件。会議で確定したものだけ）
## 宿題
- （1 行 1 件。担当者・期限・内容）
却下された案・見送りになった案・まだ検討中の案は入れない。推測で埋めない。
最後の返答は件数だけ（決定 N 件、宿題 M 件）。本文は返さない。"""
# researcher.md / researcher.toml に足した行と同じ文
RULE = "\n長いファイルは先に行数を数え（`wc -l`）、先頭から末尾まで範囲を分けて全部読んでから書く。途中までで書き始めない（ツールの出力は 1 万トークン前後で切られる）。"


def gen():
    random.seed(20260914)
    events = [("dec", random.choice(DP).format(x=t)) for t, _ in DEC] + \
             [("hw", random.choice(HP).format(w=w, d=d, x=x)) for w, d, x in HW] + \
             [("dis", random.choice(RP[k]).format(x=t)) for t, _, k in DIS]
    random.shuffle(events)
    lines = ["# 基盤刷新プロジェクト 第 9 回定例 文字起こし（2026-09-11）", ""]
    for _, text in events:
        for _ in range(random.randint(18, 28)):
            lines.append(f"{random.choice(SP)}: {random.choice(FILL)}")
        lines.append(f"{random.choice(SP)}: {text}")
    for _ in range(30):
        lines.append(f"{random.choice(SP)}: {random.choice(FILL)}")
    open(f"{E}/transcript.md", "w").write("\n".join(lines) + "\n")
    json.dump({"dec": [k for _, k in DEC], "hw": HW_KEY, "dis": [k for _, k, _ in DIS]}, open(f"{E}/truth.json", "w"), ensure_ascii=False)
    print(f"{len(lines)} lines -> {E}/transcript.md")


def score(path, truth):
    if not os.path.exists(path):
        return None
    parts = re.split(r"^##\s*", open(path).read(), flags=re.M)
    norm = lambda s: re.sub(r"[ \u3000]", "", s)  # 「木曜 14 時」と「木曜14時」を同じに数える
    dec = norm(next((s for s in parts if s.startswith("決定")), ""))
    hw = norm(next((s for s in parts if s.startswith("宿題")), ""))
    d = sum(norm(k) in dec for k in truth["dec"]); h = sum(norm(k) in hw for k in truth["hw"]); x = sum(norm(k) not in dec and norm(k) not in hw for k in truth["dis"])
    n = len(truth["dec"]) + len(truth["hw"]) + len(truth["dis"])
    return {"dec": d, "hw": h, "dis_ok": x, "acc": round((d + h + x) / n, 3)}


def one(model, effort, i, rule, truth):
    d = tempfile.mkdtemp(prefix=f"eff-{model}-{effort}-{i}-", dir=f"{E}/runs")
    shutil.copy(f"{E}/transcript.md", f"{d}/transcript.md")
    cmd = ["codex", "exec", "--json", "-m", model, "-c", f'model_reasoning_effort="{effort}"', "-s", "workspace-write", "--skip-git-repo-check",
           "--ephemeral", "--ignore-user-config", "-C", d, "-o", f"{d}/last.txt", PROMPT + (RULE if rule else "")]
    t0 = time.time()
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=900)
    wall = round(time.time() - t0, 1); usage = {}; err = ""
    for line in p.stdout.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("type") == "turn.completed":
            usage = ev.get("usage", {})
        if ev.get("type") == "error":
            err = ev.get("message", "")[:200]
    open(f"{d}/stdout.jsonl", "w").write(p.stdout); open(f"{d}/stderr.txt", "w").write(p.stderr)
    return {"model": model, "effort": effort, "rule": rule, "i": i, "rc": p.returncode, "wall_s": wall,
            **{k: usage.get(k) for k in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")},
            "score": score(f"{d}/out.md", truth), "err": err, "dir": os.path.basename(d)}


def run():
    n, rule = int(sys.argv[2]), sys.argv[3] == "rule"
    specs = [s.split(":") for s in sys.argv[4].split(",")]  # model:effort,...
    truth = json.load(open(f"{E}/truth.json"))
    os.makedirs(f"{E}/runs", exist_ok=True); os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
    jobs = [(m, e, i, rule, truth) for m, e in specs for i in range(n)]
    with ThreadPoolExecutor(3) as ex, open(RESULTS, "a") as out:
        for r in ex.map(lambda j: one(*j), jobs):
            out.write(json.dumps(r, ensure_ascii=False) + "\n"); out.flush()
            print(r["model"], r["effort"], "rule" if rule else "bare", r["i"], r["score"], r["wall_s"], r.get("output_tokens"), flush=True)


def summary():
    rows = [json.loads(l) for l in open(RESULTS) if l.strip()]
    keys = sorted({(r["model"], r["effort"], r.get("rule", False)) for r in rows})
    print("| model | effort | 読み切り規則 | n | 正答率 中央値 | 全問正解 | 出力トークン 中央値 | 秒 中央値 |")
    print("|---|---|---|---|---|---|---|---|")
    for k in keys:
        g = [r for r in rows if (r["model"], r["effort"], r.get("rule", False)) == k and r.get("score")]
        acc = [r["score"]["acc"] for r in g]
        print(f"| {k[0]} | {k[1]} | {'あり' if k[2] else 'なし'} | {len(g)} | {statistics.median(acc):.3f} | {sum(a == 1.0 for a in acc)}/{len(g)} "
              f"| {int(statistics.median(r['output_tokens'] for r in g))} | {statistics.median(r['wall_s'] for r in g):.0f} |")


if __name__ == "__main__":
    os.makedirs(E, exist_ok=True)
    {"gen": gen, "run": run, "summary": summary}[sys.argv[1]]()
