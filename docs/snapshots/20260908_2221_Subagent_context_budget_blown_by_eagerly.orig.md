Title: Subagent context budget blown by eagerly-materialized MCP tool schemas and skill listing

URL Source: https://github.com/anthropics/claude-code/issues/60141

Published Time: 2026-05-18T07:18:39.000Z

Markdown Content:
## Summary

Spawned subagents (`Agent` / Task tool) eagerly materialize two large

 payloads into their context at boot:

1.   The full JSON-Schema of every MCP tool in the subagent's `Tools:`

 allowlist.
2.   A `skill_listing` attachment with all registered skills (names +

 many full descriptions) — `skillCount: 451` in my install.

With a moderate MCP set (~30 servers) plus a populated skill registry,

 this consumes ~140-180k tokens before the subagent has read a single

 byte — pushing many agents past the 200k input cap on their very first

 turn, even with tiny user prompts.

The parent session avoids this via the `ToolSearch` / deferred-tool

 mechanism: only tool _names_ are injected, and full schemas are fetched

 on demand. That affordance is not extended to subagents, and the skill

 listing is not deferred at all.

## Repro

Environment:

*   Claude Code 2.1.138
*   ~30 MCP servers connected (PostHog, Notion, Firebase, GitHub,

 computer-use, mobai, Desktop Commander, filesystem, playwright,

 context7, ecc:*, etc.)
*   ~451 skills registered (ecc/ccg/anthropic-skills/design/data/etc.)
*   Parent session context (Opus 4.7, 1M window): 
    *   Messages 53.7k · Skills 24.2k · Memory 20.7k · System 8.8k
    *   MCP tools (deferred) 328.8k · System tools (deferred) 25k
    *   Loaded total: ~105k / 1M (10%) — comfortable

Steps:

1.   From a parent session with the above MCP + skill set, dispatch any

 subagent whose `Tools:` includes `*` or a broad MCP slice (e.g.

`general-purpose`, several `ecc:*` agents). User prompt can be

 trivial — "read these 5 files and report a table."
2.   The subagent dies on its first turn with:

`400 invalid_request_error: prompt is too long: 201866 tokens > 200000 maximum`

The 201,866-token figure is **identical** across four independent

 failing agents with completely different (and small) user prompts in

 the same session — proving the bloat is in the bootstrap context, not

 the prompts. Failing agent transcripts in

`/private/tmp/claude-<uid>/<cwd-slug>/<session>/tasks/*.output` are

 3-line files: user prompt → bootstrap attachment → 400 error. No tool

 calls happen.

## Evidence

Redacted excerpt from a failing agent's output file

 (`a973f037d7536d7fc.output`). Note the `skill_listing` attachment with

`skillCount: 451` injected into the subagent at boot, immediately

 followed by the 400 error:

Redacted transcript (3 lines)

[
  {
    "isSidechain": true,
    "type": "user",
    "message": {
      "role": "user",
      "content": "In /Users/.../reps-frontend/, read app/onboarding/_layout.tsx and each onboarding screen (welcome, signin, name, age, gender, struggles, contexts, goals, freetext-intro, freetext-situation, freetext-trigger, freetext-goal, generating, reveal, ready). Also locate...[truncated]"
    },
    "timestamp": "2026-05-18T07:10:16.362Z"
  },
  {
    "isSidechain": true,
    "type": "attachment",
    "attachment": {
      "type": "skill_listing",
      "content": "- exercise-ab-test\n- ui-driver-runner\n- mock-screen\n- ...[~450 more entries, many with full descriptions]...",
      "skillCount": 451,
      "isInitial": true
    },
    "timestamp": "2026-05-18T07:10:16.364Z"
  },
  {
    "isSidechain": true,
    "type": "assistant",
    "message": {
      "model": "<synthetic>",
      "role": "assistant",
      "stop_reason": "stop_sequence",
      "content": [{"type": "text", "text": "Prompt is too long"}],
      "usage": { "input_tokens": 0, "output_tokens": 0 }
    },
    "error": "invalid_request",
    "errorDetails": "400 {\"type\":\"error\",\"error\":{\"type\":\"invalid_request_error\",\"message\":\"prompt is too long: 201866 tokens > 200000 maximum\"},\"request_id\":\"...\"}",
    "isApiErrorMessage": true,
    "apiErrorStatus": 400
  }
]

## Why this happens (best guess from observation)

1.   Each subagent type declares an explicit `Tools:` allowlist

 (`Tools: *`, `Tools: All tools except ...`, or an enumerated list).

 The harness injects full tool schemas for everything in that

 allowlist at spawn time.
2.   `ToolSearch` and the "deferred tools available" SessionStart

 reminder are parent-session affordances. The deferral bootstrap

 instructions are not replayed into spawned agents, and schemas are

 eagerly injected anyway.
3.   The `skill_listing` attachment is unconditionally injected as an

 initial attachment to every subagent, regardless of whether the

 agent could plausibly invoke any of those skills.

## Impact

*   `Explore`, `general-purpose`, and several `ecc:*` agents are

 effectively unusable for users with a moderate MCP + skill set.
*   Failures are silent from the user's POV — the parent just sees the

 agent "return nothing." Debugging requires digging into

`/private/tmp/claude-<uid>/.../tasks/*.output`.
*   The 200k cap is hit before the agent's first tool call, so retrying

 / shorter prompts do nothing.
*   The only current workaround is to prune MCP servers and skills

 globally, which punishes the parent session for a subagent problem.

## Suggested fix

1.   **Extend deferred-tool loading to subagents.**

 Subagent system prompts should inject MCP tool _names + short

 descriptions_ by default, not full schemas. Include `ToolSearch` in

 the default subagent toolset and replay the deferral bootstrap

 reminder.
2.   **Defer skill listing similarly.**

 Inject skill names only at boot; full descriptions on demand. 451

 skills × ~50 chars each = a non-trivial bootstrap tax that almost

 no subagent invocation actually needs.
3.   **Per-subagent opt-out** for short-lived agents that genuinely need

 eager loading.
4.   **Surface a clearer error**: when a subagent fails its first turn

 with `prompt is too long`, the parent should see a structured

 diagnostic, not a silent empty return.

## Workarounds users can apply today

*   Reduce connected MCP servers.
*   Reduce installed skill plugins (the ecc/ccg/anthropic-skills sets are

 the heaviest in my install).
*   Prefer narrow-allowlist subagent types (e.g. `ecc:code-reviewer` with

`Tools: Read, Grep, Glob, Bash` succeeds where `general-purpose`

 fails on the same prompt).
*   Skip subagents for path/symbol lookups; `rg`/`cat` via Bash is

 cheaper and doesn't pay the bootstrap tax.
