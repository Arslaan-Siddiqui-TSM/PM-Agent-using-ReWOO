import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure model with better rate limiting and retry settings
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.6,
    google_api_key=GOOGLE_API_KEY,
    max_retries=6,  # Increase max retries for rate limits
    request_timeout=120,  # Increase timeout to 2 minutes
)
