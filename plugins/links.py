from pyrogram import Client, filters
from utils.database import get_categories, get_links_by_category
from utils.keyboard import generate_inline_category_keyboard, generate_pagination_keyboard

@Client.on_callback_query(filters.regex(r"^categories"))
async def categories(client, message):
    # Fetch all categories from the database
    categories = await get_categories()
    if not categories:
        await message.reply_text("No categories found.")
        return

    # Generate inline keyboard with categories
    keyboard = generate_inline_category_keyboard(categories)
    await message.edit_message_text(
        text="Choose a category:",
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex(r"^category:"))
async def show_links(client, callback_query):
    category = callback_query.data.split(":")[1]
    # Fetch the first 5 links in the selected category
    links = await get_links_by_category(category, skip=0, limit=10)

    if not links:
        await callback_query.message.edit_text(f"No links found in category: {category}")
        return

    # Format the links as a response message
    response = f"Links in {category}:\n\n"
    response += "\n".join([f"{link['name']}: {link['link']}" for link in links])

    # Generate pagination buttons (optional)
    keyboard = generate_pagination_keyboard(category, 1)

    # Edit the original message to show links and pagination
    await callback_query.edit_message_text(
        text=response,
        disable_web_page_preview=True,
        reply_markup=keyboard
    )
