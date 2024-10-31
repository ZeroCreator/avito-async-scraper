"""Модуль с набором вспомогательных функций для парсинга Avito."""

import json
import urllib.parse
import requests
import logging
from bs4 import BeautifulSoup

from avito_scraper import headers

#HEADERS = headers.HEADERS
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9,ru;q=0.8",
    "cache-control": "no-cache",
    "if-none-match": 'W/"1ab2a4-06WEUY1WWfo3V0iuYEknSn5YA3w"',
    "priority": "u=0, i",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": 'luri=rostov-na-donu; srv_id=8KK9YyOzHMU530KD.778kI8kFSR8L-BtRKDc-5llSQnz15qVsX066bnbReuYkc9q289NpPcB6okVdMFM=.eqY9MV-f_ON8K2QfHx3kYdiOpL79ZuJP-a1jFpsNzGk=.web; u=32q43sii.pwh5sg.tfhriqxf4200; buyer_location_id=652000; _ym_uid=1729841569399688140; _ym_d=1729841569; ma_prevFp_3485699018=1337127825|3318434555|3318434555|888000370|2219907560|959198862|3530670207|888000370|1068634537|3180462103|1068634537|3653699262|3274927332|3579944471|3778137224|3579944471|888000370|1068634537|567689674|888000370|621576841|3530670207|3579944471|1068634537|444832511|668684770|3579944471|2366566551|3075504818|888000370|2895824364|3708322660|718548439|3308070491; SEARCH_HISTORY_IDS=0; ma_prevVisId_3485699018=a37fe1c7bc44719f8ea16bceac3f9981; __ai_fp_uuid=b763a51850673e0a%3A1; __upin=AtsPu6VLTINVzkua7KE2aw; ma_id=6885850771718015665251; gMltIuegZN2COuSe=EOFGWsm50bhh17prLqaIgdir1V0kgrvN; uxs_uid=5731c9e0-92a3-11ef-b3ec-b7d9d604abc7; _buzz_fpc=JTdCJTIydmFsdWUlMjIlM0ElN0IlMjJ1ZnAlMjIlM0ElMjJlYzEyOGNmM2M5ZWVkY2ZiMzMzMTI5MDA1NzNkYzQwNCUyMiUyQyUyMmJyb3dzZXJWZXJzaW9uJTIyJTNBJTIyMTIwLjAlMjIlMkMlMjJ0c0NyZWF0ZWQlMjIlM0ExNzI5ODQxNTY5NjgyJTdEJTJDJTIycGF0aCUyMiUzQSUyMiUyRiUyMiUyQyUyMmRvbWFpbiUyMiUzQSUyMi53d3cuYXZpdG8ucnUlMjIlMkMlMjJleHBpcmVzJTIyJTNBJTIyU2F0JTJDJTIwMjUlMjBPY3QlMjAyMDI1JTIwMDclM0EzMiUzQTUxJTIwR01UJTIyJTJDJTIyU2FtZVNpdGUlMjIlM0ElMjJMYXglMjIlN0Q=; _buzz_aidata=JTdCJTIydmFsdWUlMjIlM0ElN0IlMjJ1ZnAlMjIlM0ElMjJBdHNQdTZWTFRJTlZ6a3VhN0tFMmF3JTIyJTJDJTIyYnJvd3NlclZlcnNpb24lMjIlM0ElMjIxMjAuMCUyMiUyQyUyMnRzQ3JlYXRlZCUyMiUzQTE3Mjk4NDE1Njk3NTclN0QlMkMlMjJwYXRoJTIyJTNBJTIyJTJGJTIyJTJDJTIyZG9tYWluJTIyJTNBJTIyLnd3dy5hdml0by5ydSUyMiUyQyUyMmV4cGlyZXMlMjIlM0ElMjJTYXQlMkMlMjAyNSUyME9jdCUyMDIwMjUlMjAwNyUzQTMyJTNBNTElMjBHTVQlMjIlMkMlMjJTYW1lU2l0ZSUyMiUzQSUyMkxheCUyMiU3RA==; _buzz_mtsa=JTdCJTIydmFsdWUlMjIlM0ElN0IlMjJ1ZnAlMjIlM0ElMjJhMzdmZTFjN2JjNDQ3MTlmOGVhMTZiY2VhYzNmOTk4MSUyMiUyQyUyMmJyb3dzZXJWZXJzaW9uJTIyJTNBJTIyMTIwLjAlMjIlMkMlMjJ0c0NyZWF0ZWQlMjIlM0ExNzI5ODQxNTY5NTY4JTdEJTJDJTIycGF0aCUyMiUzQSUyMiUyRiUyMiUyQyUyMmRvbWFpbiUyMiUzQSUyMi53d3cuYXZpdG8ucnUlMjIlMkMlMjJleHBpcmVzJTIyJTNBJTIyU2F0JTJDJTIwMjUlMjBPY3QlMjAyMDI1JTIwMDclM0EzMiUzQTUxJTIwR01UJTIyJTJDJTIyU2FtZVNpdGUlMjIlM0ElMjJMYXglMjIlN0Q=; _gcl_au=1.1.278616208.1729937918; _ga=GA1.1.540504396.1729937924; tmr_lvid=faa8d70946034430ac6d120923ec5e4d; tmr_lvidTS=1729937924211; adrcid=A-ZWKL0ajq2rdeba1Y88x9g; adrcid=A-ZWKL0ajq2rdeba1Y88x9g; ma_cid=3307287821729937939; _ym_isad=2; luri=rostov-na-donu; f=5.0c4f4b6d233fb90636b4dd61b04726f147e1eada7172e06c47e1eada7172e06c47e1eada7172e06c47e1eada7172e06cb59320d6eb6303c1b59320d6eb6303c1b59320d6eb6303c147e1eada7172e06c8a38e2c5b3e08b898a38e2c5b3e08b890df103df0c26013a7b0d53c7afc06d0b2ebf3cb6fd35a0ac0df103df0c26013a0df103df0c26013a1772440e04006defc7cea19ce9ef44010f7bd04ea141548c78ba5f931b08c66a2a125ecd8b100f4a7b0d53c7afc06d0b03c77801b122405c2da10fb74cac1eab2da10fb74cac1eabdc5322845a0cba1af722fe85c94f7d0c2da10fb74cac1eab2da10fb74cac1eabf0c77052689da50d2da10fb74cac1eab3c02ea8f64acc0bd853206102760b3e6de87ad3b397f946b4c41e97fe93686adbf5c86bc0685a4ff6e9b8b28e6c8b01602c730c0109b9fbbde81d25d6721ea6f6bb0c2793bb80c690e28148569569b79aa6ba8d287ec3f6e98bc5fdf0f9301182ebf3cb6fd35a0ac0df103df0c26013a28a353c4323c7a3aefcfb0a8b11101953c397c664b5c08f13de19da9ed218fe23de19da9ed218fe2555de5d65c04a913f0d2c94a7c2a35336c61a72e2a72865b; ft="wouq3Ok60Eu/H+3Ray+G7P+lKBcOenKaL25PL1uwl6PQwVMoEZK1al9c7sNaZV6EqBS/4rKZaOnKOKrizFRL053ZI/tR0JlzuhmhePQqROhyEjkllefWexH1w5YPJDjaPY/mpstzRJ1olTYXbxEdqSmnL9xIP32hNQA/OQNSX6TnB9cgG05IcJ+iG3kWBsVJ"; adrdel=1730281535554; adrdel=1730281535554; acs_3=%7B%22hash%22%3A%225c916bd2c1ace501cfd5%22%2C%22nextSyncTime%22%3A1730367935827%2C%22syncLog%22%3A%7B%22224%22%3A1730281535827%2C%221228%22%3A1730281535827%2C%221230%22%3A1730281535827%7D%7D; acs_3=%7B%22hash%22%3A%225c916bd2c1ace501cfd5%22%2C%22nextSyncTime%22%3A1730367935827%2C%22syncLog%22%3A%7B%22224%22%3A1730281535827%2C%221228%22%3A1730281535827%2C%221230%22%3A1730281535827%7D%7D; domain_sid=_FZw9daR7iYjR9uXfw8jT%3A1730281544700; v=1730285759; buyer_laas_location=652000; __zzatw-avito=MDA0dBA=Fz2+aQ==; __zzatw-avito=MDA0dBA=Fz2+aQ==; yandex_monthly_cookie=true; _ym_visorc=b; sx=H4sIAAAAAAAC%2F1zSWZLiOBDG8bv4mYeUlItUt9GWtsHGYLwUdPjuE90T9FBzgV9k5Pf%2F1YAmsBFsyoliVjFIaklizMloxdh8%2FWq25qtJtt0jtuOsMESbi8EN5JLittkzvbA5NbX5MuLAsYil49QYr0UwRgzRCGZk8SFB1EDJ%2B5j9Wz4%2FN6HVaxh2cqtvwxLW8DA63G52DfOHLAFZjlPDzJyLsAYOxMihSqouFCHIWUp4yw9eh%2FGxglkH%2B5DixyUbsGm1WAoM7ofswr%2ByghqfE3MJxTpj1UcFKMFjtlDfMtdpGdrh1d5wnNbnbq73ve4XvtR%2BcK39lDGEcJwaKSqEmV3JYlzMQN7nHMhmcbn8d3PbXvzo19dT5zauvSl9152ncT537XLv%2BEP2IH%2B%2BITU7cgmMOA2aqjIYJfTgSFwk%2FisvZt%2F2%2B5VDvk%2BzXmrO0%2F1VttswTbDXzwU9kDlOTUya%2F9RAIaM3iSSisZVKtZIVzFuGrpW9G9ZvX66vfB63vo9dymPcCb%2BX9eef%2BXcbqURICQitAUvOEPrsJUWvsbJVecsReKFtn59ZZjdg0f3VP6%2Ffbqhhg1f4lAnYHacml1QtKoJHBg5WDaBNQoaqClh9yzaE1ukDYgaVZ0v2cYatH9lde6X2sw0m9HycmoLVC7pAHoy3JWsqbHPQGEwE9n8XZCl9O7d8g7E%2B6l1i6r93o8swhbO%2F3n%2B04YP9LZMpFEuJkNEGk2PN6EoxpqZEWtxbvqB9def%2BKt1Tb%2ByXaIs17bxeFyOmu%2F5cEP1xampgIyGlRKVA9k7RYkw1ijWlKOBbRlp5vS3PyS7WEPN6nqGFGSN9d1Pf%2F29Bdxz%2FBAAA%2F%2F9AaT1POQQAAA%3D%3D; dfp_group=65; abp=0; _ga_M29JC28873=GS1.1.1730293279.10.1.1730294579.60.0.0; ma_ss_64a8dba6-67f3-4fe4-8625-257c4adae014=8551797351730293281.9.1730294580.2; tmr_detect=0%7C1730294582144'}


def get_response(url, proxy):
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
        proxies={
            "http": proxy,
            "https": proxy,
        },
    )
    return response


def get_page_count(response):
    """Функция для получения количества страниц пагинации."""

    soup = BeautifulSoup(response.text, 'html.parser')
    select_page = soup.select('[aria-label="Пагинация"] ul')
    if "..." in select_page[0].text:
        page_count = select_page[0].text.split('...')[1]
        logging.info(f"Всего страниц: {page_count}")
    else:
        page_count = select_page[0].text
        page_count = [len(page_count)][0]
        logging.info(f"Всего страниц: {page_count}")

    return int(page_count)


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


def get_decoder_json(json_string):
    """Функция для декодирования данных и получения JSON."""
    decoded_json_string = urllib.parse.unquote(json_string)

    return json.loads(decoded_json_string)


def write_data_txt(data, file_name):
    """Функция для записи текста в файл."""
    with open(f'{file_name}.text', mode='w') as f:
        f.write(data)


def write_data_json(data, file_name):
    # Запись словаря в файл в формате JSON
    with open(f'{file_name}.json', mode='w') as f:
        json.dump(data, f, indent=4)  # indent=4 для форматирования
