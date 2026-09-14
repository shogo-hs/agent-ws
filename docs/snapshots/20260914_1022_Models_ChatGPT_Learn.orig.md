Title: Models | ChatGPT Learn

URL Source: https://learn.chatgpt.com/codex/models

Markdown Content:
In the ChatGPT desktop app, use the model and reasoning control beneath the composer to choose an available model and adjust its reasoning effort.

Higher reasoning effort can improve results for complex tasks, but it takes longer and uses more tokens. Start with the default effort and increase it when the task needs deeper planning or analysis.

**Ultra** mode goes beyond a single-agent run. It uses [subagents](https://learn.chatgpt.com/codex/agent-configuration/subagents) to accelerate complex work, making it useful for larger tasks that can be split across subagents.

Selections in this preview don't change your ChatGPT settings.5.6 Sol Extra High, 5 of 6.Use Left and Right arrow keys to adjust power.

[](https://learn.chatgpt.com/codex/models)[](https://learn.chatgpt.com/codex/models)[](https://learn.chatgpt.com/codex/models)[](https://learn.chatgpt.com/codex/models)[](https://learn.chatgpt.com/codex/models)[](https://learn.chatgpt.com/codex/models)

Our most capable model for complex work across code, apps, and research, combining advanced reasoning, computer use, and stronger judgment.

codex -m gpt-6-astra

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

The most capable GPT-5.6 model for complex coding, computer use, research, and cybersecurity.

codex -m gpt-5.6-sol

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Balanced GPT-5.6 model for everyday work, with performance competitive with GPT-5.5 at a lower cost.

codex -m gpt-5.6-terra

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Fast and affordable GPT-5.6 model that delivers strong capability at the lowest cost in the family.

codex -m gpt-5.6-luna

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Text-only research preview model optimized for near-instant, real-time coding iteration. Available to ChatGPT Pro users.

codex -m gpt-5.3-codex-spark

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Availability depends on the rollout, your sign-in method, and your client. See [pricing](https://learn.chatgpt.com/codex/pricing) for plan access and usage, and [workspace model availability](https://learn.chatgpt.com/codex/enterprise/workspace-model-availability#gpt-6-astra-in-enterprise) for Enterprise access.

Start with the default Power setting available to your account. Move toward **Smarter** for deeper reasoning or **Faster** for faster, lower-cost work. Open **Advanced** when you want `gpt-5.6-luna` or a specific model, reasoning effort, or speed.

The picker illustrations show GPT-5.6 controls. For eligible Pro, Business ($100), and Enterprise accounts, the Astra rollout updates the Power options to Terra Light, Sol Light, Sol Medium, Astra Light, Astra Medium, and Astra Extra High. Options can differ by plan and rollout stage.

### Experimental context management

On supported Codex clients, users signed in with ChatGPT Plus or Pro can opt in to experimental context management. Astra keeps notes across context windows and can search earlier messages and tool results from the same task. This experiment is off by default and isn't available with Business, Enterprise, or API-key sign-in at launch.

To opt in, set `features.context_management.experimental_mode = true` in your `config.toml`, then start a new task. See the [configuration reference](https://learn.chatgpt.com/codex/config-file/config-reference) for the setting and [configuration basics](https://learn.chatgpt.com/codex/config-file/config-basic) for the file location. Workspace requirements still apply.

Choose **Astra** when a task needs the strongest capability across multiple steps and tools. **Sol** offers depth and polish, **Terra** suits everyday work, and **Luna** suits clear, repeatable tasks.

### Where each model shines

*   **Astra, for the hardest end-to-end work.** Choose Astra for complete workflows across code, apps, and research that need sustained reasoning and judgment. Give it the sources, templates, constraints, and checks that define a useful result. Astra is better at asking focused questions and incorporating your guidance while keeping the original goal and constraints in view.
*   **Sol, for complex, open-ended work.** Choose Sol for ambiguous, difficult, or high-value tasks that need extra analysis, judgment, or polish, such as complex code changes, deep research, or polished documents. For narrower tasks, define what done looks like to keep the work focused.
*   **Terra, the pragmatic all-rounder.** Choose Terra for everyday work that needs strong reasoning and tool use when you do not need Sol's full depth. It is a natural starting point for work you previously gave GPT-5.5.
*   **Luna, for clear, repeatable tasks.** Choose Luna for specific, high-volume tasks when you know what a good result looks like, such as extraction, classification, transformation, and structured summaries.

### Pick a reasoning effort

Use the lowest reasoning effort that produces the result you need. Increase it for tasks that need more planning, analysis, or checking.

*   **Light** in the ChatGPT desktop app, ChatGPT Work on the web, and IDE extension, or **Low** in the CLI, suits quick, well-scoped tasks.
*   **Medium** balances speed and depth for tasks that need more planning.
*   **High** and **Extra High** suit difficult work with multiple steps, sources, or tradeoffs.

There is no exact mapping from GPT-5.5 reasoning efforts to GPT-5.6. Try a familiar task at a lower setting and adjust based on the result.

### Know when to use Max or Ultra

**Max** gives the selected model more time to reason about a single task. Use it for the hardest problems, when depth matters more than speed or usage. If you don't see Max in your options, you'll have to enable it in your app settings.

**Ultra** uses [subagents](https://learn.chatgpt.com/codex/agent-configuration/subagents) to handle separate parts of a complex task in parallel. Choose it when you can divide the work into meaningful parts. Most tasks do not need Max or Ultra.

If Ultra doesn't appear in the desktop app's model slider, go to **Settings**>**Configuration**, then turn on **Ultra in model picker slider**.

When you sign in with ChatGPT, Codex works best with the recommended models listed above.

**GPT-5.4 and GPT-5.4 mini retire from Codex on August 31, 2026.**

If you sign in with ChatGPT, replace `gpt-5.4` with `gpt-5.6-terra` and `gpt-5.4-mini` with `gpt-5.6-luna` in saved configurations, custom agents, and scheduled tasks. The OpenAI API and Codex authenticated with your own API key aren't affected.

View other models

Previous-generation flagship model for complex coding, computer use, knowledge work, and research workflows.

codex -m gpt-5.5

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Flagship model for professional work with strong coding, reasoning, tool use, and agentic workflow capabilities.

codex -m gpt-5.4

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

Fast, efficient mini model for responsive coding tasks and subagents.

codex -m gpt-5.4-mini

Capability

Speed

ChatGPT desktop app

ChatGPT web

Codex CLI

Codex IDE extension

Codex cloud

ChatGPT Credits

API Access

You can also point Codex at any model and provider that supports either the [Chat Completions](https://platform.openai.com/docs/api-reference/chat) or [Responses APIs](https://platform.openai.com/docs/api-reference/responses) to fit your specific use case.

Support for the Chat Completions API is deprecated and will be removed in future releases of Codex.

The `gpt-5.4` and `gpt-5.4-mini` models retire from Codex with ChatGPT sign-in on August 31, 2026. Replace `gpt-5.4` with `gpt-5.6-terra` and `gpt-5.4-mini` with `gpt-5.6-luna` in workspace defaults, saved model settings, managed configurations, custom agents, and scheduled tasks.

The `gpt-5.2` and `gpt-5.3-codex` models are already deprecated in Codex when you sign in with ChatGPT. Update scripts, configuration files, and `codex exec --model` commands that still reference those models.

The OpenAI API and Codex authenticated with your own API key aren't affected by the GPT-5.4 retirement. For current API model availability, see the [API models page](https://learn.chatgpt.com/api/docs/models).

The ChatGPT desktop app, Codex CLI, and IDE extension use the same `config.toml`[configuration file](https://learn.chatgpt.com/codex/config-file/config-basic). To specify a model, add a `model` entry to your configuration file. If you don't specify a model, the ChatGPT desktop app, Codex CLI, or IDE extension uses a recommended model.

`model = "gpt-5.6"`

Currently, you can't change the default model for Codex cloud chats.
