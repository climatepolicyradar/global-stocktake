import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONCEPTS_TO_INDEX: list[str] = os.getenv("CONCEPTS_TO_INDEX", "").split(",")
