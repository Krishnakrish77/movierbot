import os
import logging

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import START_MSG, CHANNELS, ADMINS, INVITE_MSG
from utils import Media
from utils.database import add_link, get_categories
from utils.keyboard import generate_inline_category_keyboard

logger = logging.getLogger(__name__)


@Client.on_message(filters.command('start'))
async def start(bot, message):
    """Start command handler"""
    if len(message.command) > 1 and message.command[1] == 'subscribe':
        await message.reply(INVITE_MSG)
    else:
        buttons = [[
            InlineKeyboardButton('Search Here', switch_inline_query_current_chat=''),
            InlineKeyboardButton('Go Inline', switch_inline_query=''),
            InlineKeyboardButton('Get Links', callback_data='categories'),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(START_MSG, reply_markup=reply_markup)


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if not (reply and reply.media):
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    msg = await message.reply("Processing...⏳", quote=True)

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media:
            media.file_type = file_type
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'file_type': media.file_type,
        'mime_type': media.mime_type
    })

    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')

@Client.on_message(filters.command("addlink") & filters.user(ADMINS))
async def create_link(client, message):
    """
    Add a new link to the database.
    Usage: /addlink category title url [searchURL]
    """
    try:
        # Extract command arguments safely
        args = message.command[1:]

        # Check if enough arguments are provided
        if len(args) < 3:
            await message.reply_text("Usage: /addlink category title url [searchURL]")
            return

        # Unpack mandatory arguments
        category = args[0]
        title = args[1]
        url = args[2]

        # Unpack optional argument if present
        search_url = args[3] if len(args) == 4 else None

        # Add the link to the database
        success = await add_link(category, title, url, search_url)
        if success:
            reply = f"✅ Link added to category '{category}' with title '{title}'."
            if search_url:
                reply += f"\n🔍 Search URL: {search_url}"
            await message.reply_text(reply)
        else:
            await message.reply_text("❌ Failed to add the link. Please try again.")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")