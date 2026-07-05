# 伪代码
# 定义一个client对象
# 定义一个tools里，里面放对save_notes函数的描述
# 定义一个建立连接，发送消息的函数send_message
# 1、把用户说的话（会触发函数调用）放进messages，并send_message
# 2、把模型返回的message提取出函数名及参数，进行函数调用（把message对象 append进消息列表
# 3、把函数调用结果append进messages里，send_message
# 4、拿到模型返回的message对象，提取回答

import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)


tools = [
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "用来保存用户笔记、知识点、计划到obisidian里，当用户说“请帮我保存xxx时”触发，用户需要提供需要保存的内容",
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
    }
]


def send_message(messages):
    response = client.chat.completions.create(
        model="deepseek-chat", messages=messages, tools=tools
    )

    return response.choices[0].message


def load_history():
    if not os.path.exists("history.json"):
        return []
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"历史文件格式损坏：{e}")
        return []


def save_history(messages):
    with open("history.json", "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def load_note():
    if os.path.exists("note.json"):
        with open("note.json", "r", encoding="utf-8") as f:
            notes = json.load(f)
    else:
        notes = []
    return notes


def save_note(f_para):
    try:
        notes = load_note()
    except Exception as e:
        print(f"读取笔记失败：{e}")
        # 代码健壮性修改1：此时继续写笔记，如果本地本身有note.json，此时写入就是把之前的笔记全覆盖了，所以要中止
        return f"保存笔记时读文件出错，错误原因：{e}"

    notes.append(f_para)
    try:
        with open("note.json", "w", encoding="utf-8") as f:
            json.dump(notes, f, ensure_ascii=False, indent=2)
            return "保存笔记成功"
    except Exception as e:
        print(f"保存笔记失败，error: {e}")
        return f"保存笔记失败，原因为：{e}"


available_tools = {"save_note": save_note}


messages = load_history()

print("下面可以开始对话，输入quit或exit退出对话", "-" * 30)

while True:
    user_input = input("\n你：").strip()
    if not user_input:
        continue
    if user_input.lower() in ["quit", "exit"]:
        save_history(messages)
        break

    messages.append({"role": "user", "content": user_input})
    try:
        message = send_message(messages)
    except Exception as e:
        print(f"调用模型出错: {e}")
        messages.pop()
        continue

    # 考虑模型返回存在多个tool_cslls
    while message.tool_calls:
        messages.append(message)
        for tool in message.tool_calls:
            tool_id = tool.id
            f_name = tool.function.name
            # 代码健壮性修改2：虽然大模型通常返回合法 JSON，但网络或模型异常时可能拿到非 JSON 字符串，
            # 直接 json.loads 会抛异常并中断整个对话循环。
            try:
                f_para = json.loads(tool.function.arguments)
            except Exception as e:
                messages.append(
                    {"role": "tool", "tool_call_id": tool_id, "content": "工具参数错误"}
                )
                continue
            func = available_tools.get(f_name)
            if func:
                results = func(f_para)
                messages.append(
                    {"role": "tool", "tool_call_id": tool_id, "content": results}
                )
            else:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": f"未知工具: {f_name}",
                    }
                )
        # 代码健壮性修改3：考虑第二次调用模型失败
        try:
            message = send_message(messages)
        except Exception as e:
            print(f"调用工具后模型返回失败：{e}")
            messages.append(
                {
                    "role": "assistant",
                    "content": "抱歉，处理您的请求时遇到错误。如果刚进行了保存操作，可能已完成，请勿重复保存。",
                }
            )
            print(f"Model:\t{messages[-1]['content']}")
            break
    # 代码健壮性修改4：加了一层守卫，若代码正常执行进入else，若while被break出来的话，证明本轮作废，没有assistant输出
    else:
        messages.append({"role": "assistant", "content": message.content})
        print(f"Model:\t{message.content}")

# print(f'messages: {messages}')
# print(f'模型返回为：{message}')
