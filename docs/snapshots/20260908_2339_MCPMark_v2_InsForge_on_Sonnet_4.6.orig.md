Title: MCPMark v2: InsForge on Sonnet 4.6

URL Source: https://insforge.dev/blog/mcpmark-benchmark-results-v2

Published Time: 2026-03-02T00:00:00.000Z

Markdown Content:
In December we published the [first MCPMark benchmark results](https://insforge.dev/blog/mcpmark-benchmark-results) comparing InsForge MCP, Supabase MCP, and Postgres MCP across 21 real-world database tasks using Claude Sonnet 4.5. InsForge came out ahead on accuracy, speed, and token efficiency.

We reran the benchmarks. This time on **Claude Sonnet 4.6**, the latest model from Anthropic. InsForge MCP achieves 28% higher Pass⁴ accuracy while using 2.4x fewer tokens than Supabase MCP. The efficiency gap has widened.

## Updated Results: Claude Sonnet 4.6[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#updated-results-claude-sonnet-46)

Same 21 MCPMark Postgres tasks, 4 runs per task, strict Pass⁴ scoring.

| Metric | InsForge | Supabase MCP |
| --- | --- | --- |
| Pass⁴ Accuracy | 42.86% | 33.33% |
| Pass@1 Average | 58.33% | 47.62% |
| Pass@4 | 76.19% | 66.67% |
| Tokens Per Run | 7.3M | 17.9M |
| Avg Tokens Per Task | 358K | 862K |
| Avg Time Per Task | 156.6s | 198.8s |
| Avg Turns Per Task | 18.6 | 17.0 |

InsForge MCP maintains higher accuracy across all three metrics and uses **2.4x fewer tokens** per run.

## Accuracy[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#accuracy)

Pass@1 is average single-run accuracy, Pass@4 means the agent passed at least once in 4 runs, and Pass⁴ requires passing all 4. InsForge passes 76% of tasks at least once (Pass@4) and 43% under strict repeated execution (Pass⁴). Supabase MCP reaches 67% and 33% respectively.

| Model | Metric | InsForge | Supabase MCP |
| --- | --- | --- | --- |
| Sonnet 4.5 | Pass⁴ | 47.6% | 28.6% |
| Sonnet 4.6 | Pass⁴ | 42.86% | 33.33% |
| Sonnet 4.6 | Pass@4 | 76.19% | 66.67% |
| Sonnet 4.6 | Pass@1 Avg | 58.33% | 47.62% |

InsForge's accuracy advantage comes from surfacing backend state before the agent acts. When the agent can see record counts, RLS policies, and foreign keys upfront, it writes correct queries on the first attempt instead of guessing and retrying. That is why the gap holds across model versions.

## The Token Gap Widened[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#the-token-gap-widened)

This is the most notable change from v1.

With Sonnet 4.5, InsForge used approximately 30% fewer tokens than Supabase MCP (8.2M vs 11.6M per run). With Sonnet 4.6, the gap has grown to **59% fewer tokens** (7.3M vs 17.9M per run).

| Model | InsForge Tokens/Run | Supabase Tokens/Run | Difference |
| --- | --- | --- | --- |
| Sonnet 4.5 | 8.2M | 11.6M | 1.4x |
| Sonnet 4.6 | 7.3M | 17.9M | 2.4x |

InsForge got slightly more efficient on Sonnet 4.6 (8.2M down to 7.3M). Supabase MCP went in the opposite direction (11.6M up to 17.9M). The newer model appears to reason more extensively when backend context is incomplete, which increases token consumption on backends that do not surface schema details upfront.

When the backend provides structured context from the start, the agent reasons less and executes more. When it does not, the agent compensates with additional discovery queries and verification steps, and that compensation costs more tokens on a more capable model.

Two factors account for most of the gap:

1.   **Documentation overhead.** Supabase's `search_docs` returns full GraphQL schema metadata on every call, 5-10x more tokens per query than InsForge's `fetch-docs`.
2.   **Exploration before execution.** Without structured schema context upfront, the agent runs more discovery queries before doing actual work.

## Speed[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#speed)

InsForge completes tasks in an average of **156.6 seconds** compared to **198.8 seconds** for Supabase MCP. This is a 1.27x speed advantage, consistent with what we observed on Sonnet 4.5.

## What This Means[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#what-this-means)

The core finding from our [original benchmark post](https://insforge.dev/blog/mcpmark-benchmark-results) holds: agents perform better when the backend gives them structured context and workflow upfront. The Sonnet 4.6 results reinforce this and show that the advantage grows as models become more capable.

More capable models do not eliminate the need for structured backend context. They amplify the cost of not having it.

We will continue running benchmarks as new models are released and as we improve the InsForge MCP layer. All benchmark methodology follows [MCPMark](https://mcpmark.ai/) standards and is fully reproducible. The latest raw results are available on [GitHub](https://github.com/InsForge/mcpmark/tree/main/results).

## Try It[](https://insforge.dev/blog/mcpmark-benchmark-results-v2#try-it)

**[InsForge on GitHub](https://github.com/InsForge/InsForge)**

**[Quickstart guide](https://github.com/InsForge/InsForge?tab=readme-ov-file#quickstart)**
