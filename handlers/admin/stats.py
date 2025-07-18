from aiogram.types import CallbackQuery
from aiogram import F
from datetime import datetime, timedelta
from utils.db_init import *
from utils.imports import *

from .admin import admin 

@admin.callback_query(F.data=='admin_stats')
async def admin_stats(callback: CallbackQuery):
    text = "<b>📊 Полная статистика бота</b>\n\n"
    
    # Общая статистика
    total_users, ref_users = await db.users.get_all_users()
    
    # Статистика по товарам
    async with db.con.cursor() as cur:
        await cur.execute('SELECT COUNT(*), SUM(purchases_count) FROM items')
        items_count, total_purchases = await cur.fetchone()
        
        await cur.execute('SELECT SUM(amount) FROM history WHERE amount > 0')
        total_income = (await cur.fetchone())[0] or 0
        
        await cur.execute('SELECT COUNT(*) FROM deposits WHERE status = "completed"')
        completed_deposits = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) FROM users WHERE is_banned = TRUE')
        banned_users = (await cur.fetchone())[0]
        
        # Новые пользователи
        today = datetime.now().strftime('%Y-%m-%d')
        await cur.execute('SELECT COUNT(*) FROM users WHERE DATE(reg_time) = ?', (today,))
        new_today = (await cur.fetchone())[0]
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        await cur.execute('SELECT COUNT(*) FROM users WHERE DATE(reg_time) >= ?', (week_ago,))
        new_week = (await cur.fetchone())[0]
        
        # Пользователи с балансом
        await cur.execute('SELECT COUNT(*) FROM users WHERE balance > 0')
        with_balance = (await cur.fetchone())[0]
        
        # Топ рефереров
        await cur.execute('''
            SELECT referrer_id, COUNT(*) as ref_count 
            FROM users 
            WHERE referrer_id IS NOT NULL 
            GROUP BY referrer_id 
            ORDER BY ref_count DESC 
            LIMIT 3
        ''')
        top_referrers = await cur.fetchall()
        
        # Финансовая статистика
        await cur.execute('SELECT SUM(amount) FROM history WHERE amount > 0 AND DATE(date) = ?', (today,))
        today_income = (await cur.fetchone())[0] or 0
        
        await cur.execute('SELECT AVG(amount) FROM history WHERE amount > 0')
        avg_check = (await cur.fetchone())[0] or 0
        
        # Топ пополнений
        await cur.execute('''
            SELECT user_id, SUM(amount) as total 
            FROM history 
            WHERE amount > 0 
            GROUP BY user_id 
            ORDER BY total DESC 
            LIMIT 3
        ''')
        top_deposits = await cur.fetchall()
        
        # Статистика по товарам
        await cur.execute('''
            SELECT id, name, purchases_count 
            FROM items 
            ORDER BY purchases_count DESC 
            LIMIT 3
        ''')
        top_items = await cur.fetchall()
        
        await cur.execute('SELECT COUNT(*) FROM items WHERE purchases_count = 0')
        no_sales = (await cur.fetchone())[0]
        
        # Активность
        await cur.execute('''
            SELECT DATE(date) as day, COUNT(*) as count 
            FROM history 
            WHERE date >= date('now', '-7 days') 
            GROUP BY day 
            ORDER BY day DESC
            LIMIT 7
        ''')
        activity_days = await cur.fetchall()
        
        await cur.execute('SELECT COUNT(DISTINCT user_id) FROM history')
        active_users = (await cur.fetchone())[0]
        
        await cur.execute('SELECT COUNT(*) / COUNT(DISTINCT user_id) FROM history')
        avg_actions = (await cur.fetchone())[0] or 0

    async with db.con.cursor() as cur:
        # Общий доход (только реальные пополнения, исключая реферальные бонусы)
        await cur.execute('''
            SELECT SUM(amount) 
            FROM history 
            WHERE amount > 0 AND comment NOT LIKE 'Реферальный бонус%'
        ''')
        total_income = (await cur.fetchone())[0] or 0
        
        # Реферальные выплаты (отдельно)
        await cur.execute('''
            SELECT SUM(amount) 
            FROM history 
            WHERE comment LIKE 'Реферальный бонус%'
        ''')
        ref_income = (await cur.fetchone())[0] or 0
        
        # Расходы пользователей (платежи за товары)
        await cur.execute('''
            SELECT SUM(amount) 
            FROM history 
            WHERE amount < 0 AND (comment LIKE 'Оплата%' OR comment LIKE 'Частичная оплата%')
        ''')
        user_expenses = (await cur.fetchone())[0] or 0  # Будет отрицательным числом
        
        # Чистая прибыль (доходы минус реферальные выплаты)
        net_profit = total_income + user_expenses  # user_expenses уже отрицательное
        
        # Депозиты сегодня
        today = datetime.now().strftime('%Y-%m-%d')
        await cur.execute('''
            SELECT SUM(amount) 
            FROM history 
            WHERE amount > 0 AND DATE(date) = ? AND comment NOT LIKE 'Реферальный бонус%'
        ''', (today,))
        today_income = (await cur.fetchone())[0] or 0
        
        # Средний чек (по реальным платежам)
        await cur.execute('''
            SELECT AVG(amount) 
            FROM history 
            WHERE amount > 0 AND comment NOT LIKE 'Реферальный бонус%'
        ''')
        avg_check = (await cur.fetchone())[0] or 0
        
        # Успешные депозиты (из таблицы deposits)
        await cur.execute('SELECT COUNT(*) FROM deposits WHERE status = "completed"')
        completed_deposits = (await cur.fetchone())[0]
    
    # Формируем текст сообщения
    text += f"""
<b>👥 Пользователи:</b>
├ Всего: <code>{total_users}</code>
├ Новых сегодня: <code>{new_today}</code>
├ Новых за неделю: <code>{new_week}</code>
├ С балансом: <code>{with_balance}</code>
├ Реферальных: <code>{ref_users}</code> ({ref_users/total_users*100:.1f}%)
└ Заблокированных: <code>{banned_users}</code>

<b>💰 Финансы:</b>
├ Общий доход: <code>{total_income:.2f}₽</code>
├ Реферальные выплаты: <code>{ref_income:.2f}₽</code>
├ Расходы пользователей: <code>{-user_expenses:.2f}₽</code>
├ Чистая прибыль: <code>{net_profit:.2f}₽</code>
├ Сегодняшний доход: <code>{today_income:.2f}₽</code>
├ Средний чек: <code>{avg_check:.2f}₽</code>
└ Успешных депозитов: <code>{completed_deposits}</code>

<b>🛍️ Товары:</b>
├ Всего: <code>{items_count}</code>
├ Без продаж: <code>{no_sales}</code>
└ Всего покупок: <code>{total_purchases}</code>

<b>📈 Активность:</b>
├ Уникальных: <code>{active_users}</code>
└ Среднее действий: <code>{avg_actions:.1f}</code>
"""

    # Добавляем топы
    text += "\n<b>🏆 Топ рефереров:</b>\n"
    if top_referrers:
        for i, (ref_id, count) in enumerate(top_referrers, 1):
            text += f"{i}. <a href='tg://user?id={ref_id}'>ID{ref_id}</a> - <code>{count}</code>\n"
    else:
        text += "└ Нет данных\n"
    
    text += "\n<b>🏅 Топ пополнений:</b>\n"
    if top_deposits:
        for i, (user_id, amount) in enumerate(top_deposits, 1):
            text += f"{i}. <a href='tg://user?id={user_id}'>ID{user_id}</a> - <code>{amount:.2f}₽</code>\n"
    else:
        text += "└ Нет данных\n"
    
    text += "\n<b>🔥 Топ товаров:</b>\n"
    if top_items:
        for i, (item_id, name, count) in enumerate(top_items, 1):
            text += f"{i}. {name} - <code>{count}</code> покупок\n"
    else:
        text += "└ Нет данных\n"
    
    # Добавляем график активности за 7 дней
    text += "\n<b>📅 Активность по дням:</b>\n"
    if activity_days:
        for day, count in activity_days:
            text += f"├ {day}: <code>{count}</code>\n"
    else:
        text += "└ Нет данных\n"
    
    # Клавиатура с кнопкой обновления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel"),
        ] 
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)