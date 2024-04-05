from sqlalchemy import create_engine, insert, text, Table, Column, MetaData, String, Integer

from config import settings     # config лежит прямо в этой папке. Там авторская возвращалка параметров

# ## Урок 1.4

# Engine
sync_engine = create_engine ( url=settings.DATABASE_URL_psycopg )

# Объект "метаданные".
metadata_obj = MetaData ()

# Объект "таблица". Привязываем его к объекту "метаданные".
workers_table = Table\
    (  "workers"
     , metadata_obj
     , Column ("id", Integer, primary_key=True)
     , Column ("user_name", String)
    )


# Создаем таблицы:
# берем метадату и подаем команду "создать физически все, что записано в этой метадате"

# В учебных целях модифицируем так, чтобы все таблицы перед (пере)созданием дропались, если существуют
def create_tables ():
    metadata_obj.drop_all (sync_engine)
    metadata_obj.create_all (sync_engine)

create_tables ()


# ### Вносим данные через core
# #### "Голый" запрос

statement_raw = \
"""INSERT INTO workers (user_name) VALUES
('Vasya'), ('Petya');"""

def insert_data_raw (stmt):
    with sync_engine.connect() as conn:
        conn.execute(text (stmt) )
        conn.commit()
        
insert_data_raw (statement_raw)

# #### Запрос как объект Алхимии
statement = insert (workers_table).values ([{'user_name': 'John'}, {'user_name': 'Bill'}])

def insert_data (stmt):
    with sync_engine.connect() as conn:
        conn.execute( stmt )
        conn.commit()
        
insert_data (statement)

# sync_engine.echo=True