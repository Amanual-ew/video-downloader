from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Social Video Downloader API is running!"}