import asyncio  # Добавьте эту строку в начало модуля
from hikkatl.types import Message, User
from hikka import loader, utils
from hikkatl.tl.types import UserStatusOnline, UserStatusOffline
import time

@loader.tds
class UserWatcherMod(loader.Module):
    """Следит за онлайн-статусом пользователей в чате"""
    strings = {"name": "UserWatcher"}

    def __init__(self):
        self.watched_users = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "check_interval",
                60,
                "Интервал проверки статуса (секунды)",
                validator=loader.validators.Integer(minimum=30, maximum=300)
            )
        )

    async def client_ready(self, client, db):
        self.client = client
        asyncio.create_task(self.status_checker())  # Теперь asyncio доступен

    async def watchcmd(self, message: Message):
        """Начать отслеживание пользователя в этом чате"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            return await utils.answer(message, "❌ Укажите ID пользователя")
        
        user_id = int(args)
        chat_id = message.chat_id
        
        try:
            user = await self.client.get_entity(user_id)
            self.watched_users[user_id] = {
                "last_status": None,
                "chat_id": chat_id,
                "last_check": time.time()
            }
            await utils.answer(
                message,
                f"👁️ Начинаю следить за пользователем {user.first_name}\n"
                f"🔔 Уведомления будут приходить сюда"
            )
        except Exception:
            await utils.answer(message, "❌ Пользователь не найден")

    async def unwatchcmd(self, message: Message):
        """Остановить отслеживание"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            return await utils.answer(message, "❌ Укажите ID пользователя")
        
        user_id = int(args)
        if user_id in self.watched_users:
            del self.watched_users[user_id]
            await utils.answer(message, "✅ Слежение остановлено")
        else:
            await utils.answer(message, "❌ Пользователь не в списке")

    async def status_checker(self):
        while True:
            try:
                current_time = time.time()
                for user_id, data in self.watched_users.copy().items():
                    if current_time - data["last_check"] > self.config["check_interval"]:
                        try:
                            user = await self.client.get_entity(user_id)
                            new_status = isinstance(user.status, UserStatusOnline)
                            last_status = data["last_status"]
                            
                            if last_status is not None and new_status != last_status:
                                status_text = "🟢 В сети" if new_status else "🔴 Не в сети"
                                await self.client.send_message(
                                    entity=data["chat_id"],
                                    message=f"👤 {user.first_name}\n{status_text}"
                                )
                            
                            self.watched_users[user_id]["last_status"] = new_status
                            self.watched_users[user_id]["last_check"] = current_time
                        except Exception as e:
                            del self.watched_users[user_id]
                
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Error in status checker: {e}")
                await asyncio.sleep(60)

    async def watcher(self, message: Message):
        """Обновление статуса при активности пользователя"""
        user_id = message.sender_id
        if user_id in self.watched_users:
            self.watched_users[user_id]["last_status"] = True
            self.watched_users[user_id]["last_check"] = time.time()
