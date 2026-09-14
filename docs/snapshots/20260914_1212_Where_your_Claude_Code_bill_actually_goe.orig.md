Title: Where your Claude Code bill actually goes — I measured 66 of my own sessions

URL Source: https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e

Published Time: 2026-05-29T16:59:51Z

Markdown Content:
I kept getting surprised by my Claude Code bill. Not "shocked" — surprised. A short refactor would cost about what I expected, and then some long debugging session would quietly cost ten times more, and I couldn't have told you _why_ from the dashboard. Totals don't explain themselves.

So I did the boring thing: I parsed my own logs. Claude Code writes a JSONL transcript for every session under `~/.claude/projects/`, and every model turn in there records its token counts — input, output, and crucially the **cache-read** and **cache-write** counts. Multiply those by the published prices and you get a per-turn, per-session cost attribution. I ran it across 66 of my real sessions (filtered to ones that actually cost something: `cost > 0` and at least 3 model turns).

Here's what I found, and it's more interesting than "AI is expensive."

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#the-one-number-everyone-quotes-is-two-different-numbers) The one number everyone quotes is two different numbers

If you've read threads about Claude Code cost, you've seen the claim that "most of your spend is re-sent context." That's true — but _how_ true depends entirely on whether you weight by **session** or by **dollar**, and almost nobody says which they mean.

In my data:

*   **The median session re-sends only ~24% of its spend as cached context.** Most sessions are short — around 29 model turns, peaking near 45k tokens of context. In a short session, the context hasn't been re-sent that many times yet, so the model's actual _output_ and the _newly-written_ context are a bigger relative slice. Re-sent context is a minority.
*   **Pooled across all 66 sessions, re-sent context is 60% of total dollars.** When you weight by dollar, a handful of long, long-context sessions dominate the total — and in _those_, the same large context gets re-sent turn after turn, so re-sent context balloons.

Both numbers are real. They just answer different questions. "What does my typical session look like?" → 24%. "Where did my month's money go?" → 60%. If someone quotes one without the other, they're telling half the story.

Here's the pooled split across all 66 sessions (total: **$2,650.90** over **4,339 model turns**):

| Spend category | Share |
| --- | --- |
| Re-sent context (cache-read) | **60%** |
| New cached context (cache-write) | 25% |
| Output — the model actually writing | 15% |
| Fresh (uncached) input | ~0% |

Only **15%** of my total spend was the model writing. The overwhelming majority was _moving context back and forth_.

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#why-this-happens-its-mechanical-not-mysterious) Why this happens (it's mechanical, not mysterious)

The model is stateless. It has no memory between turns. So on every single turn, the **entire accumulated conversation context** — every file you've read, every tool result, every previous message — gets sent again so the model can "remember" it.

Prompt caching softens the blow: that re-send is billed at the discounted cache-read rate (roughly a tenth of full input price) rather than full freight. But you still pay it _every turn_, on the _whole_ context. So as a session grows:

*   context size goes up,
*   the per-turn re-send cost goes up with it,
*   and because you're now also taking _more_ turns in that long session, you multiply a growing per-turn cost by a growing turn count.

That compounding is why cost concentrates. In my set, the median session peaked at ~45k tokens of context, but the heaviest single session peaked at **999,541 tokens** — and the average peak across all sessions was 251,371. The long sessions reach an order of magnitude higher than the typical one, and every token in that context is re-sent on every following turn. They don't cost a bit more. They cost the bill.

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#the-actuallyuseful-takeaway) The actually-useful takeaway

The honest headline isn't "Claude Code is expensive." It's:

> **A few long sessions are expensive, and in those, re-sent context is the bill.**

That reframing changes what you do about it. You don't need to micro-optimize your cheap, short sessions — they're already cheap and balanced. The leverage is entirely in the long-context marathons:

*   **`/compact` aggressively on long sessions.** It summarizes and drops the accumulated context, which directly shrinks the thing you're re-paying for every turn. The earlier you compact a long session, the more re-sends you avoid at the larger size.
*   **Start a fresh session when the task changes.** Carrying a 200k-token context into an unrelated new task means you re-pay for 200k irrelevant tokens on every turn of the new work. A fresh session starts the re-send meter near zero.
*   **Watch context growth, not just the running total.** The total tells you what already happened; the _per-turn context size_ tells you what each future turn will cost. When you see context climbing into the hundreds of thousands of tokens, that's the signal to compact or split — before, not after.
*   **Don't over-index on cache efficiency.** My median cache efficiency was ~83% (pooled 98%), which sounds great. But cache efficiency only tells you how _cheap your re-sends are_ — not _how much you're re-sending_. You can have 98% cache efficiency and still be torching money, because you're efficiently re-sending an enormous context a hundred times. The metric to watch is the re-sent-context _share of spend_, not the cache hit rate.

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#a-caveat-i-want-to-be-loud-about) A caveat I want to be loud about

This is **one heavy user's data** — mine, from building one set of projects. It is a _reference set_, not a census or a representative survey of all Claude Code users. The specific numbers (the $4.08 median, the 24%/60% split) will shift for a lighter user, a different stack, or a different price sheet. I haven't trimmed, adjusted, or curated anything — these are the tool's raw output — but a single self-measured source is inherently narrow, so treat the _shape_ as the finding and verify the _numbers_ against your own logs.

The structural part — cost concentrates in a few long sessions, and re-sent context dominates those — is a property of stateless models plus per-turn context re-send. That should hold broadly. The exact percentiles are just my sessions.

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#if-you-want-to-measure-your-own) If you want to measure your own

I wrote the parser as a small CLI to do this analysis, and it's open source. To see where _your_ spend goes:

```
npx @wartzar-bee/tokenscope
```

It reads your Claude Code logs locally — **read-only, no network, no telemetry, nothing leaves your machine** — and prints the same breakdown: output vs. re-sent context vs. new context, the per-turn context-growth curve, and which percentile your session lands in against the 66-session reference set above. `--share` emits a privacy-safe summary (aggregate numbers only — no file paths, no prompt or response content) you can paste into a thread. It's MIT, not affiliated with Anthropic, and the whole cost model is the few paragraphs above — so if you'd rather write your own parser, the logs are right there in `~/.claude/projects/` and you now know what to look for.

(Disclosure: I maintain tokenscope. I'm linking it because it's the tool I used to produce these exact numbers, not because you need it — the JSONL is yours and the math is simple.)

The full dataset — every percentile table, the SVG charts, the complete methodology and a frank limitations section — is published here: **[https://tokenscope.pages.dev/benchmark/](https://tokenscope.pages.dev/benchmark/)**

## [](https://dev.to/wartzarbee/where-your-claude-code-bill-actually-goes-i-measured-66-of-my-own-sessions-471e#takeaway) Takeaway

Don't optimize your average session; it's fine. Find your handful of long-context marathons — the ones that quietly peaked past a few hundred thousand tokens — and compact or split _those_. That's where the 60% lives.

I'd genuinely like to widen this beyond one person's logs: **if you've measured your own Claude Code (or any agent) spend, what's _your_ split between re-sent context and actual output — and does cost concentrate in a few long sessions for you too, or is your distribution flatter?**

* * *

_I measure this with [tokenscope](https://www.npmjs.com/package/@wartzar-bee/tokenscope) (`npx @wartzar-bee/tokenscope --demo` for a zero-setup sample), and to keep a cost regression from silently landing in the first place, [ci-guardrail](https://github.com/wartzar-bee/ci-guardrail) fails a PR in CI when its token cost jumps past a budget you set. Both free and open-source._
