import asyncio
import aiosqlite
import logging
from datetime import datetime, date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = "8754965889:AAEC6SYJqvhmouuQ_6fUrFc8vTwqQYT18iE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_PATH = "game.db"

# ─────────────────────────────────────────
# 📦 БАЗА ДАННЫХ
# ─────────────────────────────────────────

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY,
                xp          INTEGER DEFAULT 0,
                level       INTEGER DEFAULT 1,
                skill       INTEGER DEFAULT 0,
                income      INTEGER DEFAULT 0,
                streak      INTEGER DEFAULT 0,
                last_active TEXT DEFAULT ''
            )
        """)
        await db.commit()

async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row is None:
            await db.execute(
                "INSERT INTO users (id) VALUES (?)", (user_id,)
            )
            await db.commit()
            return {"id": user_id, "xp": 0, "level": 1,
                    "skill": 0, "income": 0, "streak": 0, "last_active": ""}
        return dict(row)

async def save_user(user: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users
            SET xp=?, level=?, skill=?, income=?, streak=?, last_active=?
            WHERE id=?
        """, (user["xp"], user["level"], user["skill"],
              user["income"], user["streak"], user["last_active"], user["id"]))
        await db.commit()

async def get_all_user_ids() -> list[int]:
    """Нужно для рассылки напоминаний."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]

# ─────────────────────────────────────────
# 🎮 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────

def xp_for_next_level(level: int) -> int:
    """XP нужно растёт с каждым уровнем — как в нормальных RPG."""
    return 100 + (level - 1) * 50

def get_rank(level: int) -> str:
    ranks = {1: "F", 3: "E", 6: "D", 10: "C", 15: "B", 21: "A", 28: "S"}
    rank = "F"
    for lvl, r in ranks.items():
        if level >= lvl:
            rank = r
    return rank

def update_streak(user: dict) -> dict:
    """Обновляет стрик: если был активен вчера — стрик растёт."""
    today = date.today().isoformat()
    last = user.get("last_active", "")
    if last == today:
        return user  # уже был сегодня
    yesterday = (date.today().toordinal() - 1)
    if last == date.fromordinal(yesterday).isoformat():
        user["streak"] += 1
    else:
        user["streak"] = 1
    user["last_active"] = today
    return user

async def award_xp(user: dict, xp: int, skill_delta: int = 0,
                   income_delta: int = 0) -> tuple[dict, str]:
    """
    Начисляет XP с учётом стрика, проверяет level up.
    Возвращает (обновлённый user, сообщение о наградах).
    """
    user = update_streak(user)

    # Бонус за стрик
    multiplier = 1.0
    streak_msg = ""
    if user["streak"] >= 7:
        multiplier = 2.0
        streak_msg = "🔥 Стрик 7+ дней — ×2 XP!\n"
    elif user["streak"] >= 3:
        multiplier = 1.5
        streak_msg = f"🔥 Стрик {user['streak']} дней — ×1.5 XP!\n"

    earned = int(xp * multiplier)
    user["xp"] += earned
    user["skill"] += skill_delta
    user["income"] += income_delta

    # Level up (может быть несколько за раз)
    level_up_msg = ""
    while user["xp"] >= xp_for_next_level(user["level"]):
        user["xp"] -= xp_for_next_level(user["level"])
        user["level"] += 1
        rank = get_rank(user["level"])
        level_up_msg += f"\n🎉 LEVEL UP! Уровень {user['level']} | Ранг {rank}"

    await save_user(user)
    return user, streak_msg, level_up_msg, earned

# ─────────────────────────────────────────
# 🎛️ КЛАВИАТУРА
# ─────────────────────────────────────────

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статы"), KeyboardButton(text="🎯 Квесты")],
        [KeyboardButton(text="🏆 Ранг")]
    ],
    resize_keyboard=True
)

# ─────────────────────────────────────────
# 🚀 ХЕНДЛЕРЫ
# ─────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    await get_user(msg.from_user.id)
    await msg.answer(
        "⚔️ *Добро пожаловать в Life RPG!*\n\n"
        "Выполняй реальные задачи — прокачивай персонажа.\n"
        "Каждый день активности увеличивает стрик и бонус XP.\n\n"
        "Используй кнопки ниже 👇",
        parse_mode="Markdown",
        reply_markup=menu
    )

@dp.message(F.text == "📊 Статы")
async def show_stats(msg: types.Message):
    user = await get_user(msg.from_user.id)
    level = user["level"]
    needed = xp_for_next_level(level)
    rank = get_rank(level)
    bar_filled = int((user["xp"] / needed) * 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    streak_icon = "🔥" if user["streak"] >= 3 else "📅"
    await msg.answer(
        f"📊 *Твой персонаж*\n\n"
        f"🏅 Уровень: {level} | Ранг: {rank}\n"
        f"⚡ XP: {user['xp']}/{needed}\n"
        f"[{bar}]\n\n"
        f"🎓 Навык: {user['skill']}\n"
        f"💰 Доход: {user['income']}\n"
        f"{streak_icon} Стрик: {user['streak']} дней",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🏆 Ранг")
async def show_rank(msg: types.Message):
    user = await get_user(msg.from_user.id)
    rank = get_rank(user["level"])
    await msg.answer(
        f"🏆 *Система рангов*\n\n"
        f"F → E (ур.3) → D (ур.6) → C (ур.10)\n"
        f"C → B (ур.15) → A (ур.21) → *S (ур.28)*\n\n"
        f"Твой текущий ранг: *{rank}*",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🎯 Квесты")
async def show_quests(msg: types.Message):
    await msg.answer(
        "🎯 *Квесты на сегодня:*\n\n"
        "🎬 `видео` — снять/смонтировать видео (+40 XP, +2 Навык)\n"
        "📚 `обучение` — пройти урок/курс (+20 XP)\n"
        "📤 `публикация` — опубликовать контент (+50 XP, +2 Доход)\n"
        "🏃 `тренировка` — физическая нагрузка (+30 XP)\n\n"
        "💡 Стрик 3+ дней = ×1.5 XP | Стрик 7+ дней = ×2 XP",
        parse_mode="Markdown"
    )

# ─── Выполнение квестов ───────────────────

QUESTS = {
    "видео":       {"xp": 40, "skill": 2, "income": 0, "emoji": "🎬"},
    "обучение":    {"xp": 20, "skill": 1, "income": 0, "emoji": "📚"},
    "публикация":  {"xp": 50, "skill": 0, "income": 2, "emoji": "📤"},
    "тренировка":  {"xp": 30, "skill": 0, "income": 0, "emoji": "🏃"},
}

@dp.message(F.text.in_(QUESTS.keys()))
async def complete_quest(msg: types.Message):
    quest_name = msg.text
    q = QUESTS[quest_name]
    user = await get_user(msg.from_user.id)

    user, streak_msg, level_up_msg, earned = await award_xp(
        user, q["xp"], q["skill"], q["income"]
    )

    response = (
        f"{q['emoji']} *Квест выполнен!*\n\n"
        f"{streak_msg}"
        f"⚡ +{earned} XP"
    )
    if q["skill"]:
        response += f" | 🎓 +{q['skill']} Навык"
    if q["income"]:
        response += f" | 💰 +{q['income']} Доход"
    if level_up_msg:
        response += level_up_msg

    await msg.answer(response, parse_mode="Markdown")

# ─────────────────────────────────────────
# ⏰ НАПОМИНАНИЯ
# ─────────────────────────────────────────

async def send_morning_reminder():
    """08:00 — выдаём квесты на день."""
    user_ids = await get_all_user_ids()
    for uid in user_ids:
        try:
            await bot.send_message(
                uid,
                "☀️ *Новый день — новые квесты!*\n\n"
                "Нажми 🎯 Квесты чтобы увидеть задания.\n"
                "Не прерывай стрик! 🔥",
                parse_mode="Markdown"
            )
        except Exception:
            pass  # пользователь мог заблокировать бота

async def send_evening_reminder():
    """21:00 — напоминаем отметить выполненное."""
    user_ids = await get_all_user_ids()
    for uid in user_ids:
        try:
            await bot.send_message(
                uid,
                "🌙 *Итоги дня*\n\n"
                "Не забудь отметить выполненные квесты!\n"
                "Напиши: `видео`, `обучение`, `публикация` или `тренировка`",
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def scheduler():
    """Простой планировщик — проверяет время каждую минуту."""
    while True:
        now = datetime.now()
        hm = (now.hour, now.minute)

        if hm == (8, 0):
            await send_morning_reminder()
        elif hm == (21, 0):
            await send_evening_reminder()

        await asyncio.sleep(60)  # проверяем каждую минуту

# ─────────────────────────────────────────
# ▶️ ЗАПУСК
# ─────────────────────────────────────────

async def main():
    await init_db()
    # Запускаем планировщик и бота параллельно
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler()
    )

if __name__ == "__main__":
    asyncio.run(main())
