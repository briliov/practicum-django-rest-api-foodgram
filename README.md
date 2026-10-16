# Foodgram

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

## About

Grocery Assistant: a service for publishing recipes, adding them to favorites, subscribing to authors and generating a consolidated shopping list with the ability to download to PDF.

### Project links

* **Project site:** [nexordon.work.gd](https://nexordon.work.gd/)
* **Server IP address:** [51.250.47.12](https://51.250.47.12)
* **Admin panel:** [nexordon.work.gd/admin/](https://nexordon.work.gd/admin/)
* **API Documentation (Redoc):** [nexordon.work.gd/api/docs/](https://nexordon.work.gd/api/docs/)

### Author of the project

* **Egor Briliov** | Backend Developer
* **Telegram** | [@briliov](https://t.me/briliov)

## Tech Stack & Infrastructure

* **Backend:** Python 3.12, Django 6.1, Django REST Framework (DRF), Djoser.
* **Database:** PostgreSQL 15 (Production) / SQLite (Local Development).
* **Frontend:** React (SPA application; the container is used for static building).
* **WSGI & Web Server:** Gunicorn, Nginx.
* **Containerization:** Docker, Docker Compose (Separate dev/prod configuration environments).
* **CI/CD:** GitHub Actions (Two independent workflow automation setups, Docker Hub, and Telegram API integration).
* **Code Quality:** Verified with Flake8 linter adhering strictly to PEP 8 standards.

The application is deployed on a virtual private server inside **four isolated containers**: `nginx`, `db` (PostgreSQL), `backend`, and `frontend`. Persistent data stores, media, and static assets are managed using Docker Volumes.

## How to install & Deploy

### Local Development Setup

1. **Clone the repository:**

```bash
bash
git clone https://github.com/nexordon/foodgram.git
cd foodgram
```

1. **Configure environment variables:**

Create a `.env` file in the root directory (where your development `docker-compose.yml` file is located):

```env
env
SECRET_KEY=your_secure_django_secret_key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

1. **Launch the local infrastructure using Docker:**

Build and start the multi-container development environment:

```bash
docker compose up -d --build
```

***Note**: In development mode (`target: development`), the backend container automatically performs database migrations (`makemigrations && migrate`), loads core system fixtures (`load_data`), and runs `collectstatic` before starting the built-in development server.*

1. **Verify execution:**

The application will be accessible via standard interfaces through the Nginx gateway on port `:80`. You can monitor log execution streams using:

```bash
docker compose logs -f backend
```

---

### CI/CD Workflow & Production Deployment

The project features fully automated staging and deployment layers controlled by **GitHub Actions** via distinct workflow routines.

#### 1. Automation Architecture & Required Secrets

To enable automated validations and delivery, make sure to provision the following environmental variables within your GitHub Repository settings (`Settings -> Secrets and variables -> Actions`):

* `DOCKER_USERNAME` / `DOCKER_PASSWORD` — Shared keys needed to publish images to DockerHub.
* `HOST` / `USER` / `SSH_KEY` — Remote Linux parameters targeted by deployment workflows.
* `TELEGRAM_TO` / `TELEGRAM_TOKEN` — Credentials required to deliver operational push alerts.

#### 2. Workflow Lifecycles

* **Development Workflow (`dev.yml`):** Automatically triggers on any push to the `dev` branch. It hosts an isolated `postgres:13.10` runner to perform code evaluation assertions (`ruff check`) and execute tests (`python manage.py test`).

* **Main Deployment Workflow (`main.yml`):** Automatically runs on any push to the `main` branch. It manages the following sequence:
  1. Runs code quality assertions and tests.
  2. Compiles production assets and pushes verified Docker images (`backend` and `frontend`) directly to your DockerHub space (`nexordon/foodgram_backend:latest`, `nexordon/foodgram_frontend:latest`).
  3. Copies the production compose definitions (`infra/docker-compose.production.yml`) and web server setup configs (`infra/nginx.conf`) to the remote hosting environment over SSH.
  4. Automatically handles deployment updates on the remote server:

     ```bash
     sudo docker compose -f docker-compose.production.yml pull
     sudo docker compose -f docker-compose.production.yml down
     sudo docker compose -f docker-compose.production.yml up -d
     sudo docker container exec foodgram-backend python manage.py migrate
     sudo docker container exec foodgram-backend python manage.py collectstatic --no-input
     ```

     *In the production environment, the backend server operates securely via a managed **Gunicorn WSGI server** binding on internal port `:8000`, while the custom **Nginx templates** route traffic and serve static files.*
  5. Dispatches an operational delivery diagnostic summary straight to the configured Telegram endpoint.

## Testing & Debugging Details

* **API Functional Testing:** The workspace contains preconfigured operational templates available inside the `postman_collection/` directory to run automated tracking assertions using Postman.
* **Reviewer Remote Infrastructure Access:** Connection strings and server access parameters required to inspect operations on active staging layers are located inside the `tests.yml` configuration mapping file (`login`, `password`, `vm_name`).
