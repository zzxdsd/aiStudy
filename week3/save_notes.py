#伪代码
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
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)


tools =[
    {   
        'type': 'function',
        'function':{
            'name': 'save_note',
            'description': '用来保存用户笔记、知识点、计划到obisidian里，当用户说“请帮我保存xxx时”触发，用户需要提供需要保存的内容',
            'parameters': {
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': '需要保存的内容，通常是一段文字描述'
                    },
                    'tag': {
                        'type': 'string',
                        'description': '标签分类，通常是一段概括性的简短文字描述，例如"python知识点"'
                    }
                },
                'required': ['content']
            }
        }
    }
]

def send_message(messages):
    response = client.chat.completions.create(
        model = 'deepseek-chat',
        messages= messages,
        tools = tools
    )

    return response.choices[0].message

def load_note():
    if os.path.exists('note.json'):
        with open('note.json', 'r', encoding= 'utf-8') as f:
            notes = json.load(f)
    else:
        notes = []
    return notes

def save_note(f_para):
    # content = f_para['content']
    # tag = f_para['tag']
    try:
        notes = load_note()
    except Exception as e:
        print(f'读取笔记失败：{e}')
        notes = []

    notes.append(f_para)
    try:
        with open ('note.json', 'w', encoding = 'utf-8') as f:
            json.dump(notes, f, ensure_ascii = False, indent = 2)
            return '保存笔记成功'
    except Exception as e:
        print(f'保存笔记失败，error: {e}')
        return f'保存笔记失败，原因为：{e}'
    
available_tools = {'save_note': save_note}


messages = []

print('下面可以开始对话，输入quit或exit退出对话', '-'*30)

while True:
    user_input = input('\n你：').strip()
    if not user_input:
        continue
    if user_input.lower() in ['quit', 'exit']:
        break

    messages.append({'role': 'user', 'content': user_input})
    try:
        message = send_message(messages)
    except Exception as e:
        print(f'调用模型出错: {e}')
        messages.pop()
        continue

    # 考虑模型返回存在多个tool_cslls
    if message.tool_calls:
        messages.append(message)
        for tool in message.tool_calls:
            tool_id = tool.id
            f_name = tool.function.name
            f_para = json.loads(tool.function.arguments)  #是个str
            func = available_tools.get(f_name)
            if func:
                results = func(f_para)
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': results})
            else:
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': f'未知工具: {f_name}'})
        message = send_message(messages)
        print(f'Model:\t{message.content}')
    else:
        messages.append({'role': 'assistant', 'content': message.content})
        print(f'Model:\t{message.content}')
    # print(f'模型返回为：{message}')
        

