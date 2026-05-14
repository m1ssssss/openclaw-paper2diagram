---
name: openclaw-paper2diagram
description: Orchestrate the OpenClaw paper-to-diagram workflow across paper upload, Gemini analysis prompt extraction, and image generation. Use when a user wants to process a paper into Nano Banana/Gemini drawing prompts and generated architecture figures with browser MCP or agent-browser automation.
---

# OpenClaw Paper To Diagram

Use the bundled orchestrator before invoking the lower-level upload, paper analysis, or draw skills.

## Workflow

1. Run the orchestrator in `prepare` mode to validate paths and create the run directory.
2. Use `upload-file` or the orchestrator upload command to upload the paper to Gemini.
3. Ask Gemini for architecture analysis and Nano Banana image prompts.
4. Save the extracted prompts to the analysis text file.
5. Run the orchestrator in `queue` mode to parse prompts and create a drawing queue.
6. Run the draw skill or browser automation against the queue, saving each image to the target path.

## Script

Use:

```bash
python openclaw-paper2diagram-1.0.0/scripts/paper2diagram_flow.py prepare <paper_name>
python openclaw-paper2diagram-1.0.0/scripts/paper2diagram_flow.py queue <paper_name>
```

Optional Linux defaults:

- papers: `/home/xie/桌面/papers`
- analysis: `/home/xie/桌面/analysis`
- images: `/home/xie/桌面/images`

Override these paths with `--papers-dir`, `--analysis-dir`, and `--images-dir`.

## Contract

Treat the generated queue file as the handoff between skills:

```text
<images>/<paper_name>/draw_queue.json
```

Each queue item contains:

- `index`
- `title`
- `prompt`
- `output_path`

Do not mark the task complete until every item has a saved image file or a recorded failure state.
