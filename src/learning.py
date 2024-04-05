# Автор пишет в .py файлах и мне легче следовать за его логикой так (хотя и не плодя их в том составе, что у него)


from sqlalchemy import create_engine, insert, text, Table, Column, MetaData, String, Integer, URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings     # config лежит прямо в этой папке. Там авторская возвращалка параметров


# ## Урок 1.3

# Это дело у нас задумано как "приложение", поэтому устроено "профессионально".
# * Настройки - в объекте **settings** в модуле **config**. Там вполне тривиальный, но специальный класс читает их из файла.
# * DSN соответственно выглядит так: ```settings.DATABASE_URL_psycopg```

# ### Создаем Engine

# In[48]:


sync_engine = create_engine(
    url=settings.DATABASE_URL_psycopg,
    echo=True,
    # pool_size=5, # max_overflow=10
)

sync_engine     # Engine(postgresql+psycopg://postgres:***@127.0.0.1:5432/Uniconf)
sync_engine.__class__       # sqlalchemy.engine.base.Engine
sync_engine.__dict__

# {'pool': <sqlalchemy.pool.impl.QueuePool at 0x1a2dab85350>,
#  'url': postgresql+psycopg://postgres:***@127.0.0.1:5432/Uniconf,
#  'dialect': <sqlalchemy.dialects.postgresql.psycopg.PGDialect_psycopg at 0x1a2dab85090>,
#  '_echo': True,
#  'logger': <sqlalchemy.log.InstanceLogger at 0x1a2d87a99c0>,
#  'hide_parameters': False,
#  '_compiled_cache': <sqlalchemy.util._collections.LRUCache at 0x1a2dab76660>
# }


# ### Подключаемся, выполняем запрос напрямую

# In[25]:


with sync_engine.connect() as conn:
    # res = conn.execute ("SELECT VERSION()")       # Not an executable object.
    # Алхимия не любит "голых" строк и принимает к исполнению запросы только "своего" типа text     (1)
    res = conn.execute (text ("SELECT VERSION()") )
    print (res)


# Это идет само подключение: при создании engine-а оно не произошло, а происходит непосредственно при обращении
# 
# 2024-04-03 13:24:30,857 INFO sqlalchemy.engine.Engine select pg_catalog.version()
# 2024-04-03 13:24:30,857 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2024-04-03 13:24:30,859 INFO sqlalchemy.engine.Engine select current_schema()
# 2024-04-03 13:24:30,860 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2024-04-03 13:24:30,862 INFO sqlalchemy.engine.Engine show standard_conforming_strings
# 2024-04-03 13:24:30,863 INFO sqlalchemy.engine.Engine [raw sql] {}

# Это пошло собственно выполнение запроса, обернутое в транзацию
# 
# 2024-04-03 13:24:30,867 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-03 13:24:30,868 INFO sqlalchemy.engine.Engine SELECT VERSION()
# 2024-04-03 13:24:30,868 INFO sqlalchemy.engine.Engine [generated in 0.00111s] {}
# <sqlalchemy.engine.cursor.CursorResult object at 0x000001A2DB8962E0>
# 2024-04-03 13:24:30,870 INFO sqlalchemy.engine.Engine ROLLBACK

# Транзакция заканчивается ROLLBACK-ом: посмотрели и хватит, ничего не трогаем      (2)
# <sqlalchemy.engine.cursor.CursorResult object at 0x000001A2DB8962E0> - это - вывод print, курсор просто так не выводится (помним по изучению psycopg)     (3)


# In[26]:


# То же самое, но с методом begin вместо connect        (2)
with sync_engine.begin() as conn:
    res = conn.execute (text ("SELECT VERSION()") )
    print (res)
    
# 2024-04-03 13:30:36,682 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-03 13:30:36,683 INFO sqlalchemy.engine.Engine SELECT VERSION()
# 2024-04-03 13:30:36,684 INFO sqlalchemy.engine.Engine [cached since 365.8s ago] {}
# <sqlalchemy.engine.cursor.CursorResult object at 0x000001A2DB8963C0>
# 2024-04-03 13:30:36,687 INFO sqlalchemy.engine.Engine COMMIT

# То же самое, но транзакция заканчивается COMMIT-ом.


# In[27]:


# Лучше по принципу "явное лучше неявного" делать так:      (2)
with sync_engine.begin() as conn:
    res = conn.execute (text ("SELECT VERSION()") )
    print (res)
    conn.commit()
    
