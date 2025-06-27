from telethon import TelegramClient, events
import os
import sys
import logging
import importlib
import glob
import time
import asyncio
import subprocess
from datetime import datetime

def print_ascii_art():
    art = """
    ╔════════════════════════════════════╗
    ║       NewEraV4 Userbot Setup       ║
    ║────────────────────────────────────║
    ║  Enter your Telegram API details   ║
    ╚════════════════════════════════════╝
    """
    print(art)

print_ascii_art()
API_ID = input("API ID: ")
API_HASH = input("API HASH: ")
OWNER_ID = int(input("OWNER ID: "))

BOT_NAME = "NewEraV4"
PREFIX = "."
logging.basicConfig(filename="newera.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(BOT_NAME)

client = TelegramClient("NewEraV4", api_id=API_ID, api_hash=API_HASH)
client.modules_help = {}
client.active_modules = {}
client.security_rules = {}
client.owner_id = OWNER_ID
client.start_time = time.time()
client.module_handlers = {}  # Для хранения обработчиков событий модулей

async def load_modules():
    module_files = glob.glob("modules/*.py")
    for module_file in module_files:
        if module_file.endswith("__init__.py"):
            continue
        module_name = os.path.basename(module_file).replace(".py", "").lower()
        if module_name not in client.active_modules:
            try:
                module = importlib.import_module(f"modules.{module_name}")
                client.active_modules[module_name] = True
                client.modules_help[module_name] = getattr(module, "commands", {})
                if hasattr(module, "init"):
                    handlers = await module.init(client, PREFIX)
                    client.module_handlers[module_name] = handlers if handlers else []
                logger.info(f"Модуль {module_name} успешно загружен")
            except Exception as e:
                logger.error(f"Ошибка загрузки модуля {module_name}: {e}")

def unload_module(module_name):
    """Функция для выгрузки модуля и удаления его обработчиков"""
    if module_name in client.module_handlers:
        for handler in client.module_handlers[module_name]:
            client.remove_event_handler(handler)
        del client.module_handlers[module_name]
    if module_name in client.active_modules:
        del client.active_modules[module_name]
    if module_name in client.modules_help:
        del client.modules_help[module_name]
    if module_name in sys.modules:
        del sys.modules[f"modules.{module_name}"]

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.help($| .*)"))
async def help_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "help" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .help запрещён!", parse_mode="html")
        return
    try:
        args = message.text.split(maxsplit=1)
        if len(args) == 1:
            help_text = (
                "<b>NewEraV4</b>\n"
                "──────────────────\n"
                "<i>Список доступных команд:</i>\n"
                "<b> | Главные</b>:\n"
                "<code>.help</code> — Показать это сообщение\n"
                "<code>.cfg</code> — Настройка модулей\n"
                "<code>.logs</code> — Логи\n"
                "<code>.lm</code> — Загрузить модуль из файла\n"
                "<code>.ulm</code> — Выгрузить модуль\n"
                "<code>.restart</code> — Перезапустить бота\n"
                "<code>.update</code> — Обновить бота или проверить обновления\n"
                "<code>.support</code> — Ссылка на тех. поддержки\n"
                "<code>.sec</code> — Управление безопасностью\n"
                "<code>.info</code> — Информация о юзерботе\n"
                "<code>.stats</code> — Стат. бота\n"
                "<code>.session</code> — Управление сессией\n"
            )
            for module, commands in client.modules_help.items():
                if not client.active_modules.get(module, False):
                    continue
                help_text += f"\n<b> {module.capitalize()}</b>:\n"
                for cmd, desc in commands.items():
                    if user_id in client.security_rules and (cmd in client.security_rules[user_id]["commands"] or module in client.security_rules[user_id]["modules"]) and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
                        continue
                    help_text += f"<code>{PREFIX}{cmd}</code> — {desc}\n"
            help_text += "──────────────────\n<b>.heta для поиска команд</b>"
            await message.edit(help_text, parse_mode="html")
        else:
            module_name = args[1].lower()
            if module_name in client.modules_help and client.active_modules.get(module_name, False):
                help_text = f"<b>Модуль {module_name.capitalize()}</b>\n──────────────────\n"
                for cmd, desc in client.modules_help[module_name].items():
                    if user_id in client.security_rules and (cmd in client.security_rules[user_id]["commands"] or module_name in client.security_rules[user_id]["modules"]) and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
                        continue
                    help_text += f"<code>{PREFIX}{cmd}</code> — {desc}\n"
                help_text += "──────────────────\n<b>.heta для поиска</b>"
                await message.edit(help_text, parse_mode="html")
            else:
                await message.edit(f"<b>Ошибка</b>: Модуль '{module_name}' не найден или отключён!", parse_mode="html")
        logger.info(f"Команда .help выполнена пользователем {message.sender_id}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .help: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.cfg($| .*)"))
