import logging
import os
import glob

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage project fixtures (save or load)'

    TARGET_DIR = getattr(
        settings, 'GLOBAL_FIXTURES_DIR', settings.BASE_DIR / 'fixtures'
    )

    MODELS = [
        'api.customuser',
        'api.ingredient',
        'api.tag',
        'api.recipe',
        'api.recipeingredient',
        'api.favorite',
        'api.following',
        'api.shoppingcart',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['save', 'load'],
            help='Choose "save" to dump data or "load" to import data'
        )

    def handle(self, *args, **options):
        if options['action'] == 'save':
            self._save_fixtures()
        else:
            self._load_fixtures()

    def _save_fixtures(self):
        os.makedirs(self.TARGET_DIR, exist_ok=True)

        for old_file in glob.glob(os.path.join(self.TARGET_DIR, '*.json')):
            try:
                os.remove(old_file)
            except OSError:
                pass

        logger.info('Starting ordered models dump...')

        for index, model_path in enumerate(self.MODELS, start=1):
            file_name = f'{index:04d}_{model_path.split(".")[-1]}.json'
            output_file = os.path.join(self.TARGET_DIR, file_name)

            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    call_command('dumpdata', model_path, indent=4, stdout=f)

                if os.path.getsize(output_file) <= 4:
                    os.remove(output_file)
                    continue

                logger.info('Saved: %s', file_name)
            except Exception as e:
                logger.error('Error dumping %s: %s', model_path, e,
                             exc_info=True)

    def _load_fixtures(self):
        if not os.path.exists(self.TARGET_DIR):
            logger.warning('Directory not found: %s', self.TARGET_DIR)
            return

        files = sorted(
            [f for f in os.listdir(self.TARGET_DIR) if f.endswith('.json')]
        )

        if not files:
            logger.warning('No fixture files found in %s', self.TARGET_DIR)
            return

        logger.info('Starting database flush before loading fixtures...')

        try:
            call_command('flush', interactive=False)
            logger.info('Database flushed successfully.')
        except Exception as e:
            logger.error('Error during database flush: %s', e, exc_info=True)
            return

        logger.info('Starting ordered fixtures load...')

        for file_name in files:
            file_path = os.path.join(self.TARGET_DIR, file_name)
            logger.info('Loading: %s...', file_name)

            try:
                call_command('loaddata', file_path)
                logger.info('Successfully loaded: %s', file_name)
            except Exception as e:
                logger.error('Error loading %s: %s', file_name, e,
                             exc_info=True)
