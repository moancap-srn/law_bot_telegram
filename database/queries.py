import aiosqlite


async def add_application(
    user_id: int, username: str, name: str, phone: str, question: str, call_time: str
) -> int:
    """
    Добавляет новую заявку в базу данных

    Аргументы:
        user_id: Telegram ID клиента
        username: Ник клиента в Telegram (может быть None)
        name: Имя клиента
        phone: Телефон клиента
        question: Суть вопроса
        call_time: Удобное время звонка

    Возвращает:
        ID новой заявки
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor = await db.execute(
            """
            INSERT INTO applications (user_id, username, name, phone, question, call_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, name, phone, question, call_time),
        )

        application_id = cursor.lastrowid

        await db.commit()

        return application_id


async def get_application_by_id(application_id: int) -> dict:
    """
    Получает заявку по её ID

    Аргументы:
        application_id: ID заявки

    Возвращает:
        Словарь с данными заявки или None, если не найдена
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, username, name, phone, question, call_time, status, created_at
            FROM applications
            WHERE id = ?
            """,
            (application_id,),
        )

        row = await cursor.fetchone()

        if row is None:
            return None

        return {
            "id": row[0],
            "user_id": row[1],
            "username": row[2],
            "name": row[3],
            "phone": row[4],
            "question": row[5],
            "call_time": row[6],
            "status": row[7],
            "created_at": row[8],
        }


async def update_application_status(application_id: int, status: str) -> bool:
    """
    Обновляет статус заявки

    Аргументы:
        application_id: ID заявки
        status: Новый статус ('new', 'accepted', 'rejected')

    Возвращает:
        True, если успешно, иначе False
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor = await db.execute(
            """
            UPDATE applications
            SET status = ?
            WHERE id = ?
            """,
            (status, application_id),
        )

        await db.commit()

        return cursor.rowcount > 0


async def get_stats() -> dict:
    """
    Получает статистику по заявкам

    Возвращает:
        Словарь со статистикой:
        {
            'today': количество заявок сегодня,
            'week': количество заявок за неделю,
            'total': общее количество заявок,
            'accepted': количество принятых заявок,
            'rejected': количество отклонённых заявок,
            'pending': количество заявок в ожидании
        }
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor_today = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE DATE(created_at) = DATE('now')
            """
        )
        today = (await cursor_today.fetchone())[0]

        cursor_week = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE created_at >= datetime('now', '-7 days')
            """
        )
        week = (await cursor_week.fetchone())[0]

        cursor_total = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            """
        )
        total = (await cursor_total.fetchone())[0]

        cursor_accepted = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE status = 'accepted'
            """
        )
        accepted = (await cursor_accepted.fetchone())[0]

        cursor_rejected = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE status = 'rejected'
            """
        )
        rejected = (await cursor_rejected.fetchone())[0]

        cursor_pending = await db.execute(
            """
            SELECT COUNT(*) FROM applications
            WHERE status = 'new'
            """
        )
        pending = (await cursor_pending.fetchone())[0]

        return {
            "today": today,
            "week": week,
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "pending": pending,
        }


async def get_all_applications() -> list:
    """
    Получает все заявки из базы данных

    Возвращает:
        Список словарей с данными заявок
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, username, name, phone, question, call_time, status, created_at
            FROM applications
            ORDER BY created_at DESC
            """
        )

        rows = await cursor.fetchall()

        applications = []
        for row in rows:
            applications.append(
                {
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "name": row[3],
                    "phone": row[4],
                    "question": row[5],
                    "call_time": row[6],
                    "status": row[7],
                    "created_at": row[8],
                }
            )

        return applications


async def get_applications_by_date(start_date: str, end_date: str) -> list:
    """
    Получает заявки за определённый период

    Аргументы:
        start_date: Дата начала в формате 'YYYY-MM-DD'
        end_date: Дата окончания в формате 'YYYY-MM-DD'

    Возвращает:
        Список словарей с данными заявок
    """
    async with aiosqlite.connect("applications.db") as db:
        cursor = await db.execute(
            """
            SELECT id, user_id, username, name, phone, question, call_time, status, created_at
            FROM applications
            WHERE DATE(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
            """,
            (start_date, end_date),
        )

        rows = await cursor.fetchall()

        applications = []
        for row in rows:
            applications.append(
                {
                    "id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "name": row[3],
                    "phone": row[4],
                    "question": row[5],
                    "call_time": row[6],
                    "status": row[7],
                    "created_at": row[8],
                }
            )

        return applications
