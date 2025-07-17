def format_profile(user: dict, stars: int, tasks_today: int) -> str:
    premium_status = "✅ Есть" if user.get('is_premium', False) else "❌ Нету"
    
    return f"""
👀 <b>Профиль:</b>

⭐️ <b>TG Premium:</b> {premium_status}
📅 <b>Дата регистрации:</b> <em>{user['reg_time']}</em>
🪪 <b>ID:</b> <code>{user['user_id']}</code>

💰 <b>Баланс $MICO:</b> {user['balance']:.2f} MitCoin
💳 <b>Баланс руб:</b> {user['rub_balance']:.2f} ₽
⭐️ <b>Баланс Stars:</b> {stars}

🚀 <b>Выполнено заданий за сегодня:</b> {tasks_today}
    """