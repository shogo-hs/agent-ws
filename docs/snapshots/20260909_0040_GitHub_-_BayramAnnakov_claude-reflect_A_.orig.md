Title: GitHub - BayramAnnakov/claude-reflect: A self-learning system for Claude Code that captures corrections, positive feedback, and preferences — then syncs them to CLAUDE.md and AGENTS.md.

URL Source: https://github.com/BayramAnnakov/claude-reflect

Markdown Content:
[![Image 1: GitHub stars](https://camo.githubusercontent.com/4344bfef6ac8ab87a1694857a786c2d1e4c55c7e8b907aa80030c5b58d47c3d2/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f73746172732f42617972616d416e6e616b6f762f636c617564652d7265666c6563743f7374796c653d666c61742d737175617265)](https://github.com/BayramAnnakov/claude-reflect/stargazers)[![Image 2: Version](https://camo.githubusercontent.com/5ade77cb999a54902aca9cd08f2b7f82ff0549ee3ab3ea23b3ebdb2f29240f66/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f76657273696f6e2d322e362e302d626c75653f7374796c653d666c61742d737175617265)](https://github.com/BayramAnnakov/claude-reflect/releases)[![Image 3: License: MIT](https://camo.githubusercontent.com/152aa2a37725b9fd554b28ff24d270f6071c67927a63e6d635a55c8e188e20c7/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4c6963656e73652d4d49542d677265656e3f7374796c653d666c61742d737175617265)](https://opensource.org/licenses/MIT)[![Image 4: Tests](https://camo.githubusercontent.com/cc67183b86a64829d53dfd093af34e412e6e423759e292c292c54e4ae590182f/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f74657374732d31363025323070617373696e672d627269676874677265656e3f7374796c653d666c61742d737175617265)](https://github.com/BayramAnnakov/claude-reflect/actions)[![Image 5: Platform](https://camo.githubusercontent.com/cd123549294b5d44c56e3573dc7a699aabfb81a958ef03211ace5fee43daa9c0/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f706c6174666f726d2d6d61634f532532302537432532304c696e757825323025374325323057696e646f77732d6c69676874677265793f7374796c653d666c61742d737175617265)](https://github.com/BayramAnnakov/claude-reflect#platform-support)

A self-learning system for Claude Code that captures corrections and discovers workflow patterns — turning them into permanent memory and reusable skills.

## What it does

[](https://github.com/BayramAnnakov/claude-reflect#what-it-does)
### 1. Learn from Corrections

[](https://github.com/BayramAnnakov/claude-reflect#1-learn-from-corrections)
When you correct Claude ("no, use gpt-5.1 not gpt-5"), it remembers forever.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  You correct    │ ──► │  Hook captures  │ ──► │  /reflect adds  │
│  Claude Code    │     │  to queue       │     │  to CLAUDE.md   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
      (automatic)            (automatic)            (manual review)
```

### 2. Discover Workflow Patterns (NEW in v2)

[](https://github.com/BayramAnnakov/claude-reflect#2-discover-workflow-patterns-new-in-v2)
Analyzes your session history to find repeating tasks that could become reusable commands.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Your past      │ ──► │ /reflect-skills │ ──► │   Generates     │
│  sessions       │     │ finds patterns  │     │   /commands     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
    (68 sessions)         (AI-powered)            (you approve)
```

Example: You've asked "review my productivity" 12 times → suggests creating `/daily-review`

## Key Features

[](https://github.com/BayramAnnakov/claude-reflect#key-features)
| Feature | What it does |
| --- | --- |
| **Permanent Memory** | Corrections sync to CLAUDE.md — Claude remembers across sessions |
| **Skill Discovery** | Finds repeating patterns in your history → generates commands |
| **Multi-language** | AI understands corrections in any language |
| **Skill Improvement** | Corrections during `/deploy` improve the deploy skill itself |

## Installation

[](https://github.com/BayramAnnakov/claude-reflect#installation)

# Add the marketplace
claude plugin marketplace add bayramannakov/claude-reflect

# Install the plugin
claude plugin install claude-reflect@claude-reflect-marketplace

# IMPORTANT: Restart Claude Code to activate the plugin

After installation, **restart Claude Code** (exit and reopen). Then hooks auto-configure and commands are ready.

> **First run?** When you run `/reflect` for the first time, you'll be prompted to scan your past sessions for learnings.

### Prerequisites

[](https://github.com/BayramAnnakov/claude-reflect#prerequisites)
*   [Claude Code](https://claude.ai/code) CLI installed
*   Python 3.6+ (included on most systems)

### Platform Support

[](https://github.com/BayramAnnakov/claude-reflect#platform-support)
*   **macOS**: Fully supported
*   **Linux**: Fully supported
*   **Windows**: Fully supported (native Python, no WSL required)

## Commands

[](https://github.com/BayramAnnakov/claude-reflect#commands)
| Command | Description |
| --- | --- |
| `/reflect` | Process queued learnings with human review |
| `/reflect --scan-history` | Scan ALL past sessions for missed learnings |
| `/reflect --dry-run` | Preview changes without applying |
| `/reflect --targets` | Show detected config files (CLAUDE.md, AGENTS.md) |
| `/reflect --review` | Show queue with confidence scores and decay status |
| `/reflect --dedupe` | Find and consolidate similar entries in CLAUDE.md |
| `/reflect --include-tool-errors` | Include tool execution errors in scan |
| `/reflect-skills` | Discover skill candidates from repeating patterns |
| `/reflect-skills --days N` | Analyze last N days (default: 14) |
| `/reflect-skills --project <path>` | Analyze specific project |
| `/reflect-skills --all-projects` | Scan all projects for cross-project patterns |
| `/reflect-skills --dry-run` | Preview patterns without generating skill files |
| `/skip-reflect` | Discard all queued learnings |
| `/view-queue` | View pending learnings without processing |

## How It Works

[](https://github.com/BayramAnnakov/claude-reflect#how-it-works)
[![Image 6: claude-reflect in action](https://github.com/BayramAnnakov/claude-reflect/raw/main/assets/reflect-demo.jpg)](https://github.com/BayramAnnakov/claude-reflect/blob/main/assets/reflect-demo.jpg)

### Two-Stage Process

[](https://github.com/BayramAnnakov/claude-reflect#two-stage-process)
**Stage 1: Capture (Automatic)**

Hooks run automatically to detect and queue corrections:

| Hook | Trigger | Purpose |
| --- | --- | --- |
| `session_start_reminder.py` | Session start | Shows pending learnings reminder |
| `capture_learning.py` | Every prompt | Detects correction patterns and queues them |
| `check_learnings.py` | Before compaction | Backs up queue and informs user |
| `post_commit_reminder.py` | After git commit | Reminds to run /reflect after completing work |

**Stage 2: Process (Manual)**

Run `/reflect` to review and apply queued learnings to CLAUDE.md.

### Detection Methods

[](https://github.com/BayramAnnakov/claude-reflect#detection-methods)
Claude-reflect uses a **hybrid detection approach**:

**1. Regex patterns (real-time capture)**

Fast pattern matching during sessions detects:

*   **Corrections**: `"no, use X"` / `"don't use Y"` / `"actually..."` / `"that's wrong"`
*   **Positive feedback**: `"Perfect!"` / `"Exactly right"` / `"Great approach"`
*   **Explicit markers**: `"remember:"` — highest confidence

**2. Semantic AI validation (during /reflect)**

When you run `/reflect`, an AI-powered semantic filter:

*   **Multi-language support** — understands corrections in any language
*   **Better accuracy** — filters out false positives from regex
*   **Cleaner learnings** — extracts concise, actionable statements

Example: A Spanish correction like `"no, usa Python"` is correctly detected even though it doesn't match English patterns.

Each captured learning has a **confidence score** (0.60-0.95). The final score is the higher of regex and semantic confidence.

### Human Review

[](https://github.com/BayramAnnakov/claude-reflect#human-review)
When you run `/reflect`, Claude presents a summary table with options:

*   **Apply** - Accept the learning and add to CLAUDE.md
*   **Edit before applying** - Modify the learning text first
*   **Skip** - Don't apply this learning

### Multi-Target Sync

[](https://github.com/BayramAnnakov/claude-reflect#multi-target-sync)
Approved learnings are synced to:

*   `~/.claude/CLAUDE.md` (global - applies to all projects)
*   `./CLAUDE.md` (project-specific)
*   `./**/CLAUDE.md` (subdirectories - auto-discovered)
*   `./.claude/commands/*.md` (skill files - when correction relates to a skill)
*   `AGENTS.md` (if exists - works with Codex, Cursor, Aider, Jules, Zed, Factory)

Run `/reflect --targets` to see which files will be updated.

### Skill Discovery

[](https://github.com/BayramAnnakov/claude-reflect#skill-discovery)
Run `/reflect-skills` to discover repeating patterns in your sessions that could become reusable skills:

```
/reflect-skills                 # Analyze current project (last 14 days)
/reflect-skills --days 30       # Analyze last 30 days
/reflect-skills --all-projects  # Analyze all projects (slower)
/reflect-skills --dry-run       # Preview patterns without generating files
```

**Features:**

*   **AI-powered detection** — uses reasoning, not regex, to find patterns
*   **Semantic similarity** — detects same intent across different phrasings
*   **Project-aware** — groups patterns by project, suggests correct location
*   **Smart assignment** — asks where each skill should go (project vs global)
*   **Generates skill files** — creates draft skills in `.claude/commands/`

**How it works:**

The skill discovers patterns by analyzing your session history semantically. Different phrasings of the same intent are recognized:

```
Session 1: "review my productivity for today"
Session 2: "how was my focus this afternoon?"
Session 3: "check my ActivityWatch data"
Session 4: "evaluate my work hours"
```

Claude reasons: _"These 4 requests have the same intent - reviewing productivity data. The workflow is: fetch time tracking data → categorize activities → calculate focus score. This is a strong candidate for /daily-review."_

**Example output:**

```
════════════════════════════════════════════════════════════
SKILL CANDIDATES DISCOVERED
════════════════════════════════════════════════════════════

Found 2 potential skills from analyzing 68 sessions:

1. /daily-review (High) — from my-productivity-tools
   → Review productivity using time tracking data
   Evidence: 15 similar requests
   Corrections learned: "use local timezone", "chat apps can be work"

2. /deploy-app (High) — from my-webapp
   → Deploy application with pre-flight checks
   Evidence: 10 similar requests
   Corrections learned: "always run tests first"

════════════════════════════════════════════════════════════

Which skills should I generate?
> [1] /daily-review, [2] /deploy-app

Where should each skill be created?
┌──────────────────────┬─────────────────────────┐
│ /daily-review        │ my-productivity-tools   │
│ /deploy-app          │ my-webapp               │
└──────────────────────┴─────────────────────────┘

Skills created:
  ~/projects/my-productivity-tools/.claude/commands/daily-review.md
  ~/projects/my-webapp/.claude/commands/deploy-app.md
```

**Generated skill file example:**

---
description: Deploy application with pre-flight checks
allowed-tools: Bash, Read, Write
---

## Context
Deployment scripts in ./scripts/deploy/

## Your Task
Deploy the application to the specified environment.

### Steps
1. Run test suite
2. Build production assets
3. Deploy to target environment
4. Verify deployment health

### Guardrails
- Always run tests before deploying
- Never deploy to production on Fridays
- Check for pending migrations

---
*Generated by /reflect-skills from 10 session patterns*

### Skill Improvement Routing

[](https://github.com/BayramAnnakov/claude-reflect#skill-improvement-routing)
When you correct Claude while using a skill (e.g., `/deploy`), the correction can be routed back to the skill file itself:

```
User: /deploy
Claude: [deploys without running tests]
User: "no, always run tests before deploying"

→ /reflect detects this relates to /deploy
→ Offers to add learning to .claude/commands/deploy.md
→ Skill file updated with new step
```

This makes skills smarter over time, not just CLAUDE.md.

## Upgrading

[](https://github.com/BayramAnnakov/claude-reflect#upgrading)
### From v2.0.x or earlier

[](https://github.com/BayramAnnakov/claude-reflect#from-v20x-or-earlier)
If you see errors like "Duplicate hooks file detected" or "No such file or directory" after updating, you need to clear the plugin cache. This is due to known Claude Code caching issues:

*   [#14061](https://github.com/anthropics/claude-code/issues/14061) - `/plugin update` doesn't invalidate cache
*   [#15369](https://github.com/anthropics/claude-code/issues/15369) - Uninstall doesn't clear cached files

# 1. Uninstall the plugin
claude plugin uninstall claude-reflect@claude-reflect-marketplace

# 2. Clear both caches (required!)
rm -rf ~/.claude/plugins/marketplaces/claude-reflect-marketplace
rm -rf ~/.claude/plugins/cache/claude-reflect-marketplace

# 3. Exit Claude Code completely (restart terminal or close app)

# 4. Reinstall
claude plugin install claude-reflect@claude-reflect-marketplace

### Standard Update

[](https://github.com/BayramAnnakov/claude-reflect#standard-update)
For normal updates (when no cache issues):

# Use the /plugin menu in Claude Code
/plugin
# Select "Update now" for claude-reflect

## Uninstall

[](https://github.com/BayramAnnakov/claude-reflect#uninstall)

claude plugin uninstall claude-reflect@claude-reflect-marketplace

## File Structure

[](https://github.com/BayramAnnakov/claude-reflect#file-structure)

```
claude-reflect/
├── .claude-plugin/
│   └── plugin.json         # Plugin manifest (auto-registers hooks)
├── commands/
│   ├── reflect.md          # Main command
│   ├── reflect-skills.md   # Skill discovery
│   ├── skip-reflect.md     # Discard queue
│   └── view-queue.md       # View queue
├── hooks/
│   └── hooks.json          # Auto-configured when plugin installed
├── scripts/
│   ├── lib/
│   │   ├── reflect_utils.py      # Shared utilities
│   │   └── semantic_detector.py  # AI-powered semantic analysis
│   ├── capture_learning.py       # Hook: detect corrections
│   ├── check_learnings.py        # Hook: pre-compact check
│   ├── post_commit_reminder.py   # Hook: post-commit reminder
│   ├── compare_detection.py      # Compare regex vs semantic detection
│   ├── extract_session_learnings.py
│   ├── extract_tool_errors.py
│   ├── extract_tool_rejections.py
│   └── legacy/                   # Bash scripts (deprecated)
├── tests/                  # Test suite
└── SKILL.md                # Skill context for Claude
```

## Features

[](https://github.com/BayramAnnakov/claude-reflect#features)
### Historical Scan

[](https://github.com/BayramAnnakov/claude-reflect#historical-scan)
First time using claude-reflect? Run:

/reflect --scan-history

This scans all your past sessions for corrections you made, so you don't lose learnings from before installation.

### Smart Filtering

[](https://github.com/BayramAnnakov/claude-reflect#smart-filtering)
Claude filters out:

*   Questions (not corrections)
*   One-time task instructions
*   Context-specific requests
*   Vague/non-actionable feedback

Only reusable learnings are kept.

### Duplicate Detection

[](https://github.com/BayramAnnakov/claude-reflect#duplicate-detection)
Before adding a learning, existing CLAUDE.md content is checked. If similar content exists, you can:

*   Merge with existing entry
*   Replace the old entry
*   Skip the duplicate

### Semantic Deduplication

[](https://github.com/BayramAnnakov/claude-reflect#semantic-deduplication)
Over time, CLAUDE.md can accumulate similar entries. Run `/reflect --dedupe` to:

*   Find semantically similar entries (even with different wording)
*   Propose consolidated versions
*   Clean up redundant learnings

Example:

```
Before:
  - Use gpt-5.1 for complex tasks
  - Prefer gpt-5.1 for reasoning
  - gpt-5.1 is better for hard problems

After:
  - Use gpt-5.1 for complex reasoning tasks
```

## Tips

[](https://github.com/BayramAnnakov/claude-reflect#tips)
1.   **Use explicit markers** for important learnings:

```
remember: always use venv for Python projects
``` 
2.   **Run /reflect after git commits** - The hook reminds you, but make it a habit

3.   **Historical scan on new machines** - When setting up a new dev environment:

```
/reflect --scan-history --days 90
``` 
4.   **Project vs Global** - Model names and general patterns go global; project-specific conventions stay in project CLAUDE.md

5.   **Discover skills monthly** - Run `/reflect-skills --days 30` monthly to find automation opportunities you might have missed

6.   **Skills get smarter** - When you correct Claude during a skill, that correction can be routed back to the skill file itself via `/reflect`

7.   **Extend session retention** - Claude Code deletes local sessions after 30 days by default. Since claude-reflect relies on session history for `/reflect --scan-history` and `/reflect-skills`, extend this in `~/.claude/settings.json`:

{ "cleanupPeriodDays": 99999 } 

## Contributing

[](https://github.com/BayramAnnakov/claude-reflect#contributing)
Pull requests welcome! Please read the contributing guidelines first.

## License

[](https://github.com/BayramAnnakov/claude-reflect#license)
MIT
