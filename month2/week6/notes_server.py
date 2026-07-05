import json
import os
from openai import OpenAI
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "用来保存用户笔记到obisidian里，当用户说“请帮我保存xxx时”触发，用户需要提供需要保存的内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "需要保存的内容，通常是一段文字描述",
                    },
                    "tag": {
                        "type": "string",
                        "description": '标签分类，通常是一段概括性的简短文字描述，例如"python知识点"',
                    },
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_note",
            "description": "用来搜索用户笔记里的内容，用户需要提供搜索关键词，当用户说“帮我找一下笔记里xx的相关内容”时触发",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_word": {
                        "type": "string",
                        "description": '搜索关键字，例如"python知识点"',
                    }
                },
                "required": ["key_word"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "del_note",
            "description": "用来删除用户笔记里的内容，用户需要提供删除的笔记id，当用户说“帮我删掉第五条笔记”时触发",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "description": "要删除的笔记id"}
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_note",
            "description": "列出用户保存的所有笔记，适用于用户想要浏览、回顾全部笔记的场景",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTE_FILE = os.path.join(BASE_DIR, "note.json")


def load_note() -> list[dict]:
    if os.path.exists(NOTE_FILE):
        with open(NOTE_FILE, "r", encoding="utf-8") as f:
            notes = json.load(f)
    else:
        notes = []
    return notes


def list_note(params: dict) -> tuple[str, str]:
    notes = load_note()
    if not notes:
        return "ok", "暂无笔记"
    return "ok", f"全部笔记为： {notes}"


def save_note(params: dict) -> tuple[bool, str]:
    # 返回 (True|False, 消息)
    try:
        notes = load_note()
    except Exception as e:
        return False, f"保存笔记时读文件出错，错误原因：{e}"

    # 并发隐患
    next_id = max((item["id"] for item in notes), default=0) + 1
    # 这种写法不可取，因为python传参传的引用，会把调用方的params也修改了
    # 只针对list和dict这种可变对象的update append等原地修改的操作，赋值操作只是指向新对象，并不会改变原对象
    # params.update({'id':next_id})
    # notes.append(params)
    new_params = {**params, "id": next_id}
    notes.append(new_params)
    try:
        with open(NOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        return True, "保存成功"
    except Exception as e:
        return False, f"保存失败，失败原因为：{e}"


def del_note(params: dict) -> tuple[str, str]:
    # 返回 ("ok" | "not_found" | "error", 消息)
    try:
        notes = load_note()
    except Exception as e:
        return "error", f"删除笔记时读文件出错，错误原因：{e}"

    raw_id = params.get("id")
    if raw_id is None:
        return "not_found", "缺少笔记ID"
    id = int(raw_id)
    if id <= 0:
        return "not_found", "该条笔记不存在"

    # ori_len = len(notes)
    # new_notes = [item for item in notes if item['id'] != id]

    # if len(new_notes) == ori_len:
    #     return "该条笔记不存在"
    flag = False
    for i in range(len(notes) - 1, -1, -1):
        if notes[i]["id"] == id:
            del notes[i]
            flag = True
            break

    if not flag:
        return "not_found", "该条笔记不存在"

    try:
        with open(NOTE_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
        return "ok", "删除成功"
    except Exception as e:
        return "error", f"删除笔记失败， 错误原因为{e}"


def search_note(params: dict) -> tuple[str, str]:
    # 返回 ("ok" | "not_found" | "error", 消息)
    result = []
    try:
        notes = load_note()
    except Exception as e:
        return "error", f"搜索笔记时读文件出错，错误原因为：{e}"

    key_word = params.get("key_word", "").lower()
    for item in notes:
        content = item.get("content", "").lower()
        tag = item.get("tag", "").lower()
        if key_word in content or key_word in tag:
            result.append(item)
    if result:
        return "ok", f"搜索到相关笔记，相关笔记为：{result}"
    else:
        return "not_found", "未找到相关笔记"


available_tools = {
    "save_note": save_note,
    "search_note": search_note,
    "del_note": del_note,
    "list_note": list_note,
}
messages = {}


def send_message(msg_list: list):
    response = client.chat.completions.create(
        model="deepseek-chat", messages=msg_list, tools=tools
    )
    return response.choices[0].message


app = FastAPI()


class ChatRequest(BaseModel):
    request: str | None = None
    session_id: str


class ChatResponse(BaseModel):
    reply: str | None = None


class SaveRequest(BaseModel):
    content: str
    tag: str | None = None


# 调用llm
@app.post("/chat")
def chat_server(chatRequest: ChatRequest):
    # global messages
    session_messages = messages.setdefault(chatRequest.session_id, [])
    user_input = chatRequest.request
    if not user_input:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="请输入内容")
        # return ChatResponse(reply="请输入内容")
    session_messages.append({"role": "user", "content": user_input})
    try:
        message = send_message(session_messages)
        print(f"llm第一次的返回为：{message}")
    except Exception as e:
        session_messages.pop()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"调用模型失败:{e}"
        )
        # return ChatResponse(reply=f"调用模型失败:{e}")

    while message.tool_calls:
        session_messages.append(message)
        for tool in message.tool_calls:
            func = available_tools.get(tool.function.name, None)
            tool_id = tool.id
            try:
                params = json.loads(tool.function.arguments)
            except Exception as e:
                session_messages.append(
                    {"role": "tool", "tool_call_id": tool_id, "content": "工具参数错误"}
                )
                continue
            if func:
                try:
                    _, result = func(params)
                except Exception as e:
                    result = f"工具执行出错： {e}"
                session_messages.append(
                    {"role": "tool", "tool_call_id": tool_id, "content": result}
                )
            else:
                session_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": f"未知工具：{tool.function.name}",
                    }
                )

        try:
            message = send_message(session_messages)
            print(f"llm第二次的返回为：{message}")
        except Exception as e:
            session_messages.append(
                {
                    "role": "assistant",
                    "content": "抱歉，处理您的请求时遇到错误。如果刚进行了保存操作，可能已完成，请勿重复保存。",
                }
            )
            return ChatResponse(reply=session_messages[-1]["content"])

    session_messages.append({"role": "assistant", "content": message.content})
    return ChatResponse(reply=message.content)


# 保存笔记
@app.post("/notes")
def save_server(saveRequest: SaveRequest):
    ok, result = save_note(saveRequest.model_dump())
    if not ok:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)
    return {"message": result}


# 获取全部笔记
@app.get("/notes")
def get_server():
    result = load_note()
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="未找到笔记")
    return {"笔记为": result}


# 根据关键词搜索笔记
@app.get("/notes/search")
def search_server(key_word: str | None = None):
    if key_word is None:
        return "请输入搜索关键词"
    status_code, result = search_note({"key_word": key_word})
    if status_code == "not_found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=result)
    if status_code == "error":
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)
    return {"message": result}


# 删除某条笔记
@app.delete("/notes/{note_id}")
def delete_server(note_id: int):
    status_code, result = del_note({"id": note_id})
    if status_code == "not_found":
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=result)
    if status_code == "error":
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result)
    return {"message": result}
