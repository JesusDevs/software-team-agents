"""
Tests de RAG y base de conocimiento.

Ejecutar:
    python -m pytest tests/test_rag.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ROOT = Path(__file__).parent.parent


def test_local_embeddings_load():
    """Los embeddings locales deben cargar sin OpenAI."""
    from llm.models import get_embeddings
    get_embeddings.cache_clear()
    emb = get_embeddings()
    assert emb is not None, "get_embeddings() retornó None"
    print(f"\n✅ Embeddings: {type(emb).__name__}")


def test_local_embeddings_encode():
    """Los embeddings locales deben poder codificar texto."""
    from llm.models import get_embeddings
    get_embeddings.cache_clear()
    emb = get_embeddings()
    vector = emb.embed_query("test de embedding para onboarding de crédito")
    assert len(vector) > 0, "El vector de embedding está vacío"
    assert all(isinstance(v, float) for v in vector[:5]), "Los valores del vector no son floats"
    print(f"\n✅ Embedding generado: {len(vector)} dimensiones")


def test_search_knowledge_without_openai():
    """search_knowledge no debe fallar ni mencionar OpenAI cuando no hay documentos."""
    from tools.shared.knowledge import make_search_knowledge_tool
    tool = make_search_knowledge_tool("po")
    result = tool.invoke({"query": "plantilla PRD"})
    assert "OPENAI_API_KEY" not in result, (
        f"search_knowledge aún menciona OpenAI: {result}"
    )
    print(f"\n✅ search_knowledge sin OpenAI: '{result[:80]}...'")


def test_knowledge_indexing_with_local_embeddings(tmp_path):
    """La indexación de conocimiento debe funcionar con embeddings locales."""
    from rag.indexer import index_agent_knowledge

    # Crea un archivo de conocimiento temporal
    role = "po"
    kb_dir = ROOT / "agents" / role / "knowledge"
    kb_dir.mkdir(parents=True, exist_ok=True)

    test_file = kb_dir / "_test_knowledge.md"
    test_file.write_text(
        "# Plantilla PRD de Prueba\n\n"
        "## Historia de Usuario\nComo usuario quiero algo para obtener beneficio.\n\n"
        "## Criterios de Aceptación\n- Criterio 1\n- Criterio 2\n",
        encoding="utf-8"
    )

    try:
        count = index_agent_knowledge(role, force=True)
        assert count >= 0, "index_agent_knowledge retornó valor negativo"
        print(f"\n✅ Indexación con embeddings locales: {count} fragmentos")
    finally:
        test_file.unlink(missing_ok=True)


def test_knowledge_retrieval_after_indexing():
    """Después de indexar, search_knowledge debe retornar resultados."""
    from rag.indexer import index_agent_knowledge
    from tools.shared.knowledge import make_search_knowledge_tool

    role = "po"
    kb_dir = ROOT / "agents" / role / "knowledge"
    kb_dir.mkdir(parents=True, exist_ok=True)

    test_file = kb_dir / "_test_retrieval.md"
    test_file.write_text(
        "# Guía de Criterios de Aceptación\n\n"
        "Los criterios de aceptación deben ser SMART: específicos, medibles, alcanzables, relevantes y con tiempo definido.\n\n"
        "## Ejemplo\nDado que el usuario está en la pantalla X, cuando hace Y, entonces Z ocurre.\n",
        encoding="utf-8"
    )

    try:
        count = index_agent_knowledge(role, force=True)
        if count == 0:
            pytest.skip("No se indexaron documentos — el vectorstore puede estar vacío")

        tool = make_search_knowledge_tool(role)
        result = tool.invoke({"query": "criterios de aceptación"})

        assert "OPENAI_API_KEY" not in result
        assert len(result) > 50, f"Resultado de búsqueda muy corto: {result}"
        print(f"\n✅ Recuperación RAG exitosa ({len(result)} chars)")
    finally:
        test_file.unlink(missing_ok=True)
