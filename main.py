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
EQUIPMENT_TYPE, UZI_TYPE, EQUIPMENT_DETAILS, YEAR, SHORT_STUDIES_COUNT, SHORT_STUDY_COST, LONG_STUDIES_COUNT, LONG_STUDY_COST, DOWNTIME, WORKING_DAYS, NEED_REPLACEMENT, CONTACT = range(12)

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
        'из-за простоя оборудования.\n\n'
        '📊 <b>Методика расчета основана на нормативах Минздрава РФ:</b>\n'
        '• Учет разной длительности исследований (15-20 мин и 30-60 мин)\n'
        '• Средневзвешенный расчет дохода в час\n'
        '• Реальные показатели потерь доходов\n\n'
        'Выберите тип аппарата:',
        parse_mode='HTML',
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
        'Введите год производства оборудования (для статистики):'
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
            '📊 <b>Учет структуры исследований</b>\n\n'
            'Согласно нормативам Минздрава, исследования различаются по длительности:\n'
            '• Короткие: 15-20 минут\n• Длинные: 30-60 минут\n\n'
            'Сколько <b>коротких исследований (15-20 мин)</b> вы проводите в час?',
            parse_mode='HTML'
        )
        return SHORT_STUDIES_COUNT
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите год цифрами:')
        return YEAR

async def short_studies_count(update: Update, context):
    user_data = context.user_data
    try:
        short_count = float(update.message.text)
        user_data['short_studies_count'] = short_count
        
        await update.message.reply_text(
            'Введите <b>среднюю стоимость короткого исследования</b> (15-20 мин) в рублях:',
            parse_mode='HTML'
        )
        return SHORT_STUDY_COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return SHORT_STUDIES_COUNT

async def short_study_cost(update: Update, context):
    user_data = context.user_data
    try:
        short_cost = float(update.message.text)
        user_data['short_study_cost'] = short_cost
        
        await update.message.reply_text(
            'Сколько <b>длинных исследований (30-60 мин)</b> вы проводите в час?',
            parse_mode='HTML'
        )
        return LONG_STUDIES_COUNT
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return SHORT_STUDY_COST

async def long_studies_count(update: Update, context):
    user_data = context.user_data
    try:
        long_count = float(update.message.text)
        user_data['long_studies_count'] = long_count
        
        await update.message.reply_text(
            'Введите <b>среднюю стоимость длинного исследования</b> (30-60 мин) в рублях:',
            parse_mode='HTML'
        )
        return LONG_STUDY_COST
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return LONG_STUDIES_COUNT

async def long_study_cost(update: Update, context):
    user_data = context.user_data
    try:
        long_cost = float(update.message.text)
        user_data['long_study_cost'] = long_cost
        
        # Расчет дохода в час
        hourly_income = (user_data['short_studies_count'] * user_data['short_study_cost'] + 
                        user_data['long_studies_count'] * user_data['long_study_cost'])
        user_data['hourly_income'] = hourly_income
        
        await update.message.reply_text(
            'Сколько <b>часов в день</b> простаивает оборудование в среднем?',
            parse_mode='HTML'
        )
        return DOWNTIME
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return LONG_STUDY_COST

async def downtime(update: Update, context):
    user_data = context.user_data
    try:
        downtime_hours = float(update.message.text)
        user_data['downtime'] = downtime_hours
        
        await update.message.reply_text(
            'Сколько <b>рабочих дней в месяце</b>? (частные клиники обычно 30):',
            parse_mode='HTML'
        )
        return WORKING_DAYS
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return DOWNTIME

