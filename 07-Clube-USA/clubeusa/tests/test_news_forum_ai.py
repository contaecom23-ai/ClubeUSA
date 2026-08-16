# tests/test_news_forum_ai.py
import pytest
from unittest.mock import patch, MagicMock

# Dados mock
MOCK_ARTICLE = {
    "id": "article-1",
    "title_pt": "EUA anuncia nova regra de visto",
    "summary_pt": "A nova regra afeta imigrantes brasileiros.",
    "category": "immigration",
    "relevance_score": 85,
    "published_at": "2026-05-13T10:00:00+00:00",
    "url": "https://example.com/news/1",
    "image_url": None,
    "status": "published",
}

MOCK_TOKEN_PAYLOAD = {"sub": "member-1", "plan": "free"}


def make_sb_mock(data):
    """Retorna mock do Supabase com data fixo."""
    m = MagicMock()
    m.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = data
    m.table.return_value.select.return_value.order.return_value.limit.return_value.execute.return_value.data = data
    return m


def test_news_categories_structure():
    """Categorias de notícias têm os campos esperados."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.news import NEWS_CATEGORIES
    assert len(NEWS_CATEGORIES) >= 4
    for cat in NEWS_CATEGORIES:
        assert "slug" in cat
        assert "name" in cat


def test_relevance_threshold():
    """Artigos com score < 40 não aparecem no feed."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.news import is_relevant
    assert is_relevant(39) is False
    assert is_relevant(40) is True
    assert is_relevant(100) is True


def test_forum_post_points():
    """Criar post dá 20 pontos, reply dá 10."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.forum import POST_POINTS, REPLY_POINTS
    assert POST_POINTS == 20
    assert REPLY_POINTS == 10


def test_forum_vote_idempotent():
    """Votar duas vezes no mesmo post retorna already_voted."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.forum import handle_vote_conflict
    result = handle_vote_conflict()
    assert result == {"ok": False, "reason": "already_voted"}


def test_assistant_system_prompt_has_context():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.assistant import AI_SYSTEM_PROMPT
    assert "imigrante" in AI_SYSTEM_PROMPT.lower()
    assert "brasileiro" in AI_SYSTEM_PROMPT.lower()
    assert "advogado" in AI_SYSTEM_PROMPT.lower()


def test_assistant_history_limit():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'clubeusa', 'api'))
    from routers.assistant import MAX_HISTORY_MESSAGES
    assert MAX_HISTORY_MESSAGES == 10
