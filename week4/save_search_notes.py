import json
import os
from openai import OpenAI

client = OpenAI(
    api_key= os.environ.get('DEEPSEEK_API_KEY'),
    base_url= "https://api.deepseek.com",
)

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'save_note',
            'description': '用来保存用户笔记到obisidian里，当用户说“请帮我保存xxx时”触发，用户需要提供需要保存的内容',
            'parameters':{
                'type': 'object',
                'properties': {
                    'content': {
                        'type': 'string',
                        'description': '需要保存的内容，通常是一段文字描述'
                    },
                    'tag': {
                        'type': 'string',
                        'description': '标签分类，通常是一段概括性的简短文字描述，例如"python知识点'
                    }
                },
                'required' : ['content']
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_note',
            'description': '用来搜索用户笔记里的内容，用户需要提供搜索关键词，当用户说“帮我找一下笔记里xx的相关内容”时触发',
            'parameters': {
                'type': 'object',
                'properties': {
                    'key_word':{
                        'type': 'string',
                        'description': '搜索关键字，例如"python知识点"'
                    }
                    #key_word和tag在语义上通常很相似，语言模型很难区分，我认为应该交给业务（函数）去做
                    # 'tag': {
                    #     'type': 'string',
                    #     'description': '标签分类，通常是一段概括性的简短文字描述，例如"python知识点'
                    # }
                },
                'required': ['key_word']
            }
        }
    }
]

def load_note():
    if os.path.exists('note.json'):
        with open('note.json', 'r', encoding='utf-8') as f:
            notes = json.load(f)
    else:
        notes = []
    return notes

def save_note(f_para):
    try:
        notes = load_note()
    except Exception as e:
        print(f'读文件出错，错误原因为：{e}')
        notes = []
    notes.append(f_para)
    try:
        with open('note.json', 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii = False, indent = 2)
        return '保存成功'
    except Exception as e:
        print(f'写文件出错，错误原因为：{e}')
        # notes.pop()  ?????
        return f'保存失败，失败原因为：{e}'

def search_note(f_para):
    result= []
    try:
        notes = load_note()
    except Exception as e:
        print(f'读文件出错，错误原因为：{e}')
        return f'笔记文件读取失败'
    
    for item in notes:
        if f_para['key_word'].lower() in item['content'].lower() or f_para['key_word'].lower() in item['tag'].lower():
            result.append(item)
    if result:
        return f'搜索到相关笔记，相关笔记为：{result}'
    else:
        return '未找到相关笔记'



availabel_tools = {'save_note': save_note, 'search_note': search_note}
messages = []

def send_message(messages):
    response = client.chat.completions.create(
        model = 'deepseek-chat',
        messages = messages,
        tools = tools
    )
    return response.choices[0].message

while True:
    user_input = input(f'\n你：').strip()
    if not user_input:
        continue
    if user_input in ['quit', 'exit']:
        break
    messages.append({'role': 'user', 'content': user_input})
    try:
        message = send_message(messages)
        print(f'第一次返回的message：{message}')
    except Exception as e:
        print(f'调用模型失败：{e}')
        messages.pop()
        continue

    while message.tool_calls:
        messages.append(message)
        for tool in message.tool_calls:
            tool_id = tool.id
            f_name = tool.function.name
            f_para = json.loads(tool.function.arguments)
            func = availabel_tools[f_name]
            if func:
                result = func(f_para)
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': result})
            else:
                messages.append({'role': 'tool',  'tool_call_id': tool_id, 'content':f'未知工具：{f_name}'})        
        try:
            message = send_message(messages)
            print(f'第2次返回的message：{message}')
        except Exception as e:
            print(f'调用模型失败：{e}')
            messages.pop()
            continue
    messages.append({'role': 'assistant', 'content': message.content})
    print(f'Model:\t{message.content}')
