raise RuntimeError(
    "app.plan.get_plan() has been removed. The system now uses the reflection-based "
    "draft/reflect/revise workflow. Import app.draft.generate_draft instead."
)