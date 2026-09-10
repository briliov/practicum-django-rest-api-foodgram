# Test Data Fixtures for Foodgram

This directory contains test data packages in JSON format used to dynamically
seed the Django database for both local development and automation test suites.

## Directory Structure and Core Files

File names must strictly follow the lowercase naming conventions specified
below to allow the custom Django management command to automatically detect
and map them to their corresponding app models:

* `customuser.json` — Baseline user accounts, custom profiles, and admin-level
  superuser accounts.
* `tag.json` — Core recipe tags (Breakfast, Lunch, Dinner, etc.) with unique
  slugs for frontend filtering.
* `ingredient.json` — Full comprehensive database of cooking ingredients with
  designated measurement units.
* `recipe.json` — Complete recipe objects including structured texts, cooking
  durations, and nested relations.
* `following.json` — Flat relational profile matrix mapping follower-to-author
  subscription connections using raw IDs.
* `favorite.json` — Flat lookup tables linking user account IDs to their
  selected favorite recipes using raw IDs.
* `shoppingcart.json` — Flat relational tables containing recipes added to
  user shopping lists using raw IDs.

## Data Formatting and Validation Rules

When adding new records or mutating existing JSON fixture files, you must
strictly follow these validation rules and schemas. Failure to do so will
cause the database import pipeline or Django auto-tests to crash:

### 1. User Profiles

The `customuser.json` configuration follows these fields:

* **email**: String. Must be globally unique and formatted as a valid email
  address (e.g., `user@foodgram.io`). This field acts as the primary login
  identifier (`USERNAME_FIELD`).
* **username**: String. Must be globally unique. Special characters are strictly
  prohibited (only alphanumeric characters, underscores `_`, dots `.`, and `@`
  are permitted).
* **is_superuser** & **is_staff**: Boolean values (`true` or `false`). For
  admin-level access to the Django panel, both options must be explicitly
  declared as `true`.

Do not include a `password` field in the JSON payload. The management script
dynamically handles password generation, hashing, and automatically assigns a
default secure password (`foodgram_test_123`) to all accounts.

### 2. Tags and Ingredients

The `tag.json` and `ingredient.json` configurations follow these fields:

* **slug** (for Tags): Strict lowercase alphanumeric characters, numbers, and
  hyphens only (e.g., `fast-food`). Duplicate slug values are rejected by
  database constraints.
* **name** (for Ingredients): Lowercase text strings (e.g., `авокадо`). Data is
  cleaned via `pandas` upon ingestion; matching duplicate name blocks are
  automatically trimmed to enforce uniqueness.

### 3. Recipes

The recipe schema inside `recipe.json` is designed as an array containing
deeply nested relational blocks:

* **author_email**: String. The migration script maps the author record by
  looking up this email address. The specified email must pre-exist inside
  the `customuser.json` dataset.
* **image**: String. Defines the relative filesystem asset path inside the
  Docker media directory (e.g., `recipes/images/default.jpg`). This field
  cannot be `null` or blank, otherwise the automated testing suite will throw
  an assertion error.
* **tags**: Array of strings. Tag names must match the exact string spelling
  and casing specified in the `name` field of `tag.json`
  (e.g., `["Завтрак", "Обед"]`).
* **ingredients**: Array of nested ingredient target objects. Each ingredient
  block must explicitly state its lowercase text name and a positive integer
  quantity:

```json
"ingredients": [
  {"name": "авокадо", "amount": 1},
  {"name": "агава сироп", "amount": 15}
]
```

The `name` key must exactly match a record in the ingredient database. The
`amount` key must be a positive integer greater than zero (`> 0`).

### 4. Interactions

The `following.json`, `favorite.json`, and `shoppingcart.json` configurations
follow these fields:

* These tables are designed as flat index pairs using raw numerical database
  IDs to maximize import velocity.
* All declared `user_id`, `following_id`, and `recipe_id` indices must physically
  exist in the active database. Database IDs are auto-incremented sequentially
  starting from `1` depending on the row execution order.

## Pipeline Execution Priority

The core automation command processes these components utilizing a synchronized
prioritization matrix. This sequence guarantees that relative cross-app
dependencies are fully satisfied before parent constraints throw an
`IntegrityError`:

1. `CustomUser` (Generates incremental database primary keys starting from `1`)
2. `Tag` (Generates incremental database primary keys starting from `1`)
3. `Ingredient` (Generates incremental database primary keys starting from `1`)
4. `Recipe` (Generates primary keys starting from `1` and dynamically links
   nested values to the intermediate `RecipeIngredient` model)
5. Interaction Layers (`Following`, `Favorite`, `ShoppingCart`)

## Execution Command

To safely wipe your active container database schema and trigger a clean,
comprehensive hot-reload of all fixture layers inside Docker, execute the
following chained pipeline snippet directly in your terminal:

```bash
docker compose exec backend python manage.py flush --no-input && \
docker compose exec backend python manage.py load_test_data
```
