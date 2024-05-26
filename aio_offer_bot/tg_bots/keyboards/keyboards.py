from telethon import Button

from tg_bots.keyboards.buttons import (dating_button, info_button,
                                       lead_magnet_button)


def get_menu_keyboard(tgbot):
    return  [
        [Button.inline(
            tgbot.lead_magnet_button, data=lead_magnet_button
        )],
        [Button.inline(
            tgbot.dating_button, data=dating_button
        )],
        [Button.inline(
            tgbot.info_button, data=info_button
        )],
    ]


def get_lead_magnet_keyboard(tgbot):
    return [
        [Button.inline(
            tgbot.dating_button, data=dating_button
        )],
        [Button.inline(
            tgbot.info_button, data=info_button
        )],
    ]


def get_dating_keyboard(tgbot):
    return [
        [Button.inline(
            tgbot.lead_magnet_button, data=lead_magnet_button
        )],
        [Button.inline(
            tgbot.info_button, data=info_button
        )],
    ]


def get_answers_keyboard(answers: list[str]):
    return [
        [Button.inline(
            answer, data=f'answer_{i}'
        )] for i, answer in enumerate(answers)
    ]


def get_info_keyboard(tgbot):
    return [
        [Button.inline(
            tgbot.lead_magnet_button, data=lead_magnet_button
        )],
        [Button.inline(
            tgbot.dating_button, data=dating_button
        )],
    ]
