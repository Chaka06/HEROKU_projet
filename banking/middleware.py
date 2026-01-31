from django.utils import translation


class UserLanguageMiddleware:
    """
    Middleware pour activer automatiquement la langue de l'utilisateur
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Récupérer la langue de l'utilisateur si connecté
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            user_language = request.user.profile.language
            if user_language:
                translation.activate(user_language)
                request.LANGUAGE_CODE = user_language
        
        response = self.get_response(request)
        return response
