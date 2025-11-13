import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
EQUIPMENT_TYPE, UZI_TYPE, EQUIPMENT_DETAILS, YEAR, COST, DOWNTIME, MIN_RESEARCH_COST, MAX_RESEARCH_COST, MIN_STUDIES_PER_HOUR, MAX_STUDIES_PER_HOUR, WORKING_DAYS, NEED_REPLACEMENT, CONTACT = range(13)

# Клавиатура для выбора оборудования
equipment_keyboard = [
    ['КТ', 'МРТ', 'Рентген'],
    ['УЗИ', 'НДА', 'ИВЛ'],
    ['Хирургический стол', 'Эндоскопия жесткая', 'Эндоскопия гибкая']
]

# Клавиатура для типов УЗИ
uzi_type_keyboard = [
    ['УЗИ Акушерство и гинекология'],
    ['УЗИ Кардиологические исследования'],
    ['УЗИ Универсальные исследования'],
    ['Другое УЗИ']
]

# Клавиатура да/нет
yes_no_keyboard = [['Да', 'Нет']]

# Оборудование, для которого НЕ предоставляем подмену
NO_REPLACEMENT_EQUIPMENT = ['КТ', 'МРТ', 'Рентген']

async def start(update: Update, context):
    await update.message.reply_text(
        'Привет! Я помогу посчитать, сколько денег теряет ваша клиника '
        'из-за простоя оборудования с учетом амортизации.\n\n'
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
    equipment = update.message.text
    user_data['equipment'] = equipment
    
    if equipment == 'УЗИ':
        await update.message.reply_text(
            'Выберите направление УЗИ исследований:',
            reply_markup=ReplyKeyboardMarkup(
                uzi_type_keyboard,
                one_time_keyboard=True
            )
        )
        return UZI_TYPE
    else:
        await update.message.reply_text(
            'Укажите марку, модель и название аппарата (например: "Philips Brilliance 64 CT" или "Siemens Magnetom Avanto 1.5T МРТ"):',
            reply_markup=ReplyKeyboardRemove()
        )
        return EQUIPMENT_DETAILS

async def uzi_type(update: Update, context):
    user_data = context.user_data
    user_data['uzi_type'] = update.message.text
    
    await update.message.reply_text(
        'Укажите марку, модель и название УЗИ аппарата (например: "GE Voluson E8" или "Philips EPIQ 7"):',
        reply_markup=ReplyKeyboardRemove()
    )
    return EQUIPMENT_DETAILS

async def equipment_details(update: Update, context):
    user_data = context.user_data
    equipment_details = update.message.text
    user_data['equipment_details'] = equipment_details
    
    await update.message.reply_text(
        'Введите год производства оборудования:'
    )
    return YEAR

async def year(update: Update, context):
    user_data = context.user_data
    try:
        year_value = int(update.message.text)
        current_year = datetime.now().year
        if year_value < 1980 or year_value > current_year:
            await update.message.reply_text(f'Пожалуйста, введите реальный год (1980-{current_year}):')
            return YEAR
        
        user_data['year'] = year_value
        equipment_age = current_year - year_value
        user_data['equipment_age'] = equipment_age
        
        await update.message.reply_text(
            'Введите первоначальную стоимость аппарата в млн руб:'
        )
        return COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите год цифрами:')
        return YEAR

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
            'Введите МИНИМАЛЬНУЮ стоимость одного исследования в рублях:'
        )
        return MIN_RESEARCH_COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return DOWNTIME

async def min_research_cost(update: Update, context):
    user_data = context.user_data
    try:
        min_cost = float(update.message.text)
        user_data['min_research_cost'] = min_cost
        
        await update.message.reply_text(
            'Введите МАКСИМАЛЬНУЮ стоимость одного исследования в рублях:'
        )
        return MAX_RESEARCH_COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return MIN_RESEARCH_COST

async def max_research_cost(update: Update, context):
    user_data = context.user_data
    try:
        max_cost = float(update.message.text)
        min_cost = user_data['min_research_cost']
        
        if max_cost <= min_cost:
            await update.message.reply_text('Максимальная стоимость должна быть больше минимальной. Введите заново:')
            return MAX_RESEARCH_COST
            
        user_data['max_research_cost'] = max_cost
        
        await update.message.reply_text(
            'Введите МИНИМАЛЬНОЕ количество исследований в час:'
        )
        return MIN_STUDIES_PER_HOUR
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return MAX_RESEARCH_COST

