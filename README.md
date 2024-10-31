# avito-scraper

Scraper для avito.ru

Техническое задание для парсинга в файле [scraper-data.md](scraper_data.md)

Со страницы берем данные строки:

`window.__initialData__`

Запуск в локальной среде.

```bash
docker run --rm --name avitoscraper-pg -v /srv/_avitoscraper_pg:/var/lib/postgresql/data -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16-alpine3.20

rye sync
rye run scraper
```

Т.к. проект совешает большое количество параллельных запросов, необходимо сразу расширить следующий системный лимит:

```bash
ulimit -n 100000
```

Запуск в production среде.

```bash
docker compose up -d
```

Пример .env файла:

```dotenv
AVITO_URLS=https://www.avito.ru/rostov-na-donu/gruzoviki_i_spetstehnika/gruzoviki/sitrak-ASgBAgICAkRUkAKOwA2SjLgB?cd=1&radius=500&searchRadius=500
PROXIES=http://user:pass@localhost:8080,http://user:pass@localhost:8080
INTERVAL_MINUTES=10
```

Для работы с базой данных используется модуль db.py.
Он содержит функции для:
- подсчета общего количества товаров;
- удаления всех товаров из таблицы и 
- удаления самой таблицы.