async def cfg_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "cfg" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .cfg запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            cfg_text = "<b>Настройка модулей</b>\n──────────────────\n"
            for module, active in client.active_modules.items():
                cfg_text += f"<b>{module.capitalize()}</b>: {'Вкл' if active else 'Выкл'}\n"
            cfg_text += "──────────────────\n<b>Использование</b>: <code>.cfg <module> <on/off></code>"
            await message.edit(cfg_text, parse_mode="html")
            return
        module_name = args[1].lower()
        if module_name not in client.modules_help:
            await message.edit(f"<b>Ошибка</b>: Модуль '{module_name}' не найден!", parse_mode="html")
            return
        if len(args) < 3 or args[2].lower() not in ["on", "off"]:
            await message.edit("<b>Использование</b>: <code>.cfg <module> <on/off></code>", parse_mode="html")
            return
        state = args[2].lower() == "on"
        client.active_modules[module_name] = state
        await message.edit(f"<b>Модуль {module_name.capitalize()} {'включён' if state else 'выключен'}</b>", parse_mode="html")
        logger.info(f"Модуль {module_name} {'включён' if state else 'выключен'} пользователем {message.sender_id}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .cfg: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.dlm($| .*)"))
async def dlm_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "dlm" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .dlm запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.edit("<b>Использование</b>: <code>.dlm <module></code>", parse_mode="html")
            return
        module_name = args[1].lower()
        if os.path.exists(f"modules/{module_name}.py"):
            module = importlib.import_module(f"modules.{module_name}")
            importlib.reload(module)
            client.active_modules[module_name] = True
            client.modules_help[module_name] = getattr(module, "commands", {})
            asyncio.create_task(module.init(client, PREFIX))
            await message.edit(f"<b>Модуль {module_name.capitalize()} загружен</b>", parse_mode="html")
            logger.info(f"Модуль {module_name} загружен пользователем {message.sender_id}")
        else:
            await message.edit(f"<b>Ошибка</b>: Файл модуля {module_name}.py не найден!", parse_mode="html")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .dlm: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.lm$"))
async def lm_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "lm" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .lm запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    if not message.is_reply:
        await message.edit("<b>Ошибка</b>: Ответьте на сообщение с файлом .py!", parse_mode="html")
        return
    try:
        replied_message = await message.get_reply_message()
        if not replied_message.file or not replied_message.file.name.endswith(".py"):
            await message.edit("<b>Ошибка</b>: Ответьте на сообщение с файлом .py!", parse_mode="html")
            return
        module_name = replied_message.file.name.replace(".py", "").lower()
        await replied_message.download_media(f"modules/{module_name}.py")
        module = importlib.import_module(f"modules.{module_name}")
        client.active_modules[module_name] = True
        client.modules_help[module_name] = getattr(module, "commands", {})
        asyncio.create_task(module.init(client, PREFIX))
        await message.edit(f"<b>Модуль {module_name.capitalize()} загружен</b>", parse_mode="html")
        logger.info(f"Модуль {module_name} загружен из файла пользователем {message.sender_id}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .lm: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.ulm($| .*)"))
async def ulm_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "ulm" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .ulm запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.edit("<b>Использование</b>: <code>.ulm <module></code>", parse_mode="html")
            return
        module_name = args[1].lower()
        if module_name in client.active_modules:
            client.active_modules[module_name] = False
            await message.edit(f"<b>Модуль {module_name.capitalize()} выгружен</b>", parse_mode="html")
            logger.info(f"Модуль {module_name} выгружен пользователем {message.sender_id}")
        else:
            await message.edit(f"<b>Ошибка</b>: Модуль {module_name} не найден!", parse_mode="html")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .ulm: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.restart$"))
