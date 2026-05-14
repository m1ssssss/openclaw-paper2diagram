## Publish to ClawHub (OpenClaw 2026.3.28)

OpenClaw installs skills from ClawHub, but **publishing** uses the separate `clawhub` CLI.

Reference: `https://docs.openclaw.ai/tools/clawhub`

### 1) Install clawhub CLI

```bash
npm i -g clawhub
# or
pnpm add -g clawhub
```

### 2) Login

```bash
clawhub login
clawhub whoami
```

### 3) Publish this skill

From the project root:

```bash
cd /Users/qbc/paper2diagram-agent
clawhub skill publish ./skills/paper2diagram \\
  --slug paper2diagram \\
  --name "Paper2Diagram (PDF→Method→Figures)" \\
  --version 0.1.0 \\
  --changelog "Initial release." \\
  --tags latest
```

### 4) Verify install

```bash
openclaw skills search "paper2diagram"
openclaw skills install paper2diagram
openclaw skills info paper2diagram
```

### 5) Update (new version)

Bump the version and publish again:

```bash
clawhub skill publish ./skills/paper2diagram \\
  --slug paper2diagram \\
  --name "Paper2Diagram (PDF→Method→Figures)" \\
  --version 0.1.1 \\
  --changelog "Improve prompts and multi-figure rendering." \\
  --tags latest
```

