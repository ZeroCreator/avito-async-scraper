"""Модуль для работы с бд.
Содержит функции для:
- подсчета общего количества товаров;
- удаления всех товаров из таблицы и
- удаления самой таблицы."""

import psycopg
import logging

table_name = "items"
dsn = "postgresql://postgres:postgres@127.0.0.1:5432/postgres"

def select_items(table_name, dsn):
    """Функция для подсчета общего количества товаров."""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM items;')

select_items("items", "postgresql://postgres:postgres@127.0.0.1:5432/postgres")


def truncate_table(table_name, dsn):
    """Функция для удаления всех товаров из таблицы."""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE {table_name};')
            logging.info(f'Все данные из таблицы {table_name} успешно удалены.')

# truncate_table("items", "postgresql://postgres:postgres@127.0.0.1:5432/postgres")


def drop_table(table_name, dsn):
    """Функция для удаления самой таблицы."""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS {table_name};')
            logging.info(f'Таблица {table_name} успешно удалена.')

#drop_table("items", "postgresql://postgres:postgres@127.0.0.1:5432/postgres")
