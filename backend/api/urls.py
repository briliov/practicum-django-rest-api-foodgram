"""URL config for Foodgram backend API application."""

from django.urls import include, path
from rest_framework import routers

from .views import IngredientsViewSet, RecipeViewSet, TagsViewSet, UsersViewSet

app_name = 'api'


router = routers.DefaultRouter()
router.register(r'users', UsersViewSet, basename='users')
router.register(r'ingredients', IngredientsViewSet, basename='ingredients')
router.register(r'tags', TagsViewSet, basename='tags')
router.register(r'recipes', RecipeViewSet, basename='recipes')


urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('', include(router.urls)),
]
