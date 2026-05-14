from typing import Any, Dict, List
from app.skills.base import BaseSkill
from app.schemas.common import SkillResult


class PromptTranslatorSkill(BaseSkill):
    name = "prompt_translator"

    def _base_style(self) -> str:
        return (
            "Style: professional academic figure, vector infographic, IEEE/NeurIPS or Medical Image Analysis style, "
            "white background, consistent typography, high contrast, clean alignment, generous spacing. "
            "Use precise arrows, subtle rounded rectangles, no clip-art, no 3D, no photorealism. "
            "Use a restrained color palette (2-4 colors) with a legend and consistent color semantics. "
            "Ensure all text is readable at 100% zoom. "
        )

    def run(self, payload: Dict[str, Any]) -> SkillResult:
        try:
            logic_json_raw = payload["logic_json_raw"]
            base = self._base_style()

            # Multi-figure package: background, architecture, innovations, experiments, limitations.
            prompts: List[Dict[str, Any]] = []

            prompts.append(
                {
                    "id": "fig1_background",
                    "title": "Research Background & Problem Setup",
                    "prompt_en": (
                        f"{base}"
                        "Create Figure 1: a concise academic overview diagram (NOT a network). "
                        "Layout: 3 columns left-to-right: (1) Problem & Motivation, (2) Key Challenge(s), "
                        "(3) Proposed Direction. Use 3-6 short bullet labels total. "
                        "Keep it abstract and high-level, suitable for a paper intro figure."
                    ),
                    "negative_prompt": "cartoon, hand-drawn, messy, dense paragraphs, tiny text",
                    "render_params": {"size": "1536x1024"},
                }
            )

            prompts.append(
                {
                    "id": "fig2_architecture",
                    "title": "Method Architecture (Main Figure)",
                    "prompt_en": (
                        f"{base}"
                        "Create Figure 2: the main method architecture diagram, in the style of a medical image analysis "
                        "encoder-decoder figure. Layout: left-to-right pipeline with labeled encoder blocks, bottleneck, "
                        "and decoder blocks, including skip connections and auxiliary branches if present. "
                        "Use colored feature-map thumbnails to represent intermediate representations, similar to "
                        "typical segmentation figures (small grids with colored blobs). "
                        "Use solid arrows for inference/data flow and dashed arrows for losses, uncertainty or supervision. "
                        "Include a compact legend explaining arrow styles and colors. "
                        f"Architecture specification (verbatim JSON, do not invent missing parts): {logic_json_raw}. "
                        "If a field is 'Not specified', omit that submodule instead of hallucinating."
                    ),
                    "negative_prompt": "photorealistic, artistic background, cluttered layout, illegible labels",
                    "render_params": {"size": "1792x1024"},
                }
            )

            prompts.append(
                {
                    "id": "fig3_innovations",
                    "title": "Core Innovations (Module Highlights)",
                    "prompt_en": (
                        f"{base}"
                        "Create Figure 3: highlight the core innovations as 3-5 callout panels around a small copy "
                        "of the main architecture. Layout: architecture mini-thumbnail in the center-left, and "
                        "numbered innovation callouts around it (top, right, bottom). Each callout includes: "
                        "(a) module name, (b) 1-line purpose, (c) what changes vs baseline. "
                        "Use thin connecting lines or arrows from each callout to the exact location on the mini-architecture. "
                        f"Use this architecture basis: {logic_json_raw}."
                    ),
                    "negative_prompt": "long paragraphs, vague labels, decorative art",
                    "render_params": {"size": "1536x1024"},
                }
            )

            prompts.append(
                {
                    "id": "fig4_experiments",
                    "title": "Experimental Results (Summary Figure)",
                    "prompt_en": (
                        f"{base}"
                        "Create Figure 4: experimental results summary as a clean multi-panel figure. "
                        "Panel A: class-wise bar chart similar to a typical paper figure; horizontal axes are metrics "
                        "(e.g., Recall), vertical axis lists classes or datasets, and for each class draw grouped bars "
                        "for baseline method(s) vs proposed method. "
                        "Panel B: ablation bar chart (x-axis: ablation setting, y-axis: metric), showing relative "
                        "improvements of key modules. "
                        "Use clear legend (colors for methods) and gridlines, but do NOT fabricate exact numeric values; "
                        "use approximate bars and labels like 'ours', 'baseline', 'variant', with neutral tick labels."
                    ),
                    "negative_prompt": "fake exact numbers, crowded tiny table, noisy chart",
                    "render_params": {"size": "1792x1024"},
                }
            )

            prompts.append(
                {
                    "id": "fig5_limitations",
                    "title": "Limitations & Failure Modes",
                    "prompt_en": (
                        f"{base}"
                        "Create Figure 5: limitations and failure modes diagram. "
                        "Layout: 2 columns: (1) Known limitations, (2) Mitigations / future work. "
                        "Each limitation is a short label with an arrow to its mitigation. "
                        "Keep tone academic and factual."
                    ),
                    "negative_prompt": "sarcastic tone, memes, clutter",
                    "render_params": {"size": "1536x1024"},
                }
            )

            return SkillResult(
                status="ok",
                data={
                    "prompts": prompts,
                },
            )
        except Exception as e:
            return SkillResult(status="error", error=str(e))
