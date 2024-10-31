import os


PG_DSN = os.getenv("PG_DSN", "postgresql://postgres:postgres@127.0.0.1:5432/postgres")

AVITO_URLS = os.getenv("AVITO_URLS", "")
if AVITO_URLS:
    AVITO_URLS = AVITO_URLS.split(",")

PROXIES = os.getenv("PROXIES", "")
if PROXIES:
    PROXIES = PROXIES.replace(" ", "").split(",")
