import asyncio
import aiosqlite
import logging
from datetime import datetime, date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

TOKEN = "8754965889:AAEC6SYJqvhmouuQ_6fUrFc8vTwqQYT18iE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_PATH = "game.db"

# ─────────────────────────────────────────
# 📦 КВЕСТЫ
# ─────────────────────────────────────────

QUESTS = {
    # 🧠 ИНТЕЛЛЕКТ
    "intel_read10":    {"name": "📖 Читал 10 стр.",          "xp": 5,  "stat": "intel",    "stat_val": 1, "emoji": "📖"},
    "intel_course":    {"name": "📚 Урок курса",              "xp": 10, "stat": "intel",    "stat_val": 1, "emoji": "📚"},
    "intel_english":   {"name": "🇬🇧 Урок английского",      "xp": 8,  "stat": "intel",    "stat_val": 1, "emoji": "🇬🇧"},
    "intel_video":     {"name": "🎥 Обучающее видео",         "xp": 2,  "stat": "intel",    "stat_val": 0, "emoji": "🎥"},
    "intel_podcast":   {"name": "🎙 Образовательный подкаст", "xp": 3,  "stat": "intel",    "stat_val": 0, "emoji": "🎙"},
    "intel_notes":     {"name": "✍️ Конспект / заметки",     "xp": 5,  "stat": "intel",    "stat_val": 1, "emoji": "✍️"},

    # 💪 СИЛА
    "strength_gym":    {"name": "🏋️ Тренировка в зале",     "xp": 15, "stat": "strength", "stat_val": 2, "emoji": "🏋️"},
    "strength_home":   {"name": "🤸 Домашняя тренировка",    "xp": 10, "stat": "strength", "stat_val": 1, "emoji": "🤸"},
    "strength_box":    {"name": "🥊 Бокс",                   "xp": 15, "stat": "strength", "stat_val": 2, "emoji": "🥊"},
    "strength_exp":    {"name": "💪 Эспандер",               "xp": 2,  "stat": "strength", "stat_val": 0, "emoji": "💪"},
    "strength_push":   {"name": "⬆️ Отжимания 30+",          "xp": 5,  "stat": "strength", "stat_val": 1, "emoji": "⬆️"},

    # ⚡ ЛОВКОСТЬ
    "agility_run":     {"name": "🏃 Пробежка",               "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "🏃"},
    "agility_stretch": {"name": "🧘 Растяжка",               "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "🧘"},
    "agility_rope":    {"name": "⚡ Скакалка",               "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "⚡"},
    "agility_swim":    {"name": "🏊 Плавание",               "xp": 10, "stat": "agility",  "stat_val": 2, "emoji": "🏊"},
    "agility_bike":    {"name": "🚴 Велосипед",              "xp": 8,  "stat": "agility",  "stat_val": 1, "emoji": "🚴"},

    # 💰 ФИНАНСОВАЯ ГРАМОТНОСТЬ
    "finance_expenses":{"name": "📊 Посчитал расходы",       "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📊"},
    "finance_content": {"name": "📤 Публикация контента",    "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📤"},
    "finance_earn":    {"name": "💵 Доп. заработок",         "xp": 15, "stat": "finance",  "stat_val": 2, "emoji": "💵"},
    "finance_invest":  {"name": "📈 Читал про инвестиции",   "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📈"},
    "finance_plan":    {"name": "🗓 Финансовый план",        "xp": 8,  "stat": "finance",  "stat_val": 1, "emoji": "🗓"},

    # ❤️ ЗДОРОВЬЕ
    "health_sleep":    {"name": "😴 Поспал 7-8 часов",       "xp": 10, "stat": "health",   "stat_val": 1, "emoji": "😴"},
    "health_noffast":  {"name": "🥗 Не ел фаст-фуд",        "xp": 2,  "stat": "health",   "stat_val": 0, "emoji": "🥗"},
    "health_snack":    {"name": "🍎 Полезный перекус",       "xp": 2,  "stat": "health",   "stat_val": 0, "emoji": "🍎"},
    "health_water":    {"name": "💧 Выпил 2л воды",          "xp": 3,  "stat": "health",   "stat_val": 0, "emoji": "💧"},
    "health_nophone":  {"name": "📵 Без телефона перед сном","xp": 5,  "stat": "health",   "stat_val": 1, "emoji": "📵"},
    "health_meditate": {"name": "🧘 Медитация 10 мин",       "xp": 5,  "stat": "health",   "stat_val": 1, "emoji": "🧘"},
}

CATEGORIES = {
    "intel":    "🧠 Интеллект",
    "strength": "💪 Сила",
    "agility":  "⚡ Ловкость",
    "finance":  "💰 Финансовая грамотность",
    "health":   "❤️ Здоровье",
}

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
                intel       INTEGER DEFAULT 0,
                strength    INTEGER DEFAULT 0,
                agility     INTEGER DEFAULT 0,
                finance     INTEGER DEFAULT 0,
                health      INTEGER DEFAULT 0,
                streak      INTEGER DEFAULT 0,
                last_active TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                user_id    INTEGER,
                quest_id   TEXT,
                quest_date TEXT,
                PRIMARY KEY (user_id, quest_id, quest_date)
            )
        """)
        await db.commit()

async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row is None:
            await db.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            await db.commit()
            return {"id": user_id, "xp": 0, "level": 1,
                    "intel": 0, "strength": 0, "agility": 0,
                    "finance": 0, "health": 0,
                    "streak": 0, "last_active": ""}
        return dict(row)

async def save_user(user: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET xp=?, level=?, intel=?, strength=?, agility=?,
            finance=?, health=?, streak=?, last_active=? WHERE id=?
        """, (user["xp"], user["level"], user["intel"], user["strength"],
              user["agility"], user["finance"], user["health"],
              user["streak"], user["last_active"], user["id"]))
        await db.commit()

async def is_quest_done_today(user_id: int, quest_id: str) -> bool:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM daily_quests WHERE user_id=? AND quest_id=? AND quest_date=?",
            (user_id, quest_id, today)
        ) as cur:
            return await cur.fetchone() is not None

