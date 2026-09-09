import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APP_NAME = os.getenv("APP_NAME", "RetailSense-AI")
ENV = os.getenv("ENV", "development")

def main():
    print(f"Starting {APP_NAME} in [{ENV}] mode...")

if __name__ == "__main__":
    main()
