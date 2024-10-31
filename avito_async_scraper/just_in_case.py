# Варианты def parse:
# С учетом 429 ошибки. Если ловим 429, то делаем time.sleep 1 минуту.
def parse() -> None:
    """Запускает парсинг avito."""
    items = []

    for url in settings.AVITO_URLS:
        pages_url = get_pages(url)
        for page_url in pages_url:
            while True:
                try:
                    response = requests.get(page_url)
                    if response.status_code == 429:
                        logging.info(
                            "Получен статус 429: слишком много запросов. Ожидание 1 минуты...")
                        time.sleep(60)
                        continue

                    # Если запрос успешен, получаем товары
                    result = get_products(page_url)
                    items.append(result)
                    break  # Выходим из цикла, если запрос успешен

                except Exception as e:
                    logging.error(f"Ошибка при запросе к {page_url}: {e}")
                    break  # Выходим из цикла в случае других ошибок

        # Объединяем все найденные товары и удаляем дубликаты
        items = set(reduce(iconcat, items, []))
        logging.info(f"Avito: всего товаров: {len(items)}")

        if items:
            database.insert_items(items)
        else:
            logging.warning("Нет товаров для добавления в базу данных.")


# Для того, чтобы записывать товары в базу после прохода каждой страницы пагинации.
def parse() -> None:
    """Запускает парсинг avito."""
    for url in settings.AVITO_URLS:
        items = []  # Список для хранения товаров
        for page in get_pages(url):
            time.sleep(10)
            result = get_products(page)
            if result:
                items.extend(result)  # Добавляем элементы из result в items
                items = list(set(items))  # Преобразуем в set и обратно в list для удаления дубликатов
                # Вставляем данные в базу после парсинга каждой страницы
                if items:
                    database.insert_items(items)  # Запись в базу после обработки каждой страницы
                    logging.info(f"Добавлено товаров в базу: {len(items)}")
                    items.clear()  # Очищаем список после вставки, чтобы не добавлять дубликаты

        logging.info(f"Avito: всего товаров добавлено: {len(items)}")

        if not items:
            logging.warning("Нет товаров для добавления в базу данных.")


# Обычная
def parse() -> set[Any]:
    """Запускает парсинг avito."""
    items = []
    for url in settings.AVITO_URLS:
        logging.info(f"Запускаю страницу {url}")
        pages = get_pages(url)
        for page in pages:
            result = get_products(page)
            items.append(result)

    items = set(reduce(iconcat, items, []))
    logging.info(f"Avito: всего товаров: {len(items)}")
    if items:
        database.insert_items(items)
    else:
        logging.warning("Нет товаров для добавления в базу данных.")

    return items


# Чтобы получить отчет с учетом даты получения товара.
def gen_file():
    with closing(psycopg.connect(settings.PG_DSN)) as conn, closing(conn.cursor()) as cursor:
        # Запрашиваем данные из базы
        today = datetime.datetime.now().date()
        cursor.execute(
            'SELECT name, article, url, attrs '
            'FROM items '
            'WHERE DATE(created_at) >= %s',
            (today,)
        )
        data = cursor.fetchall()  # Получаем все строки
        # logging.info(data)
        # Проверяем, есть ли данные
        if not data:
            logging.info("Нет товаров для записи.")  # Сообщение, если товаров нет
            return

        # Установка временной зоны
        offset = datetime.timedelta(hours=3)
        tz = datetime.timezone(offset)

        now = datetime.datetime.now().astimezone(tz=tz)
        formatted_date = now.strftime("%Y%m%d-%H-%M")

        file_name = f'avito-{formatted_date}.xlsx'


def get_products(url: str):
    products_data = get_json(url)
    if not products_data:
        logging.info("Товаров products_data нет")
        return []

    products = base.find_value_by_key(products_data, "items")

    if not products:
        logging.info("Товаров products нет")
        return []

    items = []
    for product in products:
        if product.get('urlPath'):
            item_url = f"https://www.avito.ru{product['urlPath']}"
        else:
            logging.info("Нет product['urlPath']")
            continue

        logging.info(item_url)
        product_data = get_json(item_url)
        if not product_data:
            logging.info("Товара нет")
            continue

        try:
            product_card = base.find_value_by_key(product_data, "buyerItem")

            # Получаем значение продвижения (promotion). Если его нет, то возвращаем 0.
            date_info_step = product.get("iva", {}).get("DateInfoStep", [])
            vas = date_info_step[1].get("payload", {}).get("vas", []) if len(date_info_step) > 1 else []
            promotion = vas[0].get("title", 0) if len(vas) > 0 else 0
            number_of_days_promotion = vas[0].get("slug", 0) if len(vas) > 0 else 0
            promotion_type = vas[1].get("slug", 0) if len(vas) > 0 else 0

            if promotion and promotion != "Продвинуто":
                promotion = 0

            attrs = {
                "price": int(product["priceDetailed"]["value"]), # Цена
                # "price": int(product_card["contactBarInfo"]["price"]),  # Цена
                # "price": int(product_card["ga"][1]["currency_price"]),  # Цена
                "availability": product["iva"]["BadgeBarStep"][0]["payload"]["badges"][0]["title"], # Доступность
                # "seller": product["iva"]["UserInfoStep"][0]["payload"]["profile"]["title"], # Продавец
                "seller": product_card["contactBarInfo"]["seller"]["name"],  # Продавец
                "region": product["location"]["name"], # Регион
                "promotion": promotion, # Продвижение
                "number_of_days_promotion": number_of_days_promotion, # Количество дней (продвижение)
                "promotion_type": promotion_type, # Тип продвижения
                "advertisement_date": product["iva"]["DateInfoStep"][0]["payload"]["absolute"], # Дата объявления
                # "advertisement_number": product["id"], # Номер объявления - article
                "brand": product_card["ga"][1]["marka"], # Марка
                "model": product["title"].replace(product_card["ga"][1]["marka"], "").strip(), # Модель
                "body_type": product_card["ga"][1]["tip_kuzova"], # Тип кузова
                "year_of_issue": product_card["ga"][1]["god_vypuska"], # Год выпуска
                "wheel_formula": product_card["ga"][1]["kolesnaya_formula"], # Колесная формула
                "condition": product_card["ga"][1]["condition"], # Состояние
                # "product_link": , # Ссылка на объявление - url
                "company_individual_vendor": product_card["contactBarInfo"]["publicProfileInfo"]["sellerName"], # Компания / частное лицо
            }

            item = database.Item(
                name=product["title"],
                article=product["id"],
                url=f"https://www.avito.ru{product['urlPath']}",
                attrs=attrs,
            )
            logging.info(item)
            items.append(item)

        except Exception as e:
            logging.error(f"Ошибка при парсинге страницы товара: {e}")

    return items
