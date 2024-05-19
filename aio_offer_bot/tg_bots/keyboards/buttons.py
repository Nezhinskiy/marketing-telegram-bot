menu_button = "⤴️Меню"
state2chat_gpt_button = "📝Режим: Текст"
retry_button = "🔄Повторить"
delete_dialog_button = "🗑Очистить историю"
state2img_mj_button = "🖼Режим: Графика"
instructure_button = "📋Инструкция"
pay_button = "💰Оплата"
support_button = "👨‍🚀Поддержка"
referal_button = "🤝Партнерка"
sub_chat_gpt_button = "ChatGPT"
sub_mj_button = "Midjourney"
sub_all_button = "Все включено"
unlock_mj_command = "/unlock_mj"
info_mj_command = '/info_mj'
reconnect_mj_ws_command = '/reconnect_mj_ws'
send_message_to_users_command = '/send_message'
send_message_to_unpaid_users_command = '/send_unpaid_message'
mj_queue_stats_command = '/mjq'

buttons_dict = {
    'menu_button': menu_button,
    'state2chat_gpt_button': state2chat_gpt_button,
    'retry_button': retry_button,
    'delete_dialog_button': delete_dialog_button,
    'state2img_mj_button': state2img_mj_button,
    'pay_button': pay_button,
    'support_button': support_button,
    'referral_button': referal_button,
    'sub_chat_gpt_inline': sub_chat_gpt_button,
    'sub_mj_inline': sub_mj_button,
    'sub_all_inline': sub_all_button,
    'unlock_mj_command': unlock_mj_command,
    'info_mj_command': info_mj_command,
    'reconnect_mj_ws_command': reconnect_mj_ws_command,
    'send_message_to_users_command': send_message_to_users_command,
    'send_message_to_unpaid_users_command': send_message_to_unpaid_users_command,
    'week_inline': '1 Неделя',
    'month_inline': '1 Месяц',
    'quarter_inline': '1 Квартал (3 мес.)',
    'year_inline': '1 Год',
    'unsubscribe_inline': 'Отписка',
    'pay_inline': 'Оплатить',
    'next_lesson': '⏩Дальше',
    'return_to_beginning': '🎓В начало обучения',
    'next_education': '🎓Следующее обучение',
    'education_button': '🎓Обучение',
    'previous_lesson': 'Назад',
    'pass_education': 'Пропустить',
    'start_education': 'Запустить',
    'subscribed_channel': 'Я подписался✅',
    'add_admin_bot_command': '/add_admin_bot_command'
}


all_args_commands = [
    send_message_to_users_command,
    send_message_to_unpaid_users_command,
    unlock_mj_command,
    info_mj_command,
    reconnect_mj_ws_command,
]


def get_all_args_commands(buttons):
    return [
        buttons.send_message_to_users_command,
        buttons.send_message_to_unpaid_users_command,
        buttons.unlock_mj_command,
        buttons.info_mj_command,
        buttons.reconnect_mj_ws_command,
        buttons.add_admin_bot_command
    ]


def get_all_buttons(buttons):
    return [
        buttons.menu_button,
        buttons.state2chat_gpt_button,
        buttons.retry_button,
        buttons.delete_dialog_button,
        buttons.state2img_mj_button,
        buttons.pay_button,
        buttons.support_button,
        buttons.referral_button,
        buttons.send_message_to_users_command,
        buttons.send_message_to_unpaid_users_command,
        buttons.send_message_to_unsub_users_command,
        buttons.return_to_beginning,
        buttons.next_education,
        buttons.education_button,
        buttons.unlock_mj_command,
        buttons.info_mj_command,
        buttons.reconnect_mj_ws_command,
        "/start",
        buttons.gpt_4_button,
        buttons.gpt_continue
    ]


def is_command(event, buttons):
    return any(
        [event.text.startswith(cmd) for cmd in get_all_buttons(buttons)]
    )
