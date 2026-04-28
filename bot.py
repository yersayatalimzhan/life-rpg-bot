import asyncio
import aiosqlite
import logging
import random
import io
from datetime import datetime, date
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

TOKEN = "8754965889:AAEC6SYJqvhmouuQ_6fUrFc8vTwqQYT18iE"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()
DB_PATH = "game.db"

# ══════════════════════════════════════════
# 📦 ДАННЫЕ
# ══════════════════════════════════════════

QUESTS = {
    "intel_read10":    {"name": "📖 Читал 10 стр.",           "xp": 5,  "stat": "intel",    "stat_val": 1, "emoji": "📖"},
    "intel_course":    {"name": "📚 Урок курса",               "xp": 10, "stat": "intel",    "stat_val": 1, "emoji": "📚"},
    "intel_english":   {"name": "🇬🇧 Урок английского",       "xp": 8,  "stat": "intel",    "stat_val": 1, "emoji": "🇬🇧"},
    "intel_video":     {"name": "🎥 Обучающее видео",          "xp": 2,  "stat": "intel",    "stat_val": 1, "emoji": "🎥"},
    "intel_podcast":   {"name": "🎙 Образовательный подкаст",  "xp": 3,  "stat": "intel",    "stat_val": 0, "emoji": "🎙"},
    "intel_notes":     {"name": "✍️ Конспект / заметки",      "xp": 5,  "stat": "intel",    "stat_val": 1, "emoji": "✍️"},
    "strength_gym":    {"name": "🏋️ Тренировка в зале",      "xp": 15, "stat": "strength", "stat_val": 2, "emoji": "🏋️"},
    "strength_home":   {"name": "🤸 Домашняя тренировка",     "xp": 10, "stat": "strength", "stat_val": 1, "emoji": "🤸"},
    "strength_box":    {"name": "🥊 Бокс",                    "xp": 15, "stat": "strength", "stat_val": 2, "emoji": "🥊"},
    "strength_exp":    {"name": "💪 Эспандер",                "xp": 2,  "stat": "strength", "stat_val": 0, "emoji": "💪"},
    "strength_push":   {"name": "⬆️ Отжимания 30+",           "xp": 5,  "stat": "strength", "stat_val": 1, "emoji": "⬆️"},
    "agility_run":     {"name": "🏃 Пробежка",                "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "🏃"},
    "agility_stretch": {"name": "🧘 Растяжка",                "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "🧘"},
    "agility_rope":    {"name": "⚡ Скакалка",                "xp": 5,  "stat": "agility",  "stat_val": 1, "emoji": "⚡"},
    "agility_swim":    {"name": "🏊 Плавание",                "xp": 10, "stat": "agility",  "stat_val": 2, "emoji": "🏊"},
    "agility_bike":    {"name": "🚴 Велосипед",               "xp": 8,  "stat": "agility",  "stat_val": 1, "emoji": "🚴"},
    "finance_expenses":{"name": "📊 Посчитал расходы",        "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📊"},
    "finance_content": {"name": "📤 Публикация контента",     "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📤"},
    "finance_earn":    {"name": "💵 Доп. заработок",          "xp": 15, "stat": "finance",  "stat_val": 2, "emoji": "💵"},
    "finance_invest":  {"name": "📈 Читал про инвестиции",    "xp": 5,  "stat": "finance",  "stat_val": 1, "emoji": "📈"},
    "finance_plan":    {"name": "🗓 Финансовый план",         "xp": 8,  "stat": "finance",  "stat_val": 1, "emoji": "🗓"},
    "health_sleep":    {"name": "😴 Поспал 7-8 часов",        "xp": 10, "stat": "health",   "stat_val": 1, "emoji": "😴"},
    "health_nofast":   {"name": "🥗 Не ел фаст-фуд",         "xp": 2,  "stat": "health",   "stat_val": 0, "emoji": "🥗"},
    "health_snack":    {"name": "🍎 Полезный перекус",        "xp": 2,  "stat": "health",   "stat_val": 0, "emoji": "🍎"},
    "health_water":    {"name": "💧 Выпил 2л воды",           "xp": 3,  "stat": "health",   "stat_val": 0, "emoji": "💧"},
    "health_nophone":  {"name": "📵 Без телефона перед сном", "xp": 5,  "stat": "health",   "stat_val": 1, "emoji": "📵"},
    "health_meditate": {"name": "🧘 Медитация 10 мин",        "xp": 5,  "stat": "health",   "stat_val": 1, "emoji": "🧘"},
}

CATEGORIES = {
    "intel":    "🧠 Интеллект",
    "strength": "💪 Сила",
    "agility":  "⚡ Ловкость",
    "finance":  "💰 Финансы",
    "health":   "❤️ Здоровье",
}

STAT_NAMES = {
    "intel":    "🧠 Интеллект",
    "strength": "💪 Сила",
    "agility":  "⚡ Ловкость",
    "finance":  "💰 Финансы",
    "health":   "❤️ Здоровье",
}

CLASSES = {
    "warrior": {"name": "⚔️ Воин",     "bonus_stat": "strength", "bonus": 1},
    "mage":    {"name": "🧙 Маг",      "bonus_stat": "intel",    "bonus": 1},
    "trader":  {"name": "💼 Торговец", "bonus_stat": "finance",  "bonus": 1},
}

TITLES = [
    ("🏆 Легенда",   lambda u: all(u[s] >= 20 for s in ["intel","strength","agility","finance","health"])),
    ("📖 Читатель",  lambda u: u["intel"] >= 10),
    ("💪 Спортсмен", lambda u: u["strength"] >= 10),
    ("⚡ Атлет",     lambda u: u["agility"] >= 10),
    ("💰 Инвестор",  lambda u: u["finance"] >= 10),
    ("❤️ Здоровяк",  lambda u: u["health"] >= 10),
]

ACHIEVEMENTS = [
    ("🌟 Первый шаг",    "first_quest",  lambda u: u.get("total_quests",0) >= 1),
    ("🔥 Стрик 7 дней",  "streak_7",     lambda u: u["streak"] >= 7),
    ("🔥 Стрик 30 дней", "streak_30",    lambda u: u["streak"] >= 30),
    ("⚡ Ранг E",         "rank_e",       lambda u: u["level"] >= 3),
    ("⚡ Ранг D",         "rank_d",       lambda u: u["level"] >= 6),
    ("⚡ Ранг C",         "rank_c",       lambda u: u["level"] >= 10),
    ("⚡ Ранг B",         "rank_b",       lambda u: u["level"] >= 15),
    ("⚡ Ранг A",         "rank_a",       lambda u: u["level"] >= 21),
    ("👑 Ранг S",         "rank_s",       lambda u: u["level"] >= 28),
    ("🎯 10 квестов",     "quests_10",    lambda u: u.get("total_quests",0) >= 10),
    ("🎯 50 квестов",     "quests_50",    lambda u: u.get("total_quests",0) >= 50),
    ("🎯 100 квестов",    "quests_100",   lambda u: u.get("total_quests",0) >= 100),
    ("🧠 Интеллект 10",   "intel_10",     lambda u: u["intel"] >= 10),
    ("💪 Сила 10",        "strength_10",  lambda u: u["strength"] >= 10),
    ("⚡ Ловкость 10",    "agility_10",   lambda u: u["agility"] >= 10),
    ("💰 Финансы 10",     "finance_10",   lambda u: u["finance"] >= 10),
    ("❤️ Здоровье 10",    "health_10",    lambda u: u["health"] >= 10),
    ("🪙 Богач",          "coins_100",    lambda u: u.get("coins",0) >= 100),
    ("🛒 Покупатель",     "first_buy",    lambda u: u.get("total_buys",0) >= 1),
]

WEEKLY_BOSSES = [
    {"name": "💪 Неделя силы",     "desc": "Выполни 5 силовых тренировок", "stat": "strength", "target": 5,  "xp": 100},
    {"name": "🧠 Неделя знаний",   "desc": "Выполни 7 квестов обучения",   "stat": "intel",    "target": 7,  "xp": 100},
    {"name": "🏃 Неделя движения", "desc": "Выполни 5 квестов ловкости",   "stat": "agility",  "target": 5,  "xp": 100},
    {"name": "💰 Неделя финансов", "desc": "Выполни 5 финансовых квестов", "stat": "finance",  "target": 5,  "xp": 100},
    {"name": "❤️ Неделя здоровья", "desc": "Выполни 7 квестов здоровья",  "stat": "health",   "target": 7,  "xp": 100},
    {"name": "⚔️ Неделя воина",    "desc": "Выполни 15 любых квестов",    "stat": "any",      "target": 15, "xp": 150},
]

RANDOM_EVENTS = [
    {"name": "📜 Найден свиток мудрости!", "type": "bonus_xp",   "value": 20, "msg": "+20 XP всем!"},
    {"name": "⚡ Энергетическая буря!",    "type": "bonus_xp",   "value": 15, "msg": "+15 XP всем!"},
    {"name": "🌑 Тёмная неделя...",        "type": "penalty_xp", "value": 10, "msg": "-10 XP всем..."},
    {"name": "🌟 Благословение богов!",    "type": "bonus_xp",   "value": 30, "msg": "+30 XP всем!"},
    {"name": "🪙 Дождь монет!",            "type": "bonus_coins","value": 20, "msg": "+20 монет всем!"},
]

LEVEL_CHALLENGES = {
    5:  {"name": "100 отжиманий за неделю", "reward": "🍫 Купи себе шоколадку!",      "quest": "strength_push", "target": 4},
    10: {"name": "Прочитать 50 страниц",    "reward": "🎬 Сходи в кино!",             "quest": "intel_read10",  "target": 5},
    15: {"name": "Стрик 7 дней подряд",     "reward": "🍕 Закажи любимую еду!",       "quest": None,            "target": 7},
    20: {"name": "5 тренировок за неделю",  "reward": "👟 Купи новую экипировку!",    "quest": "strength_gym",  "target": 5},
    28: {"name": "Достичь ранга S",         "reward": "🎉 Ты заслужил большую личную награду!", "quest": None, "target": 1},
}

ITEMS = {
    "xp_boost":    {"name": "⚡ Буст XP",             "desc": "Даёт +20 XP сразу",           "price": 30,  "type": "boost"},
    "heal_streak": {"name": "🔥 Восстановление стрика","desc": "Возвращает стрик до 3",       "price": 25,  "type": "streak"},
    "coins_pack":  {"name": "🪙 Пачка монет",          "desc": "Даёт +15 монет",              "price": 20,  "type": "coins"},
    "xp_big":      {"name": "💎 Большой буст XP",      "desc": "Даёт +50 XP сразу",          "price": 70,  "type": "boost_big"},
    "stat_boost":  {"name": "📈 Буст характеристик",   "desc": "+1 ко всем характеристикам", "price": 80,  "type": "stat_all"},
}

# ══════════════════════════════════════════
# 📦 БАЗА ДАННЫХ
# ══════════════════════════════════════════

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id           INTEGER PRIMARY KEY,
                name         TEXT    DEFAULT '',
                class        TEXT    DEFAULT '',
                xp           INTEGER DEFAULT 0,
                level        INTEGER DEFAULT 1,
                intel        INTEGER DEFAULT 0,
                strength     INTEGER DEFAULT 0,
                agility      INTEGER DEFAULT 0,
                finance      INTEGER DEFAULT 0,
                health       INTEGER DEFAULT 0,
                streak       INTEGER DEFAULT 0,
                last_active  TEXT    DEFAULT '',
                total_quests INTEGER DEFAULT 0,
                week_xp      INTEGER DEFAULT 0,
                week_start   TEXT    DEFAULT '',
                coins        INTEGER DEFAULT 0,
                total_buys   INTEGER DEFAULT 0
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                user_id INTEGER,
                ach_id  TEXT,
                PRIMARY KEY (user_id, ach_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS weekly_boss (
                week       TEXT PRIMARY KEY,
                boss_index INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS boss_progress (
                user_id INTEGER,
                week    TEXT,
                count   INTEGER DEFAULT 0,
                done    INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, week)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                user_id INTEGER,
                item_id TEXT,
                count   INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, item_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_shop (
                date    TEXT,
                item_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_quests (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name    TEXT,
                done_today INTEGER DEFAULT 0,
                last_done  TEXT DEFAULT ''
            )
        """)
        # Миграции
        migrations = [
            "ALTER TABLE users ADD COLUMN name TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN class TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN total_quests INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN week_xp INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN week_start TEXT DEFAULT ''",
            "ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN total_buys INTEGER DEFAULT 0",
        ]
        for m in migrations:
            try:
                await db.execute(m)
            except Exception:
                pass
        await db.commit()

async def get_user(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id=?", (user_id,)) as cur:
            row = await cur.fetchone()
        if row is None:
            await db.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
            await db.commit()
            return {"id": user_id, "name": "", "class": "", "xp": 0, "level": 1,
                    "intel": 0, "strength": 0, "agility": 0, "finance": 0,
                    "health": 0, "streak": 0, "last_active": "",
                    "total_quests": 0, "week_xp": 0, "week_start": "",
                    "coins": 0, "total_buys": 0}
        return dict(row)

async def save_user(user: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET name=?, class=?, xp=?, level=?, intel=?, strength=?,
            agility=?, finance=?, health=?, streak=?, last_active=?,
            total_quests=?, week_xp=?, week_start=?, coins=?, total_buys=?
            WHERE id=?
        """, (user.get("name",""), user.get("class",""), user["xp"], user["level"],
              user["intel"], user["strength"], user["agility"], user["finance"],
              user["health"], user["streak"], user["last_active"],
              user.get("total_quests",0), user.get("week_xp",0),
              user.get("week_start",""), user.get("coins",0),
              user.get("total_buys",0), user["id"]))
        await db.commit()

async def get_all_users() -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users") as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

async def get_all_user_ids() -> list:
    users = await get_all_users()
    return [u["id"] for u in users]

# ── Квесты ────────────────────────────────

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
        await db.execute("INSERT OR IGNORE INTO daily_quests VALUES (?,?,?)", (user_id, quest_id, today))
        await db.commit()

async def get_today_quests(user_id: int) -> list:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT quest_id FROM daily_quests WHERE user_id=? AND quest_date=?",
            (user_id, today)
        ) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]

async def had_activity_yesterday(user_id: int) -> bool:
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM daily_quests WHERE user_id=? AND quest_date=?",
            (user_id, yesterday)
        ) as cur:
            return await cur.fetchone() is not None

# ── Достижения ────────────────────────────

async def get_achievements(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ach_id FROM achievements WHERE user_id=?", (user_id,)) as cur:
            rows = await cur.fetchall()
    return [r[0] for r in rows]

async def add_achievement(user_id: int, ach_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO achievements VALUES (?,?)", (user_id, ach_id))
        await db.commit()

async def check_achievements(user_id: int, user: dict) -> list:
    existing = await get_achievements(user_id)
    new_achs = []
    for name, ach_id, check in ACHIEVEMENTS:
        if ach_id not in existing and check(user):
            await add_achievement(user_id, ach_id)
            new_achs.append(name)
    return new_achs

# ── Босс недели ───────────────────────────

async def get_current_boss() -> dict | None:
    week = date.today().isocalendar()
    week_key = f"{week[0]}-W{week[1]}"
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT boss_index FROM weekly_boss WHERE week=?", (week_key,)) as cur:
            row = await cur.fetchone()
    if row is None:
        return None
    return {**WEEKLY_BOSSES[row[0]], "week": week_key}

async def get_boss_progress(user_id: int, week: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT count, done FROM boss_progress WHERE user_id=? AND week=?",
            (user_id, week)
        ) as cur:
            row = await cur.fetchone()
    if row is None:
        return {"count": 0, "done": 0}
    return {"count": row[0], "done": row[1]}

async def update_boss_progress(user_id: int, week: str, count: int, done: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO boss_progress VALUES (?,?,?,?)",
            (user_id, week, count, done)
        )
        await db.commit()

# ── Инвентарь ─────────────────────────────

async def add_item(user_id: int, item_id: str, count: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO inventory (user_id, item_id, count) VALUES (?,?,?)
            ON CONFLICT(user_id, item_id) DO UPDATE SET count = count + ?
        """, (user_id, item_id, count, count))
        await db.commit()

async def get_inventory(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT item_id, count FROM inventory WHERE user_id=?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
    return {r[0]: r[1] for r in rows}

async def remove_item(user_id: int, item_id: str, count: int = 1):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE inventory SET count = count - ? WHERE user_id=? AND item_id=?",
            (count, user_id, item_id)
        )
        await db.execute(
            "DELETE FROM inventory WHERE user_id=? AND item_id=? AND count <= 0",
            (user_id, item_id)
        )
        await db.commit()

# ── Магазин ───────────────────────────────

async def generate_daily_shop():
    today = date.today().isoformat()
    items = random.sample(list(ITEMS.keys()), k=min(3, len(ITEMS)))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM daily_shop WHERE date=?", (today,))
        for item in items:
            await db.execute("INSERT INTO daily_shop VALUES (?,?)", (today, item))
        await db.commit()

async def get_daily_shop() -> list:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT item_id FROM daily_shop WHERE date=?", (today,)) as cur:
            rows = await cur.fetchall()
    if not rows:
        await generate_daily_shop()
        return await get_daily_shop()
    return [r[0] for r in rows]

# ── Свои квесты ───────────────────────────

async def get_custom_quests(user_id: int) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM custom_quests WHERE user_id=?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]

async def add_custom_quest(user_id: int, name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO custom_quests (user_id, name) VALUES (?,?)", (user_id, name)
        )
        await db.commit()

async def delete_custom_quest(quest_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM custom_quests WHERE id=? AND user_id=?", (quest_id, user_id)
        )
        await db.commit()

async def is_custom_quest_done_today(quest_id: int) -> bool:
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT last_done FROM custom_quests WHERE id=?", (quest_id,)
        ) as cur:
            row = await cur.fetchone()
    return row and row[0] == today

async def mark_custom_quest_done(quest_id: int):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE custom_quests SET last_done=? WHERE id=?", (today, quest_id)
        )
        await db.commit()

# ══════════════════════════════════════════
# 🎮 ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ══════════════════════════════════════════

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

def get_title(user: dict) -> str:
    for title, check in TITLES:
        if check(user):
            return title
    return "🌱 Новичок"

def progress_bar(current: int, total: int, length: int = 10) -> str:
    filled = int((current / max(total, 1)) * length)
    return "🟩" * filled + "⬜" * (length - filled)

def update_streak(user: dict) -> dict:
    today = date.today().isoformat()
    last = user.get("last_active", "")
    if last == today:
        return user
    yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
    user["streak"] = (user["streak"] + 1) if last == yesterday else 1
    user["last_active"] = today
    return user

def get_multiplier(user: dict) -> tuple:
    now = datetime.now()
    mult, msg = 1.0, ""
    if now.weekday() >= 5:
        mult = max(mult, 1.5)
        msg = "🎉 Выходной день — ×1.5 XP!\n"
    if user["streak"] >= 7:
        mult = max(mult, 2.0)
        msg = "🔥 Стрик 7+ дней — ×2 XP!\n"
    elif user["streak"] >= 3:
        mult = max(mult, 1.5)
        msg = f"🔥 Стрик {user['streak']} дней — ×1.5 XP!\n"
    return mult, msg

def update_week_xp(user: dict, earned: int) -> dict:
    week = date.today().isocalendar()
    week_key = f"{week[0]}-W{week[1]}"
    if user.get("week_start","") != week_key:
        user["week_xp"] = 0
        user["week_start"] = week_key
    user["week_xp"] = user.get("week_xp", 0) + earned
    return user

async def award_xp(user: dict, xp: int, stat: str, stat_val: int):
    user = update_streak(user)
    mult, streak_msg = get_multiplier(user)
    earned = int(xp * mult)
    coins_earned = max(1, earned // 2)

    user["xp"] += earned
    user["coins"] = user.get("coins", 0) + coins_earned
    user["total_quests"] = user.get("total_quests", 0) + 1
    user = update_week_xp(user, earned)

    if stat in user:
        user[stat] += stat_val
    # Бонус класса
    cls = user.get("class", "")
    if cls in CLASSES and CLASSES[cls]["bonus_stat"] == stat and stat_val > 0:
        user[stat] += 1

    level_up_msg = ""
    while user["xp"] >= xp_for_next_level(user["level"]):
        user["xp"] -= xp_for_next_level(user["level"])
        user["level"] += 1
        level_up_msg += f"\n🎉 *LEVEL UP!* Уровень {user['level']} | Ранг {get_rank(user['level'])}"
        if user["level"] in LEVEL_CHALLENGES:
            ch = LEVEL_CHALLENGES[user["level"]]
            level_up_msg += f"\n🔓 Челлендж разблокирован: *{ch['name']}*\n🎁 Награда: {ch['reward']}"

    await save_user(user)
    return user, streak_msg, level_up_msg, earned, coins_earned

# ══════════════════════════════════════════
# 🖼 КАРТОЧКА ПЕРСОНАЖА
# ══════════════════════════════════════════

def generate_card(user: dict) -> bytes | None:
    if not PIL_AVAILABLE:
        return None
    W, H = 600, 360
    img = Image.new("RGB", (W, H), color=(18, 18, 28))
    draw = ImageDraw.Draw(img)
    for i in range(H):
        r = int(18 + (30-18)*i/H)
        g = int(18 + (20-18)*i/H)
        b = int(28 + (50-28)*i/H)
        draw.line([(0, i), (W, i)], fill=(r, g, b))
    draw.rectangle([10, 10, W-10, H-10], outline=(80, 60, 180), width=2)
    draw.rectangle([14, 14, W-14, H-14], outline=(40, 30, 90), width=1)
    font_paths_bold = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    font_paths_regular = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    fb = fm = fs = ImageFont.load_default()
    for path in font_paths_bold:
        try:
            fb = ImageFont.truetype(path, 26)
            fm = ImageFont.truetype(path, 18)
            break
        except Exception:
            continue
    for path in font_paths_regular:
        try:
            fs = ImageFont.truetype(path, 14)
            break
        except Exception:
            continue

    rank = get_rank(user["level"])
    title = get_title(user)
    name = user.get("name") or "Герой"
    cls_name = CLASSES.get(user.get("class",""), {}).get("name","")
    draw.text((30, 28), name, font=fb, fill=(220, 210, 255))
    draw.text((30, 62), f"{cls_name}  |  {title}", font=fs, fill=(160, 140, 220))
    rank_colors = {"S":(255,215,0),"A":(200,100,255),"B":(100,180,255),
                   "C":(100,220,100),"D":(255,180,50),"E":(180,180,180),"F":(120,120,120)}
    draw.text((W-120, 28), f"Ур. {user['level']}", font=fm, fill=(200,200,255))
    draw.text((W-70,  58), f"[{rank}]", font=fb, fill=rank_colors.get(rank,(200,200,200)))
    needed = xp_for_next_level(user["level"])
    xp_pct = user["xp"] / needed
    draw.text((30, 100), f"XP: {user['xp']} / {needed}", font=fs, fill=(160,160,200))
    bx, by, bw, bh = 30, 118, W-60, 14
    draw.rectangle([bx, by, bx+bw, by+bh], fill=(40,35,70), outline=(70,60,120))
    draw.rectangle([bx, by, bx+int(bw*xp_pct), by+bh], fill=(100,80,220))
    stats = [
        ("Интеллект", user["intel"],    (120,180,255)),
        ("Сила",      user["strength"], (255,120,120)),
        ("Ловкость",  user["agility"],  (120,255,180)),
        ("Финансы",   user["finance"],  (255,220,80)),
        ("Здоровье",  user["health"],   (255,120,200)),
    ]
    sx, sy = 30, 152
    for i,(sname,sval,scolor) in enumerate(stats):
        x = sx + (i % 3)*185
        y = sy + (i // 3)*72
        draw.text((x, y),    sname, font=fs, fill=(160,160,200))
        draw.text((x, y+18), str(sval), font=fm, fill=scolor)
        fw = min(int(160*sval/max(sval,50)),160)
        draw.rectangle([x, y+42, x+160, y+50], fill=(40,35,60), outline=(60,55,90))
        draw.rectangle([x, y+42, x+fw,  y+50], fill=scolor)
    draw.text((30,   H-42), f"Стрик: {user['streak']} дней",        font=fs, fill=(200,180,255))
    draw.text((230,  H-42), f"Квестов: {user.get('total_quests',0)}", font=fs, fill=(180,180,220))
    draw.text((W-160,H-42), f"🪙 {user.get('coins',0)} монет",       font=fs, fill=(255,220,100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# ══════════════════════════════════════════
# 🎛️ КЛАВИАТУРЫ
# ══════════════════════════════════════════

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Статы"),       KeyboardButton(text="🎯 Квесты")],
            [KeyboardButton(text="🏆 Лидеры"),      KeyboardButton(text="🎖 Достижения")],
            [KeyboardButton(text="👤 Профиль"),     KeyboardButton(text="⚔️ Босс недели")],
            [KeyboardButton(text="🛒 Магазин"),     KeyboardButton(text="🎒 Инвентарь")],
            [KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )

def categories_kb():
    buttons = []
    row = []
    for cat_id, cat_name in CATEGORIES.items():
        row.append(InlineKeyboardButton(text=cat_name, callback_data=f"cat_{cat_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="✏️ Мои квесты", callback_data="cat_custom")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quests_kb(category: str, done_quests: list):
    buttons = []
    for qid, q in QUESTS.items():
        if q["stat"] == category:
            if qid in done_quests:
                label = f"✅ {q['name']}"
                cb = f"done_{qid}"
            else:
                label = f"{q['name']} +{q['xp']}XP"
                cb = f"quest_{qid}"
            buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def class_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Воин (+Сила)",        callback_data="class_warrior")],
        [InlineKeyboardButton(text="🧙 Маг (+Интеллект)",    callback_data="class_mage")],
        [InlineKeyboardButton(text="💼 Торговец (+Финансы)", callback_data="class_trader")],
    ])

# ══════════════════════════════════════════
# ⚡ АНИМАЦИЯ
# ══════════════════════════════════════════

async def animated_xp(message: types.Message, final_text: str):
    msg = await message.answer("⏳ Выполняем квест...")
    for i in range(3):
        await asyncio.sleep(0.4)
        await msg.edit_text(f"⚡ Начисление опыта{'.' * (i+1)}")
    await asyncio.sleep(0.4)
    await msg.edit_text(final_text, parse_mode="Markdown")

# ══════════════════════════════════════════
# 🚀 ХЕНДЛЕРЫ
# ══════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user = await get_user(msg.from_user.id)
    if user.get("class"):
        await msg.answer("⚔️ *Добро пожаловать обратно!*\nИспользуй кнопки ниже 👇",
                         parse_mode="Markdown", reply_markup=main_menu_kb())
        return
    name = msg.from_user.first_name or "Герой"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET name=? WHERE id=?", (name, msg.from_user.id))
        await db.commit()
    await msg.answer(
        f"⚔️ *Добро пожаловать в Life RPG, {name}!*\n\n"
        "Выполняй реальные задачи — прокачивай персонажа.\n\n"
        "Выбери свой класс:",
        parse_mode="Markdown",
        reply_markup=class_kb()
    )

@dp.callback_query(F.data.startswith("class_"))
async def choose_class(call: types.CallbackQuery):
    cls = call.data.replace("class_", "")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET class=? WHERE id=?", (cls, call.from_user.id))
        await db.commit()
    cls_name = CLASSES[cls]["name"]
    await call.message.edit_text(f"✅ Класс: *{cls_name}*\n\nОтлично! Начнём прокачку!", parse_mode="Markdown")
    await call.message.answer("Используй кнопки ниже 👇", reply_markup=main_menu_kb())

@dp.message(Command("setname"))
async def set_name(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Напиши: `/setname ТвоёИмя`", parse_mode="Markdown")
        return
    name = parts[1][:30]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET name=? WHERE id=?", (name, msg.from_user.id))
        await db.commit()
    await msg.answer(f"✅ Имя изменено на *{name}*", parse_mode="Markdown")

@dp.message(Command("today"))
async def show_today(msg: types.Message):
    done = await get_today_quests(msg.from_user.id)
    custom = await get_custom_quests(msg.from_user.id)
    today = date.today().isoformat()
    custom_done = [q for q in custom if q["last_done"] == today]
    if not done and not custom_done:
        await msg.answer("📋 Сегодня ещё ничего не выполнено. Жми 🎯 Квесты!")
        return
    total_xp = sum(QUESTS[qid]["xp"] for qid in done if qid in QUESTS)
    total_xp += len(custom_done) * 2
    text = "📋 *Сегодня выполнено:*\n\n"
    for qid in done:
        if qid in QUESTS:
            q = QUESTS[qid]
            text += f"✅ {q['name']} +{q['xp']}XP\n"
    for q in custom_done:
        text += f"✅ ✏️ {q['name']} +2XP\n"
    text += f"\n⚡ Итого: {total_xp} XP"
    await msg.answer(text, parse_mode="Markdown")

# ── Статы и профиль ───────────────────────

@dp.message(F.text == "📊 Статы")
async def show_stats(msg: types.Message):
    user = await get_user(msg.from_user.id)
    level = user["level"]
    needed = xp_for_next_level(level)
    rank = get_rank(level)
    bar = progress_bar(user["xp"], needed)
    streak_icon = "🔥" if user["streak"] >= 3 else "📅"
    title = get_title(user)
    cls_name = CLASSES.get(user.get("class",""), {}).get("name","")
    await msg.answer(
        f"📊 *Твой персонаж*\n\n"
        f"👤 {user.get('name','Герой')} | {cls_name}\n"
        f"🎭 {title}\n"
        f"🏅 Уровень: {level} | Ранг: {rank}\n"
        f"⚡ XP: {user['xp']}/{needed}\n"
        f"[{bar}]\n\n"
        f"🧠 Интеллект: {user['intel']}\n"
        f"💪 Сила: {user['strength']}\n"
        f"⚡ Ловкость: {user['agility']}\n"
        f"💰 Финансы: {user['finance']}\n"
        f"❤️ Здоровье: {user['health']}\n\n"
        f"🪙 Монеты: {user.get('coins',0)}\n"
        f"{streak_icon} Стрик: {user['streak']} дней\n"
        f"🎯 Квестов всего: {user.get('total_quests',0)}",
        parse_mode="Markdown"
    )

@dp.message(F.text == "👤 Профиль")
async def show_profile(msg: types.Message):
    user = await get_user(msg.from_user.id)
    card = generate_card(user)
    if card:
        await msg.answer_photo(
            photo=types.BufferedInputFile(card, filename="profile.png"),
            caption=f"👤 *{user.get('name','Герой')}* | {get_title(user)}",
            parse_mode="Markdown"
        )
    else:
        await show_stats(msg)

# ── Квесты ────────────────────────────────

@dp.message(F.text == "🎯 Квесты")
async def show_quests(msg: types.Message):
    await msg.answer("🎯 *Выбери категорию:*", parse_mode="Markdown", reply_markup=categories_kb())

@dp.callback_query(F.data.startswith("cat_"))
async def show_category(call: types.CallbackQuery):
    category = call.data.replace("cat_", "")
    if category == "custom":
        quests = await get_custom_quests(call.from_user.id)
        today = date.today().isoformat()
        if not quests:
            await call.message.edit_text(
                "✏️ *Мои квесты*\n\nУ тебя ещё нет своих квестов.\n\nДобавь через ⚙️ Настройки",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="back_categories")]
                ])
            )
            return
        buttons = []
        for q in quests:
            done = q["last_done"] == today
            label = f"✅ {q['name']}" if done else f"✏️ {q['name']} +2XP"
            cb = f"customdone_{q['id']}" if not done else f"alreadydone_custom"
            buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_categories")])
        await call.message.edit_text(
            "✏️ *Мои квесты* (+2 XP за каждый)\n\n✅ — уже выполнено сегодня",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        return
    done = await get_today_quests(call.from_user.id)
    await call.message.edit_text(
        f"{CATEGORIES[category]}\n\n✅ — уже выполнено сегодня",
        reply_markup=quests_kb(category, done)
    )

@dp.callback_query(F.data == "back_categories")
async def back_categories(call: types.CallbackQuery):
    await call.message.edit_text("🎯 *Выбери категорию:*", parse_mode="Markdown", reply_markup=categories_kb())

@dp.callback_query(F.data.startswith("quest_"))
async def complete_quest(call: types.CallbackQuery):
    quest_id = call.data.replace("quest_", "")
    user_id = call.from_user.id
    if await is_quest_done_today(user_id, quest_id):
        await call.answer("⚠️ Уже выполнено сегодня!", show_alert=True)
        return
    q = QUESTS[quest_id]
    user = await get_user(user_id)
    user, streak_msg, level_up_msg, earned, coins_earned = await award_xp(
        user, q["xp"], q["stat"], q["stat_val"]
    )
    await mark_quest_done(user_id, quest_id)

    # Прогресс босса
    boss = await get_current_boss()
    boss_msg = ""
    if boss:
        progress = await get_boss_progress(user_id, boss["week"])
        if not progress["done"]:
            relevant = boss["stat"] == "any" or boss["stat"] == q["stat"]
            if relevant:
                new_count = progress["count"] + 1
                boss_done = new_count >= boss["target"]
                await update_boss_progress(user_id, boss["week"], new_count, 1 if boss_done else 0)
                if boss_done:
                    user["xp"] += boss["xp"]
                    user["coins"] = user.get("coins",0) + 50
                    await save_user(user)
                    boss_msg = f"\n\n⚔️ *БОСС ПОВЕРЖЕН!* +{boss['xp']} XP +50🪙 🏆"
                else:
                    boss_msg = f"\n⚔️ Босс: {new_count}/{boss['target']}"

    new_achs = await check_achievements(user_id, user)
    ach_msg = ("\n\n🎖 *Новые достижения:*\n" + "\n".join(new_achs)) if new_achs else ""

    response = (
        f"{q['emoji']} *Квест выполнен!*\n\n"
        f"{streak_msg}"
        f"⚡ +{earned} XP  🪙 +{coins_earned} монет"
    )
    if q["stat_val"] > 0:
        response += f"  {STAT_NAMES[q['stat']]} +{q['stat_val']}"
    response += level_up_msg + boss_msg + ach_msg

    await call.answer()
    await animated_xp(call.message, response)

@dp.callback_query(F.data.startswith("customdone_"))
async def complete_custom_quest(call: types.CallbackQuery):
    quest_id = int(call.data.replace("customdone_", ""))
    if await is_custom_quest_done_today(quest_id):
        await call.answer("⚠️ Уже выполнено сегодня!", show_alert=True)
        return
    user = await get_user(call.from_user.id)
    user, streak_msg, level_up_msg, earned, coins_earned = await award_xp(user, 2, "intel", 0)
    await mark_custom_quest_done(quest_id)
    new_achs = await check_achievements(call.from_user.id, user)
    ach_msg = ("\n\n🎖 *Новые достижения:*\n" + "\n".join(new_achs)) if new_achs else ""
    response = (
        f"✏️ *Квест выполнен!*\n\n"
        f"{streak_msg}"
        f"⚡ +{earned} XP  🪙 +{coins_earned} монет"
        + level_up_msg + ach_msg
    )
    await call.answer()
    await animated_xp(call.message, response)

@dp.callback_query(F.data == "alreadydone_custom")
async def already_done_custom(call: types.CallbackQuery):
    await call.answer("⚠️ Уже выполнено сегодня! Возвращайся завтра 💪", show_alert=True)

@dp.callback_query(F.data.startswith("done_"))
async def already_done(call: types.CallbackQuery):
    await call.answer("⚠️ Уже выполнено сегодня! Возвращайся завтра 💪", show_alert=True)

# ── Лидерборд ─────────────────────────────

@dp.message(F.text == "🏆 Лидеры")
async def show_leaderboard(msg: types.Message):
    users = await get_all_users()
    if not users:
        await msg.answer("Пока нет игроков!")
        return
    top_all = sorted(users, key=lambda u: (u["level"], u["xp"]), reverse=True)[:10]
    week = date.today().isocalendar()
    week_key = f"{week[0]}-W{week[1]}"
    top_week = sorted(
        [u for u in users if u.get("week_start") == week_key],
        key=lambda u: u.get("week_xp", 0), reverse=True
    )[:5]
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 *Таблица лидеров*\n\n*Топ всех времён:*\n"
    for i, u in enumerate(top_all):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = u.get("name") or "Герой"
        rank = get_rank(u["level"])
        mark = " ◀️" if u["id"] == msg.from_user.id else ""
        text += f"{medal} {name} — Ур.{u['level']} [{rank}]{mark}\n"
    if top_week:
        text += "\n*Топ недели по XP:*\n"
        for i, u in enumerate(top_week):
            medal = medals[i] if i < 3 else f"{i+1}."
            name = u.get("name") or "Герой"
            mark = " ◀️" if u["id"] == msg.from_user.id else ""
            text += f"{medal} {name} — {u.get('week_xp',0)} XP{mark}\n"
    await msg.answer(text, parse_mode="Markdown")

# ── Достижения ────────────────────────────

@dp.message(F.text == "🎖 Достижения")
async def show_achievements(msg: types.Message):
    earned = await get_achievements(msg.from_user.id)
    text = "🎖 *Достижения*\n\n"
    for name, ach_id, _ in ACHIEVEMENTS:
        icon = "✅" if ach_id in earned else "🔒"
        text += f"{icon} {name}\n"
    await msg.answer(text, parse_mode="Markdown")

# ── Босс недели ───────────────────────────

@dp.message(F.text == "⚔️ Босс недели")
async def show_boss(msg: types.Message):
    boss = await get_current_boss()
    if not boss:
        await msg.answer("⚔️ Босс появится в понедельник!")
        return
    progress = await get_boss_progress(msg.from_user.id, boss["week"])
    bar = progress_bar(progress["count"], boss["target"])
    status = "✅ ПОБЕДА!" if progress["done"] else f"{progress['count']}/{boss['target']}"
    await msg.answer(
        f"⚔️ *{boss['name']}*\n\n"
        f"📋 {boss['desc']}\n"
        f"🏆 Награда: +{boss['xp']} XP + 50🪙\n\n"
        f"Прогресс: [{bar}] {status}",
        parse_mode="Markdown"
    )

# ── Магазин ───────────────────────────────

@dp.message(F.text == "🛒 Магазин")
async def shop(msg: types.Message):
    user = await get_user(msg.from_user.id)
    shop_items = await get_daily_shop()
    text = f"🛒 *Магазин* (обновляется каждый день)\n\n🪙 У тебя: {user.get('coins',0)} монет\n\n"
    buttons = []
    for item_id in shop_items:
        item = ITEMS.get(item_id)
        if not item:
            continue
        can_buy = user.get("coins",0) >= item["price"]
        text += f"{item['name']}\n_{item['desc']}_ — {item['price']}🪙\n\n"
        label = f"Купить {item['name']} ({item['price']}🪙)" if can_buy else f"❌ {item['name']} ({item['price']}🪙)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"buy_{item_id}")])
    await msg.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("buy_"))
async def buy_item(call: types.CallbackQuery):
    item_id = call.data.replace("buy_", "")
    item = ITEMS.get(item_id)
    if not item:
        await call.answer("❌ Предмет не найден", show_alert=True)
        return
    user = await get_user(call.from_user.id)
    if user.get("coins",0) < item["price"]:
        need = item["price"] - user.get("coins",0)
        await call.answer(f"❌ Не хватает {need}🪙", show_alert=True)
        return
    user["coins"] -= item["price"]
    user["total_buys"] = user.get("total_buys",0) + 1
    await add_item(call.from_user.id, item_id, 1)
    await save_user(user)
    new_achs = await check_achievements(call.from_user.id, user)
    ach_msg = ("\n🎖 " + ", ".join(new_achs)) if new_achs else ""
    await call.answer("✅ Куплено!", show_alert=True)
    await call.message.answer(
        f"🎉 Куплено: *{item['name']}*\n"
        f"🪙 Осталось монет: {user.get('coins',0)}\n"
        f"Используй в 🎒 Инвентарь{ach_msg}",
        parse_mode="Markdown"
    )

# ── Инвентарь ─────────────────────────────

@dp.message(F.text == "🎒 Инвентарь")
async def show_inventory(msg: types.Message):
    inv = await get_inventory(msg.from_user.id)
    if not inv:
        await msg.answer("🎒 Инвентарь пуст\n\nКупи что-нибудь в 🛒 Магазин!")
        return
    text = "🎒 *Твой инвентарь:*\n\n"
    buttons = []
    for item_id, count in inv.items():
        item = ITEMS.get(item_id)
        if not item:
            continue
        text += f"{item['name']} ×{count}\n_{item['desc']}_\n\n"
        buttons.append([InlineKeyboardButton(
            text=f"Использовать {item['name']}",
            callback_data=f"use_{item_id}"
        )])
    await msg.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("use_"))
async def use_item(call: types.CallbackQuery):
    item_id = call.data.replace("use_", "")
    user = await get_user(call.from_user.id)
    inv = await get_inventory(call.from_user.id)
    if item_id not in inv:
        await call.answer("❌ Предмета нет в инвентаре", show_alert=True)
        return
    item = ITEMS[item_id]
    result_msg = ""
    if item["type"] == "streak":
        user["streak"] = max(user["streak"], 3)
        result_msg = "🔥 Стрик восстановлен до 3!"
    elif item["type"] == "boost":
        user["xp"] += 20
        result_msg = "⚡ +20 XP получено!"
    elif item["type"] == "boost_big":
        user["xp"] += 50
        result_msg = "💎 +50 XP получено!"
    elif item["type"] == "coins":
        user["coins"] = user.get("coins",0) + 15
        result_msg = "🪙 +15 монет получено!"
    elif item["type"] == "stat_all":
        for s in ["intel","strength","agility","finance","health"]:
            user[s] += 1
        result_msg = "📈 +1 ко всем характеристикам!"
    await save_user(user)
    await remove_item(call.from_user.id, item_id, 1)
    await call.answer("✅ Использовано!", show_alert=True)
    await call.message.answer(f"✅ *{item['name']}* использован!\n{result_msg}", parse_mode="Markdown")

# ── Настройки / Свои квесты ───────────────

@dp.message(F.text == "⚙️ Настройки")
async def show_settings(msg: types.Message):
    quests = await get_custom_quests(msg.from_user.id)
    text = "⚙️ *Настройки*\n\n"
    text += "✏️ *Мои квесты* (+2 XP каждый, 1 раз в день)\n\n"
    buttons = []
    if quests:
        for q in quests:
            text += f"• {q['name']}\n"
            buttons.append([InlineKeyboardButton(
                text=f"🗑 Удалить: {q['name']}",
                callback_data=f"delquest_{q['id']}"
            )])
    else:
        text += "_Нет своих квестов_\n"
    text += "\nДобавить квест: напиши `/addquest Название квеста`"
    buttons.append([InlineKeyboardButton(
        text="📝 Как добавить?",
        callback_data="addquest_help"
    )])
    await msg.answer(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.message(Command("addquest"))
async def add_quest_cmd(msg: types.Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2:
        await msg.answer("Напиши: `/addquest Название квеста`\n\nНапример: `/addquest Прогулка 30 минут`", parse_mode="Markdown")
        return
    name = parts[1][:50]
    quests = await get_custom_quests(msg.from_user.id)
    if len(quests) >= 10:
        await msg.answer("❌ Максимум 10 своих квестов!")
        return
    await add_custom_quest(msg.from_user.id, name)
    await msg.answer(f"✅ Квест добавлен: *{name}*\n\nНайдёшь в 🎯 Квесты → ✏️ Мои квесты", parse_mode="Markdown")

@dp.callback_query(F.data.startswith("delquest_"))
async def delete_quest(call: types.CallbackQuery):
    quest_id = int(call.data.replace("delquest_", ""))
    await delete_custom_quest(quest_id, call.from_user.id)
    await call.answer("✅ Квест удалён", show_alert=True)
    await show_settings(call.message)

@dp.callback_query(F.data == "addquest_help")
async def addquest_help(call: types.CallbackQuery):
    await call.answer("Напиши: /addquest Название квеста", show_alert=True)

# ══════════════════════════════════════════
# ⏰ ПЛАНИРОВЩИК
# ══════════════════════════════════════════

async def send_morning_reminder():
    for uid in await get_all_user_ids():
        try:
            await bot.send_message(uid,
                "☀️ *Новый день — новые квесты!*\n\nНажми 🎯 Квесты чтобы начать прокачку. Не прерывай стрик! 🔥",
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

async def apply_daily_penalty():
    users = await get_all_users()
    for user in users:
        if user.get("total_quests", 0) == 0:
            continue
        had = await had_activity_yesterday(user["id"])
        if not had:
            user["xp"] = max(0, user["xp"] - 5)
            user["streak"] = 0
            await save_user(user)
            try:
                await bot.send_message(user["id"],
                    "😔 *Вчера не было активности...*\n\n-5 XP и стрик сброшен.\nНе сдавайся! Жми 🎯 Квесты",
                    parse_mode="Markdown")
            except Exception:
                pass

async def send_weekly_boss():
    week = date.today().isocalendar()
    week_key = f"{week[0]}-W{week[1]}"
    boss_index = random.randint(0, len(WEEKLY_BOSSES)-1)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR REPLACE INTO weekly_boss VALUES (?,?)", (week_key, boss_index))
        await db.commit()
    boss = WEEKLY_BOSSES[boss_index]
    for uid in await get_all_user_ids():
        try:
            await bot.send_message(uid,
                f"⚔️ *Новый босс недели!*\n\n*{boss['name']}*\n{boss['desc']}\n\n"
                f"🏆 Награда: +{boss['xp']} XP + 50🪙\n\nНажми ⚔️ Босс недели!",
                parse_mode="Markdown")
        except Exception:
            pass

async def send_random_event():
    event = random.choice(RANDOM_EVENTS)
    users = await get_all_users()
    for user in users:
        if event["type"] == "bonus_xp":
            user["xp"] += event["value"]
        elif event["type"] == "penalty_xp":
            user["xp"] = max(0, user["xp"] - event["value"])
        elif event["type"] == "bonus_coins":
            user["coins"] = user.get("coins",0) + event["value"]
        await save_user(user)
        try:
            await bot.send_message(user["id"],
                f"🎰 *Случайное событие!*\n\n{event['name']}\n{event['msg']}",
                parse_mode="Markdown")
        except Exception:
            pass

async def scheduler():
    while True:
        now = datetime.now()
        hm = (now.hour, now.minute)
        wd = now.weekday()
        if hm == (8,  0): await send_morning_reminder()
        if hm == (21, 0): await send_evening_reminder()
        if hm == (0,  5): await apply_daily_penalty()
        if hm == (0,  1): await generate_daily_shop()
        if hm == (9,  0) and wd == 0: await send_weekly_boss()
        if hm == (12, 0) and wd == 2: await send_random_event()
        await asyncio.sleep(60)

# ══════════════════════════════════════════
# ▶️ ЗАПУСК
# ══════════════════════════════════════════

async def main():
    await init_db()
    await generate_daily_shop()
    await asyncio.gather(
        dp.start_polling(bot),
        scheduler()
    )

if __name__ == "__main__":
    asyncio.run(main())
