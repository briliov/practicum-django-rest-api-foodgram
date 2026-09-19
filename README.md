# Foodgram

[nexordon.work.gd](https://nexordon.work.gd/) | [IP](ttps://51.250.47.108/)

![Python](https://img.shields.io/badge/python-black?style=for-the-badge&logo=python&logoColor=ffdd54)
![Django](https://img.shields.io/badge/django-black.svg?style=for-the-badge&logo=django&logoColor=3CB371)
![DRF](https://img.shields.io/badge/DRF-black?style=for-the-badge&logo=django&logoColor=red)
![Flake8](https://img.shields.io/badge/Flake8-black.svg?style=for-the-badge&logo=python&logoColor=blue)
![NodeJS](https://img.shields.io/badge/node_js-black?style=for-the-badge&logo=nodedotjs&logoColor=5FA04E)
![HTML5](https://img.shields.io/badge/html5-black.svg?style=for-the-badge&logo=html5&logoColor=D2691E)
![CSS](https://img.shields.io/badge/CSS-black?style=for-the-badge&logo=css&logoColor=9370DB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-black?style=for-the-badge&logo=postgresql&logoColor=4169E1)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Redoc](https://img.shields.io/badge/Redoc-black?style=for-the-badge&logo=googledocs&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-black?style=for-the-badge&logo=postman&logoColor=FF6C37)
![Nginx](https://img.shields.io/badge/nginx-black?style=for-the-badge&logo=nginx&logoColor=009639)
![Docker](https://img.shields.io/badge/Docker-black?style=for-the-badge&logo=Docker&logoColor=2496ED)
![GitHub Actions](https://img.shields.io/badge/GITHUB_ACTIONS-black?style=for-the-badge&logo=GITHUB&logoColor=white)
![Markdown](https://img.shields.io/badge/markdown-%23000000.svg?style=for-the-badge&logo=markdown&logoColor=white)
![PowerShell](https://img.shields.io/badge/PowerShell-black.svg?style=for-the-badge&logo=gnometerminal&logoColor=1E90FF)
![Git](https://img.shields.io/badge/git-black.svg?style=for-the-badge&logo=git&logoColor=orange)

---

## Tech Stack & Infrastructure

* **Backend:** Python 3.12, Django 3.2, Django REST Framework (DRF), Djoser.
* **Database:** PostgreSQL 15 (Production) / SQLite (Local Development).
* **Frontend:** React (SPA application; the container is used for static building).
* **WSGI & Web Server:** Gunicorn, Nginx.
* **Containerization:** Docker, Docker Compose (Separate dev/prod configuration environments).
* **CI/CD:** GitHub Actions (Two independent workflow automation setups, Docker Hub, and Telegram API integration).
* **Code Quality:** Verified with Flake8 linter adhering strictly to PEP 8 standards.

The application is deployed on a virtual private server inside **four isolated containers**: `nginx`, `db` (PostgreSQL), `backend`, and `frontend`. Persistent data stores, media, and static assets are managed using Docker Volumes.

---

## Backend & API Implementation Features

The REST API architecture strictly follows the provided requirements specification using the following solutions on the controllers and serializers level:

* **User Management & Profiles (`UsersViewSet`):**
  * Inherits standard mixins for creating, listing, retrieving, updating, and the `GenericViewSet` class. It dynamically switches to `UsersCreateSerializer` when executing the `create` action.
  * The `me` action returns the authenticated user profile (`current_user`).
  * The `me/avatar` action handles `PUT` and `DELETE` requests. Upon receiving a `DELETE` request, the avatar asset file is completely purged from media storage via `avatar.delete(save=True)`.
  * The `set_password` action secures password modifications utilizing `check_password` and `set_password` logic.
* **Subscriptions, Favorites, and Shopping Carts:**
  * Author subscriptions (`subscribe`) and viewing user subscriptions (`subscriptions`) are encapsulated inside `UsersViewSet`. The `subscriptions` method returns a paginated list of followed authors.
  * The `favorite` and `shopping_cart` actions in `RecipeViewSet` handle `POST` requests (adding via `get_or_create`) and `DELETE` requests (removing records). Unique constraints are enforced at the DB level to block duplicate records.
* **Short Link Generation:**
  * Implemented a `get-link` endpoint inside `RecipeViewSet`. It generates and returns shortened absolute web links matching the structure `https://<domain>/s/{id}/` using `request.build_absolute_uri()`.
* **Aggregating Shopping List Data to PDF:**
  * The `download_shopping_cart` endpoint groups and aggregates ingredient counts across all recipes currently pinned in the user's shopping cart. Matching ingredients are combined at the database level using `values()`, `annotate(total_amount=Sum('amount'))`, and `order_by()`.
  * The aggregated array is handled by a `generate_shopping_cart_pdf` helper tool, providing a downloaded **PDF document** stream via `FileResponse` configured with the `as_attachment=True` flag.
* **Filtering and Pagination:**
  * For recipes (`RecipeViewSet`), default ordering is set to sort by publication date newest-first (`ordering = ['-created_at']`). Integrated custom `RecipeFilter` logic and a custom page-based paginator `LimitPageNumberPagination`.
  * Ingredients (`IngredientsViewSet`) and tags (`TagsViewSet`) operate in read-only mode (`ReadOnlyModelViewSet`) without pagination. Ingredients feature case-insensitive search targeted at string starters (`search_fields = ('^name',)`).

---

## Database Architecture (Project Models)

The business logic relies on the following structural data layer models:

* **`CustomUser`:** Extends `AbstractUser`. Authentication transitions from username over to a unique `email` field. Contains an `avatar` field for profile rendering.
* **`Recipe`:** Connects an author (`CustomUser`), name, banner image, descriptive text body, cooking time in minutes, and a creation date. Linked with tags and ingredients using `ManyToManyField` relations.
* **`Ingredient`:** Inherits abstract characteristics from `NamedModel`. Enforces a composite unique index binding the ingredient name and its measurement system (`measurement_unit`).
* **`Tag`:** Inherits characteristics from `NamedModel`. Enforces a unique display name and a unique string identifier (`slug`).
* **`RecipeIngredient` (Through Model):** Connects recipes and ingredients specifying precise quantities (`amount`). Configured with a unique constraint checking matching `recipe` and `ingredients` keys.
* **`Following`:** Manages links binding subscribers (`user`) with creators (`following`). Protected against double-following entries using unique structural indexes.
* **`Favorite`:** Tracks relations connecting individual user accounts to favorited recipe records.
* **`ShoppingCart`:** Connects user profiles to pinned recipes whose components must be exported to the raw shopping sheet.

---

## Django Administration Panel Setup

The custom control dashboard has been tailored for application moderators. Shared header variables are updated (`admin.site.site_header = 'Foodgram Management Panel'`, `admin.site.index_title`, etc.), while `Following`, `Tag`, `Favorite`, and `ShoppingCart` use native configuration templates.

Key specialized `ModelAdmin` parameters are customized:

* **Custom Users (`CustomUserAdmin`):**
  * Display list columns (`list_display`): `id`, `username`, `email`.
  * Target lookup query strings (`search_fields`): `username`, `email`.
* **Recipes (`RecipeAdmin`):**
  * The main summary list view (`list_display`) columns present recipe name strings (`name`) and author accounts through a dedicated helper method `get_author_name` (with a default fallback rendering `"No Author"`).
  * Filter criteria options (`list_filter`): Fast filtering matching tag filters (`tags`).
  * Target lookup fields (`search_fields`): Lookup queries matching recipe titles (`name`) and user author names (`author__username`).
  * The detailed record page houses the aggregate counter checking how many times a recipe was added to user favorites (`get_favorite_add_count`) within `readonly_fields`. Computations are processed on the fly using ORM `.count()`.
* **Ingredients (`IngredientAdmin`):**
  * Summary overview table (`list_display`) maps measurement metrics (`measurement_unit`) and text strings formatted by `get_capitalized_name` (forcing leading characters into uppercase format).
  * Target lookup fields (`search_fields`): Filters records matching specific item names (`name`).

---

## Production Architecture & Nginx Configuration

In the production stage, the platform is orchestrated over a virtual node server running Ubuntu via containers configured in `docker-compose.production.yml`. App builds are managed at the CI/CD deployment level, saving packages out to Docker Hub before distribution pulls. The relational database container utilizes a custom `healthcheck` layer blocking adjacent startup steps until PostgreSQL completely processes initial port assignments.

**T he Nginx configuration (`nginx.conf`) runs under the following structure:**

* Network traffic hits matching `/api/` or `/admin/` entries are automatically forwarded to the WSGI application container layer to `Gunicorn` handling assignments on port `8000`.
* Configured assets paths serving core Django administrative files (`/static/admin/`), interface stylesheets (`/static/rest_framework/`), and API docs endpoints (`/api/docs/`).
* Handles user-uploaded assets from isolated directories matching `/var/www/django/media/`.
* The fallback matching location `/` serves the static compiled assets matching the production-ready React client build located inside `/usr/share/nginx/html/build`.

---

## CI/CD Workflow Automation

The pipeline layers feature two independent workflows controlled via **GitHub Actions**:

###  Development Workflow (`.github/workflows/dev.yml`)

* Triggers when changes hit development repositories on push events targeted at the `dev` branch.
* Spins up a standalone test backend runner working alongside PostgreSQL 13.10.
* Completes package assembly installs, triggers syntax validation scanning using the `flake8` package checking PEP 8 styling code guidelines, and runs Django native test suites.
* Transmits complete log updates and status diagnostics out to developer **Telegram** chats upon completing stages.

### Main Production Workflow (`.github/workflows/main.yml`)

* Triggers on merging features back into the primary release branch (`main`).
* Re-executes lint checking and integrated software test logic.
* Triggers multi-stage building (`matrix.type`) for Docker environment layers, updating registry repositories with `latest` image tags on Docker Hub.
* Imports layout updates (`docker-compose.production.yml` and `nginx.conf`) onto the target private node via SCP secure protocols (`scp-action`).
* Triggers SSH commands handling remote container environment restarts (`docker compose pull`, `docker compose down`, `docker compose up -d`), launches missing model transformations (migrations), and updates system asset catalogs via volume bindings.
* Sends final success statements to the Telegram monitoring room.

---

##  Access Control Matrix (ACL)

| Capabilities / Roles | Guest (Anonymous) | Authenticated User | Administrator |
| :--- | :---: | :---: | :---: |
| Browse recipes, tags, and profiles | ✅ | ✅ | ✅ |
| Create, edit, and delete *own* recipes | ❌ | ✅ | ✅ |
| Manage Subscriptions, Favorites, and Shopping Carts | ❌ | ✅ | ✅ |
| Password changes / Account logout logout | ❌ | ✅ | ✅ |
| Global user accounts moderation and bans | ❌ | ❌ | ✅ |
| Moderate third-party posts, configure tags/ingredients | ❌ | ❌ | ✅ |

---

## How to install

## Testing & Debugging Details

* **API Functional Testing:** The workspace contains preconfigured operational templates available inside the `postman_collection/` directory to run automated tracking assertions using Postman.
* **Reviewer Remote Infrastructure Access:** Connection strings and server access parameters required to inspect operations on active staging layers are located inside the `tests.yml` configuration mapping file (`login`, `password`, `vm_name`).