async def restart_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "restart" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .restart запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        await message.edit("<b>Перезапуск</b>", parse_mode="html")
        logger.info(f"Перезапуск бота пользователем {message.sender_id}")
        os.execv(sys.executable, ["python"] + sys.argv)
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .restart: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.update$"))
async def update_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "update" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .update запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        await message.edit("<b>Обновление</b>", parse_mode="html")
        result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if result.returncode == 0:
            await message.edit("<b>Обновление успешно! Перезапустите бота (.restart)</b>", parse_mode="html")
            logger.info(f"Обновление выполнено пользователем {message.sender_id}")
        else:
            await message.edit(f"<b>Ошибка обновления</b>:\n{result.stderr}", parse_mode="html")
            logger.error(f"Ошибка команды .update: {result.stderr}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .update: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.logs($| .*)"))
async def logs_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "logs" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .logs запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        lines = 10
        if len(args) > 1:
            lines = int(args[1])
        with open("newera.log", "r", encoding="utf-8") as f:
            log_lines = f.readlines()[-lines:]
        logs_text = "<b>Последние логи</b>\n──────────────────\n" + "".join(log_lines) + "──────────────────\n<b>Конец логов</b>"
        await message.edit(logs_text, parse_mode="html")
        logger.info(f"Команда .logs выполнена пользователем {message.sender_id}, строк: {lines}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .logs: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.terminal($| .*)"))
async def terminal_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "terminal" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .terminal запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.edit("<b>Использование</b>: <code>.terminal <команда></code>", parse_mode="html")
            return
        command = args[1]
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout or result.stderr or "Команда выполнена без вывода."
        terminal_text = f"<b>Терминал</b>\n──────────────────\n<code>{output}</code>\n──────────────────\n<b>Команда завершена</b>"
        await message.edit(terminal_text, parse_mode="html")
        logger.info(f"Команда .terminal выполнена пользователем {message.sender_id}: {command}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .terminal: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.e($| .*)"))
async def eval_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "e" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .e запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.edit("<b>Использование</b>: <code>.e <выражение></code>", parse_mode="html")
            return
        expression = args[1]
        result = eval(expression, {"__builtins__": {}}, {"client": client})
        await message.edit(f"<b>Результат</b>:\n<code>{result}</code>", parse_mode="html")
        logger.info(f"Команда .e выполнена пользователем {message.sender_id}: {expression}")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .e: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.support$"))
async def support_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "support" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .support запрещён!", parse_mode="html")
        return
    support_text = (
        "<b>Тех. Поддержка</b>\n"
        "──────────────────\n"
        "<b>></b>: <a href='https://t.me/newerahelpsupport'>@NewEraHelpSupport</a>\n"
        "──────────────────\n"
        "<b>Support</b>"
    )
    await message.edit(support_text, parse_mode="html")
    logger.info(f"Команда .support выполнена пользователем {message.sender_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.sec($| .*)"))
async def sec_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "sec" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .sec запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        if len(args) < 4:
            sec_text = (
                "<b>Настройки безопасности</b>\n"
                "──────────────────\n"
                "<b>Текущие правила</b>:\n"
            )
            for uid, rules in client.security_rules.items():
                until = "Навсегда" if rules["until"] is None else datetime.fromtimestamp(rules["until"]).strftime("%Y-%m-%d %H:%M:%S")
                sec_text += f"<b>Пользователь {uid}</b>:\n  Команды: {', '.join(rules['commands'])}\n  Модули: {', '.join(rules['modules'])}\n  До: {until}\n"
            sec_text += "──────────────────\n<b>Использование</b>: <code>.sec <@user> <command/module> <block/unblock> [seconds]</code>"
            await message.edit(sec_text, parse_mode="html")
            return
        target = args[1]
        target_user = await client.get_entity(target)
        target_id = str(target_user.id)
        target_item = args[2].lower()
        action = args[3].lower()
        duration = None if len(args) < 5 else int(args[4])
        if target_id not in client.security_rules:
            client.security_rules[target_id] = {"commands": [], "modules": [], "until": None}
        if action == "block":
            if target_item in client.modules_help or target_item in client.active_modules:
                if target_item not in client.security_rules[target_id]["modules"]:
                    client.security_rules[target_id]["modules"].append(target_item)
            else:
                if target_item not in client.security_rules[target_id]["commands"]:
                    client.security_rules[target_id]["commands"].append(target_item)
            if duration:
                client.security_rules[target_id]["until"] = time.time() + duration
            await message.edit(f"<b>{target_item.capitalize()} заблокирован для {target}</b>", parse_mode="html")
            logger.info(f"{target_item} заблокирован для {target_id} пользователем {message.sender_id}")
        elif action == "unblock":
            if target_item in client.security_rules[target_id]["modules"]:
                client.security_rules[target_id]["modules"].remove(target_item)
            if target_item in client.security_rules[target_id]["commands"]:
                client.security_rules[target_id]["commands"].remove(target_item)
            if not client.security_rules[target_id]["commands"] and not client.security_rules[target_id]["modules"]:
                del client.security_rules[target_id]
            await message.edit(f"<b>{target_item.capitalize()} разблокирован для {target}</b>", parse_mode="html")
            logger.info(f"{target_item} разблокирован для {target_id} пользователем {message.sender_id}")
        else:
            await message.edit("<b>Использование</b>: <code>.sec <@user> <command/module> <block/unblock> [seconds]</code>", parse_mode="html")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .sec: {e}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.info$"))