async def min_studies_per_hour(update: Update, context):
    user_data = context.user_data
    try:
        min_studies = float(update.message.text)
        user_data['min_studies_per_hour'] = min_studies
        
        await update.message.reply_text(
            'Введите МАКСИМАЛЬНОЕ количество исследований в час:'
        )
        return MAX_STUDIES_PER_HOUR
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return MIN_STUDIES_PER_HOUR

async def max_studies_per_hour(update: Update, context):
    user_data = context.user_data
    try:
        max_studies = float(update.message.text)
        min_studies = user_data['min_studies_per_hour']
        
        if max_studies <= min_studies:
            await update.message.reply_text('Максимальное количество должно быть больше минимального. Введите заново:')
            return MAX_STUDIES_PER_HOUR
            
        user_data['max_studies_per_hour'] = max_studies
        
        await update.message.reply_text(
            'Сколько рабочих дней в месяце? (частные клиники обычно 30):'
        )
        return WORKING_DAYS
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return MAX_STUDIES_PER_HOUR

async def working_days(update: Update, context):
    user_data = context.user_data
    try:
        working_days_value = int(update.message.text)
        if working_days_value < 1 or working_days_value > 31:
            await update.message.reply_text('Пожалуйста, введите число от 1 до 31:')
            return WORKING_DAYS
            
        user_data['working_days'] = working_days_value
        
        # Расчеты...
        avg_research_cost = (user_data['min_research_cost'] + user_data['max_research_cost']) / 2
        avg_studies_per_hour = (user_data['min_studies_per_hour'] + user_data['max_studies_per_hour']) / 2
        
        user_data['avg_research_cost'] = avg_research_cost
        user_data['avg_studies_per_hour'] = avg_studies_per_hour
        
        equipment_age = user_data['equipment_age']
        amortization_factor = max(0, 1 - (equipment_age / 15))
        amortized_cost = user_data['cost'] * amortization_factor
        
        lost_revenue_per_hour = avg_studies_per_hour * avg_research_cost
        daily_lost_revenue = lost_revenue_per_hour * user_data['downtime']
        monthly_lost_revenue = daily_lost_revenue * working_days_value
        
        monthly_loss = monthly_lost_revenue * (1 - amortization_factor * 0.3)
        
        user_data['monthly_loss'] = monthly_loss
        user_data['amortization_factor'] = amortization_factor
        user_data['amortized_cost'] = amortized_cost
        user_data['monthly_lost_revenue'] = monthly_lost_revenue
        
        await update.message.reply_text(
            'Потребуется ли вам подменное оборудование на время простоя?',
            reply_markup=ReplyKeyboardMarkup(
                yes_no_keyboard,
                one_time_keyboard=True
            )
        )
        return NEED_REPLACEMENT
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return WORKING_DAYS

async def need_replacement(update: Update, context):
    user_data = context.user_data
    need_replacement = update.message.text
    user_data['need_replacement'] = need_replacement
    
    amortization_percent = (1 - user_data['amortization_factor']) * 100
    equipment_info = user_data['equipment']
    if user_data['equipment'] == 'УЗИ' and 'uzi_type' in user_data:
        equipment_info = f"{user_data['equipment']} ({user_data['uzi_type']})"
    
    equipment_model_info = ""
    if 'equipment_details' in user_data and user_data['equipment_details']:
        equipment_model_info = f"\n• <b>Модель аппарата:</b> {user_data['equipment_details']}"
    
    replacement_offer = ""
    if need_replacement == 'Да':
        if user_data['equipment'] in NO_REPLACEMENT_EQUIPMENT:
            replacement_offer = f"\n\n⚠️ К сожалению, мы не предоставляем подменное оборудование для {user_data['equipment']} аппаратов"
        else:
            replacement_offer = f"\n\n🏥 МЫ МОЖЕМ ПРЕДЛОЖИТЬ ВАМ ПОДМЕННЫЙ {user_data['equipment'].upper()} АППАРАТ!"
            if user_data['equipment'] == 'УЗИ':
                replacement_offer += f"\nСпециализация: {user_data.get('uzi_type', 'универсальный')}"
    
    await update.message.reply_text(
        f"📉 <b>Результаты расчета с учетом амортизации:</b>\n\n"
        f"• <b>Тип аппарата:</b> {equipment_info}{equipment_model_info}\n"
        f"• <b>Год выпуска:</b> {user_data['year']} ({user_data['equipment_age']} лет)\n"
        f"• <b>Стоимость:</b> {user_data['cost']} млн руб\n"
        f"• <b>Амортизация:</b> {amortization_percent:.1f}%\n"
        f"• <b>Остаточная стоимость:</b> {user_data['amortized_cost']:.1f} млн руб\n"
        f"• <b>Простой:</b> {user_data['downtime']} ч/день\n"
        f"• <b>Рабочих дней:</b> {user_data['working_days']} в месяце\n"
        f"• <b>Стоимость исследований:</b> {user_data['min_research_cost']:,.0f} - {user_data['max_research_cost']:,.0f} руб\n"
        f"• <b>Количество исследований:</b> {user_data['min_studies_per_hour']} - {user_data['max_studies_per_hour']} в час\n"
        f"• <b>Подменное оборудование:</b> {need_replacement}\n\n"
        f"<b>ВАШИ ПОТЕРИ:</b> ~{user_data['monthly_loss']:,.0f} руб/месяц\n"
        f"<b>УТЕРЯННЫЙ ДОХОД:</b> ~{user_data['monthly_lost_revenue']:,.0f} руб/месяц{replacement_offer}\n\n"
        f"Хотите получить детальный расчет от эксперта? "
        f"Оставьте ваш телефон - перезвоню в течение 15 минут:",
        parse_mode='HTML'
    )
    return CONTACT

