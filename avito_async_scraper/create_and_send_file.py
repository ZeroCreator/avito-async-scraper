import datetime
import logging
import xlsxwriter
import psycopg
from contextlib import closing

from avito_scraper import settings

def gen_file():
    with closing(psycopg.connect(settings.PG_DSN)) as conn, closing(conn.cursor()) as cursor:
        # Запрашиваем данные из базы
        today = datetime.datetime.now().date()
        cursor.execute(
            'SELECT name, article, url, attrs '
            'FROM items '
            # 'WHERE DATE(created_at) = %s',
            # (today,)
        )
        data = cursor.fetchall()  # Получаем все строки
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

    # Создание Excel файла и добавление рабочего листа
    with xlsxwriter.Workbook(file_name) as workbook:
        worksheet = workbook.add_worksheet()

        # Запись заголовков в Excel файл
        # Определение заголовков
        headers = ['Название', 'Номер объявления', 'Ссылка на объявление']  # основные заголовки
        # Сопоставление английских ключей с русскими заголовками
        attr_mapping = {
            'seller': 'Продавец',
            'price': 'Цена',
            'brand': 'Марка',
            'model': 'Модель',
            'body_type': 'Тип кузова',
            'year_of_issue': 'Год выпуска',
            'wheel_formula': 'Колесная формула',
            'condition': 'Состояние',
            'availability': 'Доступность',
            'promotion': 'Продвижение',
            'number_of_days_promotion': 'Количество дней продвижения',
            'promotion_type': 'Тип продвижения',
            'advertisement_date': 'Дата объявления',
            'company_individual_vendor': 'Компания / частное лицо',
            'region': 'Регион'
        }

        # Добавление русских заголовков для attrs
        headers.extend(attr_mapping.values())
        worksheet.write_row(0, 0, headers)

        # Запись данных в Excel файл
        for row_num, (name, article, url, attrs) in enumerate(data, start=1):
            # print(
            #     f"Запись {row_num}: Имя={name}, Артикул={article}, url={url}, attrs={attrs}")  # Отладочная информация
            # Заполняем основные значения
            worksheet.write(row_num, 0, name)
            worksheet.write(row_num, 1, article)
            worksheet.write(row_num, 2, url)

            # Заполняем значения из словаря attrs, используя сопоставление
            for col_num, (key, russian_header) in enumerate(attr_mapping.items(), start=3):
                value = attrs.get(key,
                                  '')  # Получаем значение из словаря, если ключ отсутствует - пустая строка
                # Дополнительное логирование значения перед записью
                # print(f"Запись значения для ключа '{key}': {value}")
                worksheet.write(row_num, col_num, value)

        # Удаляем данные из таблицы
    cursor.execute('DELETE FROM items')
    conn.commit()
