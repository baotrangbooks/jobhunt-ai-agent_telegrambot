from dotenv import load_dotenv
import os

load_dotenv() # Lệnh này sẽ quét file .env và nạp các biến vào hệ thống

from webhooks import app
import uvicorn


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)