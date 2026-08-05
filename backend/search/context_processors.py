# контекстный процессор для истории поиска
from .models import SearchQuery


def search_history(request):
    if request.user.is_authenticated:
        history = SearchQuery.get_user_history(user=request.user)
    else:
        history = SearchQuery.get_user_history(session_key=request.session.session_key)

    return {
        'search_history': history
    }
