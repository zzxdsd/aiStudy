import requests

BASE_URL = "http://127.0.0.1:8000"
note_id = 4

headers = {
    "Content-type": "application/json",
}

data_chat = {
    "request": "python字典是什么？请用一句话说明并帮我保存到字典",
    "session_id": "1",
}

data_save = {"content": "今天是周六", "tag": "日期"}

req_chat = requests.post(f"{BASE_URL}/chat", headers=headers, json=data_chat)
print(f"chat_server的状态码为：{req_chat.status_code}, 返回为：{req_chat.json()}")

req_save = requests.post(f"{BASE_URL}/notes", headers=headers, json=data_save)
print(f"save_server的状态码为：{req_save.status_code}, 返回为：{req_save.json()}")

req_get = requests.get(f"{BASE_URL}/notes")
print(f"get_server的状态码为：{req_get.status_code}, 返回为：{req_get.json()}")

req_search = requests.get(f"{BASE_URL}/search", params={"key_word": "python"})
print(f"search_server的状态码为：{req_search.status_code}, 返回为：{req_search.json()}")

req_delete = requests.delete(f"{BASE_URL}/notes/{note_id}")
print(f"delete_server的状态码为：{req_delete.status_code}, 返回为：{req_delete.json()}")
