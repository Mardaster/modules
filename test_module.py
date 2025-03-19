from hikkatl.types import Message
from hikka import loader, utils
from random import choice, shuffle
import asyncio

@loader.tds
class QuizRPGMod(loader.Module):
    """Интерактивная викторина с прокачкой персонажа и битвами"""
    strings = {"name": "QuizRPG"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "question_time",
                30,
                "Время на ответ в секундах",
                validator=loader.validators.Integer(minimum=15, maximum=60)
            ),
            loader.ConfigValue(
                "categories",
                ["История", "Наука", "Кино", "Игры"],
                "Доступные категории вопросов",
                validator=loader.validators.Series()
            )
        )
        self.players = {}
        self.questions = {
            "История": [
                {"q": "Год основания Санкт-Петербурга?", "a": ["1703"]},
                {"q": "Первый человек в космосе?", "a": ["Гагарин", "Юрий Гагарин"]}
            ],
            "Наука": [
                {"q": "Химический символ золота?", "a": ["Au"]},
                {"q": "Сколько элементов в периодической таблице?", "a": ["118"]}
            ]
        }
        self.levels = {
            1: {"xp": 0, "title": "Новичок"},
            2: {"xp": 100, "title": "Ученик"},
            3: {"xp": 300, "title": "Мастер"}
        }

    async def client_ready(self, client, db):
        self.db = db

    def get_player(self, user_id):
        if user_id not in self.players:
            self.players[user_id] = {
                "xp": 0,
                "level": 1,
                "inventory": [],
                "current_battle": None
            }
        return self.players[user_id]

    async def quizcmd(self, message: Message):
        """Начать викторину в выбранной категории"""
        categories = "\n".join([
            f"{i+1}. {cat}" for i, cat in enumerate(self.config["categories"])
        ])
        await utils.answer(
            message,
            f"🎲 Выбери категорию:\n{categories}\n\nОтправь номер категории"
        )

    async def watcher(self, message: Message):
        """Обработка ответов пользователя"""
        if not message.out and self.get_player(message.sender_id)["current_battle"]:
            await self.check_answer(message)

    async def check_answer(self, message):
        user = self.get_player(message.sender_id)
        battle = user["current_battle"]
        if message.raw_text.lower() in [a.lower() for a in battle["correct_answers"]]:
            user["xp"] += 50
            await message.reply(
                f"✅ Правильно! +50 XP\n"
                f"Уровень: {user['level']} ({self.levels[user['level']]['title']})\n"
                f"Следующий уровень через {self.levels[user['level']+1]['xp'] - user['xp']} XP"
            )
        else:
            await message.reply("❌ Неверно! Попробуй ещё раз")
        user["current_battle"] = None

    async def _start_quiz(self, user_id, category):
        questions = self.questions.get(category, [])
        if not questions:
            return "В этой категории пока нет вопросов 😔"
        
        question = choice(questions)
        answers = question["a"][:3]
        shuffle(answers)
        
        user = self.get_player(user_id)
        user["current_battle"] = {
            "category": category,
            "question": question["q"],
            "correct_answers": question["a"]
        }
        
        timer = self.config["question_time"]
        return (
            f"🌀 Категория: {category}\n"
            f"❓ Вопрос: {question['q']}\n"
            f"⏳ Время на ответ: {timer} сек\n\n"
            f"Отправь ответ в чат!"
        )

    async def profilecmd(self, message: Message):
        """Посмотреть свой профиль"""
        user = self.get_player(message.sender_id)
        await utils.answer(
            message,
            f"🧙 Профиль {message.sender.first_name}\n"
            f"Уровень: {user['level']} ({self.levels[user['level']]['title']})\n"
            f"XP: {user['xp']}/{self.levels[user['level']+1]['xp']}\n"
            f"Инвентарь: {', '.join(user['inventory']) or 'пусто'}"
        )
