from __future__ import annotations

import time
import asyncio
import logging
import traceback
from functools import reduce
from operator import iconcat
import json
import urllib.parse

import aiohttp
import aiofiles

from avito_scraper import database, settings


def find_value_by_key(data, target_key):
    """Функция для получения значения по ключу во вложенных словарях."""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            # Рекурсивный вызов для вложенных словарей
            result = find_value_by_key(value, target_key)
            if result is not None:
                return result
    elif isinstance(data, list):
        for item in data:
            result = find_value_by_key(item, target_key)
            if result is not None:
                return result
    return None

async def _get_json(session, url):
    response = await session.get(
        url,
        ssl=False,
    )
    response = await response.text()

    # Проверяем на наличие блокировки
    if not 'window.__initialData__ = ' in response:
        logging.info(f"Блокировка страницы {url}")
        return []

    # Достаем из всей страницы только строку window.__initialData__
    json_string = response.split('window.__initialData__ = ')[1].split('window.__mfe__')[0]
    # Обрезаем кавычки и последний символ ";"
    json_string = json_string.strip()[1:-2]

    # Декодируем полученные данные
    decoded_json_string = urllib.parse.unquote(json_string)
    # Получаем JSON
    data = json.loads(decoded_json_string)

    return data

async def _get_pages(session, url) -> list[str]:
    pages_data = await _get_json(session, url)

    # Пишем данные в файл
    # async with aiofiles.open('pages_data.text', mode='w') as f:
    #     await f.write(pages_data)

    if not pages_data:
        return []

    pages = len(find_value_by_key(pages_data, "items"))
    return [
        f"{url}&p={page}"
        for page in range(1, pages + 1)
    ]

async def _get_products(url: str, session):
    products_data = await _get_json(session, url)
    # Пишем данные в файл
    if not products_data:
        logging.info("Товаров нет")
        return []

    products = find_value_by_key(products_data, "items")
    if not products:
        return []

    items = []
    for product in products:
        item_url = f"https://www.avito.ru{product['urlPath']}"
        time.sleep(3)
        logging.info(item_url)
        product_data = await _get_json(session, item_url)
        if not product_data:
            logging.info("Товара нет")
            return []

        product_card = find_value_by_key(product_data, "buyerItem")

        attrs = {
            "price": int(product["priceDetailed"]["value"]), # Цена
            # "price": int(product_card["contactBarInfo"]["price"]),  # Цена
            # "price": int(product_card["ga"][1]["currency_price"]),  # Цена
            "availability": product["iva"]["BadgeBarStep"][0]["payload"]["badges"][0]["title"], # Доступность
            #"seller": product["iva"]["UserInfoStep"][0]["payload"]["profile"]["title"], # Продавец
            "seller": product_card["contactBarInfo"]["seller"]["name"],  # Продавец
            "region": product["location"]["name"], # Регион
            # "promotion": product["iva"]["DateInfoStep"][1]["payload"]["vas"][0]["title"], # Продвижение
            # "promotion_date": , # Дата продвижения
            "advertisement_date": product["iva"]["DateInfoStep"][0]["payload"]["absolute"], # Дата объявления
            # "advertisement_number": , # Номер объявления
            "brand": product_card["ga"][1]["marka"], # Марка
            #"model": product["title"].replace(product_card["ga"][1]["marka"], ""), # Модель
            "body_type": product_card["ga"][1]["tip_kuzova"], # Тип кузова
            "year_of_issue": product_card["ga"][1]["god_vypuska"], # Год выпуска
            "wheel_formula": product_card["ga"][1]["kolesnaya_formula"], # Колесная формула
            "condition": product_card["ga"][1]["condition"], # Состояние
            # "product_link": , # Ссылка на объявление
            "company_individual_vendor": product_card["publicProfileInfo"]["sellerName"], # Компания / частное лицо

        }

        item = database.Item(
            article=product["id"],
            name=product["title"],
            url=f"https://www.avito.ru{product['urlPath']}",
            attrs=attrs,
        )
        logging.info(item)
        items.append(item)

    return items

async def parse() -> None:
    """Запускает парсинг avito."""
    try:
        # Создаем CookieJar для хранения куков
        cookie_jar = aiohttp.CookieJar()

        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=0),
            cookie_jar=cookie_jar,  # добавляем CookieJar в сессию
        ) as session:
            logging.info("Avito: парсинг запущен")

            # Получаем куки с первого запроса
            async with session.get(settings.AVITO_URLS[0]) as response:
                if response.status == 200:
                    logging.info(f"Куки после первого запроса: {response.cookies}")
                    hardcoded_cookies = "; ".join(
                        f"{key}={value.value}" for key, value in response.cookies.items())
                    logging.info(f"Хардкод куков: {hardcoded_cookies}")
                else:
                    logging.error(f"Ошибка при первом запросе: {response.status}")

            pages_links = await asyncio.gather(
                *[
                    _get_pages(session, supplier_id)
                    for supplier_id in settings.AVITO_URLS
                ],
            )
            pages_links = reduce(iconcat, pages_links, [])
            logging.info(f"Avito: всего страниц: {len(pages_links)}")
            items = await asyncio.gather(
                *[_get_products(url, session) for url in pages_links],
            )
            items = set(reduce(iconcat, items, []))
            logging.info(f"Avito: всего товаров: {len(items)}")
            database.insert_items(items)
    except Exception:
        logging.exception(str(traceback.format_exc()))



