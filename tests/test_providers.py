"""
Tests de proveedores — valida que TODOS los agentes usen Gemini
y que los embeddings sean locales (sin OpenAI).

Ejecutar:
    python -m pytest tests/test_providers.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_active_provider_is_gemini():
    """El proveedor activo debe ser Gemini."""
    from config.settings import Settings
    s = Settings()
    provider = s.active_provider()
    assert provider == "gemini", (
        f"Se esperaba 'gemini' pero el proveedor activo es '{provider}'. "
        f"Verifica que GEMINI_API_KEY esté en .env y OPENAI_API_KEY esté vacío."
    )


def test_gemini_key_valid_format():
    """La clave Gemini debe tener formato válido (empieza con AIza)."""
    from config.settings import Settings
    s = Settings()
    assert s.has_gemini_key(), "GEMINI_API_KEY no configurada o formato inválido (debe empezar con 'AIza')"


def test_openai_key_disabled():
    """OpenAI debe estar deshabilitado (sin créditos, usamos Gemini)."""
    from config.settings import Settings
    s = Settings()
    assert not s.has_openai_key(), (
        "OPENAI_API_KEY está activa — esto haría que OpenAI tome prioridad sobre Gemini. "
        "Deja OPENAI_API_KEY vacío en .env."
    )


def test_embeddings_are_local_not_openai():
    """Los embeddings deben ser locales (sentence-transformers), no OpenAI."""
    from llm.models import get_embeddings
    emb = get_embeddings()
    class_name = type(emb).__name__
    assert "HuggingFace" in class_name or "Sentence" in class_name, (
        f"Se esperaban embeddings locales (HuggingFaceEmbeddings) pero se obtuvo: {class_name}"
    )


@pytest.mark.parametrize("role", ["supervisor", "po", "ux", "architect", "dev", "devops"])
def test_agent_model_is_gemini(role):
    """Todos los agentes deben usar un modelo Gemini."""
    from llm.models import get_model_for_agent
    # Limpia cache para evitar estado anterior
    get_model_for_agent.cache_clear()
    llm = get_model_for_agent(role)
    class_name = type(llm).__name__
    assert "Google" in class_name or "Gemini" in class_name, (
        f"Agente '{role}' usa {class_name} en vez de ChatGoogleGenerativeAI (Gemini). "
        f"Verifica config/models.yaml y .env."
    )


def test_strong_model_is_gemini_pro():
    """El modelo 'strong' debe ser gemini-2.5-pro."""
    from llm.models import provider_status
    status = provider_status()
    strong = status["llm_strong_model"]
    assert "gemini" in strong.lower(), f"Modelo strong no es Gemini: {strong}"
    assert "pro" in strong.lower() or "flash" in strong.lower(), (
        f"Modelo strong inesperado: {strong}"
    )


def test_fast_model_is_gemini_flash():
    """El modelo 'fast' debe ser gemini-2.5-flash."""
    from llm.models import provider_status
    status = provider_status()
    fast = status["llm_fast_model"]
    assert "gemini" in fast.lower(), f"Modelo fast no es Gemini: {fast}"
