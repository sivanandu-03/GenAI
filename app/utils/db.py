from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.logger import logger

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB Atlas...")
    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
        
        # Ping the database to ensure connection is working
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB database!")
    except Exception as e:
        logger.critical(f"Failed to establish connection to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed successfully.")
