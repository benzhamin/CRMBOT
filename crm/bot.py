import asyncio
import os
import sys
from django.core.management.base import BaseCommand
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async
from django.conf import settings
from crm.models import Product, Order, Admins

import os
import django
from dotenv import load_dotenv
import logging
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()


load_dotenv()
logging.basicConfig(filename='bot.log', level=logging.INFO)
chat_id = os.getenv("CHAT_ID")

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(storage=MemoryStorage())



# Define states
class OrderStates(StatesGroup):
    product = State()
    waiting_for_amount = State()
    waiting_for_comment = State()




@sync_to_async
def get_admins():
    return list(Admins.objects.values_list('adminnumber', flat=True))

@sync_to_async
def create_product(product_name, amount):
    return Product.objects.create(product_name=product_name, amount=int(amount))

@sync_to_async
def get_all_products():
    return list(Product.objects.all().order_by('product_name'))

@sync_to_async
def get_product_by_id(product_id):
    return Product.objects.filter(id=product_id).first()

@sync_to_async
def create_order(product_id, amount, order_type, comment):
    product = Product.objects.get(id=product_id)
    return Order.objects.create(product=product, amount=amount, order_type=order_type, comment=comment)

@sync_to_async
def update_product_amount(product_id, amount, order_type):
    product = Product.objects.get(id=product_id)
    if order_type == "buy":
        product.amount = int(product.amount) + amount
    else:
        product.amount = int(product.amount) - amount
    product.save()
    return product

@dp.message(F.text == '/start')
async def start(message: Message):
    admins = await get_admins()
    if message.from_user.id not in admins:

        print(f"Unauthorized access attempt by user ID: {message.from_user.id}")
        return
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="ПРОДАЖА 💰")],
            [KeyboardButton(text="ОСТАТОК 📦")],
            [KeyboardButton(text="ЗАКУПКА 🛒")],
            [KeyboardButton(text="ДОБАВИТЬ ТОВАР ➕")]
        ],
        resize_keyboard=True,
        row_width=2,
    )
    await message.answer("Выберите опцию:", reply_markup=markup)

@dp.message(F.text == 'ДОБАВИТЬ ТОВАР ➕')
async def add_product(message: Message, state: FSMContext):
    admins = await get_admins()
    if message.from_user.id not in admins:
        print(f"Unauthorized access attempt by user ID: {message.from_user.id}")
        return
    await message.answer("Выберите продукт 📦:")
    await message.answer('Введите продукт 📦 и количество ➕ (формат: продукт,количество)')
    await state.set_state(OrderStates.product)

@dp.message(OrderStates.product)
async def process_add_product(message: Message, state: FSMContext):
    try:
        text = message.text.split(',')
        if len(text) != 2:
            await message.answer('Неверный формат. Используйте: продукт,количество')
            return
        product_name, amount = text[0].strip(), text[1].strip()
        await create_product(product_name, amount)
        await message.answer('Товар добавлен ✅')
        await state.clear()
    except ValueError:
        await message.answer('Количество должно быть числом.')
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

@dp.message(F.text == 'ОСТАТОК 📦')
async def product_remains(message: Message):
    admins = await get_admins()
    if message.from_user.id not in admins:
        print(f"Unauthorized access attempt by user ID: {message.from_user.id}")
        return
    try:
        products = await get_all_products()
        if not products:
            await message.answer("Нет доступных продуктов.")
            return
        product_list = "\n".join(f"{p.product_name} - {p.amount}К" for p in products)
        await message.answer(product_list)
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

@dp.message(F.text.in_(["ПРОДАЖА 💰", "ЗАКУПКА 🛒"]))
async def make_order(message: Message, state: FSMContext):
    admins = await get_admins()
    if message.from_user.id not in admins:
        print(f"Unauthorized access attempt by user ID: {message.from_user.id}")
        return
    
    global order_type
    order_type = "buy" if message.text == "ЗАКУПКА 🛒" else "sell"
    try:
        products = await get_all_products()
        if not products:
            await message.answer("Нет доступных продуктов.")
            return
        keyboard = [[InlineKeyboardButton(text=p.product_name, callback_data=f"product_{p.id}")] for p in products]
        await message.answer("Выберите продукт 📦:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

@dp.callback_query(F.data.startswith('product_'))
async def process_product_selection(callback_query, state: FSMContext):
    try:
        global product_id
        product_id = int(callback_query.data.split('_')[1])
        product = await get_product_by_id(product_id)
        if not product:
            await callback_query.message.answer("Продукт не найден.")
            return
        await callback_query.message.answer(f"Продукт 📦: {product.product_name}")
        await callback_query.message.delete()
        global amount_message
        amount_message = await callback_query.message.answer("Количество:")
        await state.set_state(OrderStates.waiting_for_amount)
    except Exception as e:
        await callback_query.message.answer(f'Ошибка: {str(e)}')

@dp.message(OrderStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        global amount 
        amount = int(message.text)
        await bot.delete_message(chat_id=message.chat.id, message_id=amount_message.message_id)
        await message.delete()
        await message.answer(f"Количество: {amount}К")
        global comment_message
        comment_message = await message.answer("Добавьте комментарий 📝:")
        await state.set_state(OrderStates.waiting_for_comment)
    except ValueError:
        await message.answer("Пожалуйста, введите число для количества.")
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

@dp.message(OrderStates.waiting_for_comment)
async def process_comment(message: Message, state: FSMContext):
    try:
        global comment
        global text_message
        comment = message.text
        await bot.delete_message(chat_id=message.chat.id, message_id=comment_message.message_id)
        await message.delete()
        await message.answer(f"Комментарий 📝: {comment}")
        product = await get_product_by_id(product_id)
        x = "ЗАКУПКА 🛒" if order_type == "buy" else ""
        text_message = f"{x}{amount}К {product.product_name} {comment}"
        await state.update_data(text_message=text_message)
        keyboard = [
            [InlineKeyboardButton(text="Да ✅", callback_data="confirm_yes"),
             InlineKeyboardButton(text="Нет ❌", callback_data="confirm_no")]
        ]
        await message.answer("Подтвердите?", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        await state.clear()
    except Exception as e:
        await message.answer(f'Ошибка: {str(e)}')

@dp.callback_query(F.data.startswith('confirm_'))
async def process_confirmation(callback_query, state: FSMContext):
    try:
        if callback_query.data == "confirm_yes":
            await create_order(product_id, amount, order_type, comment)
            await update_product_amount(product_id, amount, order_type)
            await callback_query.message.answer("Заказ подтвержден ✅")
            await bot.send_message(chat_id=chat_id, text=text_message)
        else:
            await callback_query.message.answer("Заказ отменен ❌")

        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.delete()
    except Exception as e:
        await callback_query.message.answer(f'Ошибка: {str(e)}')

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())