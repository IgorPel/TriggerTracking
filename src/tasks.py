import bisect
import json
import os
from collections import defaultdict

from sqlalchemy import text
from src.data.database import AsyncSessionLocal  # <--- Імпортуємо фабрику сесій
from src.crypto_client import CMClient
import asyncio
from src.celery_app import celery_app
from datetime import datetime
from celery.utils.log import get_task_logger
import redis.asyncio as redis

logger = get_task_logger(__name__)
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")



# ВИПРАВЛЕНО: Змінили t.payload->'logic_chain' на t.func
# ВИПРАВЛЕНО: operator замість operation


RAW_SQL = text("""
    SELECT
        t.id as trigger_id,
        elem->>'arg1' as asset,
        elem->>'operation' as operator,
        (elem->>'arg2')::float as threshold,
        (elem->>'part_id')::int as part_id,
        elem->>'boolean_operation' as boolean_operation
    FROM triggers AS t
    JOIN "UserToTriggers" AS ut ON t.id = ut.trigger_id
    CROSS JOIN jsonb_array_elements(t.func) as elem
    ORDER BY asset, operator, threshold ASC; 
""")


async def get_market_data_async():
    """Асинхронна обгортка для роботи з БД та API"""

    # 1. Створюємо сесію власноруч (без Depends)
    async with AsyncSessionLocal() as db:
        rows = await db.execute(RAW_SQL)
        rows = rows.all()  # ВИПРАВЛЕНО: fetchall() -> .all()
        activation_map = await db.execute(text("""SELECT DISTINCT ON (t.id)
                                                t.id, ut.is_active 
                                            FROM triggers t 
                                            JOIN "UserToTriggers" ut ON t.id = ut.trigger_id"""))
        activation_map = activation_map.all()
        activation_map = {row[0]: row[1] for row in activation_map}

    logger.info(f"NEWEST VERSION!!!!!")
    logger.info(f"\n\n{rows}")
    logger.info(f"END")

    # 2. Будуємо мапу
    market_map = defaultdict(lambda: {
        "gt": {"values": [], "meta": []},
        "lt": {"values": [], "meta": []}
    })



    for row in rows:
        asset = row.asset
        market_map[asset][row.operator]['values'].append(row.threshold)
        market_map[asset][row.operator]['meta'].append({
            "trigger_id": row.trigger_id,
            "part_id": row.part_id,
            "boolean_operation": row.boolean_operation
        })

    if not market_map:
        return None, None, None

    # 3. Отримуємо ціни
    needed_currency = list(market_map.keys())
    cm_client = CMClient()
    current_prices = await cm_client.get_prices_batch(needed_currency)
    logger.info(f"CURRENCIES: {current_prices}")
    return market_map, current_prices, activation_map



