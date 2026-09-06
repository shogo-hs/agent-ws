Title: The Subagent Tax. Claude Code Fan-Outs Cost Up to 5.9x the Tokens, and Were Never Faster

URL Source: https://systima.ai/blog/subagent-tax

Published Time: 2026-07-22T16:28:51.509Z

Markdown Content:
Claude Code's subagents used 2.6x to 5.9x as many input tokens as doing the same work sequentially, measured across three model families. They were not faster on any task we timed. And in one matched pair, cache misses pushed the price-weighted cost to roughly five times the sequential run.

Be the first to know when we publish original research or thought pieces on AI and quantum governance.

No spam. Unsubscribe at any time.

Subagents look like cheap parallelism because the parent receives only their compact results. Underneath, each one is a separate agent loop that carries its own system prompt, tools, and cache entries on every turn it takes.

Since early July, Claude Code's built-in Explore agents also inherit the parent model rather than defaulting to Haiku, so an unnoticed fan-out now runs on whatever expensive model you happen to be driving.

When we published our study of coding-agent token overhead, the loudest comment thread was about exactly this. One reader's task quietly spawned seven subagents that drained a five-hour budget, a review step tried to recruit forty-one verifiers, and later reports reached one hundred and two agents, then four hundred and fifteen. The original study held one measured fan-out already, 513,000 tokens against 121,000 for the same work done directly, its largest single multiplier. Here is the full picture, and the settings that cut the bill.

