from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.imports import _
from utils.imports import *
from utils.db_init import *
from utils.config_loader import config
import aiohttp

from API.CryptoBotAPI import *

from .menu import router 

@router.callback_query(F.data.startswith("buy_"))
async def plugin_buy_handler(callback: types.CallbackQuery, bot: Bot):
    item_id = int(callback.data.split("_")[1])
    item = await db.items.get_item(item_id)

    kb = InlineKeyboardBuilder()
    kb.button(text='CryptoBot', callback_data=f'pay_cryptobot_{item_id}')
    kb.button(text='RUB', callback_data=f'pay_rub_{item_id}')
    kb.button(text='Назад', callback_data=f'plugin_{item_id}')
    kb.adjust(1)
    await callback.message.delete()
    await callback.message.answer(_("Выберите способ оплаты:"), reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("pay_rub_"))
async def pay_from_cryptobot_handler(callback: types.CallbackQuery, bot: Bot):
    item_id = int(callback.data.split("_")[2])
    kb = InlineKeyboardBuilder()
    kb.button(text='Оплатить', url='@titleplugins_support')
    kb.button(text='Назад', callback_data=f'buy_{item_id}')
    await callback.message.edit_text('Для оплаты напишите админу в лс и переведите деньги по полученным реквезитам. Деньги начисляться на баланс.')

