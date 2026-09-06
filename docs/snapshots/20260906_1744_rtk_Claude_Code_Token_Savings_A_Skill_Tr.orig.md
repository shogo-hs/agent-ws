Title: rtk Claude Code Token Savings: A Skill Trial Benchmark

URL Source: https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/

Markdown Content:
[![Image 1: Ai logo](https://blog.jetbrains.com/wp-content/uploads/2024/01/JetBrains-AI.svg)](https://blog.jetbrains.com/ai/)
Supercharge your tools with AI-powered features inside many JetBrains products

[AI](https://blog.jetbrains.com/ai/category/ai/)[AI Assistant](https://blog.jetbrains.com/ai/category/ai-assistant/)

## Does “rtk” skill really cut agent tokens by 60–90%? We tested it

![Image 2: Denis Shiryaev](https://blog.jetbrains.com/wp-content/uploads/2025/10/IMG_6963-e1759851102680-200x200.jpg)

July 20, 2026

Does “rtk” reduce Claude Code token usage?

Part 2 of a series where we take public “token saving” add-ons for coding agents and run the same paired A/B benchmark against each of them. Part 1 was the [caveman skill](https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/) (advertised −65%, measured −8.5%).

> **TL;DR: rtk advertised saving: 60–90%. Measured on real agent work: +7.6% more expensive at low reasoning effort (p=0.004), ±0% at high effort. Setup: Claude Code 2.1.201 · claude-sonnet-5 low and high efforts · SkillsBench. Task quality: unchanged in both arms, at both effort levels.**

What rtk promises

−60–90%

token cut per its README; −80% in its own demo session

Best it could do here

≈−3%

most of what the model reads never passes through rtk — computed for free before spending a cent

What we actually paid

+7.6%

MORE per typical task with rtk installed (80 tasks, low effort, p=0.004). With high effort: no difference at all

Task quality

no change

across 151 paired tasks: 10 slightly better, 8 slightly worse, 133 identical — a coin flip

## Why we ran this

[rtk (“Rust Token Killer”)](https://github.com/rtk-ai/rtk) is a CLI proxy with a simple, appealing pitch: your agent runs `git status`, rtk intercepts it, runs the real command, and hands the model a compressed version of the output — `* master / M a.txt / ?? b.txt` instead of eleven lines of porcelain. A Claude Code PreToolUse hook rewrites eligible shell commands transparently, so the model doesn’t even have to know rtk exists. The README promises **60–90% less token consumption** and walks through a 30-minute session where 118k tokens of command output become 24k.

The compression itself is real and often tasteful. Here is rtk on a live repo, captured from our test container:

# git status                              # rtk git status
On branch master                          * master
Changes not staged for commit:             M a.txt
  (use "git add <file>..." to update…)   ?? b.txt
	modified:   a.txt
Untracked files:
  (use "git add <file>..." to include…)
	b.txt
no changes added to commit …

# python -m pytest  (19 lines)            # rtk pytest
…full pytest output…                      Pytest: 2 passed, 1 failed
                                          Failures:
                                          1. [FAIL] test_fail
                                               test_demo.py:3: in test_fail
                                               E  AssertionError: one is not two
We liked the idea enough to test it properly. Two questions the README doesn’t answer:

First, **how much of a real agent session is Bash output at all?** The savings table assumes the agent shells out for everything. But Claude Code reads files with its built-in `Read` tool, searches with `Grep`, and both bypass the Bash hook completely (rtk’s docs acknowledge this). Whatever those tools carry, rtk can never touch.

Second, **does compression cost correctness?** A filter that summarizes test output is making an editorial judgment about what the model needs. If it drops the one line that mattered, the agent re-runs commands, reads files raw, or, worse, declares victory on a failing build. Token savings that come with a quality tax are not savings.

## Setup

**Harness**Harbor 0.18 – Docker sandboxes, task verifiers, paired runs
**Agent**Claude Code 2.1.201, headless, `bypassPermissions`, pinned in both arms
**Model**`claude-sonnet-5` – full run twice: at low and at high reasoning effort
**Benchmark**SkillsBench, 86 of 87 tasks, auto-graded 0–1 with partial credit
**Arm A**stock Claude Code
**Arm B**rtk v0.43.0 exactly as `rtk init -g` ships it: binary + PreToolUse hook + RTK.md
**Volume**4 paired runs (10-task smoke, same 10 at k=3, full 86 at low effort, full 86 at high effort) total of 425 billed trials, ≈USD 320 (Harbor-recorded USD 317 plus reconstructed subagent spend)

Because the hook rewrites every eligible `Bash` call mechanically, arm B measures rtk’s _as-shipped ceiling_: no “did the model remember to use it” gap to argue about. Every with-rtk trial also persists rtk’s own audit log and analytics database, as proof the treatment actually fired.

## Finding 1: Most agent bytes never touch the hook

Before spending anything we replayed 83 existing baseline transcripts (same model, same benchmark) and asked: if rtk had been installed, what could it even have touched?

How much of an agent's shell work can rtk even touch?

1,056 shell commands from 83 real agent sessions, sorted by whether rtk has a rule for them.

rtk can rewrite these (git, ls, cat, pytest…)

349

no rule for these (python3, project scripts, loops…)

525

skipped on purpose (tricky shell syntax)

182

Only 1 in 3 shell commands is something rtk can rewrite. Half of what agents actually run — python3, project scripts, shell loops — isn't in rtk's rulebook at all.

data as table
| series | value |
| --- | --- |
| rtk can rewrite these (git, ls, cat, pytest…) | 349 |
| no rule for these (python3, project scripts, loops…) | 525 |
| skipped on purpose (tricky shell syntax) | 182 |

Everything the model reads back from its tools — and the slice rtk can shrink

1.9 million characters of tool output from those same sessions. rtk can only compress the blue slice; the rest bypasses it entirely.

shell output rtk can compress shell output it has no rule for file reading and search tools that skip rtk

20%

46%

34%

Only a fifth of what the model reads is even compressible by rtk. Squeeze all of it by 70% and the total saving still tops out around 3% of the bill.

data as table
| segment | chars | % |
| --- | --- | --- |
| shell output rtk can compress | 373,339 | 19.7 |
| shell output it has no rule for | 879,326 | 46.3 |
| file reading and search tools that skip rtk | 646,613 | 34.0 |

Two structural reasons. First, Claude Code reads files with its built-in `Read`/`Grep` tools, which bypass the Bash hook entirely; rtk’s own README admits this in a footnote. Second, half of what agents run in a shell is `python3 …` and other uncovered commands, and a sixth uses pipes-to-files, heredocs and substitutions that rtk deliberately refuses to rewrite. What’s left, 33% of Bash calls, carries just under 20% of tool-result chars; and tool results are themselves only a slice of what a session bills as input, because the same context is re-read on every turn. Squeeze rtk’s whole share by 70% and the cap works out to **≈3% of input tokens**. This number cost nothing to compute, and it predicted the outcome.

## Finding 2: No token savings; but a small, significant cost _increase_

We ran the ladder the caveman eval taught us to run. The k=1 smoke on ten deliberately Bash-heavy tasks (rtk’s best case) showed the rtk arm a median +35% more expensive. Alarming, until you know that identical attempts of the same task in the same arm differ by a median 22% in cost anyway. At k=3 most of the scare evaporated into noise (Wilcoxon p≈0.65), exactly as a k=1 mirage should.

Then the full 86 tasks gave the noise-resistant answer, and it wasn’t zero. Across 80 clean pairs the with-rtk arm came out a median **+7.6% more expensive per task** (p=0.004, after correcting a cost-accounting gap we found along the way), on **+13.8% more turns** (p=0.03) and **+14.3% more cache reads** (p=0.008). Meanwhile “new input”; the only token class rtk actually compresses, moved just +3.2% (p=0.23): a flat null precisely where the ceiling analysis said the entire benefit had to live.

Fresh tokens used WITH rtk vs without — every bar should point the other way

Each bar: how much more new text entered the model's context on a typical task with rtk installed. rtk promised 60–90% LESS.

first quick test — 10 shell-heavy tasks, one attempt

+36.3%

same 10 tasks, three attempts each

+12.6%

all 86 tasks, low reasoning effort

+3.2%

all 86 tasks, high reasoning effort

+4.3%

Why the shrinking bars? Small samples exaggerate — that +36% came from 10 tasks run once. More data pulls it toward the truth: a few percent MORE, never less. 'Fresh tokens' is exactly the thing rtk compresses, so this is where its savings were supposed to show up.

data as table
| series | value |
| --- | --- |
| first quick test — 10 shell-heavy tasks, one attempt | +36.3% |
| same 10 tasks, three attempts each | +12.6% |
| all 86 tasks, low reasoning effort | +3.2% |
| all 86 tasks, high reasoning effort | +4.3% |

Where the extra money goes (all 86 tasks, low effort)

How a typical task changed with rtk installed. The one thing rtk shrinks barely moved — sessions just ran longer.

fresh tokens — the thing rtk compresses (within noise)

+3.2%

text the model writes (within noise)

+6.7%

cost — what you pay (statistically solid)

+7.6%

conversation steps (solid)

+13.8%

re-reading its own history each step (solid)

+14.3%

The fingerprint of sessions running longer, not of compression working: more steps means the model re-reads everything so far more times — and that's what you pay for. ('Solid' = unlikely to be chance: p=0.004 for cost, 0.03 for steps, 0.008 for re-reading.)

data as table
| series | value |
| --- | --- |
| fresh tokens — the thing rtk compresses (within noise) | +3.2% |
| text the model writes (within noise) | +6.7% |
| cost — what you pay (statistically solid) | +7.6% |
| conversation steps (solid) | +13.8% |
| re-reading its own history each step (solid) | +14.3% |

The more commands the hook rewrote, the larger the penalty. On the same corrected cost basis as the headline result, heavily exposed task pairs cost about 24% more than baseline, versus 5% for pairs the hook barely touched. Controlling for task difficulty did not reproduce this pattern, so harder tasks using more Bash does not appear to explain it. Transcript forensics found no single villain: one genuinely broken rewrite (compound `find` predicates turned into usage errors and retries), a few compression-induced re-reads, and a lot of ordinary variance on the extreme pairs. A thin, systematic tax rather than a dramatic failure.

One real task, watched step by step

How much the model had to re-read at every step of the same task, with and without rtk. The rtk session took MORE steps and ended with a BIGGER pile.

with-rtk no-rtk

20k

40k

60k

80k

step in the session

Each rtk-compressed result is indeed smaller — but this session took seven extra steps, and every extra step re-reads the whole history again. That re-reading is most of an agent's bill.

data as table
| series | steps | final context (tokens) |
| --- | --- | --- |
| with-rtk | 41 | 78,472 |
| no-rtk | 34 | 68,344 |

## Finding 3: At high effort, even the penalty disappears

“You only tested at low reasoning effort” was the obvious critique, so we ran all 86 tasks again at high effort – the most expensive single run of the series. Result: the cost penalty does not replicate there. Median paired delta **+0.1%** (p=0.99), turns +0.0 (p=0.74), quality still tied. At high effort, the model seems to waste fewer turns reacting to compressed output; though at k=1 all we can say is that the penalty didn’t show up there, not that the two effort regimes probably differ. Either way, at no point did rtk _save_ anything.

Does it change when the model thinks harder? Low vs high effort

Solid square = low effort · hollow square = high effort. A marker on the zero line means rtk made no difference.

low effort high effort (hollow)

cost

conversation steps

re-reading its history

fresh tokens

text the model writes

−2%

+2%

+6%

+10%

+14%

At high effort the extra steps and re-reading vanish, and the cost penalty goes with them. But look at fresh tokens — the thing rtk compresses: flat at both settings. The promised savings never appear anywhere.

data as table
| row | low effort | high effort |
| --- | --- | --- |
| cost | 7.6% | 0.1% |
| conversation steps | 13.8% | 0% |
| re-reading its history | 14.3% | 0% |
| fresh tokens | 3.2% | 4.3% |
| text the model writes | 6.7% | 8.2% |

## Finding 4: Quality survives

The scary failure modes from rtk’s issue tracker including over-filtered test output, masked exit codes, pipes fed compressed text, they barely materialized. A forensic pass over the six smoke pairs with the biggest turn deltas found exactly one broken rewrite (the same compound-`find` failure mode the full run hit) and one case of the agent deliberately bypassing the hook, across ~150 Bash calls. In those transcripts no recovery files were read and no compressed pipe produced a wrong count (the full runs saw exactly one recovery-file read); the extra turns were overwhelmingly the model choosing different solution paths, not rtk confusion. On the full runs, task scores landed at 5 better / 4 worse / 71 tie at low effort and 5 / 4 / 62 at high (sign test p=1.0 both); showing the arms are statistically indistinguishable on quality, with partial credit counted.

One honest asterisk: on one task (`dialogue-parser`) rtk’s own binary refused to start inside the task’s image (it needs a newer glibc), so the with-rtk trial died at setup in both full runs while the plain arm scored 0.667. Paired analysis excludes that task from both arms, but it’s a real compatibility failure, not Docker noise. Even scoring every errored trial as zero, the arms stay tied (sign test p=1.0).

Did rtk break anything? The same 80 tasks, scored with and without it

Low-effort run shown; the high-effort run looks the same (5 better, 4 worse, 62 tied).

better with rtk (5)identical score (71)worse with rtk (4)

6%

89%

5%

A statistical coin flip — no damage, no improvement. (Honest caveat: ~80 tasks can only rule out big effects; catching a subtle few-point shift would take ~700 runs per side.)

data as table
| segment | tasks | % |
| --- | --- | --- |
| better with rtk (5) | 5 | 6.3 |
| identical score (71) | 71 | 88.8 |
| worse with rtk (4) | 4 | 5.0 |

## Finding 5: rtk’s own scoreboard vs the bill

This is the finding that explains the gap. Across the low-effort full run, rtk’s built-in analytics (`rtk gain`) reported **96.2 million tokens saved — 99.8% of everything it touched**; while the measured bill for the same trials went _up_. Three mechanisms make the scoreboard read high:

First, rtk counts the full raw output as its counterfactual. One `cat` of a 1.2 MB CSV logged 320k tokens “saved”, but Claude Code truncates any tool result long before 320k tokens; so the agent would have received a few thousand either way. The full run logged 190 of such giant reads at an average of ~506k “saved” tokens each. Second, rtk estimates tokens as chars÷4 at the moment of execution, while most of a session’s input cost is cached re-reads billed at a tenth of the price. Third, the hook simply never sees the majority of context. The scoreboard is grading its own homework.

What rtk promises per command — and what its own logs recorded

Hollow square = the README's promised cut · solid square = what actually happened across all 86 tasks, per rtk's own logs. (git's promises span −75…−92 by subcommand; hollow shows git status, −80.)

actually delivered promised (hollow)

git (status/log/add…) (only 4 uses)

test runners (pytest/cargo/mvn…)

grep / rg (search)

ls / tree / find / wc (listings)

cat / read (file dumps) † (not a real saving)

0%

−25%

−50%

−75%

−100%

† the grey marker is bookkeeping, not savings: rtk credits itself with the FULL size of giant files it 'compressed', but Claude Code would have cut those down anyway — nobody was ever going to be billed for them. It's the only row that beats its promise. Every honest row falls short.

data as table
| row | actually delivered | promised |
| --- | --- | --- |
| git (status/log/add…) (only 4 uses) | -44% | -80% |
| test runners (pytest/cargo/mvn…) | -47% | -90% |
| grep / rg (search) | -63% | -80% |
| ls / tree / find / wc (listings) | -63% | -80% |
| cat / read (file dumps) † (not a real saving) | -100% | -70% |

## Verdict

**Honest engineering, wrong counterfactual.** We wanted this one to win; the demo is genuinely satisfying to play with. The filters are real and often elegant; quality doesn’t suffer; the hook mechanism works exactly as designed. But on real agentic coding work the advertised 60–90% never had anywhere to live: the hook only ever sees about a fifth of the tool output, Claude Code already truncates the pathological outputs rtk brags about compressing, and the cached re-reads that dominate input cost bill at a tenth of the price. What’s left is a measured median **+7.6% cost increase at low effort and a flat zero at high effort**, a thin tax from a broken rewrite here and an extra exploration turn there, never a saving.

The deeper lesson generalizes beyond rtk: **a tool’s self-reported savings are a claim about its counterfactual, not about your bill.** rtk’s scoreboard said 96 million tokens saved while the invoice went up. If you evaluate any context-compression tool, measure the paired bill, not the tool’s diff.

## Methodology notes

Same discipline as part 1, learned the expensive way:

*   **Never trust k=1.** The run ladder was: free transcript replay → 1-trial wiring check → 10 Bash-heavy tasks at k=1 → the same 10 at k=3 → the full 86 at k=1, twice (low and high effort). Per-task scores flip freely between attempts in both arms; only paired deltas that survive the ladder get reported.
*   **Paired analysis only.** Every number compares the same task across arms under the same job; tasks that errored in either arm are excluded from both. Quality uses an exact sign test over non-ties; token/cost deltas use per-task medians plus Wilcoxon signed-rank, because arm totals are outlier-dominated, a single session crossing the 200k long-context pricing tier can bill 25× normal and flip a raw total.
*   **Endpoints pre-registered.** Primary: per-task paired delta in cost and in “new input” tokens (uncached + cache-creation; where compressed tool results actually land). Decided before any paid run, along with the adoption-stratified split.
*   **Adoption instrumented, not assumed.** Every with-rtk trial persists rtk’s hook audit log and its history.db, so we can prove per-trial that rewrites fired and executed – and distinguish “rtk saved nothing” from “rtk never ran,” which are very different findings. Depending on the run, the hook rewrote a third to a half of the Bash calls it saw (33–50%, after discounting our own per-trial wiring check); the model itself typed `rtk` six times in 86 trials.
*   **Provenance.** rtk v0.43.0 release binary (sha256-pinned), Claude Code 2.1.201 pinned in both arms, `claude-sonnet-5`, Harbor 0.18, SkillsBench with `bike-rebalance` excluded (its `allow_internet=false` crashes local Docker jobs). rtk, Harbor and SkillsBench are all Apache-2.0.

> Next in the series: drop a tool name and we’ll put it on the ladder. Few word enough. We test.

_P.S. The dithered chart style in this post is borrowed with admiration from [dither-kit](https://www.tripwire.sh/dither-kit) by grim — reimplemented from scratch as a dependency-free inline widget._

[](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#)

1.   [Why we ran this](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#why)
2.   [Setup](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#setup)
3.   [Finding 1: Most agent bytes never touch the hook](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#f1)
4.   [Finding 2: No token savings; but a small, significant cost increase](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#f2)
5.   [Finding 3: At high effort, even the penalty disappears](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#f3)
6.   [Finding 4: Quality survives](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#f4)
7.   [Finding 5: rtk’s own scoreboard vs the bill](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#f5)
8.   [Verdict](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#verdict)
9.   [Methodology notes](https://blog.jetbrains.com/ai/2026/07/rtk-claude-code-token-savings/#method)

## Discover more
