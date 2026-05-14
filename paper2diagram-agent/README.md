# paper2diagram-agent

MVP pipeline for: PDF -> Method/Architecture extraction -> logic distillation -> Banana prompt -> image render.

## 1) Setup
1. `cd /Users/qbc/paper2diagram-agent`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `cp .env.example .env` and fill keys

## 2) Run (direct pipeline)
`python -m app.main /absolute/path/to/paper.pdf 30`

## 3) OpenClaw integration
This project now includes an OpenClaw adapter layer:
- `app/openclaw/skill_registry.py`: registers all skills
- `app/openclaw/agent.py`: OpenClaw runtime adapter
- `app/openclaw_main.py`: entrypoint for local/runtime mode
- `openclaw.runtime.example.json`: runtime mapping example

### 3.1 Local mode (same logic, through OpenClaw adapter)
`python -m app.openclaw_main local /absolute/path/to/paper.pdf 30`

### 3.2 Runtime mode (connect to your OpenClaw SDK)
`python -m app.openclaw_main runtime`

If OpenClaw SDK is installed, runtime mode imports it and prints registered skills.
Then bind `SkillRegistry.call` to your OpenClaw tool registration API.

## 4) OpenClaw deployment checklist
1. Install OpenClaw SDK/CLI with your official package name/version.
2. Create an agent named `paper-review-diagram-agent`.
3. Set system prompt file: `app/prompts/agent_role.md`.
4. Set output schema file: `app/prompts/output_schema.md`.
5. Register tools:
   - `pdf_reader`
   - `section_extractor`
   - `logic_distiller`
   - `prompt_translator`
   - `banana_renderer`
   - `paper_to_diagram`
6. Route LLM tasks to Gemini model from env (`GEMINI_MODEL`).
7. Keep rendering on Banana API via `banana_renderer`.

## Notes
- If Banana API endpoint differs, edit `BANANA_PRO_BASE_URL`.
- If output is `partial_ok`, prompt generation succeeded but rendering failed; use `final_prompt` for manual retry.
- The OpenClaw adapter is intentionally version-tolerant. If your SDK API differs, only update `app/openclaw/agent.py` binding logic.
