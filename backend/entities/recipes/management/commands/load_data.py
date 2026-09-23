
import logging
import pandas
from django.core.management.base import BaseCommand
from api.models import Ingredient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage project recipe data (save or load)'

    def handle(self, *args, **options):
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
