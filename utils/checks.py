from utils.imports import *
from utils.config_loader import config


async def check_subs_op(user_id: int, bot: Bot) -> bool:
    from database.op import OpDB
    op_channels = await OpDB.get_all_op_channels()
    
    for channel in op_channels:
        try:
            member = await bot.get_chat_member(
                chat_id=channel['channel_id'],
                user_id=user_id
            )
            if member.status not in ['member', 'administrator', 'creator']:
                try:
                    await bot.send_message(
                        user_id,
                        f"❌ Для использования бота необходимо подписаться на канал: {channel['title']}",
                        reply_markup=op_subscribe_kb(channel['channel_id'])
                    )
                    return False
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
        except Exception as e:
            logger.error(f"Ошибка проверки подписки: {e}")
    
    return True