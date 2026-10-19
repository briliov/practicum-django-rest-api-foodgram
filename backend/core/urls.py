"""URLS for foodgram project."""

from django.contrib import admin
from django.urls import include, path

from .views import redirect_short_link

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("s/<int:pk>/", redirect_short_link, name="short_link"),
]