async def info_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "info" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .info запрещён!", parse_mode="html")
        return
    info_text = (
        "<b>Информация о NewEraV4</b>\n"
        "──────────────────\n"
        f"<b>UB</b>: {BOT_NAME}++\n"
        f"<b>Telethon</b>: 1.30.3\n"
        f"<b>Префикс</b>: <code>{PREFIX}</code>\n"
        f"<b>Модулей загружено</b>: {len(client.active_modules)}\n"
        "──────────────────\n"
        "<b>Best UB</b>"
    )
    await message.edit(info_text, parse_mode="html")
    logger.info(f"Команда .info выполнена пользователем {message.sender_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.stats$"))
async def stats_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "stats" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .stats запрещён!", parse_mode="html")
        return
    uptime = int(time.time() - client.start_time)
    uptime_str = f"{uptime // 3600}ч {(uptime % 3600) // 60}м {uptime % 60}с"
    stats_text = (
        "<b>NewEraV4</b>\n"
        "──────────────────\n"
        f"<b>Время работы</b>: {uptime_str}\n"
        f"<b>Активных модулей</b>: {sum(1 for m in client.active_modules.values() if m)}\n"
        f"<b>Заблокир. пользователей</b>: {len(client.security_rules)}\n"
        "──────────────────\n"
        "<b>Stats</b>"
    )
    await message.edit(stats_text, parse_mode="html")
    logger.info(f"Команда .stats выполнена пользователем {message.sender_id}")

@client.on(events.NewMessage(outgoing=True, pattern=r"^\.session($| .*)"))
async def session_command(event):
    message = event.message
    user_id = str(message.sender_id)
    if user_id in client.security_rules and "session" in client.security_rules[user_id]["commands"] and (client.security_rules[user_id]["until"] is None or client.security_rules[user_id]["until"] > time.time()):
        await message.edit("<b>Ошибка</b>: Доступ к команде .session запрещён!", parse_mode="html")
        return
    if message.sender_id != client.owner_id:
        await message.edit("<b>Ошибка</b>: Только админ может использовать эту команду!", parse_mode="html")
        return
    try:
        args = message.text.split()
        if len(args) < 2:
            session_text = (
                "<b>Управление сессией</b>\n"
                "──────────────────\n"
                "<b>Команды</b>:\n"
                "<code>.session generate</code> — Сгенерировать новую сессию\n"
                "<code>.session delete</code> — Удалить текущую сессию\n"
                "──────────────────\n"
                "<b>Осторожно</b>"
            )
            await message.edit(session_text, parse_mode="html")
            return
        action = args[1].lower()
        if action == "generate":
            new_session = TelegramClient(f"NewEraV4_{int(time.time())}", api_id=API_ID, api_hash=API_HASH)
            await new_session.connect()
            await message.edit("<b>Новая сессия сгенерирована! Проверьте файл сессии.</b>", parse_mode="html")
            logger.info(f"Новая сессия сгенерирована пользователем {message.sender_id}")
        elif action == "delete":
            os.remove("NewEraV4.session")
            await message.edit("<b>Сессия удалена! Перезапустите бота.</b>", parse_mode="html")
            logger.info(f"Сессия удалена пользователем {message.sender_id}")
        else:
            await message.edit("<b>Использование</b>: <code>.session <generate/delete></code>", parse_mode="html")
    except Exception as e:
        await message.edit(f"<b>Ошибка</b>: {e}", parse_mode="html")
        logger.error(f"Ошибка команды .session: {e}")

async def main():
    await client.start()
    await load_modules()
    logger.info("Бот запущен")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