async def contact(update: Update, context):
    user_data = context.user_data
    phone = update.message.text
    
    equipment_info = user_data['equipment']
    if user_data['equipment'] == 'УЗИ' and 'uzi_type' in user_data:
        equipment_info = f"{user_data['equipment']} ({user_data['uzi_type']})"
    
    equipment_model_info = ""
    if 'equipment_details' in user_data and user_data['equipment_details']:
        equipment_model_info = f"\nМодель: {user_data['equipment_details']}"
    
    admin_message = (
        "🚨 НОВЫЙ ЛИД С РАСЧЕТОМ АМОРТИЗАЦИИ!\n\n"
        f"Телефон: {phone}\n"
        f"Оборудование: {equipment_info}{equipment_model_info}\n"
        f"Год выпуска: {user_data['year']} ({user_data['equipment_age']} лет)\n"
        f"Амортизация: {(1 - user_data['amortization_factor']) * 100:.1f}%\n"
        f"Потери: {user_data['monthly_loss']:,.0f} руб/мес\n"
        f"Утерянный доход: {user_data['monthly_lost_revenue']:,.0f} руб/мес\n"
        f"Стоимость аппарата: {user_data['cost']} млн руб\n"
        f"Стоимость исследований: {user_data['min_research_cost']:,.0f} - {user_data['max_research_cost']:,.0f} руб\n"
        f"Количество исследований: {user_data['min_studies_per_hour']} - {user_data['max_studies_per_hour']} в час\n"
        f"Подменное оборудование: {user_data['need_replacement']}\n"
        f"Рабочих дней: {user_data['working_days']}"
    )
    
    if user_data['need_replacement'] == 'Да':
        if user_data['equipment'] in NO_REPLACEMENT_EQUIPMENT:
            admin_message += f"\n\n❌ НЕ ПРЕДОСТАВЛЯЕМ ПОДМЕНУ: {user_data['equipment']}"
        else:
            admin_message += f"\n\n✅ МОЖЕМ ПРЕДЛОЖИТЬ ПОДМЕННЫЙ АППАРАТ"
            if user_data['equipment'] == 'УЗИ':
                admin_message += f"\nТип УЗИ: {user_data.get('uzi_type', 'Не указан')}"
    
    await context.application.bot.send_message(
        chat_id=797093764, 
        text=admin_message
    )
    
    await update.message.reply_text(
        'Спасибо! Ваш запрос передан эксперту. '
        'Мы свяжемся с вами в ближайшее время.\n\n'
        'Для нового расчета отправьте /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context):
    await update.message.reply_text(
        'Расчет отменен. Для нового расчета отправьте /start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    # ВАЖНО: Используем Application вместо Updater
    application = Application.builder().token("8378315151:AAGkqCMlMbD54PdlpOjgxy1F-EatxPtgRTg").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EQUIPMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_type)],
            UZI_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, uzi_type)],
            EQUIPMENT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_details)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year)],
            COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, cost)],
            DOWNTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, downtime)],
            MIN_RESEARCH_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_research_cost)],
            MAX_RESEARCH_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_research_cost)],
            MIN_STUDIES_PER_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, min_studies_per_hour)],
            MAX_STUDIES_PER_HOUR: [MessageHandler(filters.TEXT & ~filters.COMMAND, max_studies_per_hour)],
            WORKING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, working_days)],
            NEED_REPLACEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, need_replacement)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
