import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
REDIS_URL = os.getenv("REDIS_URL")