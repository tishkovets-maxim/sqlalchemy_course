# Автор пишет в .py файлах и мне легче следовать за его логикой так (хотя и не плодя их в том составе, что у него)
# Тут оставляю финальное состояние
import asyncio
from sqlalchemy import create_engine, insert, text, Table, Column, MetaData, String, Integer
from sqlalchemy.ext.asyncio import create_async_engine

from config import settings     # config лежит прямо в этой папке. Там авторская возвращалка параметров
# * Настройки - в объекте **settings** в модуле **config**. Там вполне тривиальный, но специальный класс читает их из файла.
# * DSN соответственно выглядит так: ```settings.DATABASE_URL_psycopg```



# ## Урок 1.3
# ### Создаем Engine
sync_engine = create_engine\
(   url=settings.DATABASE_URL_psycopg
    # , echo=True
    # pool_size=5, # max_overflow=10
)

# ### Подключаемся, выполняем запрос напрямую


print ('Sync connection:')
with sync_engine.connect() as conn:
    res = conn.execute (text ("SELECT VERSION()") )
    print (res.first())
    conn.commit()
# # ('PostgreSQL 14.4, compiled by Visual C++ build 1914, 64-bit',)       # один кортежик


# # ### Асинхронное подключение
# # В классе настроек мы отдельно прописали подключение через асинхронный драйвер.
# # Мне это сейчас надо меньше, но коли автор разбирает - тоже посмотрю

async_engine = create_async_engine(
    url=settings.DATABASE_URL_asyncpg,
    echo=True,
    # pool_size=5, # max_overflow=10
)


# Асинхронновое.
print ('Async connection:')
async def async_get ():
    async with async_engine.begin() as conn:
        res = await conn.execute (text ("SELECT VERSION()") )
        print (res.first())
        conn.commit()
        
asyncio.run ( async_get() )


# sync_engine.echo=True