async def mark_quest_done(user_id: int, quest_id: str):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO daily_quests VALUES (?, ?, ?)",
            (user_id, quest_id, today)
        )
        await db.commit()

async def get_all_user_ids() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM users") as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]

# ─────────────────────────────────────────
# 🎮 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ─────────────────────────────────────────

def xp_for_next_level(level: int) -> int:
    return 100 + (level - 1) * 50

def get_rank(level: int) -> str:
    if level >= 28: return "S"
    if level >= 21: return "A"
    if level >= 15: return "B"
    if level >= 10: return "C"
    if level >= 6:  return "D"
    if level >= 3:  return "E"
    return "F"

def update_streak(user: dict) -> dict:
    today = date.today().isoformat()
    last = user.get("last_active", "")
    if last == today:
        return user
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
    user["streak"] = (user["streak"] + 1) if last == yesterday else 1
    user["last_active"] = today
    return user

async def award_xp(user: dict, xp: int, stat: str, stat_val: int):
    user = update_streak(user)
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
    if stat in user:
        user[stat] += stat_val

    level_up_msg = ""
    while user["xp"] >= xp_for_next_level(user["level"]):
        user["xp"] -= xp_for_next_level(user["level"])
        user["level"] += 1
        level_up_msg += f"\n🎉 LEVEL UP! Уровень {user['level']} | Ранг {get_rank(user['level'])}"

    await save_user(user)
    return user, streak_msg, level_up_msg, earned

# ─────────────────────────────────────────
# 🎛️ КЛАВИАТУРЫ
# ─────────────────────────────────────────

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статы"), KeyboardButton(text="🎯 Квесты")],
        [KeyboardButton(text="🏆 Ранг")]
    ],
    resize_keyboard=True
)

