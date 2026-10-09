"""Custom django command for loadding ingredients data."""

import logging

import pandas
from django.core.management.base import BaseCommand

from entities.recipes.models import Ingredient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Helping command for load ingredients data."""
    help = 'Loads ingredients data'

    def handle(self, *args, **options):
        """Handler for Ingredients load command."""
        ingredients_data = pandas.read_json('data/ingredients.json'
                                            ).to_dict(orient='records')
        count_before = Ingredient.objects.count()
        ingredients_instances = [Ingredient(**ingredient_data)  # type: ignore
                                 for ingredient_data in ingredients_data]
        Ingredient.objects.bulk_create(ingredients_instances,
                                       ignore_conflicts=True)
        count_after = Ingredient.objects.count()
        added_count = count_after - count_before
        logger.info('Операция завершена. Успешно добавлено новых записей: '
                    f'{added_count}')
