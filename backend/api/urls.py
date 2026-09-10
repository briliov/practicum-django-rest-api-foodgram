"""URL config for Foodgram backend API application."""

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
# Click to add a breakpoint
from rest_framework import routers

from .views import IngredientsViewSet, RecipeViewSet, TagsViewSet, UsersViewSet

app_name = 'api'

# Initialize the standard REST framework router
router = routers.DefaultRouter()

# Register API viewsets with the router
router.register(r'users', UsersViewSet, basename='users')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')

# Define URL patterns for the API application
urlpatterns = [
    # Djoser authentication and user management endpoints
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),

    # Main API endpoints registered via the router
    path('', include(router.urls)),

    # OpenAPI schema generation and Redoc documentation endpoints
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='schema-redoc'
    ),
]
