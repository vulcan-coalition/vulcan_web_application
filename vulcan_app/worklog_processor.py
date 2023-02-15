import os
from configuration import get_config
import threading
from datetime import datetime, timedelta
import time
import record
from services import Worklog, log_all


dir_path = os.path.dirname(os.path.realpath(__file__))
artifacts_path = os.path.join(dir_path, "..", "artifacts")


async def execute_update(from_time, to_time):
    app_id = get_config("log_app_name")
    records = await record.get_latest_answers(from_time=from_time, to_time=to_time)
    # records are Pydantic object not json object

    user_records = {}
    for r in records:
        if r.email not in user_records:
            user_records[r.email] = []
        user_records[r.email].append(r)

    worklogs = []
    for user, user_records in user_records.items():
        user_records.sort(key=lambda x: x.stamp)
        last_stamp = datetime.min
        for r in user_records:
            duration = (r.stamp - last_stamp).total_seconds()
            worklogs.append(
                Worklog(
                    stamp=r.stamp,
                    app_id=app_id,
                    user_id=r.email,
                    disability=r.disability,
                    amount=r.diffamount,
                    duration=duration if duration < 600 else 0,
                    score=-1
                )
            )
            last_stamp = r.stamp

    print("Total records", len(worklogs))
    if len(worklogs) > 0:
        return await log_all(worklogs)
    return True


thread_running = True


async def run_update(update_period_in_seconds):
    print("Converter update thread is starting...")

    last_update_stamp_path = os.path.join(artifacts_path, "last_update_stamp")

    if not os.path.exists(last_update_stamp_path):
        last_converter_update = datetime.utcnow() - timedelta(days=350)
    else:
        with open(last_update_stamp_path, "r") as file:
            last_converter_update = datetime.fromtimestamp(float(file.read()))

    while thread_running:
        now = datetime.utcnow()
        if (now - last_converter_update).total_seconds() > update_period_in_seconds:
            print("computing logs...", now)
            if await execute_update(last_converter_update, now):
                last_converter_update = now
                with open(last_update_stamp_path, "w") as file:
                    file.write(str(last_converter_update.timestamp()))
        time.sleep(60)


the_thread = None


def set_update_schedule(update_period_in_seconds=60):
    global the_thread, thread_running
    terminate_schedule()
    the_thread = threading.Thread(target=run_update, args=(update_period_in_seconds,))
    thread_running = True
    the_thread.start()


def terminate_schedule():
    global thread_running
    thread_running = False
    if the_thread:
        the_thread.join()


if __name__ == '__main__':
    import asyncio
    asyncio.run(run_update(3600))
