
from mysql.db import Base, db
from mysql.inserts.order import update_orders_in_db
from time import sleep


async def update_mysql():
    try:
        Base.metadata.create_all(bind=db.engine)

        await update_orders_in_db()
    except Exception as e:
        print('Waiting for 10 seconds')
        sleep(10)
        await update_mysql()
        print(e)
