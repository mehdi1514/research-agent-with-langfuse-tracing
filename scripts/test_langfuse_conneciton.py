import os
from langfuse import get_client
from dotenv import load_dotenv

load_dotenv()

def test_langfuse_connection():
    print("Loading envrionment variables")

    try:
        LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY")
        LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY")
        LANGFUSE_BASE_URL = os.environ.get("LANGFUSE_BASE_URL")
        print("Environment variables loaded successfully")
    except Exception as e:
        print(f"Error loading environment variables: {e}")
        return 1

    print("Connecting to Langfuse...")

    langfuse = get_client()

    if langfuse.auth_check():
        print("Langfuse client is authenticated and ready!")
    else:
        print("Authentication failed. Please check your credentials and host.")

if __name__ == "__main__":
    test_langfuse_connection()
