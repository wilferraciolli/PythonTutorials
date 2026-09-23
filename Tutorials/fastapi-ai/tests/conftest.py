import pytest


@pytest.fixture(autouse=True)
def no_real_post_indexing():
    """
    API tests must not embed posts through the real Workers AI (.env may hold
    live credentials). Post/comment search indexing is switched off for the
    app here; test_post_search.py covers it with a fake embedder.
    """
    from main import app
    from routers.deps import get_post_search_service

    app.dependency_overrides[get_post_search_service] = lambda: None
    yield
    app.dependency_overrides.pop(get_post_search_service, None)
