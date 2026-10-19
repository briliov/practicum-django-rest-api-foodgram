from django.shortcuts import get_object_or_404, redirect

from entities.recipes.models import Recipe


def redirect_short_link(request, pk):
    """Redirect page with a short link to the recipe frontend."""
    recipe = get_object_or_404(Recipe, pk=pk)
    return redirect(f"/recipes/{recipe.pk}")
