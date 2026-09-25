# ruff: noqa: F821

import asyncio
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
PERSPECTIVES = [
    (
        "climate-physics",
        "Climate physics and boundary-layer response",
    ),
    (
        "thermodynamics",
        "Thermodynamics, exergy, and applied energy systems",
    ),
    (
        "optimization",
        "Optimization formulation and algorithmic validity",
    ),
    (
        "environment-health",
        "Environmental science and heat-health interpretation",
    ),
    (
        "reproducibility",
        "Statistics, provenance, and computational reproducibility",
    ),
    (
        "editorial",
        "Applied Energy editorial fit, manuscript logic, and claim strength",
    ),
]

SCHEMA = {
    "type": "object",
    "properties": {
        "perspective": {"type": "string"},
        "verdict": {"type": "string"},
        "fatal": {"type": "array", "items": {"type": "string"}},
        "major": {"type": "array", "items": {"type": "string"}},
        "minor": {"type": "array", "items": {"type": "string"}},
        "required_fixes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "perspective",
        "verdict",
        "fatal",
        "major",
        "minor",
        "required_fixes",
    ],
}


async def review(label, perspective):
    return await agent(
        phase="review",
        label=label,
        vm_mode="shared",
        soft_time_limit_minutes=12,
        schema=SCHEMA,
        prompt=(
            f"Read-only adversarial review of {PROJECT / 'submission'}/"
            "manuscript_applied_energy.docx and the supporting code, canonical "
            "CSV results, figures, supplement, and provenance in the same "
            "project. Do not edit files, switch branches, run expensive global "
            "analysis, or contact the user. Review specifically from this "
            f"perspective: {perspective}. Separate evidence from inference. "
            "Check novelty, methods, result identities, figure/table support, "
            "reproducibility, and overclaiming as relevant. Prioritize findings "
            "by likely desk-reject/major-revision impact and give concrete "
            "required fixes. Return a concise structured review."
        ),
    )


async def main():
    await register_workflow(
        {
            "name": "global-heat-adversarial-review",
            "description": (
                "Six independent reviews of the local Applied Energy package"
            ),
            "product": "global_heat_allocation manuscript",
            "soft_time_limit_minutes": 12,
            "phases": [
                {
                    "title": "review",
                    "detail": "Independent disciplinary and editorial reviews",
                    "labels": [label for label, _ in PERSPECTIVES],
                }
            ],
        }
    )
    log("Starting six independent adversarial reviews")
    reviews = await parallel(
        [
            (lambda label=label, perspective=perspective: review(label, perspective))
            for label, perspective in PERSPECTIVES
        ]
    )
    log("All reviews completed")
    print(json.dumps(reviews, indent=2, sort_keys=True))


asyncio.run(main())
