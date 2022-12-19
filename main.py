import logging
from aiogram import Bot, Dispatcher, executor, types
from config import API_TOKEN, admin
import keyboard as kb
from onesec_api import Mailbox
import json
import asyncio
import sqlite3
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

storage = MemoryStorage()
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
connection = sqlite3.connect('data.db')
q = connection.cursor()

class CellarImport(StatesGroup):
	rasst = State()

@dp.message_handler(content_types=['text'], text='✉️ Получить почту')
async def takeamail(m: types.Message):
	ma = Mailbox('')
	email = f'{ma._mailbox_}@1secmail.com'
	await m.answer(f'📫 Вот твоя почта: {email}\nОтправляй письмо.\nПочта проверяется автоматически, каждые 5 секунд, если придет новое письмо, мы вас об этом оповестим!\n\n<b>На 1 почту можно получить только - 1 письмо.</b>\n<b>Работоспособность почты - 10 минут!</b>', parse_mode='HTML')
	while True:
		mb = ma.filtred_mail()
		if isinstance(mb, list):
			mf = ma.mailjobs('read',mb[0])
			js = mf.json()
			fromm = js['from']
			theme = js['subject']
			mes = js['textBody']
			await m.answer(f'📩 Новое письмо:\n<b>От</b>: {fromm}\n<b>Тема</b>: {theme}\n<b>Сообщение</b>: {mes}', reply_markup=kb.menu, parse_mode='HTML')
			break
		else:
			pass
		await asyncio.sleep(5)

@dp.message_handler(content_types=['text'], text='🔐 Случайный пароль')
async def randompass(m: types.Message):
	ma = Mailbox('')
	passw = ma.rand_pass_for()
	await m.answer(f'🔑 Я сгенерировал для тебя пароль, держи: `{passw}`\n\n*Сгенерированный пароль никому не виден, можешь не беспокоиться*', parse_mode='MarkdownV2')

@dp.message_handler(commands=['admin'])
async def adminstration(m: types.Message):
	if m.chat.id == admin:
		await m.answer('Добро пожаловать в админ панель.', reply_markup=kb.apanel)
	else:
		await m.answer('Черт! Ты меня взломал :(')

@dp.message_handler(content_types=['text'])
async def texthandler(m: types.Message):
	q.execute(f"SELECT * FROM users WHERE user_id = {m.chat.id}")
	result = q.fetchall()
	if len(result) == 0:
		uid = 'user_id'
		sql = 'INSERT INTO users ({}) VALUES ({})'.format(uid, m.chat.id)
		q.execute(sql)
		connection.commit()
	await m.answer(f'Приветствую тебя, {m.from_user.mention}\nЭтот бот создан для быстрого получения временной почты.\nИспользуй кнопки ниже 👇', reply_markup=kb.menu)
 
@dp.callback_query_handler(lambda call: call.data.startswith('stats'))    
async def statistics(call):
	re = q.execute(f'SELECT * FROM users').fetchall()
	kol = len(re)
	connection.commit()
	await call.message.answer(f'Всего пользователей: {kol}')

@dp.callback_query_handler(lambda call: call.data.startswith('rass'))    
async def usender(call):
	await call.message.answer('Введите текст для рассылки.\n\nДля отмены нажмите кнопку ниже 👇', reply_markup=kb.back)
	await CellarImport.rasst.set()

@dp.message_handler(state=CellarImport.rasst)
async def process_name(message: types.Message, state: FSMContext):
	q.execute(f'SELECT user_id FROM users')
	row = q.fetchall()
	connection.commit()
	if message.text == 'Отмена':
		await message.answer('Отмена! Возвращаю в главное меню.', reply_markup=kb.menu)
		await state.finish()
	else:
		info = row
		await message.answer('Начинаю рассылку...')
		for i in range(len(info)):
			try:
				await bot.send_message(info[i][0], str(message.text))
			except:
				pass
		await message.answer('Рассылка завершена.', reply_markup=kb.menu)
		await state.finish()

if __name__ == '__main__':
	executor.start_polling(dp, skip_updates=True) # Запуск