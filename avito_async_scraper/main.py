import sys
import time
import logging
from pathlib import Path

sys.path.append(str(Path(__name__).parent.parent))

from avito_scraper import database, settings, create_and_send_file, avito, proxy

logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s %(levelname)-s %(message)s",
    level=logging.INFO,
)


def main() -> None:
    logging.info("Инициализирую схему данных")
    database.init_schema()

    logging.info(f"Запускаю парсинг")

    items = avito.parse(),
    logging.info(f"Найдено {len(items)} товаров, генерирую файл...")

    # Проверяем, собраны ли товары
    logging.info(items)
    if items and items[0]:  # Если список не пуст
        logging.info(f"Найдено {len(items)} товаров, генерирую файл...")
        time.sleep(10)
        create_and_send_file.gen_file()
    else:
        logging.warning("Товары не найдены, файл не будет создан.")

    logging.info(f"Парсинг завершен")

    # create_and_send_file.gen_file()


if __name__ == "__main__":
    main()