# 2024-04-03 13:33:30,155 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-03 13:33:30,156 INFO sqlalchemy.engine.Engine SELECT VERSION()
# 2024-04-03 13:33:30,157 INFO sqlalchemy.engine.Engine [cached since 539.3s ago] {}
# <sqlalchemy.engine.cursor.CursorResult object at 0x000001A2DB896510>
# 2024-04-03 13:33:30,160 INFO sqlalchemy.engine.Engine COMMIT

# Автоматического завершения нет. Вместо него - выполняется **явно** прописанный COMMIT


# In[ ]:


# Рассмотрим, что за тип text       (1)

text ("SELECT VERSION()")   # <sqlalchemy.sql.elements.TextClause object at 0x000001A2DB8B43D0>
text ("SELECT VERSION()").__dict__  # {'_bindparams': {}, 'text': 'SELECT VERSION()'}
', '.join ([x for x in text ("SELECT VERSION()").__dir__() if x[0] !='_'])

# У него есть дофига чего
# 'text, key, bindparams, columns, type, comparator, self_group, allows_lambda, uses_inspection, subquery, memoized_attribute, memoized_instancemethod, supports_execution, 
# is_select, is_update, is_insert, is_text, is_delete, is_dml, options, execution_options, get_execution_options, description, is_clause_element, is_selectable, entity_namespace, 
# unique_params, params, compare, get_children, inherit_cache, stringify_dialect, compile, label'


# In[30]:


# (3) чтобы явно посмотреть что в курсоре - берем методы all / first
# Осторожно - под курсором лежит все, что выдала база. Эти методы - дают просто доступ к уже полученной куче данных

with sync_engine.begin() as conn:
    res = conn.execute (text ("SELECT VERSION()") )
    print (res.all())
    conn.commit()

# [('PostgreSQL 14.4, compiled by Visual C++ build 1914, 64-bit',)]     # список кортежей из строк

with sync_engine.begin() as conn:
    res = conn.execute (text ("SELECT VERSION()") )
    print (res.first())
    conn.commit()

# ('PostgreSQL 14.4, compiled by Visual C++ build 1914, 64-bit',)       # один кортежик


# ### Асинхронное подключение

# In[35]:


# В классе настроек мы отдельно прописали подключение через асинхронный драйвер.
# Мне это сейчас надо меньше, но коли автор разбирает - тоже посмотрю

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
    # pool_size=5, # max_overflow=10
)

async_engine.__class__      # sqlalchemy.ext.asyncio.engine.AsyncEngine


# In[44]:


# Короче вот так это все у него выглядит, но из юпитера не запускается: RuntimeError: asyncio.run() cannot be called from a running event loop
# Ну и бог с ним

# async def async_get ():
#     async with async_engine.begin() as conn:
#         res = await conn.execute (text ("SELECT VERSION()") )
#         print (res.first())
#         conn.commit()
        
# asyncio.run ( async_get() )


# ## Урок 1.4

# ### Создаем таблицу через core
# Будем делать "проект" с работниками, работодателями и резюме

# In[46]:


metadata_obj = MetaData ()
# Объект "метаданные". Хранит собственно метаданные обо всем, что мы наделали на стороне приложения - тут в питонном скрипте.
# Пока пустой.


# In[54]:


# Создаем объект "таблица". Привязываем его к объекту "метаданные". Теперь действия с этой таблицей будут как-то отображаться там.
# Сам объект "таблица" создается тут, в скрипте. За его синхронизацию с базой отвечают "метаданные".

workers_table = Table\
    (  "workers"
     , metadata_obj
     , Column ("id", Integer, primary_key=True)
     , Column ("user_name", String)
    )


# In[51]:


# Создаем таблицы

def create_tables ():
    metadata_obj.create_all (sync_engine)

# Берем "мету", передаем ей ссылку на "движок" (где у нас подключена база), создаем на этом движке все, что записано в мете.
# В функцию обернуто, потому что дальше это у нас будет вписываться в некий класс.
# (за точным делением автора на модули - особо не слежу)

create_tables ()


# 2024-04-03 15:33:44,436 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-03 15:33:44,443 INFO sqlalchemy.engine.Engine SELECT pg_catalog.pg_class.relname 
# FROM pg_catalog.pg_class JOIN pg_catalog.pg_namespace ON pg_catalog.pg_namespace.oid = pg_catalog.pg_class.relnamespace 
# WHERE pg_catalog.pg_class.relname = %(table_name)s::VARCHAR AND pg_catalog.pg_class.relkind = ANY (ARRAY[%(param_1)s::VARCHAR, %(param_2)s::VARCHAR, %(param_3)s::VARCHAR, %(param_4)s::VARCHAR, %(param_5)s::VARCHAR]) AND pg_catalog.pg_table_is_visible(pg_catalog.pg_class.oid) AND pg_catalog.pg_namespace.nspname != %(nspname_1)s::VARCHAR
# 2024-04-03 15:33:44,447 INFO sqlalchemy.engine.Engine [generated in 0.00390s] {'table_name': 'workers', 'param_1': 'r', 'param_2': 'p', 'param_3': 'f', 'param_4': 'v', 'param_5': 'm', 'nspname_1': 'pg_catalog'}
# 2024-04-03 15:33:44,473 INFO sqlalchemy.engine.Engine 
# CREATE TABLE workers (
# 	id SERIAL NOT NULL, 
# 	user_name VARCHAR, 
# 	PRIMARY KEY (id)
# )


