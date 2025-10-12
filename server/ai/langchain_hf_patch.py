"""Compatibility layer for LangChain HuggingFace embeddings.

This module maps the deprecated `langchain.embeddings.HuggingFaceEmbeddings`
entry point to the modern implementation provided by `langchain_huggingface`.
Importing this module ensures that existing code paths that still rely on
LangChain's legacy location seamlessly receive the updated class.
"""

try:
    from langchain_huggingface import HuggingFaceEmbeddings as _NewHFEmbeddings
except ImportError:  # pragma: no cover - optional dependency
    _NewHFEmbeddings = None

if _NewHFEmbeddings is not None:
    try:
        import langchain.embeddings.huggingface as _legacy_module

        _legacy_module.HuggingFaceEmbeddings = _NewHFEmbeddings
    except ImportError:
        # If LangChain's legacy module cannot be imported we silently ignore it;
        # callers that rely on the new package can import it directly.
        pass

    try:
        import langchain.embeddings as _legacy_package

        _legacy_package.HuggingFaceEmbeddings = _NewHFEmbeddings
    except ImportError:
        pass
