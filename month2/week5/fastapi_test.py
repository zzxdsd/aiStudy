from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Note(BaseModel):
    content: str
    tag: str | None = None


@app.get("/items/{item_id}")
def item_read(item_id: int):
    return {"item_id": item_id}


@app.get("/search/")
def search(key_word: str | None = None):
    if key_word is None:
        return {"key_word": "搜索关键词为空"}
    return {"key_word": key_word}


@app.post("/notes")
def update(note: Note):
    return {"笔记内容": note.content, "标签": note.tag}
    # return note


@app.get("/health")
def get_status():
    return {"status": "ok"}
