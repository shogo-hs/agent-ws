Title: clerk: Auto-Summarize Your Claude Code Sessions

URL Source: https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87

Published Time: 2026-04-17T06:24:08Z

Markdown Content:
[Skip to content](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#main-content)

[![Image 1: DEV Community](https://media2.dev.to/dynamic/image/quality=100/https://dev-to-uploads.s3.amazonaws.com/uploads/logos/resized_logo_UQww2soKuUsjaOGNB38o.png)](https://dev.to/)

[Powered by Algolia](https://www.algolia.com/developers/?utm_source=devto&utm_medium=referral)

[Log in](https://dev.to/enter?signup_subforem=1)[Create account](https://dev.to/enter?signup_subforem=1&state=new-user)

## DEV Community

![Image 2](https://assets.dev.to/assets/heart-plus-active-9ea3b22f2bc311281db911d416166c5f430636e76b15cd5df6b3b841d830eefa.svg)0 Add reaction 

![Image 3](https://assets.dev.to/assets/sparkle-heart-5f9bee3767e18deb1bb725290cb151c25234768a0e9a2bd39370c382d02920cf.svg)0 Like ![Image 4](https://assets.dev.to/assets/multi-unicorn-b44d6f8c23cdd00964192bedc38af3e82463978aa611b4365bd33a0f1f4f3e97.svg)0 Unicorn ![Image 5](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)0 Exploding Head ![Image 6](https://assets.dev.to/assets/raised-hands-74b2099fd66a39f2d7eed9305ee0f4553df0eb7b4f11b01b6b1b499973048fe5.svg)0 Raised Hands ![Image 7](https://assets.dev.to/assets/fire-f60e7a582391810302117f987b22a8ef04a2fe0df7e3258a5f49332df1cec71e.svg)0 Fire 

0 Jump to Comments 0 Save  Boost 

Pick as gem

Copy link

Copied to Clipboard

[Share to X](https://twitter.com/intent/tweet?text=%22clerk%3A%20Auto-Summarize%20Your%20Claude%20Code%20Sessions%22%20by%20Vulcan%20Shen%20%23DEVCommunity%20https%3A%2F%2Fdev.to%2Fvulcan_shen_acdbffa0285d2%2Fclerk-auto-summarize-your-claude-code-sessions-4m87)[Share to LinkedIn](https://www.linkedin.com/shareArticle?mini=true&url=https%3A%2F%2Fdev.to%2Fvulcan_shen_acdbffa0285d2%2Fclerk-auto-summarize-your-claude-code-sessions-4m87&title=clerk%3A%20Auto-Summarize%20Your%20Claude%20Code%20Sessions&summary=A%20CLI%20tool%20that%20turns%20Claude%20Code%20sessions%20into%20a%20searchable%20knowledge%20base%20you%20own.%20Plain%20markdown%2C%20no%20lock-in.&source=DEV%20Community)[Share to Facebook](https://www.facebook.com/sharer.php?u=https%3A%2F%2Fdev.to%2Fvulcan_shen_acdbffa0285d2%2Fclerk-auto-summarize-your-claude-code-sessions-4m87)[Share to Mastodon](https://s2f.kytta.dev/?text=https%3A%2F%2Fdev.to%2Fvulcan_shen_acdbffa0285d2%2Fclerk-auto-summarize-your-claude-code-sessions-4m87)

[Share Post via...](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#)[Report Abuse](https://dev.to/report-abuse)

[![Image 8: Cover image for clerk: Auto-Summarize Your Claude Code Sessions](https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Frc44ag90hlihjok4ai3e.png)](https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Frc44ag90hlihjok4ai3e.png)

[![Image 9: Vulcan Shen](https://media2.dev.to/dynamic/image/width=50,height=50,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Fuser%2Fprofile_image%2F3874809%2F48989896-dd70-436a-bb13-2b5bd2739722.png)](https://dev.to/vulcan_shen_acdbffa0285d2)

[Vulcan Shen](https://dev.to/vulcan_shen_acdbffa0285d2)
Posted on Apr 17•Edited on Apr 19

# clerk: Auto-Summarize Your Claude Code Sessions

[#ai](https://dev.to/t/ai)[#productivity](https://dev.to/t/productivity)[#cli](https://dev.to/t/cli)[#opensource](https://dev.to/t/opensource)

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#what-is-clerk) What is clerk

clerk is a CLI tool that hooks into Claude Code. Every time a session ends, it generates an incremental summary and saves it as a plain markdown file. Over time, your sessions become a searchable, organized knowledge base.

```
brew install vulcanshen/tap/clerk
clerk install
```

After that, it runs silently. No commands to remember, no habits to build.

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#what-it-solves) What it solves

Claude Code has no memory across sessions. When you need to look back — recover context, search past work, or generate a report — there's nothing to work with.

You could ask Claude to re-read old transcripts, but each time it re-processes the entire raw conversation, burning tokens. Across multiple sessions and projects, that's expensive and slow.

clerk does one API call per session at the moment it ends. By the time you need a report, everything is already summarized.

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#what-you-can-do-with-it) What you can do with it

**Weekly reports**

```
clerk report --days 7
```

Reads all summaries from the past 7 days, sends them to Claude, outputs a structured report with summary, by-date, and by-project views. One command, one API call.

**Context recovery**

Type `/clerk-resume` in Claude Code. clerk returns your past summaries and transcript paths so Claude can rebuild context without you hunting for session IDs.

**Search**

Type `/clerk-search` in Claude Code. Search past work by keyword across all projects using AI semantic matching.

**Daily summaries**

Automatic. Every session end produces an incremental summary, organized by date and project:

```
~/.clerk/summary/
├── 20260414/
│   ├── my-api-server.md
│   └── frontend-app.md
└── 20260418/
    └── my-api-server.md
```

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#how-it-works) How it works

```
Session ends → clerk feed (background) → read transcript → call claude -p → save summary + index
```

*   Hooks into Claude Code via SessionStart/SessionEnd hooks
*   Cursor tracking — only processes new messages since last run
*   MCP server for `/clerk-resume` and `/clerk-search` integration
*   Single Go binary, no dependencies beyond Claude Code

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#your-data-your-tools) Your data, your tools

All output is plain markdown with YAML frontmatter. No proprietary format, no lock-in.

Your files work with any text editor, Obsidian, Notion, grep, or your own scripts. If you uninstall clerk and Claude Code, your summaries remain — organized, searchable, and linked.

Everything runs locally. No remote services, no accounts, no data leaving your machine.

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#install) Install

```
# Homebrew
brew install vulcanshen/tap/clerk

# Or install script
curl -fsSL https://raw.githubusercontent.com/vulcanshen/clerk/main/install.sh | sh

# Or from source
go install github.com/vulcanshen/clerk@latest
```

Then run `clerk install` to set up hooks, MCP server, and skills.

Cross-platform: macOS, Linux, Windows.

* * *

GitHub: [github.com/vulcanshen/clerk](https://github.com/vulcanshen/clerk)

[![Image 10: profile](https://media2.dev.to/dynamic/image/width=64,height=64,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Forganization%2Fprofile_image%2F1%2Fd908a186-5651-4a5a-9f76-15200bc6801f.jpg) The DEV Team](https://dev.to/devteam)Promoted

*   [What's a billboard?](https://dev.to/billboards)
*   [Manage preferences](https://dev.to/settings/customization#sponsors)

* * *

*   [Report billboard](https://dev.to/report-abuse?billboard=263574)

[![Image 11: Google article image](https://media2.dev.to/dynamic/image/width=775%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fbebechien.github.io%2Fcozy-corner-future%2Fimages%2Fgemma-skills.png)](https://dev.to/googleai/a-warm-welcome-to-gemma-skills-4466?bb=263574)

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#a-warm-welcome-to-gemmaskills)[A Warm Welcome to "gemma-skills"](https://dev.to/googleai/a-warm-welcome-to-gemma-skills-4466?bb=263574)

Gemma, a family of open models, are lightweight, remarkably capable, and have a wonderful "tunability" that makes them perfect for personal projects and enterprise-grade applications alike.

[Read more →](https://dev.to/googleai/a-warm-welcome-to-gemma-skills-4466?bb=263574)

 Read More 

## Top comments (0)

Subscribe

![Image 12: pic](https://media2.dev.to/dynamic/image/width=256,height=,fit=scale-down,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F8j7kvp660rqzt99zui8e.png)

Personal Trusted User[Create template](https://dev.to/settings/response-templates)
Templates let you quickly answer FAQs or store snippets for re-use.

Submit Preview[Dismiss](https://dev.to/404.html)

[Code of Conduct](https://dev.to/code-of-conduct)•[Report abuse](https://dev.to/report-abuse)

Are you sure you want to hide this comment? It will become hidden in your post, but will still be visible via the comment's [permalink](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#).

- [x] 
Hide child comments as well

 
Confirm

For further actions, you may consider blocking this person and/or [reporting abuse](https://dev.to/report-abuse)

[![Image 13: profile](https://media2.dev.to/dynamic/image/width=64,height=64,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Forganization%2Fprofile_image%2F1%2Fd908a186-5651-4a5a-9f76-15200bc6801f.jpg) The DEV Team](https://dev.to/devteam)Promoted

*   [What's a billboard?](https://dev.to/billboards)
*   [Manage preferences](https://dev.to/settings/customization#sponsors)

* * *

*   [Report billboard](https://dev.to/report-abuse?billboard=263397)

[![Image 14: Google article image](https://media2.dev.to/dynamic/image/width=775%2Cheight=%2Cfit=scale-down%2Cgravity=auto%2Cformat=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2Fsfehx1wjdkf0q365gq6g.png)](https://dev.to/gde/top-gen-ai-frameworks-for-java-in-2026-a-hands-on-comparison-3e29?bb=263397)

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#top-gen-ai-frameworks-for-java-in-2026-a-handson-comparison)[Top Gen AI Frameworks for Java in 2026: A Hands-On Comparison](https://dev.to/gde/top-gen-ai-frameworks-for-java-in-2026-a-hands-on-comparison-3e29?bb=263397)

This article covers the four frameworks I have personally used to ship Java AI applications: Genkit Java, Spring AI, LangChain4j, and Google ADK Java. Each one represents a meaningfully different bet on what a Java AI framework should be, and understanding those differences will save you from picking the wrong tool.

[Read more →](https://dev.to/gde/top-gen-ai-frameworks-for-java-in-2026-a-hands-on-comparison-3e29?bb=263397)

[![Image 15](https://media2.dev.to/dynamic/image/width=90,height=90,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Fuser%2Fprofile_image%2F3874809%2F48989896-dd70-436a-bb13-2b5bd2739722.png) Vulcan Shen](https://dev.to/vulcan_shen_acdbffa0285d2)

Follow

 R&D Engineer working on Kubernetes, cloud infra, and Java backend systems. Occasional open-source tool builder when the pain gets bad enough. 

*    Joined  Apr 12, 2026 

### More from [Vulcan Shen](https://dev.to/vulcan_shen_acdbffa0285d2)

[I built a CLI to stop explaining what /etc/hosts is #go#cli#devops#opensource](https://dev.to/vulcan_shen_acdbffa0285d2/i-built-a-cli-to-stop-explaining-what-etchosts-is-4f0o)

👋 Kindness is contagious

*   [What's a billboard?](https://dev.to/billboards)
*   [Manage preferences](https://dev.to/settings/customization#sponsors)

* * *

*   [Report billboard](https://dev.to/report-abuse?billboard=236587)

Explore this insightful write-up embraced by the inclusive DEV Community. **Tech enthusiasts of all skill levels** can contribute insights and expand our shared knowledge.

Spreading a simple "thank you" uplifts creators—let them know your thoughts in the discussion below!

At DEV, **collaborative learning fuels growth** and forges stronger connections. If this piece resonated with you, a brief note of thanks goes a long way.

## [](https://dev.to/vulcan_shen_acdbffa0285d2/clerk-auto-summarize-your-claude-code-sessions-4m87#-cta-httpsdevtoenterstatenewuser-)[Okay](https://dev.to/enter?state=new-user&bb=236587)

[DEV Community](https://dev.to/) — A space to discuss and keep up software development and manage your software career

*   [Home](https://dev.to/)
*   [DEV Challenges](https://dev.to/challenges)
*   [DEV++](https://dev.to/++)
*   [Videos](https://dev.to/videos)
*   [DEV Education Tracks](https://dev.to/deved)
*   [DEV Help](https://dev.to/help)
*   [Advertise on DEV](https://dev.to/advertise)
*   [Organization Accounts](https://dev.to/organizations)
*   [DEV Showcase](https://dev.to/showcase)
*   [About](https://dev.to/about)
*   [Contact](https://dev.to/contact)
*   [Free Postgres Database](https://dev.to/free-postgres-database-tier)
*   [DEV Shop](https://shop.forem.com/)
*   [MLH](https://mlh.io/)

*   [Code of Conduct](https://dev.to/code-of-conduct)
*   [Privacy Policy](https://dev.to/privacy)
*   [Terms of Use](https://dev.to/terms)

Built on [Forem](https://www.forem.com/) — the [open source](https://dev.to/t/opensource) software that powers [DEV](https://dev.to/) and other inclusive communities.

Made with love and [Ruby on Rails](https://dev.to/t/rails). DEV Community © 2016 - 2026.

![Image 16: DEV Community](https://media2.dev.to/dynamic/image/width=190,height=,fit=scale-down,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.amazonaws.com%2Fuploads%2Farticles%2F8j7kvp660rqzt99zui8e.png)

We're a place where coders share, stay up-to-date and grow their careers.

[Log in](https://dev.to/enter?signup_subforem=1)[Create account](https://dev.to/enter?signup_subforem=1&state=new-user)

![Image 17](https://assets.dev.to/assets/sparkle-heart-5f9bee3767e18deb1bb725290cb151c25234768a0e9a2bd39370c382d02920cf.svg)![Image 18](https://assets.dev.to/assets/multi-unicorn-b44d6f8c23cdd00964192bedc38af3e82463978aa611b4365bd33a0f1f4f3e97.svg)![Image 19](https://assets.dev.to/assets/exploding-head-daceb38d627e6ae9b730f36a1e390fca556a4289d5a41abb2c35068ad3e2c4b5.svg)![Image 20](https://assets.dev.to/assets/raised-hands-74b2099fd66a39f2d7eed9305ee0f4553df0eb7b4f11b01b6b1b499973048fe5.svg)![Image 21](https://assets.dev.to/assets/fire-f60e7a582391810302117f987b22a8ef04a2fe0df7e3258a5f49332df1cec71e.svg)
