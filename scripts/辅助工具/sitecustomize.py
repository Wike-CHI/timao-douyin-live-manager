"""Project-wide Python startup customisations.

This module is imported automatically by the Python interpreter (when present
on ``sys.path``) and allows us to perform early runtime adjustments before any
application code runs.

Currently it ensures that LangChain's deprecated HuggingFace embeddings entry
point is transparently mapped to the new ``langchain_huggingface`` package so
that legacy imports continue to function without warnings.
"""

try:  # pragma: no cover - import hook best-effort only
    import server.ai.langchain_hf_patch  # noqa: F401
except Exception:
    # We deliberately swallow all exceptions to avoid impacting interpreter
    # startup; the application will simply continue without the compatibility
    # shim if the import fails for any reason.
    pass
