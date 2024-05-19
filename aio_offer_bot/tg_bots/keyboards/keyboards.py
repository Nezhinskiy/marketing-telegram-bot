from telethon import Button




def unsub_answer_keyboard(answers, buttons):
    keyboard = [
        [Button.inline(answer, data=f'answer_{idx}')]
        for idx, answer in enumerate(answers)
    ]
    keyboard.append(
        [Button.inline(buttons.hand_write_inline_button, data='hand_write')]
    )
    return keyboard
