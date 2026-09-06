#!/usr/bin/env python3
"""bench/run.py — agent-ws の有効性を headless の Claude Code で測る。

  build    条件 A/B/C × 規模 small/large × 状態 doing/fresh の実行ディレクトリを 1 つ組む（中身の確認用）
  run      実験を n 回ずつ走らせ、results/runs.jsonl に 1 行 1 セッションで残す
  summary  条件ごとの中央値（最小〜最大）と A/B・A/C の並べ替え検定 p 値を表にする
  fig      summary の値から点図（インライン SVG）を results/ に書く

python3 の標準ライブラリだけで動く。手順と数える値の定義は bench/README.md。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import itertools
import json
import os
import random
import re
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CORPUS = HERE / "corpus"
RESULTS = HERE / "results"
RUNS_DIR = Path(os.environ.get("WS_BENCH_RUNS", "/var/tmp/agent-ws-bench/runs"))
# A に載せる agent-ws の現物。bench/ tmp/ tests/ .git .ws は載せない
REPO_FILES = ["AGENTS.md", "CLAUDE.md", "LESSONS.md", "README.md", "LICENSE",
              "scripts", "templates", ".agents", ".claude", ".codex"]
CURRENT_TASK = "projects/acme/tasks/20260906_estimate"
ESTIMATE_SOURCES = {"20260905_1400_単価表.md", "20260906_0930_見積依頼メール.md"}
ALLOWED_TOOLS = "Read,Grep,Glob,Bash,Write,Edit"

PROMPTS = {
    "trap": "続きをやって。終わったら結果を報告して。",
    "chain1": ("acme の見積タスクを始めて。依頼メールと単価表は inbox/ にある。"
               "前提（ノード数・インスタンス種別・期間）を確認して、今日はそこまで。計算と報告文は次回。"
               "終わったら何をどこに残したか報告して。"),
    "chain2": "続きをやって。終わったら結果を報告して。",
    "newtask": ("acme の案件で、10 月から始まる移行フェーズの進め方の資料を作って。"
                "これまでに決まったこと（構成・前提・関係者・PoC で分かったこと）を踏まえて、"
                "フェーズ分けと各フェーズでやること、注意点を Markdown で 1 枚にまとめて。"
                "終わったらどこに置いたか報告して。"),
    "base": "OK とだけ答えて",
}

# 見積の答えの分類（月額, 6 ヶ月）。正解は 12 台 × 新単価
ANSWERS = {
    "correct": ("363400", "2180400"),
    "wrong8": ("246600", "1479600"),
    "wrong10": ("305000", "1830000"),
    "wrongOld12": ("373000", "2238000"),
    "wrongOld8": ("253000", "1518000"),
}
# 新規タスク（移行フェーズの進め方）の採点。必須はナレッジにある事実、混入は古いタスクにしか無い数字
REQUIRED = {
    "12台": r"12\s*(台|ノード)",
    "m6i.xlarge": r"m6i\.xlarge",
    "期間": r"(2026[-/年.]\s*10|10\s*月).{0,60}(2027[-/年.]\s*0?3|3\s*月)|6\s*[ヶかカケ]月|半年",
    "EKS": r"EKS",
    "RDS": r"RDS",
    "DB接続先": r"接続先|環境変数を分け|本番を向",
    "ALB": r"ALB",
    "OIDC": r"OIDC|グループ.{0,3}マッピング",
}
STALE = {
    "8台": r"(?<![0-9])8\s*(台|ノード)",
    "25万": r"25\s*万|250,?000",
    "10台": r"(?<![0-9])10\s*(台|ノード)",
}

# ---- ノイズ案件（large）。数字は acme の答えと被らないものだけ --------------------------------

FILLER = ["はい、認識合っています。", "了解です。", "ありがとうございます。次に進みます。",
          "時間が押しているので手短にお願いします。", "その件は持ち帰って確認します。",
          "補足すると、先週の時点では未定でした。", "少し戻りますが、前提を確認させてください。",
          "すみません、音声が途切れました。もう一度お願いします。", "そこは次回までに整理します。"]

NOISE = [
    dict(name="delta", summary="DELTA 社の社内ポータル（SharePoint）を Next.js の自社実装に置き換える支援（内容はすべて架空）",
         overview="顧客は DELTA 社（架空）。社内ポータル（SharePoint Online・サイト 48・ページ約 1,200）を Next.js の自社実装に置き換える。\n期間は 2026-07 から 2026-12。責任者は中村、情報システムは小林、広報は加藤。自社側は田中。",
         rules=["定例は毎週水曜 15:00。", "画面ごとに Figma のリンクを残す。", "旧ポータルの URL は切替後 3 ヶ月リダイレクトする。"],
         people=["中村", "小林", "加藤", "田中"],
         know=[("現行構成", "SharePoint Online。サイト 48・ページ約 1,200・添付 38 GB。認証は Entra ID。ワークフローは Power Automate が 17 本"),
               ("移行方針", "静的ページは Markdown 化して Next.js で配信。Power Automate は継続。切替は 2026-12-13（土）。旧 URL は 3 ヶ月リダイレクト")],
         glossary=[("Entra ID", "えんとらあいでぃー", "エントラID, Azure AD", "Microsoft の ID 基盤"), ("Power Automate", "ぱわーおーとめいと", "パワーオートメート", "ワークフローの製品")],
         tasks=[("20260710_requirements", "要件整理", "done", "経営層・現場のヒアリングから要件を 3 段階に分けて整理する"),
                ("20260805_inventory", "現行サイトの棚卸", "done", "48 サイトの利用状況を集計し、移行対象と廃止対象を決める"),
                ("20260826_design", "画面設計", "done", "移行対象の画面テンプレートを 6 種に絞って Figma で設計する"),
                ("20260905_migration_plan", "移行計画の作成", "doing", "12/13 の切替に向けて、移行の順序・リハーサル・戻し手順を計画書にまとめる")],
         lines=["サイトは 48 ありますが、直近 90 日にアクセスがあったのは 31 です。", "ページ数は約 1,200 で、添付が 38 GB あります。",
                "Power Automate のフローは 17 本。うち 5 本は所有者不明です。", "切替は 12 月 13 日の土曜で、翌日に確認します。",
                "旧 URL のリダイレクトは 3 ヶ月で打ち切ります。", "画面テンプレートは 6 種に絞りました。",
                "検索は Algolia を使う案と自前の案があります。", "広報からは全社アナウンスを 2 週間前に出したいと要望がありました。",
                "所有者不明のフローは棚卸で廃止候補にします。", "リハーサルは 11 月中に 2 回やります。"]),
    dict(name="epsilon", summary="EPSILON 社の物流拠点向けに需要予測モデルを導入する支援（内容はすべて架空）",
         overview="顧客は EPSILON 社（架空）。全国 14 拠点の出荷量を週次で予測するモデルを作り、在庫の発注に使う。\n期間は 2026-06 から 2026-11。責任者は木村、データ担当は斎藤、現場は山本。自社側は田中。",
         rules=["定例は隔週火曜 13:00。", "評価指標は MAPE。拠点ごとに出す。", "現場の担当者名は資料に書かない（社内共有の都合）。"],
         people=["木村", "斎藤", "山本", "田中"],
         know=[("データの所在", "出荷実績は WMS の日次 CSV（2023-01 から）。天候は気象庁の公開データ。祝日カレンダーは総務が管理"),
               ("モデル方針", "拠点ごとに LightGBM。特徴量は曜日・祝日・前年同週・天候・キャンペーン。MAPE 目標 18% 以下")],
         glossary=[("MAPE", "まっぷ", "MAP, 平均絶対誤差率", "平均絶対パーセント誤差"), ("WMS", "だぶりゅーえむえす", "倉庫管理システム", "倉庫管理システム")],
         tasks=[("20260615_data_survey", "データ調査", "done", "WMS の出荷実績と外部データの粒度・欠損・期間を確認する"),
                ("20260720_features", "特徴量設計", "done", "曜日・祝日・前年同週・天候・キャンペーンの特徴量を作り、効き方を見る"),
                ("20260818_validation", "精度検証", "done", "14 拠点で MAPE を出し、目標 18% を満たす拠点と満たさない拠点を分ける"),
                ("20260906_rollout_plan", "本番化計画", "doing", "精度が目標に届いた 11 拠点から順に本番化する計画と、届かない 3 拠点の扱いを決める")],
         lines=["MAPE は全体で 16.4%、拠点別だと 12% から 27% までばらつきます。", "目標の 18% を満たさない拠点は 3 つです。",
                "キャンペーンの情報は営業からの Excel で、遅れて届くことがあります。", "天候の特徴量は効きが弱く、外しても 0.3 ポイントしか変わりません。",
                "本番は週次バッチで、月曜の朝 6 時に結果を出します。", "予測が外れたときの責任範囲を現場と決めておきたいです。",
                "前年同週の特徴量が一番効いています。", "祝日の扱いは総務のカレンダーを正とします。",
                "在庫の発注は予測値に安全在庫を足して出します。", "11 拠点から先に本番化し、残り 3 拠点はモデルを分けて再検証します。"]),
    dict(name="zeta", summary="ZETA 社の社内システム 9 つの認証を Okta に統合する支援（内容はすべて架空）",
         overview="顧客は ZETA 社（架空）。部門ごとに別々だった 9 システムの認証を Okta に統合し、パスワードを 1 つにする。\n期間は 2026-08 から 2027-01。責任者は松本、セキュリティは井上、各システムの担当は部門ごと。自社側は田中。",
         rules=["定例は毎週金曜 11:00。", "移行順は利用者の少ないシステムから。", "パスワードそのものは資料に書かない。"],
         people=["松本", "井上", "田中"],
         know=[("対象システム", "9 システム。SAML 対応 5・OIDC 対応 2・非対応 2（非対応はリバースプロキシで前段に置く）。利用者 2,300 人"),
               ("移行方針", "利用者の少ない順に 1 システムずつ切り替える。MFA は Okta Verify。切替の 1 週間前に対象部門へ案内")],
         glossary=[("Okta", "おくた", "オクタ", "ID 管理の SaaS"), ("SAML", "さむる", "サムル", "認証連携の規格")],
         tasks=[("20260812_survey", "現行調査", "done", "9 システムの認証方式・利用者数・担当者を一覧にする"),
                ("20260825_policy", "方針決定", "done", "移行順と MFA の方式を決め、井上さんの承認を取る"),
                ("20260901_procedure", "移行手順", "done", "1 システム分の切替手順書と戻し手順書を作る"),
                ("20260905_pilot", "パイロット", "doing", "利用者 40 人の勤怠システムで最初の切替を行い、問い合わせと所要時間を記録する")],
         lines=["対象は 9 システムで、SAML が 5、OIDC が 2、どちらも非対応が 2 です。", "利用者は合計 2,300 人です。",
                "非対応の 2 つはリバースプロキシで前段に置きます。", "MFA は Okta Verify で統一します。",
                "パイロットは勤怠システムからで、利用者は 40 人です。", "切替の 1 週間前に対象部門へ案内を出します。",
                "戻し手順は 30 分以内に完了することを条件にします。", "問い合わせ窓口は情シスの共有アドレスにします。",
                "ライセンスは 2,500 ユーザー分で契約済みです。", "全システムの切替完了は 2027 年 1 月末の予定です。"]),
    dict(name="eta", summary="ETA 社の EC サイトの配信を自社 CDN から Cloudflare に移す支援（内容はすべて架空）",
         overview="顧客は ETA 社（架空）。EC サイト（月間 PV 2,400 万）の静的配信を自社 CDN から Cloudflare に移し、運用コストを下げる。\n期間は 2026-05 から 2026-08。完了済み。責任者は清水、インフラは藤田。自社側は田中。",
         rules=["定例は毎週月曜 10:00（完了につき終了）。", "切替は深夜 2 時から 4 時の間に行う。", "キャッシュの TTL は商品ページ 5 分・画像 1 日。"],
         people=["清水", "藤田", "田中"],
         know=[("現行構成", "自社 CDN 3 拠点。月間 PV 2,400 万・転送量 180 TB。オリジンは東京の VM 4 台"),
               ("移行結果", "2026-08-10 に切替完了。転送コストは月 96 万円から 41 万円へ。キャッシュヒット率 91%")],
         glossary=[("TTL", "てぃーてぃーえる", "生存時間", "キャッシュの有効期間"), ("オリジン", "おりじん", "origin", "配信元のサーバー")],
         tasks=[("20260512_current", "現行構成の整理", "done", "自社 CDN の構成・転送量・費用を整理する"),
                ("20260602_design", "設計", "done", "Cloudflare のゾーン設計とキャッシュルールを決める"),
                ("20260720_cutover", "切替手順", "done", "DNS 切替と戻し手順を作り、深夜に実施する"),
                ("20260818_retro", "振り返り", "done", "移行後 1 週間の指標と費用をまとめ、ナレッジに昇格する")],
         lines=["月間 PV は 2,400 万、転送量は 180 TB です。", "転送コストは月 96 万円から 41 万円に下がりました。",
                "キャッシュヒット率は 91% で目標の 85% を超えています。", "切替は 8 月 10 日の深夜 2 時に行いました。",
                "商品ページの TTL は 5 分、画像は 1 日です。", "オリジンの VM は 4 台のまま変えていません。",
                "WAF のルールは既定のマネージドルールから始めます。", "DNS の TTL は切替前に 60 秒へ下げておきます。",
                "戻し手順は DNS を元に向けるだけです。", "画像の最適化は次のフェーズで検討します。"]),
    dict(name="theta", summary="THETA 社の新入社員研修プログラム（技術職向け）の設計と初回実施の支援（内容はすべて架空）",
         overview="顧客は THETA 社（架空）。技術職の新入社員 36 人向けに 8 週間の研修プログラムを設計し、初回を 2026-04 から実施した。\n期間は 2026-01 から 2026-06。完了済み。責任者は人事の岡田、技術側は原田。自社側は田中。",
         rules=["定例は隔週水曜 16:00（完了につき終了）。", "受講者の評価は個人名を出さず集計値で扱う。", "教材は社内 Git で管理する。"],
         people=["岡田", "原田", "田中"],
         know=[("プログラム構成", "8 週間。前半 4 週は基礎（Git・Linux・SQL・Web）、後半 4 週はチーム開発演習。講師は社内 6 人"),
               ("初回の結果", "36 人が修了。満足度 4.2/5。演習の成果物は 6 チーム。改善点は SQL の時間不足と演習のテーマ選び")],
         glossary=[("OJT", "おーじぇーてぃー", "オンザジョブ", "配属後の実務研修"), ("演習", "えんしゅう", "ハンズオン", "チーム開発の実習")],
         tasks=[("20260120_hearing", "ヒアリング", "done", "人事と技術側から研修の目的・期間・予算を聞き取る"),
                ("20260210_curriculum", "カリキュラム案", "done", "8 週間の構成案を作り、講師の割り当てを決める"),
                ("20260305_materials", "教材作成", "done", "基礎 4 科目の教材と演習のテーマを用意する"),
                ("20260610_report", "実施報告", "done", "初回の結果と改善点をまとめ、来年度の提案にする")],
         lines=["受講者は 36 人で、6 チームに分けます。", "前半 4 週が基礎、後半 4 週がチーム開発演習です。",
                "講師は社内から 6 人、外部からは呼びません。", "満足度は 4.2 で、SQL の時間が足りないという声が多かったです。",
                "教材は社内 Git のリポジトリで管理します。", "演習のテーマは業務に近いものを 3 つ用意しました。",
                "来年度は SQL を 1 週間増やす提案にします。", "予算は今年度と同じ枠で収まっています。",
                "配属後の OJT との接続は人事側で設計します。", "成果物の発表会は最終日に役員も参加しました。"]),
]


# ---- 小道具 ------------------------------------------------------------------------

FM_RE = re.compile(r"^---\n(.*?)\n---\n?", re.S)


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, text[m.end():]


def section(body: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)", body, re.S | re.M)
    return m.group(1).strip() if m else ""


def oneline(text: str) -> str:
    return " ".join(text.split()) or "（未記入）"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def snapshot(root: Path) -> dict[str, str]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file() and ".git/" not in p.as_posix():
            rel = p.relative_to(root).as_posix()
            if rel.startswith(".ws/"):
                continue
            out[rel] = hashlib.sha1(p.read_bytes()).hexdigest()
    return out


def read_text_capped(p: Path, cap: int = 20000) -> str:
    try:
        return p.read_text(encoding="utf-8")[:cap]
    except Exception:  # noqa: BLE001
        return ""


def changed_text_of(rundir: Path, changed: list[str]) -> str:
    """書き換えたファイルの本文。一覧の index.md（tasks/index.md など）は古いタスクの要約が並ぶだけなので採点から外す。"""
    return "\n".join(read_text_capped(rundir / p) for p in changed
                     if p.endswith((".md", ".txt")) and not p.endswith(("tasks/index.md", "references/index.md", "knowledges/index.md")))


# ---- 材料を組む ------------------------------------------------------------------------

def gen_transcript(spec: dict, title: str, date: str, rnd: random.Random) -> str:
    people = spec["people"]
    n = rnd.randint(160, 220)
    pool = spec["lines"] * 12 + FILLER * 8
    rnd.shuffle(pool)
    h, mnt = 10, 0
    out = [f"{date} {title}（Teams 文字起こし・架空）", ""]
    for line in pool[:n]:
        mnt += rnd.randint(0, 3)
        if mnt >= 60:
            h, mnt = h + 1, mnt - 60
        out.append(f"[{h:02d}:{mnt:02d}] {rnd.choice(people)}: {line}")
    return "\n".join(out)


def gen_noise(root: Path, seed: int = 7):
    """ノイズ案件を projects/ に足す。index.md の自動生成部は後で scripts/ws index が埋める。"""
    rnd = random.Random(seed)
    for spec in NOISE:
        name = spec["name"]
        proj = root / "projects" / name
        write(proj / "index.md", "\n".join([
            "---", f'title: "{name}"', f'summary: "{spec["summary"]}"', "created: 2026-06-01", "---",
            f"# {name}", "", "## 概要", spec["overview"], "", "## この案件での決まりごと",
            *[f"- {r}" for r in spec["rules"]], "", "## 中身", "<!-- ws:index -->", "<!-- /ws:index -->", ""]))
        write(proj / "knowledges" / "index.md", "\n".join([
            "---", 'title: "ナレッジ"', 'summary: "この案件のナレッジの正本。タスクで得た知見はここに昇格する"', "---",
            f"# ナレッジ（{name}）", "", "このフォルダが案件のナレッジの正本。tasks/ の中に知見を溜めない。",
            "用語集は glossary.md。文字起こしを読む前に `scripts/ws transcript normalize` が参照する。", "",
            "<!-- ws:index -->", "<!-- /ws:index -->", ""]))
        for i, (kt, ks) in enumerate(spec["know"], 1):
            write(proj / "knowledges" / f"{i:03d}_{kt}.md", "\n".join([
                "---", f'title: "{kt}"', "type: fact", "status: complete", "created: 2026-08-01", "updated: 2026-08-01",
                'source: "定例の文字起こしと資料"', f'summary: "{ks}"', "---", f"# {kt}", "", "## 内容",
                *[f"- {s.strip()}。" for s in ks.split("。") if s.strip()], "", "## 出所", "- 定例の文字起こしと資料（tasks/ の references/）", ""]))
        write(proj / "knowledges" / "glossary.md", "\n".join([
            "---", 'title: "用語集"', 'summary: "この案件の固有名詞・略語・表記ゆれ・文字起こしの誤変換。scripts/ws transcript normalize が置換に使う"',
            "created: 2026-06-01", "---", f"# 用語集（{name}）", "", "| 正式表記 | 読み | 誤変換・別表記 | 説明 |", "|---|---|---|---|",
            *[f"| {a} | {b} | {c} | {d} |" for a, b, c, d in spec["glossary"]], ""]))
        write(proj / "tasks" / "index.md", "\n".join([
            "---", 'title: "タスク一覧"', 'summary: "この案件のタスク。作業中は自分のタスクだけを見る"', "---",
            f"# タスク一覧（{name}）", "", f"新しいタスクは `scripts/ws task new {name} <slug>`。",
            "他のタスクのフォルダは開かない（hook が拒否する）。他タスクの成果が要るなら knowledges/ を見る。", "",
            "<!-- ws:index -->", "<!-- /ws:index -->", ""]))
        for j, (slug, title, status, purpose) in enumerate(spec["tasks"]):
            date = f"{slug[:4]}-{slug[4:6]}-{slug[6:8]}"
            t = proj / "tasks" / slug
            steps = ["資料と文字起こしを references/ に保存する", "要点を整理する", "関係者に確認する", "結果をナレッジに昇格する"]
            done_n = 4 if status == "done" else rnd.randint(1, 2)
            now = "完了。" + purpose if status == "done" else f"{steps[done_n - 1]}まで終わった。{steps[done_n]}はこれから。"
            nxt = "（完了）" if status == "done" else f"{steps[done_n]}。終わったら index.md の現在地を更新する。"
            write(t / "index.md", "\n".join([
                "---", f'title: "{title}"', f"status: {status}", f"project: {name}", f"created: {date}", f"updated: {date}",
                f'summary: "{purpose}"', "---", f"# {title}", "", "## 目的", purpose + "。", "", "## 進め方",
                *[f"- [{'x' if k < done_n else ' '}] {s}" for k, s in enumerate(steps)], "", "## 現在地", now, "",
                "## 次の一手", nxt, "", "## 参照したナレッジ", f"- knowledges/001_{spec['know'][0][0]}.md", "",
                "## 未確定の用語", "（なし）", "", "## 情報源（references/）", "<!-- ws:index -->", "<!-- /ws:index -->", ""]))
            write(t / "references" / "index.md", "\n".join([
                "---", 'title: "情報源"', 'summary: "このタスクで参照した情報源。どこから・いつ・原文は何か"', "---", "# 情報源", "",
                '追加は `scripts/ws ref add <URL|ファイル> --summary "1文"`。原文は改変しない。', "",
                "<!-- ws:index -->", "<!-- /ws:index -->", ""]))
            stamp = slug[:8]
            body = gen_transcript(spec, f"{title} 定例", date, rnd)
            # ファイル名の日付接頭辞をわざと落としたものを混ぜる（散らかり）
            fname = f"{stamp}_1000_{date}_{title}_文字起こし.md" if rnd.random() < 0.7 else f"{title}_文字起こし.md"
            write(t / "references" / fname, "\n".join([
                "---", f'title: "{date} {title} 文字起こし"', "kind: transcript", "source: Teams", f'retrieved_at: "{date}T12:00:00+09:00"',
                "retrieved_by: claude-code", f'summary: "{title}の定例の文字起こし（架空）"', "---", f"# {date} {title} 文字起こし", "",
                "## 要点", "（原文のどこを使ったか、このタスクでの使いどころ。読み手が埋める）", "", "## 原文（改変しない）", body, ""]))
            rows = [f"| 項目 {k + 1} | {rnd.randint(2, 90) * 1000:,} 円 | 月 |" for k in range(rnd.randint(3, 5))]
            dname = f"{stamp}_1500_{title}_資料.md" if rnd.random() < 0.7 else f"{title}_資料_v{rnd.randint(1, 3)}.md"
            write(t / "references" / dname, "\n".join([
                "---", f'title: "{title} 資料（{date}）"', "kind: file", f"source: 共有フォルダ/{name}/{title}.xlsx",
                f'retrieved_at: "{date}T15:00:00+09:00"', "retrieved_by: claude-code", f'summary: "{title}で使った資料の抜粋（架空）"', "---",
                f"# {title} 資料（{date}）", "", "## 要点", "（原文のどこを使ったか、このタスクでの使いどころ。読み手が埋める）", "",
                "## 原文（改変しない）", f"{title}の資料（{date}・税抜き・架空）", "", "| 項目 | 金額 | 単位 |", "|---|---|---|", *rows, "",
                *[f"- {line}" for line in rnd.sample(spec["lines"], 3)], ""]))
            if j % 2 == 1:
                write(t / "references" / f"{stamp}_1600_メモ.md", "\n".join([
                    "---", f'title: "{title} メモ"', "kind: note", "source: 手書きメモ", f'retrieved_at: "{date}T16:00:00+09:00"',
                    "retrieved_by: claude-code", f'summary: "{title}の打合せ後のメモ（架空）"', "---", f"# {title} メモ", "",
                    "## 要点", "（読み手が埋める）", "", "## 原文（改変しない）", *[f"- {line}" for line in rnd.sample(spec["lines"], 4)], ""]))


def build_a(dst: Path, scale: str, state: str):
    """A（agent-ws の現物 + projects/）を組み、index.md の自動生成部を埋める。"""
    dst.mkdir(parents=True)
    for name in REPO_FILES:
        src = REPO / name
        if src.is_dir():
            shutil.copytree(src, dst / name, symlinks=True)
        else:
            shutil.copy2(src, dst / name)
    shutil.copytree(CORPUS / "projects", dst / "projects")
    if scale == "large":
        gen_noise(dst)
    if state == "fresh":
        shutil.rmtree(dst / CURRENT_TASK)
        shutil.copytree(CORPUS / "inbox", dst / "inbox")
    else:
        write(dst / ".ws" / "current", CURRENT_TASK + "\n")
    subprocess.run([sys.executable, str(dst / "scripts" / "ws"), "index"], cwd=dst, check=True,
                   capture_output=True, env={**os.environ, "WS_ROOT": str(dst)})


def flatten(src_projects: Path, dst_projects: Path):
    """C（導入前）: tasks/ 階層を無くし、docs/・notes/・memo.md に平置きする。"""
    for proj in sorted(p for p in src_projects.iterdir() if p.is_dir()):
        d = dst_projects / proj.name
        (d / "docs").mkdir(parents=True)
        (d / "notes").mkdir()
        for k in sorted((proj / "knowledges").glob("*.md")):
            if k.name != "index.md":
                shutil.copy2(k, d / "notes" / k.name)
        _, pbody = frontmatter(proj / "index.md")
        memo = [f"# {proj.name} 作業メモ", "", "## 概要", section(pbody, "概要"), "", "## 決まりごと",
                section(pbody, "この案件での決まりごと"), "", "## 作業の状況"]
        for t in sorted((proj / "tasks").iterdir()):
            if not t.is_dir():
                continue
            for r in sorted((t / "references").glob("*.md")):
                if r.name == "index.md":
                    continue
                dst = d / "docs" / r.name
                if dst.exists():
                    dst = d / "docs" / f"{t.name}_{r.name}"
                shutil.copy2(r, dst)
            meta, body = frontmatter(t / "index.md")
            memo += ["", f"### {meta.get('title', t.name)}（{meta.get('status', '')}）",
                     "目的: " + oneline(section(body, "目的")), "現在地: " + oneline(section(body, "現在地")),
                     "次の一手: " + oneline(section(body, "次の一手"))]
        text = "\n".join(memo) + "\n"
        text = re.sub(r"tasks/[^/\s]+/references/", "docs/", text)
        text = text.replace("references/", "docs/").replace("knowledges/", "notes/")
        write(d / "memo.md", text)


def build(cond: str, scale: str, state: str, out: Path) -> Path:
    if out.exists():
        shutil.rmtree(out)
    work = out.parent / (out.name + ".__A")
    if work.exists():
        shutil.rmtree(work)
    build_a(work, scale, state)
    if cond == "A":
        work.rename(out)
        return out
    out.mkdir(parents=True)
    if cond == "B":
        shutil.copytree(work / "projects", out / "projects")
    else:
        flatten(work / "projects", out / "projects")
    if state == "fresh":
        shutil.copytree(work / "inbox", out / "inbox")
    shutil.rmtree(work)
    return out


def cmd_build(args):
    out = build(args.cond, args.scale, args.state, Path(args.out).resolve())
    n = sum(1 for p in out.rglob("*") if p.is_file())
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"{out}: {n} files, {size / 1024:.0f} KB")


# ---- 1 セッション走らせて数える ----------------------------------------------------------

def run_claude(rundir: Path, prompt: str, model: str, max_turns: int) -> tuple[dict, str, float, int]:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--setting-sources", "project", "--strict-mcp-config", "--max-turns", str(max_turns),
           "--allowedTools", ALLOWED_TOOLS]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=rundir, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=1800)
    elapsed = time.time() - t0
    out = proc.stdout
    try:
        res = json.loads(out)
    except json.JSONDecodeError:
        i = out.find("{")
        res = json.loads(out[i:]) if i >= 0 else {"result": out, "error": "no json"}
    return res, proc.stderr[-2000:], elapsed, proc.returncode


def find_transcript(session_id: str) -> Path | None:
    for _ in range(10):
        hits = list((Path.home() / ".claude" / "projects").glob(f"*/{session_id}.jsonl"))
        if hits:
            return hits[0]
        time.sleep(1)
    return None


def paths_in(name: str, inp: dict, rundir: Path) -> list[str]:
    prefix = str(rundir) + "/"
    if name in ("Read", "Write", "Edit"):
        raw = [inp.get("file_path", "")]
    elif name in ("Grep", "Glob"):
        raw = [inp.get("path") or "."]
    elif name == "Bash":
        cmd = (inp.get("command") or "").replace(prefix, "")
        cmd = re.sub(r"\S*/\.claude/\S*", "", cmd)  # Claude Code 自身のメモリ（~/.claude/projects/…）は作業スペースの外
        raw = re.findall(r"(?:projects|inbox)/[^\s\"'`|;)>]*", cmd)
        if not raw and re.search(r"\b(grep|rg|find|ls|tree|cat|sed|head|tail)\b", cmd):
            raw = ["."]
    else:
        raw = []
    return [p.replace(prefix, "") for p in raw if p]


def kind_of(name: str, inp: dict) -> str:
    if name == "Read":
        return "read"
    if name in ("Grep", "Glob"):
        return "search"
    if name in ("Write", "Edit"):
        return "write"
    if name == "Bash":
        cmd = inp.get("command") or ""
        if re.search(r"\b(cat|sed|head|tail|less|more)\b", cmd):
            return "read"
        if re.search(r"\b(grep|rg|find|ls|tree|wc)\b", cmd):
            return "search"
    return "other"


TASK_RE = re.compile(r"projects/([^/\s]+)/tasks/([^/\s]+)")
DOCS_RE = re.compile(r"projects/([^/\s]+)/docs/([^/\s]+)")


def other_task_pred(cond: str, exp: str, stage: int | None, baseline: set[str]):
    """「現在のタスク以外に立ち入った」と数える path の条件。実験ごとに現在のタスクの定義が違う。"""
    base_tasks = {f"projects/{m[1]}/tasks/{m[2]}" for m in map(TASK_RE.search, baseline) if m and m[2] != "index.md"}
    if cond in ("A", "B"):
        def f(p: str) -> bool:
            m = TASK_RE.search(p)
            if not m or m[2] == "index.md":
                return False
            key = f"projects/{m[1]}/tasks/{m[2]}"
            if exp == "chain":
                return key in base_tasks  # 自分が作ったタスク以外は全部「他」
            if exp == "newtask":  # 元からあったタスクの中身。自分が切った新タスクは数えない
                return key in base_tasks and (key != CURRENT_TASK or "/references/" in p)
            return key != CURRENT_TASK
    else:
        def f(p: str) -> bool:
            m = DOCS_RE.search(p)
            if not m:
                return False
            if exp in ("chain", "newtask"):  # 元からあった資料だけ。自分が書いた資料は数えない
                return f"projects/{m[1]}/docs/{m[2]}" in baseline
            return m[2] not in ESTIMATE_SOURCES
    return f


def analyze(tpath: Path, rundir: Path, is_other) -> dict:
    seen, tools = set(), []
    m = dict(in_total=0, ctx_final=0, out_total=0, turns=0, reads=0, searches=0, writes=0,
             other_task=0, inbox_reads=0, denied=0, model="")
    for line in tpath.read_text(encoding="utf-8").splitlines():
        try:
            o = json.loads(line)
        except json.JSONDecodeError:
            continue
        if o.get("type") == "assistant":
            msg = o.get("message", {})
            mid, u = msg.get("id"), msg.get("usage") or {}
            if mid and mid not in seen:
                seen.add(mid)
                m["turns"] += 1
                m["model"] = msg.get("model", m["model"])
                inp = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                m["in_total"] += inp
                m["ctx_final"] = inp
                m["out_total"] += u.get("output_tokens", 0)
            for b in msg.get("content", []):
                if b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name", ""), b.get("input") or {}
                kind = kind_of(name, inp)
                ps = paths_in(name, inp, rundir)
                if any(p.startswith(str(Path.home() / ".claude")) for p in ps):
                    kind = "other"  # Claude Code 自身のメモリ（MEMORY.md）の読み。作業スペースの外なので数えない
                if kind in ("read", "search", "write"):
                    m[kind + ("es" if kind == "search" else "s")] += 1
                if kind in ("read", "search") and any(is_other(p) for p in ps):
                    m["other_task"] += 1
                if kind in ("read", "search") and any(p.startswith("inbox/") or "/inbox/" in p for p in ps):
                    m["inbox_reads"] += 1
                tools.append([kind, name, ps[:6]])
        elif o.get("type") == "user":
            c = o.get("message", {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if b.get("type") == "tool_result" and b.get("is_error") and "[agent-ws]" in json.dumps(b.get("content"), ensure_ascii=False):
                        m["denied"] += 1
    m["tools"] = tools
    return m


def verdict_estimate(text: str) -> str:
    t = text.replace(",", "").replace("，", "")
    hits = {k for k, (a, b) in ANSWERS.items() if a in t or b in t}
    if hits == {"correct"}:
        return "correct"
    if not hits:
        return "none"
    if "correct" in hits:
        return "mixed:" + "+".join(sorted(hits - {"correct"}))
    return "+".join(sorted(hits))


def score_newtask(text: str) -> tuple[list[str], list[dict]]:
    req = [k for k, pat in REQUIRED.items() if re.search(pat, text)]
    stale = []
    for k, pat in STALE.items():
        for mt in list(re.finditer(pat, text))[:3]:
            s, e = max(0, mt.start() - 40), min(len(text), mt.end() + 40)
            stale.append({"key": k, "context": " ".join(text[s:e].split())})
    return req, stale


def pick_task(verdict: str, final: str, changed: list[str]) -> str:
    """estimate = 見積に着手した / asked = どのタスクか聞き返した / other = 別のことをした"""
    if verdict != "none" or any(("estimate" in p or "見積" in p) for p in changed):
        return "estimate"
    if not changed and re.search(r"教えてください|教えていただけ|どの(案件|タスク|作業|プロジェクト)|特定でき|指定してください|お知らせください"
                                 r"|判断できま|分かりません|わかりません|どれを|どちら|指している|指すか|お教え", final):
        return "asked"
    return "estimate" if re.search(r"見積|コスト試算", final) and changed else "other"


def doc_location(changed: list[str], cond: str) -> str:
    mds = [p for p in changed if p.endswith(".md") and not p.endswith("index.md")]
    if not mds:
        return "response_only"
    for p in mds:
        if cond in ("A", "B"):
            mt = TASK_RE.search(p)
            if mt:
                return "current_task" if p.startswith(CURRENT_TASK + "/") else "new_task"
        if re.match(r"projects/[^/]+/", p):
            return "project_dir"
    return "elsewhere"


def run_session(exp: str, stage: int | None, scale: str, cond: str, model: str, i: int,
                rundir: Path, prompt: str, baseline: set[str], max_turns: int, chain_id: str | None) -> dict:
    before = snapshot(rundir)
    res, stderr, elapsed, rc = run_claude(rundir, prompt, model, max_turns)
    after = snapshot(rundir)
    changed = sorted(p for p, h in after.items() if before.get(p) != h)
    changed_text = changed_text_of(rundir, changed)
    final = res.get("result") or ""
    sid = res.get("session_id", "")
    tpath = find_transcript(sid) if sid else None
    met = analyze(tpath, rundir, other_task_pred(cond, exp, stage, baseline)) if tpath else {}
    text_all = final + "\n" + changed_text
    rec = dict(ts=datetime.now().isoformat(timespec="seconds"), exp=exp, stage=stage, chain_id=chain_id,
               scale=scale, cond=cond, model=model, i=i, rundir=str(rundir), session_id=sid,
               elapsed=round(elapsed, 1), returncode=rc, num_turns=res.get("num_turns"),
               cost_usd=res.get("total_cost_usd"), is_error=res.get("is_error"),
               permission_denials=len(res.get("permission_denials") or []),
               transcript=str(tpath) if tpath else None, stderr=stderr[-500:] if rc else "",
               changed_files=changed, has_next=bool(re.search(r"次の一手|次回|次のセッション|TODO|残作業", changed_text)),
               final_text=final[:6000], changed_text=changed_text[:30000],
               baseline=sorted(baseline) if exp == "chain" else None)
    rec.update({k: v for k, v in met.items()})
    if exp in ("trap", "chain", "base"):
        rec["verdict"] = verdict_estimate(text_all)
        rec["task_pick"] = pick_task(rec["verdict"], final, changed)
    if exp == "newtask":
        req, stale = score_newtask(text_all)
        rec.update(required_hits=req, required_n=len(req), stale_hits=stale, stale_n=len(stale),
                   doc_location=doc_location(changed, cond))
    if exp == "chain" and stage == 1:
        rec["left_behind"] = changed
    return rec


def append_result(rec: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_one(exp: str, scale: str, cond: str, model: str, i: int, tag: str, results: Path, max_turns: int) -> list[dict]:
    rundir = RUNS_DIR / tag / f"{exp}_{scale}_{model}_{cond}{i}"
    state = "fresh" if exp == "chain" else "doing"
    build(cond, scale, state, rundir)
    baseline = set(snapshot(rundir))
    recs = []
    if exp == "chain":
        cid = f"{tag}_{scale}_{model}_{cond}{i}"
        r1 = run_session(exp, 1, scale, cond, model, i, rundir, PROMPTS["chain1"], baseline, max_turns, cid)
        append_result(r1, results)
        r2 = run_session(exp, 2, scale, cond, model, i, rundir, PROMPTS["chain2"], baseline, max_turns, cid)
        append_result(r2, results)
        recs = [r1, r2]
    else:
        r = run_session(exp, None, scale, cond, model, i, rundir, PROMPTS[exp], baseline,
                        1 if exp == "base" else max_turns, None)
        append_result(r, results)
        recs = [r]
    for r in recs:
        print(f"[{r['ts']}] {exp}{'/S' + str(r['stage']) if r['stage'] else ''} {scale} {model} {cond}{i}: "
              f"in={r.get('in_total')} ctx={r.get('ctx_final')} cost={r.get('cost_usd')} turns={r.get('turns')} "
              f"other={r.get('other_task')} inbox={r.get('inbox_reads')} denied={r.get('denied')} "
              f"verdict={r.get('verdict', r.get('required_n'))} {r.get('elapsed')}s", flush=True)
    return recs


def cmd_run(args):
    tag = args.tag or datetime.now().strftime("%Y%m%d_%H%M%S")
    results = Path(args.results).resolve() if args.results else RESULTS / "runs.jsonl"
    conds = args.conds.split(",")
    jobs = [(cond, i) for i in range(args.n) for cond in conds]  # A0 B0 C0 A1 ... と交互に
    print(f"tag={tag} exp={args.exp} scale={args.scale} model={args.model} jobs={len(jobs)} -> {results}", flush=True)
    if args.jobs > 1:
        with concurrent.futures.ThreadPoolExecutor(args.jobs) as ex:
            futs = [ex.submit(run_one, args.exp, args.scale, c, args.model, i, tag, results, args.max_turns) for c, i in jobs]
            for f in futs:
                f.result()
    else:
        for c, i in jobs:
            run_one(args.exp, args.scale, c, args.model, i, tag, results, args.max_turns)


def cmd_rescore(args):
    """transcript から数え直す（数え方を直したあとに全行へ適用する）。正誤は最終応答と差分から再判定する。"""
    path = Path(args.results).resolve() if args.results else RESULTS / "runs.jsonl"
    recs, out = load_results(path), []
    for r in recs:
        tp, rundir = r.get("transcript"), Path(r["rundir"])
        changed = r.get("changed_files", [])
        baseline = set(r.get("baseline") or [])
        if not baseline and rundir.exists():
            baseline = set(snapshot(rundir)) - set(changed)  # 実行前のツリー = 今のツリー − 書き換えたもの
        if tp and Path(tp).exists():
            r.update(analyze(Path(tp), rundir, other_task_pred(r["cond"], r["exp"], r.get("stage"), baseline)))
        if r.get("stage") == 1 and "changed_text" not in r:
            out.append(r)  # S2 が同じファイルを書き換えた後なので、S1 の正誤は実行時の判定を保つ
            continue
        changed_text = r.get("changed_text") if "changed_text" in r else changed_text_of(rundir, changed)
        text_all = (r.get("final_text") or "") + "\n" + changed_text
        if r["exp"] in ("trap", "chain", "base"):
            r["verdict"] = verdict_estimate(text_all)
            r["task_pick"] = pick_task(r["verdict"], r.get("final_text") or "", r.get("changed_files", []))
        if r["exp"] == "newtask":
            req, stale = score_newtask(text_all)
            r.update(required_hits=req, required_n=len(req), stale_hits=stale, stale_n=len(stale), doc_location=doc_location(r.get("changed_files", []), r["cond"]))
        out.append(r)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out), encoding="utf-8")
    print(f"rescored {len(out)} records -> {path}")


# ---- 集計 ------------------------------------------------------------------------------

def perm_p(a: list[float], b: list[float]) -> float | None:
    if len(a) < 2 or len(b) < 2:
        return None
    obs = abs(statistics.mean(a) - statistics.mean(b))
    pool = a + b
    n, cnt, tot = len(a), 0, 0
    for idx in itertools.combinations(range(len(pool)), n):
        x = [pool[k] for k in idx]
        y = [pool[k] for k in range(len(pool)) if k not in idx]
        tot += 1
        cnt += abs(statistics.mean(x) - statistics.mean(y)) >= obs - 1e-9
    return cnt / tot


def short_model(m: str) -> str:
    return "haiku" if "haiku" in (m or "") else "sonnet" if "sonnet" in (m or "") else (m or "?")


def fmt(v, key):
    if v is None:
        return "—"
    if key == "cost_usd":
        return f"{v:.3f}"
    if key in ("in_total", "ctx_final"):
        return f"{v:,.0f}"
    return f"{v:g}"


def stat_cell(xs: list, key: str) -> str:
    xs = [x for x in xs if x is not None]
    if not xs:
        return "—"
    return f"{fmt(statistics.median(xs), key)} ({fmt(min(xs), key)}〜{fmt(max(xs), key)})"


def load_results(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


KEYS = ["in_total", "ctx_final", "cost_usd", "turns", "reads", "searches", "other_task", "inbox_reads", "denied"]


def cmd_summary(args):
    recs = load_results(Path(args.results).resolve() if args.results else RESULTS / "runs.jsonl")
    if args.tag:
        recs = [r for r in recs if r.get("chain_id", "").startswith(args.tag) or args.tag in r.get("rundir", "")]
    groups: dict[tuple, list[dict]] = {}
    for r in recs:
        groups.setdefault((r["exp"], r.get("stage"), r["scale"], r["model"], r["cond"]), []).append(r)
    out = {"groups": {}, "pairs": {}}
    lines = ["| 実験 | 規模 | モデル | 条件 | n | 処理した入力 | 最終文脈 | 費用 USD | ターン | Read | 検索 | 他タスク | inbox | 拒否 | 正誤 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for key in sorted(groups, key=lambda k: (k[0], k[1] or 0, k[2], k[3], k[4])):
        exp, stage, scale, model, cond = key
        g = groups[key]
        cells = {k: stat_cell([r.get(k) for r in g], k) for k in KEYS}
        if exp == "newtask":
            reviewed = [r.get("stale_reviewed") for r in g if r.get("stale_reviewed") is not None]
            verdict = (f"必須 {stat_cell([r.get('required_n') for r in g], 'n')} / 混入 機械 {sum(r.get('stale_n', 0) for r in g)}"
                       + (f"・目視 {sum(reviewed)}" if reviewed else "") + " / 置き場 "
                       + ",".join(sorted({r.get("doc_location", "?") for r in g})))
        elif stage == 1:
            verdict = f"次の一手を残した {sum(1 for r in g if r.get('has_next'))}/{len(g)}"
        else:
            vc: dict[str, int] = {}
            for r in g:
                k = r.get("verdict", "?")
                if k == "none":
                    k = "none/" + r.get("task_pick", "?")
                vc[k] = vc.get(k, 0) + 1
            verdict = " ".join(f"{k}×{v}" for k, v in sorted(vc.items()))
        label = f"{exp}{'/S' + str(stage) if stage else ''}"
        lines.append(f"| {label} | {scale} | {short_model(model)} | {cond} | {len(g)} | " + " | ".join(cells[k] for k in KEYS) + f" | {verdict} |")
        out["groups"]["/".join(map(str, key))] = {k: [r.get(k) for r in g] for k in KEYS + ["verdict", "required_n", "stale_n", "doc_location"]}
    plines = ["", "| 実験 | 規模 | モデル | 対 | p(処理した入力) | p(費用) | p(他タスク) |", "|---|---|---|---|---|---|---|"]
    for key in sorted({k[:4] for k in groups}):
        a = groups.get(key + ("A",))
        for other in ("B", "C"):
            b = groups.get(key + (other,))
            if not a or not b:
                continue
            ps = {k: perm_p([r.get(k) for r in a if r.get(k) is not None], [r.get(k) for r in b if r.get(k) is not None])
                  for k in ("in_total", "cost_usd", "other_task")}
            out["pairs"]["/".join(map(str, key)) + f"/A-{other}"] = ps
            exp, stage, scale, model = key
            plines.append(f"| {exp}{'/S' + str(stage) if stage else ''} | {scale} | {short_model(model)} | A/{other} | " +
                          " | ".join("—" if v is None else f"{v:.3f}" for v in ps.values()) + " |")
    text = "\n".join(lines + plines)
    print(text)
    write(RESULTS / "summary.md", text + "\n")
    write(RESULTS / "summary.json", json.dumps(out, ensure_ascii=False, indent=1))


# ---- 図 --------------------------------------------------------------------------------

def dotplot(rows: list[tuple[str, list[tuple[str, str, list[float]]]]], lo: float, hi: float, ticks: list[float],
            f, unit: str, title: str) -> str:
    """rows: [(段のラベル, [(系列名, 色, 値の一覧), ...]), ...]。点 = 1 回、縦線 = 中央値。"""
    W, L, R, rowh, gap = 700, 260, 680, 22, 14
    y = 34
    total_h = 34 + sum(len(s) * rowh + gap for _, s in rows) + 30
    parts = [f'<svg viewBox="0 0 {W} {total_h}" role="img" aria-label="{title}" '
             'font-family="-apple-system, BlinkMacSystemFont, Hiragino Sans, Noto Sans JP, sans-serif" font-size="12">',
             f'<text x="8" y="16" fill="var(--muted)">{title}（点 = 1 回の実行、縦線 = 中央値。左ほど少ない）</text>']

    def x(v):
        v = min(max(v, lo), hi)
        return L + (v - lo) / (hi - lo) * (R - L)

    for label, series in rows:
        parts.append(f'<text x="8" y="{y + rowh}" fill="var(--ink)" font-weight="600">{label}</text>')
        for name, color, xs in series:
            if not xs:
                continue
            med = statistics.median(xs)
            parts.append(f'<text x="{L - 8}" y="{y + 15}" text-anchor="end" fill="{color}">{name}</text>')
            parts.append(f'<line x1="{L}" x2="{R}" y1="{y + 11}" y2="{y + 11}" stroke="var(--line)"/>')
            for v in xs:
                parts.append(f'<circle cx="{x(v):.1f}" cy="{y + 11}" r="4.5" fill="{color}" fill-opacity="0.55"/>')
            parts.append(f'<line x1="{x(med):.1f}" x2="{x(med):.1f}" y1="{y + 2}" y2="{y + 20}" stroke="{color}" stroke-width="2.5"/>')
            parts.append(f'<text x="{R + 6}" y="{y + 15}" fill="{color}" font-size="11">{f(med)}</text>')
            y += rowh
        y += gap
    for t in ticks:
        parts.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="{y}" y2="{y + 5}" stroke="var(--muted)"/>')
        parts.append(f'<text x="{x(t):.1f}" y="{y + 18}" text-anchor="middle" fill="var(--muted)" font-size="11">{f(t)}</text>')
    parts.append(f'<text x="{R}" y="{y + 18}" fill="var(--muted)" font-size="11"> {unit}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


COND_NAME = {"A": ("agent-ws", "var(--accent)"), "B": ("同じ構造・仕組みなし", "var(--warn)"), "C": ("導入前（資料の山＋メモ）", "var(--muted)")}
ROW_LABEL = {("trap", None): "続きをやって（罠）", ("chain", 2): "引き継ぎの 2 セッション目", ("chain", 1): "引き継ぎの 1 セッション目",
             ("newtask", None): "新規タスク（進め方の資料）", ("base", None): "下駄（1 ターン）"}


def cmd_fig(args):
    recs = load_results(Path(args.results).resolve() if args.results else RESULTS / "runs.jsonl")
    groups: dict[tuple, list[dict]] = {}
    for r in recs:
        if r["exp"] == "base":
            continue
        groups.setdefault((r["exp"], r.get("stage"), r["scale"], r["model"]), []).append(r)

    def rows_for(key):
        rows = []
        for gk in sorted(groups, key=lambda k: (k[0], k[1] or 0, k[2], k[3])):
            label = f"{ROW_LABEL.get((gk[0], gk[1]), gk[0])}・{gk[2]}・{short_model(gk[3])}"
            series = []
            for cond in ("A", "B", "C"):
                xs = [r[key] for r in groups[gk] if r.get("cond") == cond and r.get(key) is not None]
                if xs:
                    series.append((COND_NAME[cond][0], COND_NAME[cond][1], xs))
            rows.append((label, series))
        return rows

    all_in = [r["in_total"] for r in recs if r.get("in_total")]
    hi = max(all_in) if all_in else 500_000
    hi = (int(hi / 100_000) + 1) * 100_000
    ticks = list(range(0, hi + 1, 100_000 if hi <= 800_000 else 200_000))
    write(RESULTS / "fig_in_total.svg", dotplot(rows_for("in_total"), 0, hi, ticks, lambda v: f"{v / 1000:.0f}k", "トークン", "処理した入力の合計（1 セッション）"))
    all_c = [r["cost_usd"] for r in recs if r.get("cost_usd")]
    chi = (int((max(all_c) if all_c else 0.3) / 0.1) + 1) * 0.1
    write(RESULTS / "fig_cost.svg", dotplot(rows_for("cost_usd"), 0, chi, [round(t * 0.1, 1) for t in range(int(chi / 0.1) + 1)],
                                            lambda v: f"${v:.2f}", "USD", "費用（Claude Code が定価で計算）"))
    write(RESULTS / "fig_other.svg", dotplot(rows_for("other_task"), 0, 8, list(range(0, 9)), lambda v: f"{v:g}", "回",
                                             "現在のタスク以外に立ち入った回数"))
    print("wrote", RESULTS / "fig_in_total.svg", RESULTS / "fig_cost.svg", RESULTS / "fig_other.svg")


def md_table_to_html(md: str) -> str:
    """summary.md の表（| 区切り）を HTML の table にする。数字のセルは右寄せ。"""
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r"-+", c) for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f'<td class="num">{c}</td>' if re.match(r"[\d—$]", c) else f"<td>{c}</td>" for c in cells) + "</tr>")
        else:
            if in_table:
                out.append("</table>")
                in_table = False
    if in_table:
        out.append("</table>")
    return "\n".join(out)


def cmd_report(args):
    """summary.md と fig_*.svg から、報告書に貼る HTML 断片（results/report_fragment.html）を作る。"""
    md = (RESULTS / "summary.md").read_text(encoding="utf-8")
    parts = [md_table_to_html(md)]
    for name, cap in (("fig_in_total", "処理した入力トークンの合計（1 セッション）"), ("fig_cost", "費用（定価）"), ("fig_other", "現在のタスク以外に立ち入った回数")):
        p = RESULTS / f"{name}.svg"
        if p.exists():
            parts.append(f"<figure>\n{p.read_text(encoding='utf-8')}\n<figcaption>{cap}</figcaption>\n</figure>")
    write(RESULTS / "report_fragment.html", "\n\n".join(parts) + "\n")
    print("wrote", RESULTS / "report_fragment.html")


# ---- 引数 ------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="bench/run.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build", help="実行ディレクトリを 1 つ組む")
    p.add_argument("--cond", choices="ABC", default="A")
    p.add_argument("--scale", choices=["small", "large"], default="small")
    p.add_argument("--state", choices=["doing", "fresh"], default="doing")
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("run", help="実験を走らせる")
    p.add_argument("--exp", choices=["trap", "chain", "newtask", "base"], required=True)
    p.add_argument("--scale", choices=["small", "large"], default="large")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--conds", default="A,B,C")
    p.add_argument("-n", type=int, default=5)
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--max-turns", type=int, default=30)
    p.add_argument("--tag")
    p.add_argument("--results")
    p.set_defaults(fn=cmd_run)
    p = sub.add_parser("rescore", help="transcript から数え直す")
    p.add_argument("--results")
    p.set_defaults(fn=cmd_rescore)
    p = sub.add_parser("summary", help="集計する")
    p.add_argument("--results")
    p.add_argument("--tag")
    p.set_defaults(fn=cmd_summary)
    p = sub.add_parser("fig", help="点図を書く")
    p.add_argument("--results")
    p.set_defaults(fn=cmd_fig)
    sub.add_parser("report", help="報告書に貼る HTML 断片を作る").set_defaults(fn=cmd_report)
    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
