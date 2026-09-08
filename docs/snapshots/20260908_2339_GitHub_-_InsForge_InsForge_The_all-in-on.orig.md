Title: GitHub - InsForge/InsForge: The all-in-one, open-source backend platform for agentic coding. InsForge gives your coding agent database, auth, storage, compute, hosting, and AI gateway to ship full-stack apps end-to-end.

URL Source: https://github.com/InsForge/InsForge

Markdown Content:
⭐ _Help us reach more developers and grow the InsForge community. Star this repo!_

The all-in-one, open-source backend platform for agentic coding. InsForge gives your coding agent database, auth, storage, compute, hosting, and AI gateway to ship full-stack apps end-to-end.

read-me.mp4[Video 3](https://private-user-images.githubusercontent.com/50334568/589419689-345efbc6-ca63-4189-bde0-12ef3bda561b.mp4?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3ODg4Nzg2MzksIm5iZiI6MTc4ODg3ODMzOSwicGF0aCI6Ii81MDMzNDU2OC81ODk0MTk2ODktMzQ1ZWZiYzYtY2E2My00MTg5LWJkZTAtMTJlZjNiZGE1NjFiLm1wND9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjA5MDglMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwOTA4VDE0Mzg1OVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWZlZmM0OTgzYWQ4MzEwOWRkNzk1ODM5YTY5YzUzYTU3OWQyMzhhZTBhOGY5YzQ3MTU4NmI1YTY5OGZjMTdjNjQmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JnJlc3BvbnNlLWNvbnRlbnQtdHlwZT12aWRlbyUyRm1wNCJ9.MkDKN0jgsUSQ2Odqzsm0Dx-btYeyqF6GyCRHLmwW0-I)

### How it works

[](https://github.com/InsForge/InsForge#how-it-works)
Coding agents interact with InsForge through one of two interfaces:

*   **MCP Server** (self-hosted and cloud): exposes InsForge's operations as tools any MCP-compatible agent can call.
*   **CLI + Skills** (cloud only): a command-line interface paired with Skills that agents invoke directly from the terminal.

Both interfaces let coding agents operate the backend like backend engineers:

*   **Read backend context and state**: Pull documentation, schemas, metadata (deployed functions, bucket contents, auth config), and runtime logs, so the agent has what it needs to write code, verify what it built, and debug when something breaks.
*   **Configure primitives**: Deploy edge functions, run database migrations, create storage buckets, set up auth providers, and configure other backend resources directly.

Loading

graph TB

    subgraph TOP[" "]
        AG[AI Coding Agents]
    end

    subgraph MID[" "]
        SL[InsForge]
    end

    AG --> SL

    SL --> AUTH[Authentication]
    SL --> DB[Database]
    SL --> ST[Storage]
    SL --> EF[Edge Functions]
    SL --> MG[Model Gateway]
    SL --> CP[Compute]
    SL --> DEP[Deployment]

    classDef bar fill:#0b0f14,stroke:#30363d,stroke-width:1px,color:#ffffff
    classDef card fill:#161b22,stroke:#30363d,stroke-width:1px,color:#ffffff

    class AG,SL bar
    class AUTH,DB,ST,EF,MG,CP,DEP card

    style TOP fill:transparent,stroke:transparent
    style MID fill:transparent,stroke:transparent

    linkStyle default stroke:#30363d,stroke-width:1px

### Core Products

[](https://github.com/InsForge/InsForge#core-products)
*   **Authentication**: User management, authentication, and sessions
*   **Database**: Postgres relational database
*   **Storage**: S3-compatible file storage
*   **Model Gateway**: OpenAI-compatible API across multiple LLM providers
*   **Edge Functions**: Serverless code running on the edge
*   **Compute** (private preview): Long-running container services
*   **Site Deployment**: Site build and deployment

## ⭐️ Star the Repository

[](https://github.com/InsForge/InsForge#%EF%B8%8F-star-the-repository)
[![Image 1: Star InsForge](https://github.com/InsForge/InsForge/raw/main/assets/insforge-star.gif)](https://github.com/InsForge/InsForge/blob/main/assets/insforge-star.gif)

If you find InsForge useful or interesting, a GitHub Star ⭐️ would be greatly appreciated.

## Quickstart

[](https://github.com/InsForge/InsForge#quickstart)
### Cloud-hosted: [insforge.dev](https://insforge.dev/)

[](https://github.com/InsForge/InsForge#cloud-hosted-insforgedev)
[![Image 2: InsForge.dev](https://camo.githubusercontent.com/be4e556d227a42da0b53a8823dc03db4472fbeb970a539f566ac812f0e09c64a/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f696e73666f7267652e6465762d3138313831383f6c6f676f3d646174613a696d6167652f737667253262786d6c3b6261736536342c50484e325a79423361575230614430694d6a51774969426f5a576c6e61485139496a49304d434967646d6c6c64304a76654430694d434177494449304d4341794e44416949475a7062477739496d3576626d5569494868746247357a50534a6f644852774f693876643364334c6e637a4c6d39795a7938794d4441774c334e325a79492b50484268644767675a443069545449324c6a45784f4451674d5441784c6a5a444d6a4d754d6a6b7a4f5341354f4334334f444d7a4944497a4c6a49354d7a6b674f5451754d6a45324e6941794e6934784d54673049446b784c6a524d4f5463754e7a45324e7941794d4577794d4441674d6a424d4e7a63754d6a59674d5451794c6a52444e7a51754e444d314e5341784e4455754d6a4533494459354c6a67314e6a49674d5451314c6a49784e7941324e7934774d7a4533494445304d693430544449324c6a45784f4451674d5441784c6a5a614969426d6157787350534a3361476c305a534976506a78775958526f49475139496b30784e5455754d6a5578494463334c6a4d334e5577794d4441674d544979566a49794e4577784d4451754d544135494445794f43347a4e7a564d4d5455314c6a49314d5341334e79347a4e7a56614969426d6157787350534a3361476c305a534976506a777663335a6e50676f3d266c6f676f436f6c6f723d7768697465)](https://insforge.dev/)

### Self-hosted: Docker Compose

[](https://github.com/InsForge/InsForge#self-hosted-docker-compose)
Prerequisites: [Docker](https://www.docker.com/) with Compose v2.

#### 1. Setup

[](https://github.com/InsForge/InsForge#1-setup)

curl -fsSL https://raw.githubusercontent.com/InsForge/InsForge/main/deploy/setup.sh | sh -s ~/insforge

Fetches the files the stack reads and generates `JWT_SECRET`, `ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `ROOT_ADMIN_PASSWORD`, and the two access keys into `~/insforge/.env` (mode 600). Nothing is started. Re-running refreshes the files and keeps every value you have set — it only ever adds `COMPOSE_FILE`, or points it at this checkout's compose file if it still names the development one.

cd ~/insforge
$EDITOR .env          # API_BASE_URL, VITE_API_BASE_URL — the URL browsers will use
docker compose up -d

`.env` sets `COMPOSE_FILE`, so plain `docker compose` commands work from that directory — no `-f` flags to remember.

[![Image 3: Deploy on Docker](https://github.com/InsForge/InsForge/raw/main/deploy/buttons/docker.png)](https://github.com/InsForge/InsForge/blob/main/deploy/docker-deploy.md)

Building from source instead
For working on InsForge itself. `docker-compose.prod.yml` reads the same variables but generates nothing, so set the secrets in `.env` yourself before starting anything you expose.

git clone https://github.com/InsForge/InsForge.git
cd InsForge
cp .env.example .env
$EDITOR .env
docker compose -f docker-compose.prod.yml up

Set `JWT_SECRET`, `ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, and `ROOT_ADMIN_PASSWORD` — `.env.example` ships placeholders for them, and the compose file falls back to published defaults for any you leave unset. Set `ACCESS_API_KEY` and `ACCESS_ANON_KEY` too if you want to know your own keys; left empty, the backend generates a pair only it knows.

This path passes `-f` explicitly, which overrides `COMPOSE_FILE`. Add overlays as further `-f` flags rather than editing that variable.

#### 2. Connect InsForge MCP

[](https://github.com/InsForge/InsForge#2-connect-insforge-mcp)
Open [http://localhost:7130](http://localhost:7130/)

Follow the steps to connect InsForge MCP Server.

[![Image 4: Connect InsForge MCP](https://github.com/InsForge/InsForge/raw/main/assets/connect.png)](https://github.com/InsForge/InsForge/blob/main/assets/connect.png)

#### 3. Verify installation

[](https://github.com/InsForge/InsForge#3-verify-installation)
To verify the connection, send the following prompt to your agent:

```
I'm using InsForge as my backend platform, call InsForge MCP's fetch-docs tool to learn about InsForge instructions.
```

#### 4. Running Multiple Projects

[](https://github.com/InsForge/InsForge#4-running-multiple-projects)
Give each project its own directory:

curl -fsSL https://raw.githubusercontent.com/InsForge/InsForge/main/deploy/setup.sh | sh -s ~/project1
curl -fsSL https://raw.githubusercontent.com/InsForge/InsForge/main/deploy/setup.sh | sh -s ~/project2

Then give each a project name and its own ports. Both `.env` files start with `COMPOSE_PROJECT_NAME=insforge`, and **two directories sharing that name share containers** — the second `up -d` adopts the first's, rebuilt with the second's config. Set it before starting anything.

`~/project1/.env` keeps the default ports — which collide with the `~/insforge` instance from the quickstart above if it is still running. Stop that one, or give `project1` its own ports the way `project2` has:

COMPOSE_PROJECT_NAME=project1

`~/project2/.env`:

COMPOSE_PROJECT_NAME=project2
POSTGRES_PORT=5442
POSTGREST_PORT=5440
APP_PORT=7230
AUTH_PORT=7231
DENO_PORT=7233

Now each directory is a separate instance with its own containers, volumes, database, and secrets:

cd ~/project1 && docker compose up -d
cd ~/project2 && docker compose up -d

`docker compose ps`, `logs -f`, and `down` operate on whichever directory you run them from.

#### 5. Storage Backends (Optional)

[](https://github.com/InsForge/InsForge#5-storage-backends-optional)
InsForge stores files on the local filesystem by default. Backing storage with an S3-compatible store also enables the S3-compatible gateway at `/storage/v1/s3` (use `aws` CLI, rclone, or any AWS SDK against your InsForge Storage).

Append one overlay to `COMPOSE_FILE` in `.env`. Bundled MinIO, whose store stays internal to the Docker network:

COMPOSE_FILE=deploy/docker-compose/docker-compose.yml:docker-compose.minio.yml

Or RustFS, an Apache-2.0 licensed alternative:

COMPOSE_FILE=deploy/docker-compose/docker-compose.yml:docker-compose.rustfs.yml

Keep one — the file is read as shell assignments, so a second line replaces the first. Then `docker compose up -d` as usual.

The overlays ship with default store credentials — set `MINIO_ROOT_USER`/`MINIO_ROOT_PASSWORD` (or `RUSTFS_ACCESS_KEY`/`RUSTFS_SECRET_KEY`) in `.env` before production use.

Or bring your own S3-compatible store (AWS S3, MinIO, RustFS, Wasabi, R2, Tencent COS, Aliyun OSS ...) by setting `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` — plus `S3_ENDPOINT_URL` for non-AWS providers — in `.env`. If the endpoint is not reachable by browsers (private network), also set `S3_USE_PRESIGNED_URLS=false` to enable proxy mode.

See the [self-hosted storage guide](https://docs.insforge.dev/deployment/self-host-storage) for provider notes, presigned vs. proxy mode, and upgrade tips.

### One-click Deployment

[](https://github.com/InsForge/InsForge#one-click-deployment)
In addition to running InsForge locally, you can also launch InsForge using a pre-configured setup. This allows you to get up and running quickly with InsForge without installing Docker on your local machine.

| Railway | Zeabur | Sealos | RepoCloud |
| --- | --- | --- | --- |
| [![Image 5: Deploy on Railway](https://camo.githubusercontent.com/88cb27bf937b98276737ba7888269a1bc9495d8670f63e1acc908b3442841114/68747470733a2f2f7261696c7761792e636f6d2f627574746f6e2e737667)](https://railway.com/deploy/insforge) | [![Image 6: Deploy on Zeabur](https://camo.githubusercontent.com/4862f766bfb933cf474ec456099790bafc15f298c4ae2aded29cd85052b3c880/68747470733a2f2f7a65616275722e636f6d2f627574746f6e2e737667)](https://zeabur.com/templates/Q82M3Y) | [![Image 7: Deploy on Sealos](https://camo.githubusercontent.com/ea79f0254cdc854923560e4dc71f7e63ffe09b31cad41657a11a077dccdee01d/68747470733a2f2f7365616c6f732e696f2f4465706c6f792d6f6e2d5365616c6f732e737667)](https://sealos.io/products/app-store/insforge) | [![Image 8: Deploy on RepoCloud](https://camo.githubusercontent.com/bb59e7a3c986f97daed8cee9518a0e5edf7567e1b7823158ea3f946ef15768db/68747470733a2f2f64313674307063343834367835322e636c6f756466726f6e742e6e65742f6465706c6f796c6f62652e737667)](https://repocloud.io/details/InsForge/) |

## Contributing

[](https://github.com/InsForge/InsForge#contributing)
**Contributing**: If you're interested in contributing, you can check our guide here [CONTRIBUTING.md](https://github.com/InsForge/InsForge/blob/main/CONTRIBUTING.md). We truly appreciate pull requests, and all types of help are appreciated!

**Support**: If you need any help or support, we're responsive on our [Discord channel](https://discord.com/invite/MPxwj5xVvW), and also feel free to email us [info@insforge.dev](mailto:info@insforge.dev) too!

## Documentation & Support

[](https://github.com/InsForge/InsForge#documentation--support)
### Documentation

[](https://github.com/InsForge/InsForge#documentation)
*   **[Official Docs](https://docs.insforge.dev/introduction)** - Comprehensive guides and API references

### Community

[](https://github.com/InsForge/InsForge#community)
*   **[Discord](https://discord.com/invite/MPxwj5xVvW)** - Join our vibrant community
*   **[Twitter](https://x.com/InsForge)** - Follow for updates and tips

### Contact

[](https://github.com/InsForge/InsForge#contact)
*   **Email**: [info@insforge.dev](mailto:info@insforge.dev)

## License

[](https://github.com/InsForge/InsForge#license)
This project is licensed under the Apache License 2.0 - see the [LICENSE](https://github.com/InsForge/InsForge/blob/main/LICENSE) file for details.

* * *

[![Image 9: Star History Chart](https://camo.githubusercontent.com/7da8430f6ea7ad215fed990069a4b8df748e912841205ed0c7bc8ee6ff90c289/68747470733a2f2f6170692e737461722d686973746f72792e636f6d2f7376673f7265706f733d496e73466f7267652f496e73466f72676526747970653d44617465)](https://www.star-history.com/#InsForge/InsForge&Date)

## Badges

[](https://github.com/InsForge/InsForge#badges)
Show your project is built with InsForge.

### Made with InsForge

[](https://github.com/InsForge/InsForge#made-with-insforge)[![Image 10: Made with InsForge](https://camo.githubusercontent.com/e23fffd1db316f831eeec569309def4ee22463862d3a464a296a32c22ef95441/68747470733a2f2f696e73666f7267652e6465762f62616467652d6d6164652d776974682d696e73666f7267652e737667)](https://insforge.dev/)
**Markdown:**

[![Made with InsForge](https://insforge.dev/badge-made-with-insforge.svg)](https://insforge.dev)

**HTML:**

<a href="https://insforge.dev">
  <img
    width="168"
    height="30"
    src="https://insforge.dev/badge-made-with-insforge.svg"
    alt="Made with InsForge"
  />
</a>

### Made with InsForge (dark)

[](https://github.com/InsForge/InsForge#made-with-insforge-dark)[![Image 11: Made with InsForge](https://camo.githubusercontent.com/b4d5017c12ebd66dcfc7efbe46d1867914638260f2e77b55e099a7529c4df049/68747470733a2f2f696e73666f7267652e6465762f62616467652d6d6164652d776974682d696e73666f7267652d6461726b2e737667)](https://insforge.dev/)
**Markdown:**

[![Made with InsForge](https://insforge.dev/badge-made-with-insforge-dark.svg)](https://insforge.dev)

**HTML:**

<a href="https://insforge.dev">
  <img
    width="168"
    height="30"
    src="https://insforge.dev/badge-made-with-insforge-dark.svg"
    alt="Made with InsForge"
  />
</a>

⭐ **Star us on GitHub** to get notified about new releases!
