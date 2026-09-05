import logging
import os
import sys
from typing import Any
import pandas as pd
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)


class Command(BaseCommand):
    help = 'Imports test data from JSON files into Django models dynamically.'

    def handle(self, *args: Any, **options: Any) -> None:
        folder_path: str = 'test_data'

        if not os.path.exists(folder_path):
            raise CommandError(f"Folder '{folder_path}' not found.")

        file_names = self._get_json_files(folder_path)
        if not file_names:
            return

        for file_name in file_names:
            model_name = self._get_model_name(file_name)
            TargetModel = self._get_django_model(model_name)
            if not TargetModel:
                logger.error(f'Model {model_name} not found in app api '
                             f'for file {file_name}.')
                continue
            file_path = os.path.join(folder_path, file_name)
            rows = self._get_parse_and_clean_json(file_path, file_name)
            if rows is None:
                continue

            self._bulk_insert_to_db(TargetModel, rows, model_name)

    def _get_json_files(self, folder_path: str) -> list[str] | None:
        file_names: list[str] = [
            name for name in os.listdir(folder_path)
            if name.endswith('.json')
        ]
        if not file_names:
            logger.warning(f"No JSON files found in '{folder_path}' folder.")
            return None
        return file_names

    def _get_model_name(self, file_name: str) -> str:
        clean_name: str = file_name.removesuffix('.json').rstrip('s')
        return clean_name.capitalize()

    def _get_django_model(self, model_name: str) -> type[Model] | None:
        try:
            return apps.get_model(app_label='api', model_name=model_name)
        except LookupError:
            return None

    def _get_parse_and_clean_json(self, file_path: str, file_name: str
                                  ) -> list[dict[str, Any]] | None:
        try:
            df: pd.DataFrame = pd.read_json(file_path)
            df = df.dropna().drop_duplicates()
            return df.to_dict(orient='records')
        except Exception as e:
            logger.error(
                f"Failed to read or parse JSON file '{file_name}': {e}")
            return None

    def _bulk_insert_to_db(self,
                           TargetModel: type[Model],
                           rows: list[dict[str, Any]],
                           model_name: str) -> None:
        pool: list[Model] = [TargetModel(**row) for row in rows]
        if pool:
            TargetModel.objects.bulk_create(pool, ignore_conflicts=True)
            logger.info(f"Successfully loaded data into '{model_name}' model.")
