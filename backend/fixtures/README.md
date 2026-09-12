# Test Data Fixtures for Foodgram

This directory contains test data packages in JSON format used to dynamically
seed the Django database for both local development and automation test suites.

Unlike monolithic database dumps, this system isolates entities into separate
files to preserve transparency and enforce data integrity.

## Directory Structure and Ordered Files

File names strictly utilize a sequential four-digit numerical prefix (`0000_`)
generated automatically by the custom Django management command. This prefix
acts as a hard requirement for the data layer, forcing the file system to read
and sort entities in accordance with their database relations:

* `0001_customuser.json` — Baseline user accounts, custom profiles, and
  admin-level superuser accounts.
* `0002_ingredient.json` — Full comprehensive database of cooking ingredients
  with designated measurement units.
* `0003_tag.json` — Core recipe tags (Breakfast, Lunch, Dinner, etc.) with
  unique slugs for frontend filtering.
* `0004_recipe.json` — Complete recipe objects containing structured
  descriptions, cooking durations, and primary relation keys.
* `0005_recipeingredient.json` — Intermediate relational lookup table mapping
  precise ingredient quantities to corresponding recipe objects.
* `0006_favorite.json` — Flat lookup tables linking user account IDs to their
  selected favorite recipes using raw foreign keys.
* `0007_following.json` — Flat relational profile matrix mapping
  follower-to-author subscription connections using raw foreign keys.
* `0008_shoppingcart.json` — Flat relational tables containing recipes added
  to user shopping lists using raw foreign keys.

## Data Formatting and Validation Rules

When adding new records or mutating existing JSON fixture files, you must
strictly follow these validation rules and schemas. Failure to do so will
cause the database import pipeline or Django auto-tests to crash:

### 1. User Profiles (`0001_customuser.json`)

* **email**: String. Must be globally unique and formatted as a valid email
  address. This field acts as the primary login identifier (`USERNAME_FIELD`).
* **username**: String. Must be globally unique. Special characters are
  strictly prohibited (only alphanumeric characters, underscores `_`, dots `.`,
  and `@` are permitted).
* **is_superuser** & **is_staff**: Boolean values (`true` or `false`). For
  admin-level access to the Django panel, both options must be explicitly
  declared as `true`.

### 2. Ingredients and Tags (`0002_ingredient.json` & `0003_tag.json`)

* **name** (for Ingredients): Lowercase text strings (e.g., `авокадо`). Data
  must enforce uniqueness constraints.
* **measurement_unit** (for Ingredients): Lowercase string representation of
  metric values (e.g., `г`, `мл`, `шт`).
* **slug** (for Tags): Strict lowercase alphanumeric characters, numbers, and
  hyphens only (e.g., `fast-food`). Duplicate slug values are rejected by
  database constraints.

### 3. Recipes and Relationships (`0004_recipe.json` & `0005_recipeingredient.json`)

* **author** / **user**: Integer. Must match an explicit primary key (`pk`)
  previously instantiated inside the `customuser` dataset.
* **image**: String. Defines the relative filesystem asset path inside the
  Docker media directory (e.g., `recipes/images/default.jpg`). This field
  cannot be `null` or blank.
* **amount** (inside RecipeIngredient): Must be a positive integer greater
  than zero (`> 0`).

## Pipeline Execution Priority

The core automation tool processes these components utilizing a synchronized
prioritization matrix. This sequence guarantees that relative cross-app
dependencies are fully satisfied before parent constraints throw an
`IntegrityError`:

1. `CustomUser` (Generates incremental database primary keys starting from `1`)
2. `Ingredient` (Generates incremental database primary keys starting from `1`)
3. `Tag` (Generates incremental database primary keys starting from `1`)
4. `Recipe` (Depends on existing User and Tag IDs)
5. `RecipeIngredient` (Depends on existing Recipe and Ingredient IDs)
6. Interaction Layers (Includes `Favorite`, `Following`, `ShoppingCart` entries
   relying on valid records above)

## Execution Commands

All fixture pipelines have been unified into a single custom management
interface. You no longer need to trigger individual `dumpdata` or `loaddata`
layers manually.

### 1. Hot-Reloading Data (Flush & Load)

To safely wipe your active container database schema and trigger a clean,
comprehensive hot-reload of all sequential fixture layers inside Docker,
execute the following sub-command:

```bash
docker compose exec backend python manage.py fixtures load
```

*Note: This operation runs in non-interactive mode. It automatically executes
a database `flush`, drops all current rows, resets primary key auto-increments,
and sequences the data load sequentially from `0001` to `0008`.*

### 2. Exporting Data (Save)

To freeze your active container database state, automatically wipe the old file
cache, and regenerate separate ordered JSON schemas directly inside the
project root, execute:

```bash
docker compose exec backend python manage.py fixtures save
```

## Logging and Monitoring

The execution pipeline integrates with the core Django `logging` engine. Every
data transaction (including directory purges, database flushes, and file
loading workflows) outputs verbose metrics to the system logging handler.

In the event of an import failure, the log stream will automatically capture
full stack traces via `exc_info=True` to isolate broken relational primary
keys.
