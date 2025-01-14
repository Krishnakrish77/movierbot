from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_inline_category_keyboard(categories):
    buttons = []
    for category in categories:
        buttons.append(
            [InlineKeyboardButton(text=category, callback_data=f"category:{category}")]
        )
    return InlineKeyboardMarkup(buttons)

def generate_pagination_keyboard(category, page):
    return InlineKeyboardMarkup([
        [
            # InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{category}_{page}"),
            InlineKeyboardButton("Back", callback_data="categories"),
            # InlineKeyboardButton("➡️ Next", callback_data=f"next_{category}_{page}")
        ]
    ])