@celery_app.task
def cheacking_triggers():
    logger.info("------------START CHECKING TRIGGERS-------------")

    # Запускаємо асинхронний код з синхронної задачі
    try:
        market_map, current_prices, activation_map = asyncio.run(get_market_data_async())
    except Exception as e:
        logger.error(f"ERROR 0: {e}")
        return

    if not market_map or not current_prices:
        logger.info("No active triggers or empty prices.")
        return

    state_map = defaultdict(dict)

    # ВИПРАВЛЕНО: Використовуємо .items() для правильного проходу по словнику
    for currency, price in current_prices.items():
        if price is None or currency not in market_map:
            continue

        map_data = market_map[currency]

        # --- ЛОГІКА ДЛЯ БІЛЬШЕ (gt) ---
        # Всі пороги, що менші за поточну ціну - виконались (True)
        res_gt = bisect.bisect_right(map_data["gt"]["values"], price)
        meta_gt = map_data["gt"]["meta"]

        for i in range(res_gt):
            state_map[meta_gt[i]["trigger_id"]][meta_gt[i]["part_id"]] = True
            state_map[meta_gt[i]["trigger_id"]][f'operation_{meta_gt[i]["part_id"]}'] = meta_gt[i]["boolean_operation"]
        for i in range(res_gt, len(map_data["gt"]["values"])):
            state_map[meta_gt[i]["trigger_id"]][meta_gt[i]["part_id"]] = False
            state_map[meta_gt[i]["trigger_id"]][f'operation_{meta_gt[i]["part_id"]}'] = meta_gt[i]["boolean_operation"]

        # --- ЛОГІКА ДЛЯ МЕНШЕ (lt) ---
        # Всі пороги, що більші за поточну ціну - виконались (True)
        res_lt = bisect.bisect_right(map_data["lt"]["values"], price)
        meta_lt = map_data["lt"]["meta"]

        for i in range(res_lt):
            state_map[meta_lt[i]["trigger_id"]][meta_lt[i]["part_id"]] = False
            state_map[meta_lt[i]["trigger_id"]][f'operation_{meta_lt[i]["part_id"]}'] = meta_lt[i]["boolean_operation"]

        for i in range(res_lt, len(map_data["lt"]["values"])):
            state_map[meta_lt[i]["trigger_id"]][meta_lt[i]["part_id"]] = True
            state_map[meta_lt[i]["trigger_id"]][f'operation_{meta_lt[i]["part_id"]}'] = meta_lt[i]["boolean_operation"]

    activated_triggers = []


    print(f"Map of States on {datetime.now()}:\n{dict(state_map)}", flush=True)


    for id_trigger, result in state_map.items():
        logger.info(f"Trigger {id_trigger}: {result}")
        result_trigger = result[0]
        boolean_operation = result["operation_0"]
        for i in range(1, int(len(result) / 2)):
            tmp = result[i]
            if boolean_operation == "AND":
                result_trigger = result_trigger & tmp
                if not result_trigger:
                    break
            elif boolean_operation == "OR":
                result_trigger = result_trigger | tmp

            boolean_operation = result[f"operation_{i}"]

        logger.info(f"Trigger {id_trigger}: {result_trigger}")
        logger.info(f"State: {activation_map[id_trigger]}")

        if activation_map[id_trigger] and not result_trigger:
            activated_triggers.append(id_trigger)
        elif not activation_map[id_trigger] and result_trigger:
            activated_triggers.append(id_trigger)

    if activated_triggers:
        logger.info(f"Activated triggers: {activated_triggers}")
        try:
            asyncio.run(AlarmUsers(activated_triggers))
        except Exception as e:
            logger.error(f"ERROR 1:: {e}")
    else:
        logger.info(f"No active triggers or empty prices.")
    #logger.info(f"\n\nActivated triggers: {activated_triggers}", flush=True)


async def AlarmUsers(activated : list):
    sql = text("""SELECT t.user_id, t.trigger_id, t.is_active FROM "UserToTriggers" t WHERE trigger_id = ANY(:triggers)""")
    sqlAct = text("""UPDATE "UserToTriggers" SET is_active = NOT is_active, last_triggered=:time  WHERE trigger_id = ANY(:triggers)""")
    async with AsyncSessionLocal() as db:
        time_activation = datetime.now()
        await db.execute(sqlAct, {"triggers": activated, "time": time_activation})
        await db.commit()
        rows = await db.execute(sql, {"triggers": activated})
        rows = rows.all()


        logger.info(f"Found {rows} users to trigger.")

    if rows is None:
        logger.info(f"No users to trigger.")
        return

    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        async with redis_client.pipeline() as pipe:
            for row in rows:
                channel = f"alerts-{row[0]}"
                payload = json.dumps({
                    "type": "TRIGGER_ACTIVATED" if row[2] else "TRIGGER_DEACTIVATED",
                    "trigger_id": str(row[1]),
                    "message": 'TRIGGER',
                    "timestamp": str(time_activation),
                })
                logger.info(f"Channel: {channel} sending payload: {payload}.")
                pipe.publish(channel, payload)
            await pipe.execute()
    except Exception as e:
        logger.error(f"ERROR 2: {e}")