# 2024-04-03 15:33:44,474 INFO sqlalchemy.engine.Engine [no key 0.00160s] {}
# 2024-04-03 15:33:44,554 INFO sqlalchemy.engine.Engine COMMIT


# Можем видеть, какой запрос сгенерировала алхимия. В нашем случае - вполне разумный запрос.


# In[55]:


# В учебных целях модифицируем так, чтобы все таблицы перед (пере)созданием дропались, если существуют

def create_tables ():
    # metadata_obj.drop_all (sync_engine)
    metadata_obj.create_all (sync_engine)

create_tables ()

# Короче тут выполняется две транзакции. В одной DROP TABLE workers, во второй - создание как выше


# ### Вносим данные через core

# #### "Голый" запрос

# In[58]:


# Вносим "голый" запрос.

statement = \
"""INSERT INTO workers (user_name) VALUES
('Vasya'), ('Petya');"""

def insert_data_raw (stmt):
    with sync_engine.connect() as conn:
        conn.execute(text (stmt) )
        conn.commit()
        
insert_data_raw (statement)

# 2024-04-03 20:20:10,181 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-03 20:20:10,181 INFO sqlalchemy.engine.Engine INSERT INTO workers (user_name) VALUES
# ('Vasya'), ('Petya');
# 2024-04-03 20:20:10,182 INFO sqlalchemy.engine.Engine [cached since 164.7s ago] {}
# 2024-04-03 20:20:10,185 INFO sqlalchemy.engine.Engine COMMIT


# #### Запрос как объект Алхимии

# В данном случае формируем объект "insert".
# 
# По читаемости, конечно, не сильно лучше голого СКЛ, 
# 
# но позволяет явно оперировать с питонными объектами:
# * берем объект "таблица работников"
# * передаем ему *список* записей, с заполненным полем "имя"
# 
# **TODO:** а что если передать РАЗНОЕ число полей в разных записях?

# In[63]:


statement = insert (workers_table).values ([{'user_name': 'John'}, {'user_name': 'Bill'}])

def insert_data (stmt):
    with sync_engine.connect() as conn:
        conn.execute( stmt )
        conn.commit()
        
insert_data (statement)


# 2024-04-04 13:06:28,880 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2024-04-04 13:06:28,881 INFO sqlalchemy.engine.Engine INSERT INTO workers (user_name) VALUES (%(user_name_m0)s::VARCHAR), (%(user_name_m1)s::VARCHAR)
# 2024-04-04 13:06:28,882 INFO sqlalchemy.engine.Engine [no key 0.00236s] {'user_name_m0': 'John', 'user_name_m1': 'Bill'}
# 2024-04-04 13:06:28,884 INFO sqlalchemy.engine.Engine COMMIT

# Скоммитилось


# In[65]:


statement       # <sqlalchemy.sql.dml.Insert object at 0x000001A2DC499250>
statement.__dict__

# {'table': Table('workers', MetaData(), Column('id', Integer(), table=<workers>, primary_key=True, nullable=False), Column('user_name', String(), table=<workers>), schema=None),
#  '_multi_values': ([{'user_name': 'John'}, {'user_name': 'Bill'}],),
#  'dialect_options': {},
#  '_generate_cache_key': <function sqlalchemy.util.langhelpers.HasMemoized.memoized_instancemethod.<locals>.oneshot.<locals>.memo(*a, **kw)>,
#  '_memoized_keys': frozenset({'_generate_cache_key'}),
#  'description': None,
#  'dialect_kwargs': <sqlalchemy.sql.base._DialectArgView at 0x1a2dbcd8f50>
# }

# Есть таблица, с полной ее метой, есть заносимые строки, есть всякие не очень понятные сейчас параметры.


# ## Урок 1.5

# In[ ]:





# In[66]:


# УНЕСТИ В КОПИЛКУ - конвертюнство блокнота в *.py

try:   
    get_ipython().system('jupyter nbconvert --to python learning.ipynb')
    # Python конвертируется в .py, скрипт конвертируется в .html
         # file_name.ipynb - имя файла текущего модуля
except:
    pass

