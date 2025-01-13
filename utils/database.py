import re
import logging

from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError

from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER
from .helpers import unpack_new_file_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
database = client[DATABASE_NAME]
instance = Instance.from_db(database)


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME

@instance.register
class Links(Document):
    name = fields.StrField(required=True)
    link = fields.StrField(required=True)
    category = fields.StrField(required=True)
    searchURL = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$name', )


async def save_file(media):
    """Save file in database"""

    file_id, file_ref = unpack_new_file_id(media.file_id)

    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=media.file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
    else:
        try:
            await file.commit()
        except DuplicateKeyError:
            logger.warning(media.file_name + " is already saved in database")
        else:
            logger.info(media.file_name + " is saved in database")


async def get_search_results(query, file_type=None, max_results=10, offset=0):
    """For given query return (results, next_offset)"""

    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_\(\)\[\]]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], ''

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter)

    # Sort by recent
    cursor.sort('$natural', -1)

    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)

    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset

async def add_link(name, link, category, searchURL=None):
    """
    Add a new link to the database.
    :param name: Name or title of the link.
    :param link: The URL of the link.
    :param category: Category of the link.
    :param searchURL: Optional search URL for the link.
    :return: Success message or error.
    """
    try:
        # Check if the link already exists
        existing_link = await Links.find_one({"link": link})
        if existing_link:
            return f"Link '{name}' already exists in the database."

        # Add the new link
        new_link = Links(name=name, link=link, category=category, searchURL=searchURL)
        await new_link.commit()
        return True
    except Exception as e:
        logger.exception(f"Error adding link: {str(e)}")
        return False


# Fetch links by category with pagination
async def get_links_by_category(category, skip, limit):
    try:
        results = await Links.find({"category": category}).skip(skip).limit(limit).to_list(length=limit)
        return results
    except Exception as e:
        logger.exception('Failed to get links by category')


# Get distinct categories
async def get_categories():
    return await Links.find().distinct("category")