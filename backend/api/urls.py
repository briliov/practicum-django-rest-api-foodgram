"""URL config for Foodgram backend API application."""

from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from .views import (UsersViewSet, IngredientsViewSet, TagsViewSet,
                    SubscriptionViewSet, RecipeViewSet)


app_name = 'api'

router = routers.DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register(r'users', SubscriptionViewSet, basename='users-subscription')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='schema-redoc'
    ),
]
