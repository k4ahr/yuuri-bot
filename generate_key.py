import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

def main():
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        print("Error: ENCRYPTION_KEY not found in .env file.")
        return
        
    try:
        fernet = Fernet(encryption_key.encode())
    except Exception as e:
        print(f"Error initializing Fernet: {e}")
        return

    server_id = input("Enter the Discord Server ID to license: ").strip()
    if not server_id.isdigit():
        print("Error: Server ID must be a number.")
        return
        
    encrypted = fernet.encrypt(server_id.encode('utf-8'))
    print("\nActivation Key (Provide this to the server admin):")
    print("-" * 50)
    print(encrypted.decode('utf-8'))
    print("-" * 50)

if __name__ == "__main__":
    main()

