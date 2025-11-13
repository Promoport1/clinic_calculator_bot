import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
EQUIPMENT_TYPE, COST, DOWNTIME, RESEARCH_COST, CONTACT = range(5)

# Обновленная клавиатура для выбора оборудования
equipment_keyboard = [
    ['КТ', 'МРТ', 'Рентген'],
    ['УЗИ', 'НДА', 'ИВЛ'],
    ['Хирургический стол', 'Эндоскопия жесткая', 'Эндоскопия гибкая']
]

async def start(update: Update, context):
    await update.message.reply_text(
        'Привет! Я помогу посчитать, сколько денег теряет ваша клиника '
        'из-за простоя оборудования.\n\n'
        'Выберите тип аппарата:',
        reply_markup=ReplyKeyboardMarkup(
            equipment_keyboard, 
            one_time_keyboard=True,
            input_field_placeholder='КТ, МРТ, Рентген...'
        )
    )
    return EQUIPMENT_TYPE

async def equipment_type(update: Update, context):
    user_data = context.user_data
    user_data['equipment'] = update.message.text
    
    await update.message.reply_text(
        'Введите стоимость аппарата в млн руб:',
        reply_markup=ReplyKeyboardRemove()
    )
    return COST

async def cost(update: Update, context):
    user_data = context.user_data
    try:
        cost_value = float(update.message.text)
        user_data['cost'] = cost_value
        
        await update.message.reply_text(
            'Сколько часов в день простаивает оборудование в среднем?'
        )
        return DOWNTIME
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return COST

async def downtime(update: Update, context):
    user_data = context.user_data
    try:
        downtime_hours = float(update.message.text)
        user_data['downtime'] = downtime_hours
        
        await update.message.reply_text(
            'Введите стоимость одного исследования в рублях:'
        )
        return RESEARCH_COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return DOWNTIME

async def research_cost(update: Update, context):
    user_data = context.user_data
    try:
        research_cost_value = float(update.message.text)
        user_data['research_cost'] = research_cost_value
        
        # Расчет потерь
        lost_revenue = user_data['downtime'] * user_data['research_cost'] * 2  # 2 исследования в час
        fixed_costs = user_data['downtime'] * 4000  # фиксированные расходы
        daily_loss = lost_revenue + fixed_costs
        monthly_loss = daily_loss * 30
        
        user_data['monthly_loss'] = monthly_loss
        
        await update.message.reply_text(
            f"📉 <b>Результаты расчета:</b>\n\n"
            f"• <b>Тип аппарата:</b> {user_data['equipment']}\n"
            f"• <b>Стоимость:</b> {user_data['cost']} млн руб\n"
            f"• <b>Простой:</b> {user_data['downtime']} ч/день\n"
            f"• <b>Стоимость исследования:</b> {user_data['research_cost']} руб\n\n"
            f"<b>ВАШИ ПОТЕРИ:</b> ~{monthly_loss:,.0f} руб/месяц\n\n"
            f"Хотите получить детальный расчет от эксперта? "
            f"Оставьте ваш телефон - перезвоню в течение 15 минут:",
            parse_mode='HTML'
        )
        return CONTACT
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return RESEARCH_COST

async def contact(update: Update, context):
    user_data = context.user_data
    phone = update.message.text
    
    # Сохраняем данные
    lead_data = {
        'equipment': user_data['equipment'],
        'cost': user_data['cost'],
        'downtime': user_data['downtime'],
        'research_cost': user_data['research_cost'],
        'monthly_loss': user_data['monthly_loss'],
        'phone': phone
    }
    
    # Отправляем уведомление администратору (Вам, Константин)
    admin_message = (
        "🚨 НОВЫЙ ЛИД!\n\n"
        f"Телефон: {phone}\n"
        f"Оборудование: {user_data['equipment']}\n"
        f"Потери: {user_data['monthly_loss']:,.0f} руб/мес\n"
        f"Стоимость аппарата: {user_data['cost']} млн руб"
    )
    
    await context.bot.send_message(chat_id=797093764, text=admin_message)
    
    await update.message.reply_text(
        'Спасибо! Ваш запрос передан эксперту. '
        'Мы свяжемся с вами в ближайшее время.\n\n'
        'Для нового расчета отправьте /start'
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text(
        'Расчет отменен. Для нового расчета отправьте /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    # ВСТАВЛЕН ВАШ ТОКЕН
    updater = Updater("8378315151:AAGkqCMlMbD54PdlpOjgxy1F-EatxPtgRTg")
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EQUIPMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_type)],
            COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, cost)],
            DOWNTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, downtime)],
            RESEARCH_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, research_cost)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
