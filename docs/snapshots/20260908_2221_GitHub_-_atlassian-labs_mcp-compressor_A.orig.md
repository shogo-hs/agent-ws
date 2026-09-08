Title: GitHub - atlassian-labs/mcp-compressor: An MCP server wrapper for reducing tokens consumed by MCP tools, available in typescript, python, and rust

URL Source: https://github.com/atlassian-labs/mcp-compressor

Markdown Content:
[![Image 1: MCP Toplist](https://camo.githubusercontent.com/3c8e981d318786ff07a4fb1ac44fb05f778e419d44753e516f7f5415fff35bbf/68747470733a2f2f6d6370746f706c6973742e636f6d2f62616467652f676c616d6125324661746c61737369616e2d6c6162732532466d63702d636f6d70726573736f722e737667)](https://mcptoplist.com/server/glama%2Fatlassian-labs%2Fmcp-compressor)

[![Image 2: Release](https://camo.githubusercontent.com/714dc1b5358c85f5b7d4a9b919ed75effad39b68e7dbdb7fe140a2c05fa70c5b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f762f72656c656173652f61746c61737369616e2d6c6162732f6d63702d636f6d70726573736f72)](https://github.com/atlassian-labs/mcp-compressor/releases)[![Image 3: Build status](https://camo.githubusercontent.com/627c3bd68474aa3a1a7b0d6475e8fd6c298002e3ed3518fcc175b3a7c59d5fc4/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f616374696f6e732f776f726b666c6f772f7374617475732f61746c61737369616e2d6c6162732f6d63702d636f6d70726573736f722f6d61696e2e796d6c3f6272616e63683d6d61696e)](https://github.com/atlassian-labs/mcp-compressor/actions/workflows/main.yml?query=branch%3Amain)[![Image 4: Commit activity](https://camo.githubusercontent.com/f969ecc03638559d8d690abf470b32e3706670b061e00627c33d4111894c327e/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f636f6d6d69742d61637469766974792f6d2f61746c61737369616e2d6c6162732f6d63702d636f6d70726573736f72)](https://github.com/atlassian-labs/mcp-compressor/commits/main)[![Image 5: License](https://camo.githubusercontent.com/b34f6e737313cb2794a705787535c2138659a2e344ab34a7f88ebdf97d241e9b/68747470733a2f2f696d672e736869656c64732e696f2f6769746875622f6c6963656e73652f61746c61737369616e2d6c6162732f6d63702d636f6d70726573736f72)](https://github.com/atlassian-labs/mcp-compressor/blob/main/LICENSE)

`mcp-compressor` helps agents use large MCP servers without spending huge amounts of context on tool descriptions and schemas.

It can run as a CLI MCP proxy, or be embedded directly from Python, TypeScript, or Rust.

*   **Documentation**: [https://atlassian-labs.github.io/mcp-compressor/](https://atlassian-labs.github.io/mcp-compressor/)
*   **Repository**: [https://github.com/atlassian-labs/mcp-compressor/](https://github.com/atlassian-labs/mcp-compressor/)
*   **Blog**: [https://www.atlassian.com/blog/developer/mcp-compression-preventing-tool-bloat-in-ai-agents/](https://www.atlassian.com/blog/developer/mcp-compression-preventing-tool-bloat-in-ai-agents/)

## Why mcp-compressor?

[](https://github.com/atlassian-labs/mcp-compressor#why-mcp-compressor)
A powerful MCP server can expose dozens or hundreds of tools. Each tool has a name, description, input schema, and sometimes large nested JSON Schema details. Sending all of that to a model up front can waste thousands of tokens before the agent has done any useful work.

For example, large public MCP servers can spend thousands or tens of thousands of tokens on tool descriptions alone. That creates three problems:

*   models spend context on tools they may never call,
*   cost increases for every request that carries the tool list,
*   adding multiple MCP servers quickly overwhelms practical context budgets.

`mcp-compressor` changes the interaction pattern: the model sees a small compressed surface first, asks for the full schema only for the selected tool, and then invokes that tool.

## Pattern 1: compressed MCP proxy

[](https://github.com/atlassian-labs/mcp-compressor#pattern-1-compressed-mcp-proxy)
Use this when you want any MCP client to see a smaller tool surface.

Loading

sequenceDiagram
    participant Client as MCP client / agent
    participant Proxy as mcp-compressor
    participant Backend as Backend MCP server

    Client->>Proxy: tools/list
    Proxy->>Backend: tools/list
    Backend-->>Proxy: all backend tools and schemas
    Proxy-->>Client: compact wrapper tools
    Client->>Proxy: get_tool_schema(tool_name)
    Proxy-->>Client: full schema for selected tool
    Client->>Proxy: invoke_tool(tool_name, input)
    Proxy->>Backend: tools/call selected backend tool
    Backend-->>Proxy: tool result
    Proxy-->>Client: result

The frontend usually exposes only:

*   `get_tool_schema`
*   `invoke_tool`
*   optionally `list_tools` at `max` compression

## Pattern 2: local proxy for SDKs and generated clients

[](https://github.com/atlassian-labs/mcp-compressor#pattern-2-local-proxy-for-sdks-and-generated-clients)
Use this when your application wants to embed compression directly and call tools from code or shell commands.

Loading

flowchart LR
    App[Python / TypeScript / Rust app]
    SDK[CompressorClient]
    Proxy[Local session proxy\n/token auth]
    Generated[Generated CLI / Python / TS clients]
    Backend[MCP backend servers]

    App --> SDK
    SDK --> Proxy
    Generated --> Proxy
    Proxy --> Backend

The SDK starts a local session proxy for generated clients. Generated clients call that proxy using a session token. Your app does **not** need to spawn a `mcp-compressor` stdio subprocess.

## Features

[](https://github.com/atlassian-labs/mcp-compressor#features)
*   [Compressed MCP proxy](https://atlassian-labs.github.io/mcp-compressor/usage/cli/#standard-mcp-proxy) for existing MCP clients.
*   [Compression levels](https://atlassian-labs.github.io/mcp-compressor/concepts/how-it-works/#compression-levels): `low`, `medium`, `high`, `max`.
*   [Python, TypeScript, and Rust SDKs](https://atlassian-labs.github.io/mcp-compressor/usage/sdks/) with aligned `CompressorClient` APIs.
*   [Local TypeScript tool compression](https://atlassian-labs.github.io/mcp-compressor/usage/sdks/#compress-local-typescript-tools) for AI SDK-style in-process tools.
*   [CLI Mode and Code Mode generated clients](https://atlassian-labs.github.io/mcp-compressor/usage/generated-clients/): shell commands plus Python/TypeScript functions.
*   [Just Bash integration](https://atlassian-labs.github.io/mcp-compressor/usage/just-bash/) for command-oriented agents.
*   [Remote streamable HTTP MCP backends](https://atlassian-labs.github.io/mcp-compressor/usage/auth-and-remote/).
*   [OAuth support](https://atlassian-labs.github.io/mcp-compressor/usage/auth-and-remote/#native-oauth) for providers that support browser authorization.
*   [Tool filters and TOON output](https://atlassian-labs.github.io/mcp-compressor/concepts/configuration/#filters) to further reduce context.
*   [Atlassian MCP example](https://atlassian-labs.github.io/mcp-compressor/examples/atlassian/) with OAuth-first usage.

## Quick example

[](https://github.com/atlassian-labs/mcp-compressor#quick-example)
=== "CLI"

```
```bash
mcp-compressor -c medium -- python server.py
```
```

=== "Python"

```
```python
from mcp_compressor import CompressorClient

with CompressorClient(
    servers={"alpha": {"command": "python", "args": ["server.py"]}},
    compression_level="medium",
) as proxy:
    print([tool.name for tool in proxy.tools])
    print(proxy.invoke("echo", {"message": "hello"}))
```
```

=== "TypeScript"

```
```ts
import { CompressorClient } from "@atlassian/mcp-compressor";

const proxy = await new CompressorClient({
  servers: { alpha: { command: "python", args: ["server.py"] } },
  compressionLevel: "medium",
}).connect();

try {
  console.log(proxy.tools.map((tool) => tool.name));
  console.log(await proxy.invoke("echo", { message: "hello" }));
} finally {
  proxy.close();
}
```
```

=== "Rust"

```
```rust
use mcp_compressor::compression::CompressionLevel;
use mcp_compressor::sdk::{CompressorClient, ServerConfig};
use serde_json::json;

let proxy = CompressorClient::builder()
    .server("alpha", ServerConfig::command("python").arg("server.py"))
    .compression_level(CompressionLevel::Medium)
    .build()
    .connect()
    .await?;

let result = proxy.invoke("echo", json!({ "message": "hello" })).await?;
```
```

## Generated clients

[](https://github.com/atlassian-labs/mcp-compressor#generated-clients)
**CLI Mode** generates shell commands:

mcp-compressor --cli-mode --server-name atlassian -- https://mcp.atlassian.com/v1/mcp
atlassian get-accessible-atlassian-resources

**Code Mode** generates Python or TypeScript functions:

# generated-py/atlassian.py
import atlassian

resources = atlassian.getAccessibleAtlassianResources()

import { getAccessibleAtlassianResources } from "./generated-ts/atlassian.ts";

const resources = await getAccessibleAtlassianResources();

See [Code Mode and generated clients](https://atlassian-labs.github.io/mcp-compressor/usage/generated-clients/) for more detail.

## Where to go next

[](https://github.com/atlassian-labs/mcp-compressor#where-to-go-next)
1.   [Install the package you need](https://atlassian-labs.github.io/mcp-compressor/getting-started/installation/).
2.   Run the [quickstart](https://atlassian-labs.github.io/mcp-compressor/getting-started/quickstart/).
3.   Read [how compression works](https://atlassian-labs.github.io/mcp-compressor/concepts/how-it-works/).
4.   Choose between [CLI usage](https://atlassian-labs.github.io/mcp-compressor/usage/cli/), [SDK usage](https://atlassian-labs.github.io/mcp-compressor/usage/sdks/), [generated clients](https://atlassian-labs.github.io/mcp-compressor/usage/generated-clients/), and [Just Bash](https://atlassian-labs.github.io/mcp-compressor/usage/just-bash/).
