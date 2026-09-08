Title: MCP is up to 32× more expensive than CLI. Here’s why we still use it.

URL Source: https://www.scalekit.com/blog/mcp-vs-cli-use

Published Time: 2026-05-27T05:34:08.461Z

Warning: Target URL returned error 404: Not Found

Markdown Content:
Announcing CIMD support for MCP Client registration

[Learn more](https://www.scalekit.com/blog/cimd-support-for-mcp)

![Image 1](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b1585f82e4135229d984a8_MCP%20vs%20CLI.webp)

[![Image 2](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/6a7184e741bd5cd71e1d773e_author-Ravi%20Madabhushi.png)](https://www.scalekit.com/blog/mcp-vs-cli-use#)

![Image 3](https://cdn.prod.website-files.com/65b87d98fa638289e10b8f61/6a6b2bc8f5d68e194df09663_icon-chatgpt.svg)

Open in ChatGPT

We ran 75 benchmark runs **comparing CLI and MCP** for AI agent tasks. CLI won on every efficiency metric — 10 to 32× cheaper, 100% reliable versus MCP’s 72%.

If that were the whole story, this post would be three paragraphs long: use CLI, add a skills file, move on.

But we’re [building agents that act on behalf of other people’s users](https://www.scalekit.com/blog/delegated-agent-access), inside other people’s organizations, across third-party services those organizations control. And the moment you cross that boundary, from “I’m automating my own workflow” to “my product automates workflows for my customers,” every efficiency advantage CLI has becomes an architectural liability.

This post has two halves. The first gives you the benchmark data – use it, it’s real. The second explains why the data alone will mislead you if you’re building anything beyond a personal developer tool.

## The Benchmark

### Three ways to connect an AI agent to GitHub

_Same model (Claude Sonnet 4). Same tasks. Same prompts. Only the tool interface changes._

**CLI:** Hand the agent a bash tool. No guidance. It figures out `gh` commands on its own.

**CLI + Skills:** Same bash tool, plus ~800 tokens of tips — useful `gh` flags, output formatting patterns, common workflows. This is how tools like OpenClaw work in practice.

**MCP:** Connect to GitHub’s official Copilot MCP server at `api.githubcopilot.com/mcp/`. The agent gets all 43 tool schemas automatically.

Five read-only tasks against `anthropics/anthropic-sdk-python`: get repo info, fetch PR details, read metadata, summarize merged PRs, find release dependencies. All deterministic, all verifiable.

## The Numbers

### Token usage: MCP costs 4–32× more

![Image 4](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b153d82879dbe857d5f5ad_Token%20Usage%20Per%20Task.png)

Token Usage Per Task

Task

CLI

CLI + Skills

MCP

Repo language & license

1,365

4,724

44,026 (32×)

PR details & review status

1,648

2,816

32,279 (20×)

Repo metadata & install

9,386

12,210

82,835 (9×)

Merged PRs by contributor

5,010

6,107

33,712 (7×)

Latest release & deps

8,750

6,860

37,402 (4×)

_Median tokens per run. All CLI vs MCP differences statistically significant (p < 0.05)._

For the simplest task — “what language is this repo?” — the CLI agent needs 1,365 tokens. The MCP agent needs 44,026. The difference is almost entirely schema: 43 tool definitions injected into every conversation, of which the agent uses one or two.

## The Biggest Surprise

### MCP fails 28% of the time

![Image 5](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b1542d5ca03c50ffdea5b7_MCP%20Failure%20Rate%20MCP%20vs%20CLI.png)

MCP Failure Rate

Of 25 MCP runs, 7 failed with `ConnectTimeout`.

**CLI:** 25/25 (100%). **CLI+Skills:** 25/25 (100%). **MCP:** 18/25 (72%).

Every failure was a TCP-level timeout — the connection to GitHub’s Copilot MCP server never completed. Not an MCP protocol error. Not a bad tool call. The remote server just didn’t respond in time.

CLI agents don’t have this problem. `gh` runs locally. There’s no remote server to time out.

## Under the Hood

### The schema bloat problem

MCP’s overhead isn’t a protocol problem. It’s a schema injection problem.

![Image 6](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b1547103c941e3d6c445ca_Anatomy%20of%20Schema%20Bloat.png)

Anatomy of Schema Bloat

GitHub’s Copilot [MCP server](https://www.scalekit.com/blog/what-is-an-mcp-server) exposes 43 tools. Every time the [agent makes a tool call](https://www.scalekit.com/blog/tool-calling-authentication-ai-agents), the entire schema for all 43 tools is part of the conversation context. For a simple “get repo info” call, the agent carries schemas for creating gists, managing pull request reviews, configuring webhooks — tools it will never touch.

The CLI agent doesn’t have this problem. It knows `gh` from training data. It composes the right command in one shot. No schema overhead. No discovery step.

> **The 800-token trick:**A skill-augmented CLI — just an 800-token document of `gh`tips — reduces tool calls by a third and latency by a third versus naive CLI. That’s the best ROI in this entire benchmark. Any team can apply this today.

## At Scale

### Monthly cost: $3.20 vs $55.20 for the same work

![Image 7](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b154c6b4fb89d1abf55a61_Cost%20%26%20Reliability%20MCP%20vs%20CLI.png)

Cost & Reliability at Scale

At Claude Sonnet 4 pricing ($3/M input, $15/M output), running 10,000 operations per month:

*   **CLI:** ~$3.20/month
*   **MCP (Direct):** ~$55.20/month
*   **MCP via Gateway:** ~$5/month (estimated, with schema filtering)

That’s a 17× cost multiplier for MCP, and a 28% failure rate on top of it.

At this point, the case for CLI looks overwhelming. Cheaper, more reliable, simpler. If you stopped reading here, you’d conclude MCP is a protocol in search of a problem.

That conclusion would be correct for developer tools. It would be dangerously wrong for anything else.

## The Part Most Takes Miss

### The question isn’t “CLI or MCP.” It’s “who is your agent acting for?”

Every benchmark in the CLI-vs-MCP discourse, including ours, tests the same scenario: a single developer [automating their own workflow](https://www.scalekit.com/blog/agent-workflows-remote-mcp-servers). In that world, CLI wins. Obviously. The agent inherits your credentials, acts with your permissions, and the only person at risk is you.

But that’s not what most AI products look like in production. If you’re building a B2B SaaS, a project management tool, a support platform, a code review assistant, your agent doesn’t act as you. It acts as your customer’s employees, inside your customer’s organizations, touching your customer’s data across services your customer controls.

Here’s what that looks like concretely:

![Image 8](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b15543af6e187d2be8711b_Agent%20Actions%20Needed.png)

Imagine you’re building an AI assistant for a project management platform. A user at Acme Corp says: “Create a Jira ticket from this GitHub PR and notify the team on Slack.” Your agent needs to read from GitHub, write to Jira, and send on Slack — using that specific user’s permissions, scoped to Acme’s data, without leaking anything into Globex’s Jira or Initech’s Slack.

That’s three layers of identity resolving simultaneously on every agent action:

**Agent identity** — which agent is making this request? This is how you rate-limit, prevent abuse, and maintain an audit trail back to your product.

**User identity** — which user authorized this action? The agent can only do what this specific user can do. OAuth scopes enforce this at the protocol level.

**Tenant identity** — which organization does this user belong to? Acme’s repos must never appear in Globex’s Jira. This is data isolation, and getting it wrong isn’t a bug — it’s a breach.

### Now try doing this with `gh auth login`

When you run `gh auth login`, your agent inherits your personal token. One credential, one user. Now multiply by three organizations, each with dozens of users, each with different permission levels across GitHub, Jira, and Slack.

**One credential, many users.** CLI auth gives the agent YOUR GitHub token. To act as User A at Acme and User B at Globex, you’d need to manage a token vault, swap credentials per request, and handle refresh cycles — all in application code. _You’ve just rebuilt half of OAuth in your backend._

**No tenant isolation.** With ambient credentials, there’s no protocol-level boundary between tenants. A bug in your token-swapping code could send Acme’s data to Globex’s Jira. _This is a data breach, not a bug._

**No consent flow.** CLI tokens are created by the developer. There’s no way for end users to grant scoped access and revoke it later. You’d need to collect credentials directly or build your own OAuth integration per service. _You’re now building auth infrastructure, not your product._

**No audit trail.** Shell history logs commands, not who authorized them. When Acme’s security team asks “which of our users triggered that GitHub action?”, you have no protocol-level answer. _Enterprise customers won’t ship without this._

### This isn’t theoretical

OpenClaw showed what happens when CLI-based agents go multi-user without protocol-level authorization:

*   ‍**10,000+ exposed instances** leaking credentials, API keys, and session tokens to the public internet. _(Bitsight)_**‍**
*   **12% of community skills** found to be malicious — injecting code, exfiltrating data, or establishing persistence. _(Astrix Security)_**‍**
*   **770,000 agents** open to remote hijacking via a vulnerability that let malicious websites take over agent sessions. _(SecurityWeek)_

These aren’t bugs in OpenClaw’s code. They’re consequences of an architecture where shell access and ambient credentials operate without authorization boundaries. The properties that make CLI agents fast — ambient auth, arbitrary execution, zero protocol overhead — are exactly the properties that create security incidents when agents cross from developer tool to customer-facing product.

## What MCP Gets Right

### The protocol tax buys you three things CLI can’t provide

**Per-user authorization.**[OAuth 2.1 with PKCE](https://www.scalekit.com/blog/oauth-2-1-mcp-secure-ai-integrations). Each user grants scoped access to your agent. They can see what they authorized. They can revoke it. Your application never touches their credentials. _This is how you get past enterprise security review._

**Explicit tool boundaries.** The agent can only call declared tools. No arbitrary shell commands. No “the agent figured out how to `curl` a private API.” Every operation is typed, scoped, and predictable. _This is how you prevent the OpenClaw failure mode._

**Structured audit trail.** Every tool call produces a typed record that addresses the [agent access control problem](https://www.scalekit.com/blog/iam-ai-agents-access-control): who authorized it, what was requested, what was returned. Not shell history — structured, queryable, attributable to a specific user and tenant. _This is what enterprise compliance requires._

The properties that make MCP expensive — explicit schemas, OAuth handshakes, structured responses — are the same properties that make it governable. You’re not paying a tax for overhead. You’re paying for authorization infrastructure that CLI agents would need to rebuild from scratch.

## Decision Framework

### Match the modality to the deployment

![Image 9](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b155877f685184780b87ff_MAtch%20Modality%20%26%20Deployment.png)

Decision Framework

Category

CLI + Skills

MCP (Direct)

MCP via Gateway

**Token efficiency**

Best

4-32× overhead

~CLI range

**Reliability**

100%

72%

~99%

**Per-user OAuth**

Not supported

OAuth 2.1

OAuth 2.1 + SSO

**Tenant isolation**

App-layer only

Session-scoped

Policy-driven

**Audit trail**

Shell history

Per-request

Centralized

**Best for**

Developer is the user

Agents act for customers

Enterprise multi-tenant

**Building a developer tool where the user is the developer?** Use CLI+Skills. Add an 800-token skill file. You’ll get the best efficiency we measured, and you don’t need per-user auth because you are the user.

**Building a product where agents act on behalf of customers?** You need [MCP’s authorization model](https://www.scalekit.com/blog/mcp-authorization-agentic-workflows). But don’t connect directly to 43-tool servers — the cost and reliability numbers we showed you are real.

**Building multi-tenant enterprise infrastructure?** You need both: MCP’s auth model for governance, plus a [gateway](https://www.scalekit.com/blog/what-mcp-gateway) that solves the efficiency and reliability problems our benchmark exposed.

## The Architecture

### A gateway gives you CLI efficiency with MCP authorization

![Image 10](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69b1567951e8615e5088d338_CLI%20Efficiency%20MCP%20authorization.png)

MCP Gateway

**Schema filtering.** Instead of injecting all 43 GitHub tool schemas, a gateway returns only the 2-3 tools relevant to the current request. That takes MCP from 44,000 tokens to ~3,000 — approaching CLI efficiency. _~90% token reduction._

**Connection pooling.** Instead of each agent session establishing its own TCP connection to every MCP server, a gateway maintains persistent connections and absorbs transient failures. _28% failure rate → ~1%._

**Auth centralization.** Instead of each agent managing OAuth tokens per service, the gateway handles token refresh, scope enforcement, and audit logging in one place. _Single auth boundary per tenant._

This is the architecture we’re building at [Scalekit](https://scalekit.com/). The benchmark data convinced us it’s necessary — and showed us exactly where the optimization opportunities are.

## Try It Yourself

The full benchmark framework is open source:

Copied

```
git clone https://github.com/scalekit-inc/mcp-vs-cli-benchmark
cd mcp-vs-cli-benchmark
uv sync
uv run bench run --skills --runs 5 --service github --clean
```

You’ll need a GitHub PAT and an Anthropic API key. The harness runs all three modalities, generates statistical comparisons, and produces interactive charts. We’d welcome reproductions at larger sample sizes (n=30) and with additional services.

> **The schema bloat problem is engineering. The connection reliability problem is infrastructure. The authorization gap is architecture. Match the modality to what you’re building.**

_Resources:_

*   ‍[_Code and data_](https://github.com/scalekit-inc/mcp-vs-cli-benchmark)
*   [Get in touch to discuss further](mailto:ravi@scalekit.com)

## Frequently Asked Questions

### **1. What's the difference between MCP and CLI for AI agents — and why does it matter?**

MCP (Model Context Protocol) is a standardized protocol for connecting AI agents to external tools and data sources via structured, typed interfaces with built-in authorization. CLI gives agents direct shell access to run command-line tools like `gh`, `psql`, or `kubectl`. The distinction matters because they solve different problems. CLI wins on efficiency — it's faster, cheaper, and more debuggable. MCP wins on governance — it provides per-user OAuth, explicit tool boundaries, and structured audit trails. Choosing between them depends less on personal preference and more on who your agent is acting for.

### 2. My agent works fine with CLI today. When should I start thinking about MCP?

The inflection point is when your agent stops acting as you and starts acting on behalf of other people. If you're automating your own GitHub workflow, CLI is the right call — it's simpler and dramatically cheaper. But if you're building a product where your agent reads a customer's repos, writes to their Jira, or messages their Slack team, you've crossed into territory where CLI's ambient credentials become an architectural liability. At that point, you need per-user OAuth, tenant isolation, and an auditable record of every action — none of which CLI can provide at the protocol level.

### 3. How much more expensive is MCP compared to CLI in practice?

Benchmarks comparing identical tasks on the same model (Claude Sonnet 4) against GitHub's Copilot MCP server show MCP costs 4–32× more tokens than CLI, depending on the task. The primary driver is schema bloat: MCP injects definitions for every available tool into every conversation. GitHub's server exposes 43 tools, so even a simple "get repo info" task carries schemas for webhook management, gist creation, and PR review configuration — tools the agent never uses. At 10,000 operations per month, that translates to roughly $3 for CLI versus $55 for direct MCP. A gateway that filters schemas to only relevant tools can close most of this gap.

### 4. What is schema bloat and how do you fix it?

Schema bloat occurs because MCP servers inject definitions for all available tools into every agent conversation, regardless of which tools are actually needed for the task at hand. A server with 43 tools means the agent carries 43 schemas on every single call, even when it only uses one or two. The fix is schema filtering at a gateway layer — instead of passing all 43 definitions, the gateway returns only the 2–3 tools relevant to the current request. This alone can reduce MCP token usage by roughly 90%, bringing costs close to CLI efficiency while preserving MCP's authorization model.

### 5. What does an MCP gateway actually do, and do I need one?

An MCP gateway sits between your agents and upstream MCP servers, solving the three practical problems that make direct MCP connections expensive and unreliable. First, it filters schemas — returning only the tool definitions relevant to the current task rather than all 43, cutting token overhead by roughly 90%. Second, it pools connections — maintaining persistent TCP connections to upstream servers so individual agent sessions don't absorb timeout failures. Third, it centralizes auth — handling OAuth token refresh, scope enforcement, and audit logging in one place rather than per-agent. If you're building a developer tool for your own use, you don't need a gateway. If you're building a multi-tenant product where agents act on behalf of customers, a gateway is what makes MCP's authorization model economically viable.

1

![Image 11](https://cdn.prod.website-files.com/65b87d98fa638289e10b8f61/6a6b2bc8f5d68e194df09663_icon-chatgpt.svg)

Open in ChatGPT

On this page

[The Benchmark](https://www.scalekit.com/blog/mcp-vs-cli-use#the-benchmark)

This is some text inside of a div block.

[The Numbers](https://www.scalekit.com/blog/mcp-vs-cli-use#the-numbers)

This is some text inside of a div block.

[The Biggest Surprise](https://www.scalekit.com/blog/mcp-vs-cli-use#the-biggest-surprise)

This is some text inside of a div block.

[Under the Hood](https://www.scalekit.com/blog/mcp-vs-cli-use#under-the-hood)

This is some text inside of a div block.

[At Scale](https://www.scalekit.com/blog/mcp-vs-cli-use#at-scale)

This is some text inside of a div block.

[The Part Most Takes Miss](https://www.scalekit.com/blog/mcp-vs-cli-use#the-part-most-takes-miss)

This is some text inside of a div block.

[What MCP Gets Right](https://www.scalekit.com/blog/mcp-vs-cli-use#what-mcp-gets-right)

This is some text inside of a div block.

[Decision Framework](https://www.scalekit.com/blog/mcp-vs-cli-use#decision-framework)

This is some text inside of a div block.

[The Architecture](https://www.scalekit.com/blog/mcp-vs-cli-use#the-architecture)

This is some text inside of a div block.

[Try It Yourself](https://www.scalekit.com/blog/mcp-vs-cli-use#try-it-yourself)

This is some text inside of a div block.

[Frequently Asked Questions](https://www.scalekit.com/blog/mcp-vs-cli-use#frequently-asked-questions)

This is some text inside of a div block.

Share this article

## Related posts

[![Image 12](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/69972d7a7a827cabf8bee3f3_WebMCP%20explained.png)](https://www.scalekit.com/blog/webmcp-the-missing-bridge-between-ai-agents-and-the-web)

Feb 19, 2026

[![Image 13](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/682d9d39da359e82ebb0368a_MCP%20servers%20are%20the%20new%20backend_%20Let%E2%80%99s%20stop%20shipping%20them%20unsecured.webp)](https://www.scalekit.com/blog/ship-secure-mcp-server)

May 21, 2025

[![Image 14](https://cdn.prod.website-files.com/65c0f620358c5fe6bbcbf231/68935baefb9adb19ea37fd33_Should%20You%20Wrap%20MCP%20Around%20Your%20Existing%20API_.webp)](https://www.scalekit.com/blog/wrap-mcp-around-existing-api)

Aug 6, 2025

## Acquire enterprise customers with

‍_zero upfront cost._

Every feature unlocked. No hidden fees.