# from __future__ import annotations
#
# import time
# from typing import Any
#
# import logging
# from functools import reduce
# from operator import iconcat
# from bs4 import BeautifulSoup
#
# from avito_scraper.proxy import get_proxy
# from avito_scraper import base, database, settings
#
#
# CAPCHA = 'Доступ ограничен: проблема с IP'
# INITIAL_DATA = 'window.__initialData__ = '
#
#
# def get_pages(url):
#     page_urls = []
#
#     proxy = get_proxy()
#     response = base.get_response(url, proxy)
#
#     # Получаем количество страниц пагинации
#     page_count = base.get_page_count(response)
#
#     for page in range(page_count):
#         page_url = f"{url}&p={page + 1}"
#         logging.info(f"Текущая страница: {page_url}")
#         page_urls.append(page_url)
#
#     return page_urls
#
#
# def get_products(url: str):
#     proxy = get_proxy()
#     soup = BeautifulSoup(base.get_response(url, proxy).text, 'html.parser')
#     products = soup.select('[data-marker="item"]')
#
#     items = []
#     for product in products:
#         if item_url := product.select('[itemprop="url"]')[0].attrs['href']:
#             item_url = f"https://www.avito.ru{item_url}"
#         else:
#             logging.info("Нет product")
#             continue
#
#         logging.info(item_url)
#
#         name = product.select('[class^="iva-item-title"]')[0].text
#         product_link = name.attrs['href']
#         article = product_link.split('_')[-1]
#
#         # Получаем значение продвижения (promotion). Если его нет, то возвращаем 0.
#         # promotion = product.select('[itemprop="url"]') if 0 else 0
#         # number_of_days_promotion = product.select('[itemprop="url"]') if 0 else 0
#         # promotion_type = product.select('[itemprop="url"]') if 0 else 0
#         price = product.select('meta[itempror="price"]')[0].attrs['content']
#         availability = product.select('[class^="iva-item-badgeBarStep"]')
#
#         # if promotion and promotion != "Продвинуто":
#         #     promotion = 0
#
#         #Заходим на страницу чтобы получит атрибуты
#         proxy = get_proxy()
#         product_data = BeautifulSoup(base.get_response(url, proxy).text, 'html.parser')
#         product_attrs = product_data.select('[data-marker="item-view/item-params"]')
#         logging.info(product_attrs)
#
#         seller = product.select('[itemprop="url"]')
#         region = product.select('[itemprop="url"]')
#         advertisement_date = product.select('[itemprop="url"]')
#         brand = product.select('[itemprop="url"]')
#         model = product.select('[itemprop="url"]')
#         body_type = product.select('[itemprop="url"]')
#         year_of_issue = product.select('[itemprop="url"]')
#         wheel_formula = product.select('[itemprop="url"]')
#         condition = product.select('[itemprop="url"]')
#         company_individual_vendor = product.select('[itemprop="url"]')
#
#
#         attrs = {
#             "price": price, # Цена
#             "availability": availability, # Доступность
#             "seller": seller,  # Продавец
#             "region": region, # Регион
#             # "promotion": promotion, # Продвижение
#             # "number_of_days_promotion": number_of_days_promotion, # Количество дней (продвижение)
#             # "promotion_type": promotion_type, # Тип продвижения
#             "advertisement_date": advertisement_date, # Дата объявления
#             "brand": brand, # Марка
#             "model": model, # Модель
#             "body_type": body_type, # Тип кузова
#             "year_of_issue": year_of_issue, # Год выпуска
#             "wheel_formula": wheel_formula, # Колесная формула
#             "condition": condition, # Состояние
#             "company_individual_vendor": company_individual_vendor, # Компания / частное лицо
#         }
#
#         item = database.Item(
#             name=name,
#             article=article,
#             url=product_link,
#             attrs=attrs,
#         )
#         logging.info(item)
#         items.append(item)
#
#     return items
#
#
# def parse() -> set[Any]:
#     """Запускает парсинг avito."""
#     items = []
#     for url in settings.AVITO_URLS:
#         logging.info(f"Запускаю страницу {url}")
#         pages = get_pages(url)
#         time.sleep(5)
#         for page in pages:
#             result = get_products(page)
#             items.append(result)
#
#     items = set(reduce(iconcat, items, []))
#     logging.info(f"Avito: всего товаров: {len(items)}")
#     if items:
#         database.insert_items(items)
#     else:
#         logging.warning("Нет товаров для добавления в базу данных.")
#
#     return items