def categories_keyboard():
    buttons = []
    row = []
    for cat_id, cat_name in CATEGORIES.items():
        row.append(InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quests_keyboard(category: str, done_quests: list):
    buttons = []
    for quest_id, quest in QUESTS.items():
        if quest["stat"] == category:
            if quest_id in done_quests:
                label = f"✅ {quest['name']}"
                cb = f"done_{quest_id}"
            else:
                label = f"{quest['name']} +{quest['xp']}XP"
                cb = f"quest_{quest_id}"
            buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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
        reply_markup=main_menu
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
        f"🧠 Интеллект: {user['intel']}\n"
        f"💪 Сила: {user['strength']}\n"
        f"⚡ Ловкость: {user['agility']}\n"
        f"💰 Финансы: {user['finance']}\n"
        f"❤️ Здоровье: {user['health']}\n\n"
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
        f"B (ур.15) → A (ур.21) → *S (ур.28)*\n\n"
        f"Твой текущий ранг: *{rank}*",
        parse_mode="Markdown"
    )

@dp.message(F.text == "🎯 Квесты")
async def show_quests(msg: types.Message):
    await msg.answer(
        "🎯 *Выбери категорию квестов:*",
        parse_mode="Markdown",
        reply_markup=categories_keyboard()
    )

@dp.callback_query(F.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    category = call.data.replace("cat_", "")
    user_id = call.from_user.id
    today = date.today().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT quest_id FROM daily_quests WHERE user_id=? AND quest_date=?",
            (user_id, today)
        ) as cur:
            rows = await cur.fetchall()
    done_quests = [r[0] for r in rows]

    await call.message.edit_text(
        f"{CATEGORIES[category]}\n\n✅ — уже выполнено сегодня",
        reply_markup=quests_keyboard(category, done_quests)
    )

@dp.callback_query(F.data == "back_categories")
async def back_to_categories(call: types.CallbackQuery):
    await call.message.edit_text(
        "🎯 *Выбери категорию квестов:*",
        parse_mode="Markdown",
        reply_markup=categories_keyboard()
    )

@dp.callback_query(F.data.startswith("quest_"))
async def complete_quest(call: types.CallbackQuery):
    quest_id = call.data.replace("quest_", "")
    user_id = call.from_user.id

    if await is_quest_done_today(user_id, quest_id):
        await call.answer("⚠️ Уже выполнено сегодня!", show_alert=True)
        return

    q = QUESTS[quest_id]
    user = await get_user(user_id)
    user, streak_msg, level_up_msg, earned = await award_xp(
        user, q["xp"], q["stat"], q["stat_val"]
    )
    await mark_quest_done(user_id, quest_id)

    stat_names = {
        "intel":    "🧠 Интеллект",
        "strength": "💪 Сила",
        "agility":  "⚡ Ловкость",
        "finance":  "💰 Финансы",
        "health":   "❤️ Здоровье",
    }

    response = f"{q['emoji']} *Квест выполнен!*\n\n{streak_msg}⚡ +{earned} XP"
    if q["stat_val"] > 0:
        response += f" | {stat_names[q['stat']]} +{q['stat_val']}"
    if level_up_msg:
        response += level_up_msg

    await call.answer()
    await call.message.answer(response, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("done_"))
async def already_done(call: types.CallbackQuery):
    await call.answer("⚠️ Уже выполнено сегодня! Возвращайся завтра 💪", show_alert=True)

# ─────────────────────────────────────────
# ⏰ НАПОМИНАНИЯ
# ─────────────────────────────────────────

async def send_morning_reminder():
    for uid in await get_all_user_ids():
        try:
            await bot.send_message(uid,
                "☀️ *Новый день — новые квесты!*\n\nНажми 🎯 Квесты чтобы начать прокачку.\nНе прерывай стрик! 🔥",
                parse_mode="Markdown")
        except Exception:
            pass

async def send_evening_reminder():
    for uid in await get_all_user_ids():
        try:
            await bot.send_message(uid,
                "🌙 *Итоги дня*\n\nНе забудь отметить выполненные квесты!\nНажми 🎯 Квесты 👇",
                parse_mode="Markdown")
        except Exception:
            pass

async def scheduler():
    while True:
        now = datetime.now()
        if (now.hour, now.minute) == (8, 0):
            await send_morning_reminder()
        elif (now.hour, now.minute) == (21, 0):
            await send_evening_reminder()
        await asyncio.sleep(60)

# ─────────────────────────────────────────
# ▶️ ЗАПУСК
# ─────────────────────────────────────────

async def main():
    await init_db()
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler()
    )

if __name__ == "__main__":
    asyncio.run(main())
