from fastapi import FastAPI

app = FastAPI(title="Chess Tutor")

@app.get("/")
def root():
    return {"status": "ok"}