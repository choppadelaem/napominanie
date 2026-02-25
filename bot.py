import urllib.request
import json
import time
from datetime import datetime

# ===== НАСТРОЙКИ =====
TOKEN = "8708579784:AAGyuQZw2zDGhzLFivf45CHfGmVkG5Fo7Yg"
CHAT_ID = "1435830704"
# ======================

# ---------- Список команд ----------
COMMANDS = {
            "/set ": "- Чтобы добавить напоминание.",

            "/list ": "- Чтобы увидеть свои напоминания.",

            "/edit_time ": "- Чтобы изменить время напоминания.",
            
            "@choppadelaem ": "- Чтобы помогли разобраться. \n"
    
}


# ---------- Telegram ----------
def send_request(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if data:
        data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
    else:
        req = urllib.request.Request(url)

    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode("utf-8"))


def send_message(text, reply_markup=None):
    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    if reply_markup:
        data["reply_markup"] = reply_markup

    send_request("sendMessage", data)

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"

    response = urllib.request.urlopen(url)
    return json.loads(response.read().decode("utf-8"))



def send_main_menu():
    keyboard = {
        "inline_keyboard": [
            [{"text": "➕ Добавить напоминание", "callback_data": "menu_add"}],
            [{"text": "📋 Список напоминаний", "callback_data": "menu_list"}],
            [{"text": "ℹ️ Помощь", "callback_data": "menu_help"}]
        ]
    }

    send_message(
        "🤖 *Меню управления напоминаниями*\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

def send_reply_keyboard(): #ОБЫЧНЫЕ КНОПКИ
    keyboard = {
        "keyboard": [
            [{"text": "➕ Создать напоминание"}],
            [{"text": "📋 Мои напоминания"}],
            [{"text": "✏ Изменить напоминания"}],
            [{"text": "ℹ Помощь"}]
        ],
        "resize_keyboard": True
    }

    send_message("Главное меню:", reply_markup=keyboard)


def send_cancel_keyboard():
    keyboard = {
        "keyboard": [
            [{"text": "❌ Отмена"}]
        ],
        "resize_keyboard": True
    }

    send_message("Создаем новое напоминание :)", reply_markup=keyboard)



def show_schedule():
    schedule = load_schedule()

    if not schedule:
        send_message("📭 Напоминаний нет")
        return

    buttons = []
    result = "📅 Напоминания:\n\n"

    for i, item in enumerate(schedule):
        item_type = item.get("type", "weekly")

        if item_type == "weekly":
            desc = f"{weekday_names.get(item.get('weekday'))} в {item.get('hour'):02d}:{item.get('minute'):02d}"
        else:
            desc = f"{item.get('day'):02d}.{item.get('month'):02d} в {item.get('hour'):02d}:{item.get('minute'):02d}"

        result += f"{i+1}) {desc} — {item.get('text')}\n"

        buttons.append([
            {
                "text": f"❌ Удалить {i+1}",
                "callback_data": f"delete_{i}"
            },
            {
                "text": f"✏ Изменить время {i+1}",
                "callback_data": f"edit_time_{i}"
            }
        ])

    reply_markup = {"inline_keyboard": buttons}
    send_message(result, reply_markup=reply_markup)


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    if offset:
        url += f"?offset={offset}"

    response = urllib.request.urlopen(url)
    return json.loads(response.read().decode("utf-8"))


# ---------- Работа с файлами ----------
def load_schedule():
    try:
        with open("schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_schedule(schedule):
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


# ---------- Дни недели ----------
russian_days = {
    "пн": 0, "пон": 0, "понедельник": 0,
    "вт": 1, "вторник": 1,
    "ср": 2, "среда": 2,
    "чт": 3, "четверг": 3,
    "пт": 4, "пятница": 4,
    "сб": 5, "суббота": 5,
    "вс": 6, "воскресенье": 6
}

weekday_names = {
    0: "Понедельник",
    1: "Вторник",
    2: "Среда",
    3: "Четверг",
    4: "Пятница",
    5: "Суббота",
    6: "Воскресенье"
}


print("Бот запущен ✅")
pending_time_edit = None  # хранит индекс напоминания для изменения времени
creation_state = None
creation_data = {}
last_update_id = None
last_trigger = None

while True:
    now = datetime.now()
    schedule = load_schedule()
    updated_schedule = []

    # ✅ Проверка расписания
    for item in schedule:

        item_type = item.get("type", "weekly")  # защита от старых записей
        send = False

        # ---- Еженедельные ----
        if item_type == "weekly":
            if (
                item.get("weekday") == now.weekday() and
                item.get("hour") == now.hour and
                item.get("minute") == now.minute
            ):
                send = True

        # ---- По дате ----
        elif item_type == "date":
            try:
                event_time = datetime(
                    now.year,
                    item.get("month"),
                    item.get("day"),
                    item.get("hour"),
                    item.get("minute")
                )
            except:
                continue

            # Удаляем только если день уже прошёл
            if event_time.date() < now.date():
                continue

            if (
                item.get("day") == now.day and
                item.get("month") == now.month and
                item.get("hour") == now.hour and
                item.get("minute") == now.minute
            ):
                send = True
           

        # ---- Отправка ----
        if send:
            trigger_key = (
                f"{now.date()}_{now.hour}_{now.minute}_"
                f"{item.get('text')}"
            )

            if last_trigger != trigger_key:
                send_message(item.get("text"))
                last_trigger = trigger_key

            if item_type == "date":
                continue  # не сохраняем одноразовое после отправки

        updated_schedule.append(item)

    save_schedule(updated_schedule)

    # ✅ Проверка сообщений
    updates = get_updates(last_update_id)
    if updates["result"]:
        for update in updates["result"]:
            last_update_id = update["update_id"] + 1

            # ---------- Нажатие кнопки ----------
            if "callback_query" in update:
                query_id = update["callback_query"]["id"]
                data = update["callback_query"]["data"]

                send_request("answerCallbackQuery", {
                    "callback_query_id": query_id
                })

                if data == "menu_add":
                    send_message(
                        "Чтобы добавить напоминание используйте формат:\n\n"
                        "/set понедельник 20:00 спорт\n"
                        "или\n"
                        "/set 21.01 18:30 встреча"
                    )
                    continue

                elif data == "menu_list":
                    show_schedule()
                    continue

                elif data == "menu_help":
                    result = "📌 Если тебе мало кнопок, то у тебя есть команды:\n\n"
                    for cmd, description in COMMANDS.items():
                        result += f"{cmd}\n{description}\n\n"
                    send_message(result)
                    continue

                elif data.startswith("edit_time_"):
                    index = int(data.split("_")[2])
                    schedule = load_schedule()

                    if 0 <= index < len(schedule):

                        # ✅ СБРОС СОЗДАНИЯ
                        creation_state = None
                        creation_data = {}

                        # ✅ ВКЛЮЧАЕМ РЕЖИМ РЕДАКТИРОВАНИЯ
                        pending_time_edit = index

                        send_cancel_keyboard()
                        send_message("На какое время поменяем?")

                    continue

                elif data.startswith("delete_"):
                    index = int(data.split("_")[1])
                    schedule = load_schedule()

                    if 0 <= index < len(schedule):
                        schedule.pop(index)
                        save_schedule(schedule)
                        send_message("✅ Напоминание удалено")
                    continue

                

            # ---------- Обычные сообщения ----------
            if "message" in update:
                chat_id = str(update["message"]["chat"]["id"])
                if chat_id != CHAT_ID:
                    continue

                text = update["message"].get("text", "")

                # ===== Отмена создания =====
                if text == "❌ Отмена":

                    # Отмена создания
                    if creation_state is not None:
                        creation_state = None
                        creation_data = {}
                        send_message("❌ Создание напоминания отменено")
                        send_reply_keyboard()
                        continue

                    # Отмена редактирования времени
                    if pending_time_edit is not None:
                        pending_time_edit = None
                        send_message("❌ Изменение времени отменено")
                        creation_data = {}
                        send_reply_keyboard()
                        continue

                    continue

                # ===== Редактирование времени =====
                if pending_time_edit is not None:
                    try:
                        hour, minute = map(int, text.split(":"))

                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError

                        schedule = load_schedule()
                        schedule[pending_time_edit]["hour"] = hour
                        schedule[pending_time_edit]["minute"] = minute
                        save_schedule(schedule)

                        send_message("✅ Время успешно обновлено")
                        pending_time_edit = None
                        send_reply_keyboard()

                    except:
                        send_message("❌ Неверный формат. Введите ЧЧ:ММ")

                    continue
                

                # ===== Создание напоминания (FSM) =====
                if creation_state == "waiting_for_day":
                    day_input = text.lower()

                    # Проверка даты
                    if "." in day_input:
                        try:
                            day, month = map(int, day_input.split("."))

                            # Проверяем реальность даты
                            test_date = datetime(datetime.now().year, month, day)

                            creation_data["type"] = "date"
                            creation_data["day"] = day
                            creation_data["month"] = month

                        except ValueError:
                            send_message("❌ Неверная дата. Пример корректного ввода: 21.01")
                            continue
                    else:
                        weekday = russian_days.get(day_input)
                        if weekday is None:
                            send_message("❌ Где-то ошибка, давай ещё раз.")
                            continue

                        creation_data["type"] = "weekly"
                        creation_data["weekday"] = weekday

                    creation_state = "waiting_for_time"
                    send_message("В какое время напомнить?\n(Например: 20:00)")
                    continue


                elif creation_state == "waiting_for_time":
                    try:
                        hour, minute = map(int, text.split(":"))
                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError
                    except:
                        send_message("❌ Ой, ошибка. Пример: 20:00")
                        continue

                    creation_data["hour"] = hour
                    creation_data["minute"] = minute

                    creation_state = "waiting_for_text"
                    send_message("О чем напомнить?)")
                    continue


                elif creation_state == "waiting_for_text":
                    creation_data["text"] = text

                    schedule = load_schedule()
                    schedule.append(creation_data)
                    save_schedule(schedule)

                    send_message("✅ Создали напоминание. Скоро увидимся!")
                    send_reply_keyboard()

                    creation_state = None
                    creation_data = {}

                    continue


                # ===== /start =====
                if text.startswith("/start"):
                    send_reply_keyboard()
                    continue
                
                # ===== Обычные кнопки =====
                elif text == "➕ Создать напоминание":
                    # ✅ СБРОС РЕДАКТИРОВАНИЯ
                    pending_time_edit = None

                    creation_state = "waiting_for_day"
                    creation_data = {}

                    send_cancel_keyboard()
                    send_message(
                        "В какой день или дату напомнить? \n(Например: понедельник/пн/21.01)"
                        
                    )
                    continue
                
                elif text == "📋 Мои напоминания":
                    show_schedule()
                    continue

                elif text == "✏ Изменить напоминания":
                    show_schedule()  # тот же список с inline-кнопками
                    continue

                elif text == "ℹ Помощь":
                    result = "📌 Если тебе мало кнопок, у тебя есть команды:\n\n"
                    for cmd, description in COMMANDS.items():
                        result += f"{cmd}\n{description}\n\n"
                    send_message(result)
                    continue


                # ===== /set =====
                elif text.startswith("/set"):
                    parts = text.strip().split(maxsplit=3)

                    if len(parts) < 4:
                        send_message(
                            "Ой-ой, ошибочка.\n"
                            "Формат ввода:\n"
                            "/set понедельник 20:00 текст\n"
                            "/set 21.01 18:30 текст"
                        )
                        continue

                    day_input = parts[1].lower()
                    time_input = parts[2]
                    reminder_text = parts[3]

                    # Проверка времени
                    try:
                        hour, minute = map(int, time_input.split(":"))
                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError
                    except:
                        send_message("Ошибка формата времени. Пример: 20:00")
                        continue

                    schedule = load_schedule()

                    # ---- ДАТА ----
                    if "." in day_input:
                        try:
                            day, month = map(int, day_input.split("."))

                            schedule.append({
                                "type": "date",
                                "day": day,
                                "month": month,
                                "hour": hour,
                                "minute": minute,
                                "text": reminder_text
                            })

                            save_schedule(schedule)
                            send_message("✅ Одноразовое напоминание добавлено")

                        except:
                            send_message("Ошибка формата даты. Пример: 21.01")

                        continue

                    # ---- ДЕНЬ НЕДЕЛИ ----
                    weekday = russian_days.get(day_input)
                    if weekday is None:
                        send_message("Ошибка: неверный день или дата")
                        continue

                    schedule.append({
                        "type": "weekly",
                        "weekday": weekday,
                        "hour": hour,
                        "minute": minute,
                        "text": reminder_text
                    })

                    save_schedule(schedule)
                    send_message("✅ Напоминание добавлено")
                    continue


                # ===== /list =====
                elif text.startswith("/list"):
                    show_schedule()
                    continue


                # ===== /help =====
                elif text.startswith("/help"):
                    result = "📌 Если тебе мало кнопок, у тебя есть команды:\n\n"

                    for cmd, description in COMMANDS.items():
                        result += f"{cmd}{description}\n\n"

                    send_message(result.strip())
                    continue


                # ===== /edit_time =====
                elif text.startswith("/edit_time"):
                    parts = text.strip().split()


                    if len(parts) != 3:
                        send_message("Упс, неправильно. \n" "Формат: /edit_time НОМЕР В СПИСКЕ НАПОМИНАНИЙ ЧЧ:ММ")
                        continue

                    try:
                        index = int(parts[1]) - 1
                        hour, minute = map(int, parts[2].split(":"))

                        if not (0 <= hour <= 23 and 0 <= minute <= 59):
                            raise ValueError

                    except:
                        send_message("Ошибка формата. Пример: /edit_time 2 21:30")
                        continue

                    schedule = load_schedule()

                    if 0 <= index < len(schedule):
                        schedule[index]["hour"] = hour
                        schedule[index]["minute"] = minute
                        save_schedule(schedule)
                        send_message("✅ Время напоминания обновлено")
                    else:
                        send_message("❌ Напоминание с таким номером не найдено")

                    continue

        

    time.sleep(0.2)
