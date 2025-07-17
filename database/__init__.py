from .create import DataBase

# Инициализация базы данных при импорте
db = DataBase()

async def init_db():
    await db.create()
    return db

# Экспортируем методы для удобного доступа
add_user = db.users.add_user
get_user = db.users.get_user
update_balance = db.users.update_balance
ban_user = db.users.ban_user
unban_user = db.users.unban_user
set_language = db.users.set_language
check_subs = db.users.check_subs
get_all_users = db.users.get_all_users

add_item = db.items.add_item
get_item = db.items.get_item
get_all_items = db.items.get_all_items
update_item = db.items.update_item
delete_item = db.items.delete_item
increment_purchases = db.items.increment_purchases

create_deposit = db.deposits.create_deposit
get_deposit = db.deposits.get_deposit
update_deposit_status = db.deposits.update_deposit_status

get_op_channels = db.op.get_op_channels
add_op_channel = db.op.add_op_channel
remove_op_channel = db.op.remove_op_channel

add_record = db.history.add_record
get_user_history = db.history.get_user_history
get_all_history = db.history.get_all_history
get_stats = db.history.get_stats