import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from update_mysql import update_mysql
from update_qdrant import update_qdrant
from dotenv import load_dotenv

load_dotenv()


async def main():

    if os.getenv('UPDATE_STORAGE', 'false').lower() == 'false':
        print('No need to update storage. Exiting...')
        return

    if os.getenv('UPDATE_MYSQL', 'false').lower() == 'true':
        await update_mysql()

    if os.getenv('UPDATE_QDRANT', 'false').lower() == 'true':
        await update_qdrant()

    scheduler = AsyncIOScheduler()
    # scheduler.add_job(
    #     update_qdrant,
    #     "cron",
    #     CronTrigger.from_crontab("0 0 * * 0")  # At 00:00 on Sunday.
    # )
    scheduler.start()

    try:
        # Run the scheduler forever
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
