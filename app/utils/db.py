from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.utils.logger import logger

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB Atlas...")
    if not settings.MONGODB_URL or settings.MONGODB_URL.strip() == "":
        logger.error("MONGODB_URL environment variable is not configured. Running without database integration.")
        return

    try:
        db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
        db_instance.db = db_instance.client[settings.MONGODB_DB_NAME]
        
        # Ping the database to ensure connection is working (with a short timeout)
        import asyncio
        await asyncio.wait_for(db_instance.client.admin.command('ping'), timeout=5.0)
        logger.info("Successfully connected to MongoDB database!")
    except Exception as e:
        logger.error(f"Failed to establish connection to MongoDB: {e}. Running without database integration.")
        db_instance.db = None

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
        logger.info("MongoDB connection closed successfully.")