This is a follow-up to [our harness token study](https://systima.ai/blog/claude-code-vs-opencode-token-overhead). The method, the logging proxy, and the tamper-evident dataset are the same, and the rig is open source.

## Why subagents feel free and are not

A subagent looks like delegation. The parent hands off a job, the subagent goes away and works, and a tidy result comes back. The parent's own context stays clean.

The cost hides in three places that the tidy result does not show you.

Each subagent is a fresh agent. It boots with its own system prompt and its own tool schemas, and it re-reads that baseline on every turn it takes, not once.

The parent can pay again on resume. While subagents run, the orchestrator's cached context can age out, and a fan-out that outlasts the cache window re-primes the parent's stack at write rates. Our lanes were short enough that the parent returned to a warm cache every time, so treat this one as mechanism rather than measurement.

And the work multiplies. Two subagents running several turns each add several more full-baseline requests to the session, on top of the parent's own.

## What one fan-out actually cost

We gave Claude Code a task and let it fan out to two subagents. We ran the identical task directly for comparison. Both produced correct results.

The direct run took roughly 121,000 cumulative metered input tokens. The fan-out took 513,000, a 4.2x multiplier.

The captured requests show where it went.

| Request class | Requests | System prompt | Tools |
| --- | --- | --- | --- |
| Parent session | 3 | 27,781 chars | 27 |
| Subagent | 5 | 3,554 chars | 24 |

Every one of those five subagent requests carried its own 3,554-char system prompt and 24 of the 27 tools, and re-read a 38,000 to 69,000 token prefix. Five separate agent loops, each re-paying its own baseline on every turn, is the tax.

## The parent ingests results, not transcripts

One thing the data settles cleanly. The parent does not swallow each subagent's entire transcript.

Across its three requests the parent's message payload grew from 8,551 to 12,490 to 15,332 characters. Those increments are the size of returned results, a few thousand characters each, not whole sub-sessions. A full subagent transcript would be tens of thousands of characters.

So the multiplication is not the parent re-reading everything the subagents did. It is the subagents themselves, each a full agent in its own right, running in parallel.

## Are the subagent prompts cached, or re-sent each time

This was the sharpest disagreement in the thread. Some readers said the shared system prompt is cached and therefore cheap. Others said subagents stopped caching it.

Our captures lean towards cached, and the fresh lanes strengthen it across both new model families. In every same-model fan-out lane on Opus and on Fable, the first subagent request read 39,000 to 88,000 tokens from cache and wrote only a few hundred to roughly 6,000. That is the signature of a cache hit on the shared prefix, not a fresh write.

The exceptions matter more, and a thread comment predicted their mechanism. Parallel spawns can race the cache; identical requests fired before the first has finished writing its prefix cannot read it, and there is no in-flight deduplication to save them.

Our captures carry exactly that signature. Every unexpected full-prefix re-write inside a fan-out lane, meaning one where the prefix had already been written or read earlier in the lane, landed while a sibling request of the same profile was still in flight. One Haiku subagent fired six seconds after its sibling and wrote its full 52,022-token prefix with zero cache read. One Fable subagent fired twelve seconds behind two siblings that had each read the same 47,552-token prefix, and missed with a 40,829-token write. One Opus subagent turn re-wrote 56,906 tokens mid-lane with a sibling in flight. We found no unexpected re-write without concurrency.

The counterpoint appeared too. The five-subagent Opus lane fired its five spawns inside twenty seconds against a prefix warmed by an earlier lane, and every one of them read clean. So the shared prompt is cached, and a simultaneous fan-out against a cold cache is exactly where it misses, re-paying the full prefix at premium write rates each time. Caches also do not cross models, so subagents pinned to a different model maintain their own cache entry, which is how a Haiku miss can happen under an Opus parent.

The remaining caveat is unchanged. All of this ran through [Meridian](https://github.com/rynfar/meridian), an open-source local proxy that bridges a Claude Max or Pro subscription with standard developer environments by translating requests from external coding applications into the official format required by the Claude Agent SDK, the underlying engine for Claude Code. Meridian manages caching itself, and cache attribution is exactly the measurement a gateway is most likely to distort. The pattern is now consistent across lanes and model families, but a raw-API confirmation stays on the list before we state it as settled fact.

## Fan-out versus sequential, measured

We ran the same small task three ways on Opus, through the same rig, each in a fresh workspace isolated from the others. All three completed the task correctly. Wall time in the tables below is the elapsed clock time from launching a lane to its final response.

| Lane | Metered requests | Metered input tokens | Cache writes | Wall time |
| --- | --- | --- | --- | --- |
| Sequential, no subagents | 4 | 295,271 | 14,660 | 4m 15s |
| Two subagents | 12 | 762,226 | 135,825 | 8m 0s |
| Five subagents | 15 | 945,187 | 40,814 | 4m 45s |

Two subagents cost 2.6x the sequential run in metered tokens. Five cost 3.2x. On Sonnet in the original study the two-subagent multiplier was 4.2x, so the width of the tax varies with the model and with how many turns each subagent decides to take.

The metered totals understate the price difference. The sequential lane's tokens were mostly cache reads, billed at a tenth of the input rate. The two-subagent lane's cost was concentrated in premium-rate cache writes, including a 49,576-token write on the parent's first turn and that 56,906-token mid-lane re-write. Weight each lane by published API cache pricing and the two-subagent fan-out lands at roughly five times the sequential cost, and the five-subagent lane at roughly three times. Subscription plans meter quota rather than list prices, so the weighting is an API-rate statement, not a claim about your Max allowance.

That ordering surprises people. Five subagents metered more tokens than two but cost less in weighted terms, because the two-subagent lane suffered two full prefix re-writes and the five-subagent lane did not. The mid-session re-write events the original study flagged move the bill around more than fan-out width does.

One fairness note. The lanes ran back to back, so the sequential lane enjoyed a warm cache on its reads. Give it a cold first write and the two-subagent multiplier drops from 2.6x to roughly 2.2x metered. Every conclusion survives the adjustment.

And the speed argument never showed up. The two-subagent lane took eight minutes against the sequential lane's four and a quarter, and even five parallel subagents only matched sequential pace. On a task this small the orchestration overhead swallowed the parallelism whole.

## The same matrix on Fable 5

We repeated the three-way matrix on Claude Fable 5, first confirming the gateway was genuinely serving Fable rather than silently substituting another model. All three lanes completed the task correctly.

| Lane | Metered requests | Metered input tokens | vs sequential | Wall time |
| --- | --- | --- | --- | --- |
| Sequential, no subagents | 3 | 166,459 | 1.0x | 2m 15s |
| Two subagents | 13 | 974,987 | 5.9x | 7m 0s |
| Five subagents | 15 | 781,293 | 4.7x | 17m 0s |

The tax is wider on Fable than on Opus. The two-subagent fan-out cost 5.9x its sequential baseline, against 2.6x on Opus, largely because Fable's subagents took more turns over the same work.

The inversion shows up again, and this time in the raw metered numbers. Five subagents metered fewer tokens than two, because the two-subagent lane's workers ran four turns each while the five-subagent lane's ran roughly three. How many turns each subagent chooses to take moves the bill more than how many subagents you spawn.

Fable also extends the model-conditional prompt finding from the original study down into subagent traffic. The subagent system prompt measured 3,554 chars on Sonnet, 3,981 on Opus, and 4,509 on Fable, always with the same reduced 24-tool set.

One disclosure applies to every Fable row. The gateway served a few late parent turns as Opus with no fallback marker, one request in the sequential lane, three in the two-subagent lane, and one in the five-subagent lane, while every subagent request was genuinely served Fable. All three lanes share that mixture, so the multipliers between them stand; treat the absolute Fable figures as gateway-mixed.

## The model-inheritance trap

Since Claude Code 2.1.198, released on 1 July 2026, the built-in Explore agent inherits the main session's model, capped at Opus, instead of running on Haiku as it used to. ([changelog](https://code.claude.com/docs/en/changelog))

That is a quiet cost change. A fan-out that used to spin up cheap Haiku explorers now spins up copies of whatever expensive model you are driving, unless you say otherwise.

We measured what saying otherwise is worth. The same two-subagent fan-out ran once with inherited Opus subagents and once with the subagents pinned to Haiku while the parent stayed on Opus.

| Lane | Metered input tokens | Subagent requests | Wall time |
| --- | --- | --- | --- |
| Two inherited Opus subagents | 762,226 | 8 | 8m 0s |
| Two Haiku-pinned subagents | 481,387 | 3 | 3m 45s |

The pinned lane metered 37 per cent fewer input tokens, finished in under half the time, and moved roughly 150,000 of its remaining tokens onto Haiku's price sheet, a small fraction of Opus rates. The Haiku subagents also finished in three requests where the Opus ones took eight, which is its own saving.

One new cost appears. Caches do not cross models, so the Haiku subagents maintain their own cache entry, and one of ours re-wrote its full 52,022-token prefix with zero cache read. On a one-off fan-out that write eats into the saving; across a session of repeated fan-outs it amortises.

This is one matched pair, not a distribution. But the direction is unambiguous, and it prices the changelog change above. An Explore swarm that inherits Opus instead of running on Haiku costs roughly the difference between those two rows every time it fires.

## How to cut the tax

The thread supplied the mitigations. Here is what we can put numbers on.

Pin subagents to a cheaper model rather than inheriting the driver. Measured above; 37 per cent fewer metered tokens, under half the wall time, and the subagent traffic billed at Haiku rates.

Prefer sequential work when the sub-tasks are not genuinely independent. Measured above; the sequential lane metered 2.6x fewer tokens than the two-subagent fan-out, cost roughly five times less on a price-weighted basis, and was faster.

Deny the Explore fan-out entirely by adding `Agent(Explore)` to the deny list in `~/.claude/settings.json`. The Task tool was renamed Agent in Claude Code 2.1.63, and the older `Task(Explore)` form readers shared still works as an alias. Cap concurrency too, so a review step cannot recruit forty-one verifiers. We did not run matched lanes for these; they gate the swarm rather than shrink it, so when they bite, the saving is the whole fan-out delta above.

And stagger cold fan-outs. The cache race above only bites when parallel spawns hit a cold prefix together, so when you do fan out wide, letting the first subagent start before the rest follow avoids paying the full prefix several times over.

## OpenCode, for contrast

OpenCode's subagents carry a deliberately leaner profile. On the versions we measured, its Explore subagent requests carried a 1,485-char system prompt and 5 tools, against Claude Code's roughly 4,000 chars and 24 tools on the same Opus path. The design philosophy differs, and the per-subagent floor differs with it.

The totals stay honestly unquantified, for the second study in a row. Our matched OpenCode fan-out spawned its two Explore agents, one finished its half, the other stalled, we ended the run after fifteen minutes, and none of the subagent responses carried parseable usage through our gateway. We do not know whether the hang belongs to OpenCode's task tool, to the gateway's handling of it, or to the pairing; a raw-API run would separate them.

## The dataset

As before, every captured request is written into a tamper-evident, SHA-256 hash-chained audit trail, so the numbers here are checkable rather than asserted. The chain for this session's lanes verifies at 105 entries with no breaks. The rig, the fresh subagent lanes, and the aggregated results are open source at [github.com/systima-ai/agentic-coding-tools-comparison](https://github.com/systima-ai/agentic-coding-tools-comparison). We are also preparing the full capture set from both studies, requests, responses, and usage telemetry, as a standalone public dataset for anyone to run their own analyses on; that release gets its own post.

## The takeaway

Subagents are not free parallelism. Each one is a full agent carrying its own baseline on every turn, a cold parallel spawn can re-buy that baseline outright at premium write rates, and on small tasks the fan-out is slower as well as dearer. For genuinely independent work on a big surface it buys you speed. For everything else it mostly buys you a bigger bill.

Measure it at the boundary, pin your subagents to a model you would pay for knowingly, and turn the swarm off when you do not need it.

If you run agentic systems where token cost and auditability both matter, that instrumentation is the work we do. See [LLM Cost Optimisation](https://systima.ai/services/llm-cost-optimisation), or read the [companion piece on reducing LLM costs](https://systima.ai/blog/reducing-llm-costs).
