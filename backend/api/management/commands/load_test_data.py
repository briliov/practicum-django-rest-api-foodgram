import json
import logging
import os
from typing import Any, Dict, List, Type

import pandas as pd
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Model
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Dynamically imports test data from JSON files into Django models."""

    help = 'Imports test data from JSON files with an elegant TUI.'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.user_model = get_user_model()

    def handle(self, *args: Any, **options: Any) -> None:
        folder_path = 'test_data'
        if not os.path.exists(folder_path):
            raise CommandError(f"Folder '{folder_path}' not found.")

        file_names = self._get_json_files(folder_path)
        if not file_names:
            return

        file_names.sort(key=self._get_load_priority)

        self.console.print(
            "\n[bold r]🚀 STARTING TEST DATA IMPORT[/bold r]\n"
        )
        self._execute_import(folder_path, file_names)
        self.console.print(
            "\n[bold green]✨ IMPORT SUCCESSFUL![/bold green]\n"
        )

    def _get_json_files(self, folder_path: str) -> List[str]:
        return [
            name for name in os.listdir(folder_path)
            if name.endswith('.json')
        ]

    def _get_load_priority(self, filename: str) -> int:
        priorities = {
            'customuser': 1,
            'tag': 2,
            'ingredient': 3,
            'recipe': 4,
            'following': 5,
            'favorite': 6,
            'shoppingcart': 7
        }
        clean_name = filename.lower().removesuffix('.json')
        return priorities.get(clean_name, 8)

    def _get_model_name(self, file_name: str) -> str:
        clean_name: str = file_name.removesuffix('.json')
        if clean_name.lower() == 'shoppingcart':
            return 'ShoppingCart'
        return clean_name.capitalize()

    def _get_django_model(self, model_name: str) -> type[Model] | None:
        try:
            return apps.get_model(app_label='api', model_name=model_name)
        except LookupError:
            return None

    def _get_parse_and_clean_json(
        self, file_path: str, file_name: str
    ) -> List[Dict[str, Any]] | None:
        try:
            if 'recipe' in file_name.lower():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            df = pd.read_json(file_path)
            return df.dropna().drop_duplicates().to_dict(orient='records')
        except Exception as e:
            logger.error(f"Failed to parse '{file_name}': {e}")
            return None

    def _execute_import(
        self, folder_path: str, file_names: List[str]
    ) -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Processing...[/cyan]", total=len(file_names)
            )

            for file_name in file_names:
                self._import_single_file(folder_path, file_name)
                progress.update(task, advance=1)

    def _import_single_file(self, folder_path: str, file_name: str) -> None:
        model_name = self._get_model_name(file_name)
        target_model = self._get_django_model(model_name)

        if not target_model:
            self.console.print(
                f"[bold red]❌ Model '{model_name}' not found.[/bold red]"
            )
            return

        file_path = os.path.join(folder_path, file_name)
        rows = self._get_parse_and_clean_json(file_path, file_name)
        if rows:
            self._insert_by_strategy(target_model, rows, model_name)

    def _insert_by_strategy(
        self,
        target_model: Type[Model],
        rows: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        strategies = {
            self.user_model: self._insert_users,
            'Recipe': self._insert_recipes,
        }
        handler = strategies.get(target_model) or strategies.get(
            model_name, self._insert_basic
        )
        handler(target_model, rows, model_name)

    def _insert_users(
        self,
        target_model: Type[Model],
        rows: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        pool = []
        table = Table(
            title=f"👤 Users ({model_name})",
            title_style="bold magenta",
            header_style="bold cyan"
        )
        table.add_column("Username", style="green")
        table.add_column("Email", style="yellow")
        table.add_column("Status", style="blue")

        for row in rows:
            user = target_model(**row)
            if hasattr(user, 'set_password'):
                user.set_password('foodgram_test_123')  # type: ignore
            pool.append(user)

            status = (
                "Administrator" if row.get("is_superuser") else "User"
            )
            table.add_row(row.get("username"), row.get("email"), status)

        if pool:
            target_model.objects.bulk_create(pool, ignore_conflicts=True)
            self.console.print(table)

    def _insert_recipes(
        self,
        target_model: Type[Model],
        rows: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        table = Table(
            title=f"🍳 Recipes ({model_name})",
            title_style="bold r",
            header_style="bold cyan"
        )
        table.add_column("Recipe Name", style="white")
        table.add_column("Author", style="green")
        table.add_column("Tags", style="magenta", justify="center")
        table.add_column("Ingredients", style="yellow", justify="center")
        table.add_column("Status", justify="center")

        for row in rows:
            self._process_recipe_row(target_model, row, table)

        self.console.print(table)

    def _process_recipe_row(
        self, target_model: Type[Model], row: Dict[str, Any], table: Table
    ) -> None:
        ingredients_data = row.pop('ingredients', [])
        tags_data = row.pop('tags', [])
        author_email = row.pop('author_email', None)

        author = self.user_model.objects.filter(email=author_email).first()
        if not author:
            table.add_row(
                row.get('name'),
                f"Missing ({author_email})",
                "-", "-",
                "[bold red]Skipped[/bold red]"
            )
            return

        row['author'] = author

        with transaction.atomic():
            recipe, created = target_model.objects.get_or_create(
                name=row.get('name'), defaults=row
            )
            if not created:
                table.add_row(
                    row.get('name'),
                    author.username,
                    "-", "-",
                    "[bold yellow]Exists[/bold yellow]"
                )
                return

            tag_model = apps.get_model(app_label='api', model_name='Tag')
            tags_qs = tag_model.objects.filter(name__in=tags_data)
            recipe.tags.set(tags_qs)  # type: ignore

            ing_count = self._attach_ingredients(recipe, ingredients_data)
            table.add_row(
                recipe.name,  # type: ignore
                author.username,
                str(tags_qs.count()),
                str(ing_count),
                "[bold green]Created[/bold green]"
            )

    def _attach_ingredients(
        self, recipe: Model, ingredients_data: List[Dict[str, Any]]
    ) -> int:
        ingredient_model = apps.get_model(
            app_label='api', model_name='Ingredient'
        )
        recipe_ingredient_model = apps.get_model(
            app_label='api', model_name='RecipeIngredient'
        )
        added_count = 0

        for ing in ingredients_data:
            ing_name = ing.get('name')
            db_ing = ingredient_model.objects.filter(
                name__iexact=ing_name
            ).first()

            if db_ing:
                recipe_ingredient_model.objects.get_or_create(
                    recipe=recipe,
                    ingredients=db_ing,
                    defaults={'amount': ing.get('amount', 0)}
                )
                added_count += 1
            else:
                self.console.print(
                    f"  [yellow]⚠️ Warning:[/yellow] "
                    f"Ingredient '{ing_name}' not found."
                )
        return added_count

    def _insert_interactions(
        self,
        target_model: Type[Model],
        rows: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        success_count = 0
        recipe_model = apps.get_model(app_label='api', model_name='Recipe')

        for row in rows:
            user = self.user_model.objects.filter(
                email=row.get('user_email')
            ).first()

            if 'author_email' in row:
                author = self.user_model.objects.filter(
                    email=row.get('author_email')
                ).first()
                if user and author:
                    target_model.objects.get_or_create(
                        user=user,
                        following=author
                    )
                    success_count += 1

            elif 'recipe_name' in row:
                recipe = recipe_model.objects.filter(
                    name=row.get('recipe_name')
                ).first()
                if user and recipe:
                    target_model.objects.get_or_create(
                        user=user,
                        recipe=recipe
                    )
                    success_count += 1

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_row(
            f"🔗 Interaction [bold blue]{model_name}[/bold blue]:",
            f"successfully mapped [bold green]{success_count}[/bold green] "
            f"relations."
        )
        self.console.print(table)

    def _insert_basic(
        self,
        target_model: Type[Model],
        rows: List[Dict[str, Any]],
        model_name: str
    ) -> None:
        pool = [target_model(**row) for row in rows]
        if pool:
            target_model.objects.bulk_create(pool, ignore_conflicts=True)
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_row(
                f"📦 Model [bold cyan]{model_name}[/bold cyan]:",
                f"loaded [bold green]{len(pool)}[/bold green] records."
            )
            self.console.print(table)
