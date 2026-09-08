Title: The Subagent Tax, Measured: 23,747 Turns of Real Billing Data

URL Source: https://theinfinity.dev/articles/subagent-cost-measured

Published Time: 2026-08-19

Markdown Content:
Across 34 days of my own agent work — 345 transcripts, 23,747 billed turns, $5,435 at list pricing — the subagents I spawned accounted for 12.8% of the turns and **4.6% of the [bill](https://theinfinity.dev/articles/subagent-cost-measured#)**. A subagent turn cost $0.082. A main-loop turn cost $0.250. Delegating was three times cheaper per turn.

That is the opposite of what the internet says. The circulating number is a tax: one widely shared write-up measured a fan-out at 5.9× the tokens of doing the same job directly, another put it at 4.2×, a third at roughly 7×. There are stories of a 23-subagent run that burned $47,000.

Both sets of numbers are real. I reproduced the mechanism behind the tax in my own [data](https://theinfinity.dev/articles/subagent-cost-measured#), and it is not a property of subagents at all. When I hold context size and output length constant, a subagent turn costs **the same** as a main-loop turn — the ratio lands between 0.86 and 1.07 depending on the bucket. There is no delegation discount. There is no delegation penalty either.

What there is: a turn costs what it carries. Delegation is cheap when the delegate carries less, and ruinous when you hand the same heavy context to five agents at once. The agent count never enters the equation.

## What the split actually looks like

Subagents were an eighth of my turns and a twentieth of my spend. The gap is not a discount — it is the size of what each turn carried.

Real Estate Agencies

|  | cost | share of bill | turns | $/turn | avg context | avg output |
| --- | --- | --- | --- | --- | --- | --- |
| Main loop | $5,187 | 95.4% | 20,716 | $0.250 | 357,459 | 1,177 |
| Subagent | $248 | 4.6% | 3,031 | $0.082 | 102,936 | 90 |

Two ratios explain the third. Subagent turns carried 3.5× less context and produced 13× less output. Multiply those through the [price](https://theinfinity.dev/articles/subagent-cost-measured#) sheet and $0.082 is roughly what you would predict.

The five most expensive sessions in the window cost $648, $549, $360, $304 and $257. Every one of them was pure main loop, zero delegation. The $648 session ran 2,167 turns in a single conversation. Nothing I delegated came close.

## Is a subagent turn actually cheaper?

No. At the same context size and the same output length, a subagent turn costs what a main-loop turn costs. The apparent discount disappears entirely once you control for both.

Here is the same data bucketed by context size, restricted to turns that emitted fewer than 200 output tokens so that output length stops confounding the comparison:

| context in the turn | main loop $/turn | subagent $/turn | ratio |
| --- | --- | --- | --- |
| 50–100k | $0.061 | $0.066 | 1.07 |
| 100–150k | $0.086 | $0.074 | 0.86 |
| 150–200k | $0.113 | $0.108 | 0.95 |
| 200–250k | $0.131 | $0.135 | 1.03 |

That is noise around 1.0. Two of the four buckets have the subagent costing slightly _more_, which makes sense — subagents get less benefit from prompt caching. Their cache-read share was 93.0% against the main loop's 98.0%, because a fresh agent has to write its cache before it can read it.

Tax Preparation & Planning

So the model does not know or care that a turn belongs to a subagent. It bills a prompt. The prompt is the whole story, which is the same conclusion I reached [measuring 23,968 turns of prompt-to-output ratio](https://theinfinity.dev/articles/agent-token-cost-measured) and again [measuring what a memory retrieval puts into the context window](https://theinfinity.dev/articles/agent-memory-measured). Three different questions, one answer.

## Then why was my subagent bill only 4.6%?

Because a subagent starts from nothing. It does not inherit the conversation that spawned it, so it never pays for the 350,000 tokens of history sitting in the parent session.

My main loop averaged 357,459 tokens of context per turn. My subagents averaged 102,936. That is not a tuning choice, it is structural: the parent hands over a task description, not a transcript. Everything the main loop accumulated — the files it read, the commands it ran, the dead ends it backed out of — stays behind.

The output side compounds it. Main-loop turns averaged 1,177 output tokens; subagent turns averaged 90. A subagent that searches four directories and reports one file path emits almost nothing. At $25 per million output tokens, 1,177 tokens is $0.029 and 90 tokens is $0.002, and that difference alone is a third of the per-turn gap.

## What is the "subagent tax" measuring, then?

It is measuring fan-out, which multiplies context instead of dividing it. Both numbers are correct because they describe opposite shapes of the same mechanism.

When you fan out to five agents on one task, each of them loads a system prompt, a tool set, and enough of the problem to be useful. The published breakdown of a 4.2× case is explicit about this: each subagent re-read a 38,000 to 69,000 token prefix, five times over, and paid for its own baseline on every turn. Nothing was shared. That is five agents each carrying a mid-sized context where one agent carried one.

When you delegate a narrow lookup out of a 300,000-token conversation, the arithmetic runs backwards. One agent carries a small context where the alternative was one agent carrying a huge one.

Same mechanism, opposite sign. The variable that moved was never the number of agents.

## When does delegating actually pay?

It depends almost entirely on how big your main conversation already is. Below about 100k tokens of context, delegation only pays for tasks that take six or more turns. Above 250k, it pays from the first turn.

Data Management

Spawning is not free. A subagent's first turn cost $0.188 in my [data](https://theinfinity.dev/articles/subagent-cost-measured#) — 2.3× its own average — because it writes about 34,000 tokens of cache before it can read any. That fixed cost has to be earned back.

Setting spawn at $0.188, each additional subagent turn at $0.082, and comparing against a main-loop turn at the measured rate for each context band:

| your current context | inline $/turn | delegation breaks even at | verdict |
| --- | --- | --- | --- |
| 50–100k | $0.101 | 5.6 turns | only for long tasks |
| 100–150k | $0.118 | 2.9 turns | 3+ turn tasks |
| 150–200k | $0.139 | 1.9 turns | 2+ turn tasks |
| 200–250k | $0.167 | 1.2 turns | almost always |
| 250–300k | $0.199 | 0.9 turns | immediately |

![Image 1: Cost of a five-turn task plotted against the context already sitting in the main conversation. The delegated line is flat at $0.52 because a subagent never inherits the parent transcript; the inline line climbs from $0.51 to $0.99 because every turn re-reads a conversation that keeps growing. The two cross at roughly 80k tokens of context.](https://theinfinity.dev/images/articles/subagent-cost-measured/breakeven.svg)
Take a five-turn research task. At 50–100k of context it costs $0.51 inline and $0.52 delegated — a wash. At 250–300k it costs $1.00 inline and $0.52 delegated, so delegation is 48% cheaper.

This table is generous to the inline option, in two ways. It assumes your context stays flat while you do the work, when in reality the files you read and the output you produce all land in the conversation and inflate every turn that follows. And it ignores that the inline work permanently raises the floor for the rest of the session. Delegated work leaves no trace in the parent.

Billing & Invoicing

## What this means for how you delegate

Delegate to shed context, not to add parallelism. The saving comes from what the delegate does not carry, so anything that fattens the subagent's prompt eats the benefit directly.

Three practical consequences fall out of the numbers.

Delegate late, not early. At 60k of context there is almost nothing to save; at 300k there is half the [bill](https://theinfinity.dev/articles/subagent-cost-measured#). The same task delegated at two different points in a session has completely different economics.

Keep the brief short and the report shorter. Output cost me 13× more per main-loop turn than per subagent turn, and that gap is most of the advantage. A subagent asked to return a 2,000-token summary has spent the saving before it starts.

Do not fan out to save money — fan out for latency or independence, and [price](https://theinfinity.dev/articles/subagent-cost-measured#) it as a cost. Five agents on one task is five baselines. If they each need the same large context, you have found the expensive case, and the 4× to 6× figures in circulation are what you should expect.

## How I measured this

Every Claude Code session writes a JSONL transcript to `~/.claude/projects/`, and every assistant record carries a `usage` block with the real token counts — input, cache creation, cache read, and output. This is billing data, not an estimate of it.

Economics

```
u = record["message"]["usage"]
context = u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]
cost = (u["input_tokens"] * rate_in
        + u["cache_creation_input_tokens"] * rate_in * 1.25
        + u["cache_read_input_tokens"] * rate_in * 0.10
        + u["output_tokens"] * rate_out) / 1e6
```

Subagent turns carry `isSidechain: true`. That flag is what makes this measurable at all — without it, delegated work is indistinguishable from the rest.

Two traps cost me a first pass each. Streaming repeats the same `message.id` across several lines, so counting rows double-counts turns; deduplicate by message id. And subagents write to their own transcript files rather than into the parent's, so splitting by file gives you 165 files that are 100% subagent and tells you nothing. Split by record.

The window is 2026-07-16 to 2026-08-19: 345 transcripts, 23,747 turns, mostly Claude Opus 5 (18,967 turns) with Opus 4.8, Sonnet 5 and Fable 5 making up the rest. Costs use list pricing with the standard 1.25× cache-write and 0.10× cache-read multipliers.

Transcripts roll off after about a month, so this is a moving window rather than a fixed archive. That is why the totals here differ slightly from the 23,968 turns I reported three days earlier — different snapshot, same machine.

Three limits worth stating. This is one developer's usage pattern, not a benchmark — my delegation habits shaped the context sizes, and yours will differ. Because subagents live in separate files, I cannot attribute a subagent back to the session that spawned it, so there is no per-session delegation ratio here. And the breakeven table is built from bucket averages, so treat it as a shape rather than a quote.

Mathematics

## FAQ

### Are subagents more expensive than doing the work inline?

Not per turn. Measured across 23,747 turns, a subagent turn cost $0.082 against a main-loop turn at $0.250. But that gap comes from subagents carrying 3.5× less context and emitting 13× less output — at equal context and output the two cost the same, within noise.

### What is the subagent tax?

It is the cost of fan-out, where several agents each load their own baseline context for one task. Published measurements put it at 4.2× to 5.9× the tokens of doing the job directly. It is real, and it applies when you parallelize; it does not apply when you delegate a narrow task out of a large conversation.

### How much does spawning a subagent cost?

About $0.188 in my [data](https://theinfinity.dev/articles/subagent-cost-measured#), which is 2.3× a subagent's average turn. The first turn writes roughly 34,000 tokens of prompt cache before anything can be read back cheaply. That fixed cost is why short delegations from a small conversation do not pay.

### When should I delegate instead of continuing inline?

When your main conversation is already large. Below 100k tokens of context, delegation only wins on tasks of six turns or more. Above 250k it wins immediately, because a single inline turn at that size costs more than spawning an agent and running it once.

Real Estate Agencies

### Does prompt caching make subagents cheaper?

The opposite, slightly. Subagent turns had a 93.0% cache-read share against the main loop's 98.0%, because a fresh agent must write its cache before it can read it. Caching favors the long-running conversation, which is the one you were trying to escape.

### Do more subagents mean a bigger bill?

Not by themselves. The count of agents does not appear anywhere in the pricing; the context each turn carries does. Five agents with small contexts can cost less than one agent with a huge one, and five agents with large contexts will cost about five times as much.

## The part I did not expect

I went in expecting to confirm the tax and instead found that agent architecture is a red herring. Single agent, subagent, fan-out, orchestrator — none of it appears on the invoice. What appears is a list of prompts and how big each one was.

That reframes the question people usually ask. "Should I use subagents?" has no cost answer. "How much context does this turn need to carry?" has one, and it is the same question whether the turn belongs to an agent, a subagent, or you.

If you want to see the shape of it before you touch your own transcripts, the [agent trace cost simulator](https://theinfinity.dev/simulators/agent-trace-cost) walks a single agent through a task and shows the prompt growing underneath it. Delegation is what happens when you refuse to let that line keep climbing.

Computer Memory
