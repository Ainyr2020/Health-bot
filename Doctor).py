import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

API_TOKEN = '7538752864:AAEoLSgAtDdP_4vXI3gS2Zu1CXYtyz8D_Wo'

# Настройка логгера
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Состояния
class Form(StatesGroup):
    gender = State()
    age = State()
    analysis = State()

# /start
@router.message(lambda message: message.text == "/start")
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🧪 Начать анализ")]],
        resize_keyboard=True
    )
    await message.answer(
        "👋 Привет! Я — твой бот-помощник по анализам. Я помогу тебе понять, в норме ли твои анализы.\n"
        "Чтобы начать, нажми кнопку ниже:",
        reply_markup=kb
    )

# Кнопка начать анализ
@router.message(lambda msg: msg.text == "🧪 Начать анализ")
async def start_analysis(message: types.Message, state: FSMContext):
    await state.set_state(Form.gender)
    await message.answer("Укажи свой пол (муж / жен):", reply_markup=ReplyKeyboardRemove())

# Получаем пол
@router.message(Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text.lower()
    if gender not in ["муж", "жен"]:
        return await message.answer("Пожалуйста, введи 'муж' или 'жен'.")
    await state.update_data(gender=gender)
    await state.set_state(Form.age)
    await message.answer("Теперь введи свой возраст:")

# Получаем возраст
@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Возраст должен быть числом.")
    await state.update_data(age=int(message.text))
    await state.set_state(Form.analysis)
    await message.answer(
        "Теперь введи свои анализы в формате:\n\nгемоглобин: 115\nжелезо: 8.5\nсахар: 6.5"
    )

# Обработка анализов
@router.message(Form.analysis)
async def process_analysis(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    gender = user_data['gender']

    lines = message.text.lower().splitlines()
    results = []
    notes = []

    for line in lines:
        if ":" not in line:
            continue
        key, val = map(str.strip, line.split(":", 1))
        if key in ["гемоглобин", "железо", "сахар"]:
            try:
                value = float(val.replace(',', '.'))
            except ValueError:
                continue

            if key == "гемоглобин":
                norm = (130, 170) if gender == "муж" else (120, 150)
            elif key == "железо":
                norm = (10.7, 30.4)
            elif key == "сахар":
                norm = (4.1, 6.1)

            low, high = norm
            if value < low:
                results.append(f"🔻 {key.capitalize()}: {value} — Понижен")
                notes.append(f"💡 {key.capitalize()} слишком низкий. Следует увеличить потребление продуктов с {key}.")
            elif value > high:
                results.append(f"🔺 {key.capitalize()}: {value} — Повышен")
                notes.append(f"💡 {key.capitalize()} повышен. Нужно проконсультироваться с врачом.")
            else:
                results.append(f"✅ {key.capitalize()}: {value} — В норме")

    response = "📋 *Результаты анализа:*\n\n" + "\n".join(results)
    if notes:
        response += "\n\n🔍 *Рекомендации:*\n" + "\n".join(notes)

    await message.answer(response, parse_mode="Markdown")
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
