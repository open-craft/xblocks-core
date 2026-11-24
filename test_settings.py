"""
Minimal Django settings for running tests on xblocks-core.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "submissions",
    "edxval",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}


ROOT_URLCONF = type(
    "URLConf",
    (),
    {
        "urlpatterns": [],
    },
)

LMS_ROOT_URL = "http://localhost:8000"

# Code jail REST service
# Set the python package.module.function that is reponsible of
# calling the remote service in charge of jailed code execution.
# For tests, we use a mock service that runs CodeJail's unsafe executor with out
# sandboxing.
CODE_JAIL_REST_SERVICE_REMOTE_EXEC = "xblock_problem.capa.testing.codejail.send_safe_exec_request_locally"

# Set the codejail remote service host
CODE_JAIL_REST_SERVICE_HOST = "http://localhost:8550"

# Set the number of seconds LMS will wait to establish an internal
# connection to the codejail remote service.
CODE_JAIL_REST_SERVICE_CONNECT_TIMEOUT = 0.5  # time in seconds

# Set the number of seconds LMS/CMS will wait for a response from the
# codejail remote service endpoint.
CODE_JAIL_REST_SERVICE_READ_TIMEOUT = 3.5  # time in seconds

# CAPA External Code Evaluation #

XQUEUE_WAITTIME_BETWEEN_REQUESTS = 5  # seconds

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "src" / "xblock_problem" / "capa" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

TRANSCRIPT_LANG_CACHE_TIMEOUT = 60 * 60 * 24  # 24 hours
