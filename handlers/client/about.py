from utils.imports import *
from utils.imports import _ 
from .menu import *

@router.callback_query(F.data=='about')
async def about_menu(callback: types.CallbackQuery):

    kb = InlineKeyboardBuilder()
    kb.button(text='📣 Наш канал', url='https://t.me/titleplugins')
    kb.button(text='💬 Наша группа', url='https://t.me/TitlePrivate')
    kb.button(text='🆘 Поддержка', url='https://t.me/titleplugins_support')
    kb.button(text='Назад', callback_data='back_menu')
    kb.adjust(1)

    await callback.message.edit_text(_('''
🚀 <b>Автоматизируйте продажи на FunPay  с нашей командой! 🚀</b>

Мы разрабатываем высококачественные плагины и ботов, которые оптимизируют ваши процессы на FunPay делая продажи проще и быстрее.

❓Почему выбирают нас:

• <b>Стабильность и скорость:</b> Наши решения работают безупречно.

• <b>Бесплатные обновления и поддержка:</b> Мы всегда на связи и улучшаем наши продукты.

• <b>Индивидуальный подход:</b> Гибкая настройка плагинов под ваши уникальные потребности.

• <b>Техническая поддержка:</b> Нужна помощь с установкой, настройкой или использованием? Мы готовы ответить на все ваши вопросы!
                                       '''), reply_markup=kb.as_markup())