async def working_days(update: Update, context):
    user_data = context.user_data
    try:
        working_days_value = int(update.message.text)
        if working_days_value < 1 or working_days_value > 31:
            await update.message.reply_text('Пожалуйста, введите число от 1 до 31:')
            return WORKING_DAYS
            
        user_data['working_days'] = working_days_value
        
        # Расчет потерь по новой формуле
        daily_loss = user_data['hourly_income'] * user_data['downtime']
        monthly_loss = daily_loss * working_days_value
        
        user_data['daily_loss'] = daily_loss
        user_data['monthly_loss'] = monthly_loss
        
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
    
    # Форматируем информацию об оборудовании
    equipment_info = user_data['equipment']
    if user_data['equipment'] == 'УЗИ' and 'uzi_type' in user_data:
        equipment_info = f"{user_data['equipment']} ({user_data['uzi_type']})"
    
    equipment_model_info = ""
    if 'equipment_details' in user_data and user_data['equipment_details']:
        equipment_model_info = f"\n• <b>Модель аппарата:</b> {user_data['equipment_details']}"
    
    # Определяем возможность предложения подменного оборудования
    replacement_offer = ""
    if need_replacement == 'Да':
        if user_data['equipment'] in NO_REPLACEMENT_EQUIPMENT:
            replacement_offer = f"\n\n⚠️ К сожалению, мы не предоставляем подменное оборудование для {user_data['equipment']} аппаратов"
        else:
            replacement_offer = f"\n\n🏥 МЫ МОЖЕМ ПРЕДЛОЖИТЬ ВАМ ПОДМЕННЫЙ {user_data['equipment'].upper()} АППАРАТ!"
            if user_data['equipment'] == 'УЗИ':
                replacement_offer += f"\nСпециализация: {user_data.get('uzi_type', 'универсальный')}"
    
    # Расчет структуры доходов для отчета
    short_income = user_data['short_studies_count'] * user_data['short_study_cost']
    long_income = user_data['long_studies_count'] * user_data['long_study_cost']
    total_hourly_income = short_income + long_income
    
    await update.message.reply_text(
        f"📉 <b>Результаты расчета по методике Минздрава РФ:</b>\n\n"
        f"• <b>Тип аппарата:</b> {equipment_info}{equipment_model_info}\n"
        f"• <b>Год выпуска:</b> {user_data['year']} ({user_data['equipment_age']} лет)\n"
        f"• <b>Простой:</b> {user_data['downtime']} ч/день\n"
        f"• <b>Рабочих дней:</b> {user_data['working_days']} в месяце\n\n"
        f"<b>СТРУКТУРА ДОХОДА В ЧАС:</b>\n"
        f"• Короткие исследования: {user_data['short_studies_count']} × {user_data['short_study_cost']:,.0f} руб = {short_income:,.0f} руб\n"
        f"• Длинные исследования: {user_data['long_studies_count']} × {user_data['long_study_cost']:,.0f} руб = {long_income:,.0f} руб\n"
        f"• <b>Итого в час:</b> {total_hourly_income:,.0f} руб\n\n"
        f"<b>ВАШИ ПОТЕРИ:</b>\n"
        f"• В день: ~{user_data['daily_loss']:,.0f} руб\n"
        f"• В месяц: ~{user_data['monthly_loss']:,.0f} руб{replacement_offer}\n\n"
        f"<i>Расчет основан на нормативах длительности исследований Минздрава РФ</i>\n\n"
        f"Хотите получить детальный расчет от эксперта? "
        f"Оставьте ваш телефон - перезвоню в течение 15 минут:",
        parse_mode='HTML'
    )
    return CONTACT

async def contact(update: Update, context):
    user_data = context.user_data
    phone = update.message.text
    
    # Формируем информацию об оборудовании
    equipment_info = user_data['equipment']
    if user_data['equipment'] == 'УЗИ' and 'uzi_type' in user_data:
        equipment_info = f"{user_data['equipment']} ({user_data['uzi_type']})"
    
    equipment_model_info = ""
    if 'equipment_details' in user_data and user_data['equipment_details']:
        equipment_model_info = f"\nМодель: {user_data['equipment_details']}"
    
    # Отправляем уведомление администратору с полной информацией
    admin_message = (
        "🚨 НОВЫЙ ЛИД С РАСЧЕТОМ ПО МЕТОДИКЕ МИНЗДРАВА!\n\n"
        f"Телефон: {phone}\n"
        f"Оборудование: {equipment_info}{equipment_model_info}\n"
        f"Год выпуска: {user_data['year']} ({user_data['equipment_age']} лет)\n"
        f"Доход в час: {user_data['hourly_income']:,.0f} руб\n"
        f"Потери в месяц: {user_data['monthly_loss']:,.0f} руб\n"
        f"Короткие исследования: {user_data['short_studies_count']} × {user_data['short_study_cost']:,.0f} руб\n"
        f"Длинные исследования: {user_data['long_studies_count']} × {user_data['long_study_cost']:,.0f} руб\n"
        f"Простой: {user_data['downtime']} ч/день\n"
        f"Подменное оборудование: {user_data['need_replacement']}\n"
        f"Рабочих дней: {user_data['working_days']}"
    )
    
    # Добавляем информацию о возможности подмены
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
    application = Application.builder().token("8378315151:AAGkqCMlMbD54PdlpOjgxy1F-EatxPtgRTg").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EQUIPMENT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_type)],
            UZI_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, uzi_type)],
            EQUIPMENT_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, equipment_details)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, year)],
            SHORT_STUDIES_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, short_studies_count)],
            SHORT_STUDY_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, short_study_cost)],
            LONG_STUDIES_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, long_studies_count)],
            LONG_STUDY_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, long_study_cost)],
            DOWNTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, downtime)],
            WORKING_DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, working_days)],
            NEED_REPLACEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, need_replacement)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main()