@router.callback_query(F.data.startswith("pay_cryptobot_"))
async def pay_from_cryptobot_handler(callback: types.CallbackQuery, bot: Bot):
    item_id = int(callback.data.split("_")[2])
    item = await db.items.get_item(item_id)
    user_id = callback.from_user.id
    
    if not item:
        await callback.answer(_("Товар не найден!"), show_alert=True)
        return

    # Получаем данные пользователя и курс
    user = await db.users.get_user(user_id)
    balance = user.get('balance', 0)
    item_price = item['price']

    try:
        usd_rate = await get_usd_to_rub_rate()
    except Exception as e:
        print(f"Ошибка получения курса: {e}")
        usd_rate = 90

    # Определяем сумму к оплате и списание с баланса
    amount_to_pay = item_price
    balance_used = 0

    if balance > 0:
        if balance >= item_price:
            # Полная оплата с баланса
            balance_used = item_price
            amount_to_pay = 0
        else:
            # Частичная оплата с баланса
            balance_used = balance
            amount_to_pay = item_price - balance

    # Если нужно оплачивать через CryptoBot
    if amount_to_pay > 0:
        amount_usd = round(amount_to_pay / usd_rate, 2)
        invoice = await create_invoice(
            amount=amount_usd,
            user_id=user_id,
            purpose=f'Покупка плагина: {item["name"]}'
        )
        invoice_id = invoice['id']
    else:
        # Полная оплата с баланса
        invoice_id = 0
        amount_usd = 0

    # Формируем сообщение
    message_text = _(
        "💳 <b>{payment_type}</b>\n\n"
        f"🧩 <b>Плагин:</b> {item['name']}\n"
        f"💰 <b>Стоимость:</b> {item_price}₽\n"
    )

    if balance_used > 0:
        message_text += _(
            f"💳 <b>Спишется с баланса:</b> {balance_used}₽\n"
        )
    
    if amount_to_pay > 0:
        message_text += _(
            f"💵 <b>К оплате:</b> {amount_to_pay}₽ (~{amount_usd}$)\n"
            f"📊 <b>Курс:</b> 1$ = {usd_rate}₽\n\n"
            "⏳ <b>Срок действия чека:</b> 3 минуты\n\n"
        )
    
    if amount_to_pay > 0:
        message_text += _(
            "➡️ Нажмите кнопку <b>'Оплатить'</b> для перехода к оплате\n"
            "✅ После оплаты нажмите <b>'Проверить'</b>"
        )
    else:
        message_text += _(
            "✅ Нажмите <b>'Получить'</b> для получения плагина"
        )

    # Определяем тип оплаты для заголовка
    payment_type = _("Оплата с баланса") if amount_to_pay == 0 else \
                 _("Комбинированная оплата") if balance_used > 0 else \
                 _("Оплата через CryptoBot")

    message_text = message_text.format(payment_type=payment_type)

    # Создаем клавиатуру
    kb = InlineKeyboardBuilder()
    
    if amount_to_pay > 0:
        kb.button(text='💳 Оплатить', url=invoice['url'])
    
    button_text = '🔄 Получить' if amount_to_pay == 0 else '🔄 Проверить'
    kb.button(
        text=button_text, 
        callback_data=f'confirmPay_{invoice_id}_{item_id}_{balance_used}'
    )
    kb.button(
        text='🔙 Назад', 
        callback_data=f'buy_{item_id}'
    )
    kb.adjust(1)

    try:
        await callback.message.edit_text(
            message_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка редактирования сообщения: {e}")
        await callback.message.delete()
        await callback.message.answer(
            message_text,
            reply_markup=kb.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("confirmPay_"))
async def confirm_pay_from_cryptobot_handler(callback: types.CallbackQuery, bot: Bot):
    parts = callback.data.split('_')
    invoice_id = int(parts[1])
    item_id = int(parts[2])
    balance_used = float(parts[3])
    user_id = callback.from_user.id
    
    # Получаем информацию о товаре
    item = await db.items.get_item(item_id)
    if not item:
        await callback.answer(_("Товар не найден!"), show_alert=True)
        return

    # Для комбинированной оплаты проверяем статус оплаты
    if invoice_id != 0:
        status = await check_payment_status(invoice_id)
        if not status:
            await callback.answer(_("Оплата не найдена"), show_alert=True)
            return

    # Записываем информацию о покупке в историю
    total_amount = item['price']
    payment_details = []
    
    # Если была частичная оплата с баланса - списываем и записываем
    if balance_used > 0:
        await db.users.update_balance(
            user_id, 
            -balance_used, 
            f"Частичная оплата товара: {item['name']}",
            operation_type="purchase",
            item_id=item_id
        )
        payment_details.append(f"С баланса: {balance_used}₽")
    
    # Если была оплата через криптобот - записываем
    if invoice_id != 0:
        amount_paid = total_amount - balance_used
        await db.history.add_record(
            user_id=user_id,
            amount=-amount_paid,
            comment=f"Оплата через CryptoBot за товар: {item['name']}",
            operation_type="purchase",
            service="cryptobot",
            item_id=item_id
        )
        payment_details.append(f"Через CryptoBot: {amount_paid}₽")
    
    # Обновляем статус оплаты
    await callback.message.edit_text(_("✅ Оплата прошла успешно! Готовим ваш плагин..."))

    # Формируем сообщение с плагином
    message_text = _(
        f"🎉 <b>Спасибо за покупку!</b>\n\n"
        f"<b>Название:</b> <code>{item['name']}</code>\n"
        f"<b>Описание:</b> <code>{item['description']}</code>\n"
        f"<b>Сумма:</b> <code>{total_amount}₽</code>\n"
        f"<b>Способ оплаты:</b> {', '.join(payment_details)}\n\n"
    )

    if item['instruction']:
        message_text += _(
            f"📝 <b>Инструкция по установке:</b>\n"
            f"<code>{item['instruction']}</code>\n\n"
        )

    message_text += _("⬇️ <b>Ваш плагин готов к скачиванию ниже</b> ⬇️")

    # Отправка контента
    try:
        if item.get('photo_path'):
            await bot.send_photo(
                chat_id=user_id,
                photo=types.FSInputFile(item['photo_path']),
                caption=message_text
            )
            await bot.send_document(
                chat_id=user_id,
                document=types.FSInputFile(item['file_path'], filename=f"{item['name']}.zip"),
                caption=_("📦 <b>Ваш плагин</b>")
            )
        else:
            await bot.send_document(
                chat_id=user_id,
                document=types.FSInputFile(item['file_path'], filename=f"{item['name']}.zip"),
                caption=message_text
            )
        
        await callback.message.edit_text(
            _("✅ <b>Плагин успешно выдан!</b>\n"
              "Проверьте свои сообщения, мы отправили вам все материалы.")
        )
    except Exception as e:
        print(f"Ошибка при отправке плагина: {e}")
        await callback.message.edit_text(
            _("⚠️ Произошла ошибка при отправке плагина. Пожалуйста, свяжитесь с поддержкой.")
        )

    # Начисляем реферальный бонус
    referrer_id = await db.users.get_referrer(user_id)
    if referrer_id:
        ref_bonus = round(item['price'] * (float(config['bot']['ref_percent']) / 100, 2))
        await db.users.update_balance(
            referrer_id,
            ref_bonus,
            f"Реферальный бонус за покупку товара {item['name']}",
            operation_type="ref_bonus",
            item_id=item_id
        )
        
        try:
            await bot.send_message(
                referrer_id,
                _("🎉 Вы получили реферальный бонус {bonus}₽ за покупку вашего реферала!").format(bonus=ref_bonus)
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление рефереру: {e}")

    # Увеличиваем счетчик покупок
    await db.items.increment_purchases(item_id)


async def process_referral_bonus(buyer_id: int, amount: float, description: str, bot: Bot = None):
    """
    Начисление реферального бонуса
    :param buyer_id: ID покупателя
    :param amount: Сумма покупки
    :param description: Описание операции
    :param bot: Экземпляр бота для отправки уведомлений
    """
    # Получаем реферера покупателя
    referrer_id = await db.users.get_referrer(buyer_id)
    
    if not referrer_id:
        return False
    
    # Рассчитываем бонус (15% от суммы)
    ref_bonus = round(amount * (float(config['bot']['ref_percent']) / 100), 2)
    
    # Начисляем бонус рефереру
    await db.users.update_balance(referrer_id, ref_bonus, f"Реферальный бонус: +{amount}₽")
    await db.users.add_ref_income(referrer_id, ref_bonus)
    
    # Отправляем уведомление рефереру
    if bot:
        try:
            await bot.send_message(
                referrer_id,
                _("💸 Вы получили реферальный бонус {bonus}₽\n"
                  "за покупку от вашего реферала!").format(bonus=ref_bonus)
            )
        except Exception as e:
            print(f"Не удалось отправить уведомление рефереру {referrer_id}: {e}")
    
    return True


async def get_usd_to_rub_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"  # Пример API
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return data['rates']['RUB']