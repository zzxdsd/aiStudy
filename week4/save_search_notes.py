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
                        'description': '标签分类，通常是一段概括性的简短文字描述，例如"python知识点"'
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
        print(f'保存笔记时读文件出错，错误原因为：{e}')
        #代码健壮性修改1：此时继续写笔记，如果本地本身有note.json，此时写入就是把之前的笔记全覆盖了，所以要中止
        return f'保存笔记时读文件出错，错误原因：{e}' 
    notes.append(f_para)
    try:
        with open('note.json', 'w', encoding='utf-8') as f:
            json.dump(notes, f, ensure_ascii = False, indent = 2)
        return '保存成功'
    except Exception as e:
        print(f'写文件出错，错误原因为：{e}')
        # notes.pop() 不需要pop，notes为局部变量，出错就直接return了，下回调用save_note会重新加载notes
        return f'保存失败，失败原因为：{e}'

def search_note(f_para):
    result= []
    try:
        notes = load_note()
    except Exception as e:
        print(f'搜索笔记时读文件出错，错误原因为：{e}')
        return f'搜索笔记时读文件出错，错误原因为：'
    
    for item in notes:
        #代码健壮性修改2：tag不一定有，直接字典[]程序会崩掉,且如果get返回none，lower()也会崩掉，所以要把none转字符串
        key_word = f_para.get('key_word', '').lower()
        content = item.get('content', '').lower()
        tag = item.get('tag', '').lower()
        if key_word in content or key_word in tag:
            result.append(item)
    if result:
        return f'搜索到相关笔记，相关笔记为：{result}'
    else:
        return '未找到相关笔记'



available_tools = {'save_note': save_note, 'search_note': search_note}
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
    #代码健壮性修改3：设置备份点，彻底解决第二轮send_message出错时会导致对话历史残缺问题。出错时把整轮对话清除。
    #但会存在对话历史中本轮清除，但实际磁盘中笔记已经存入的情况。用户以为执行失败，但其实笔记已存入
    backup_len = len(messages)

    try:
        message = send_message(messages)
        print(f'第一次返回的message：{message}')
    except Exception as e:
        print(f'调用模型失败：{e}')
        messages[:backup_len-1]
        continue

    #写法一：出错后整轮对话作废，会导致用户没收到回复，以为没保存，但磁盘实际写入了笔记
    while message.tool_calls:
        messages.append(message)
        for tool in message.tool_calls:
            tool_id = tool.id
            f_name = tool.function.name
            #代码健壮性修改4：虽然大模型通常返回合法 JSON，但网络或模型异常时可能拿到非 JSON 字符串，
            # 直接 json.loads 会抛异常并中断整个对话循环。
            try:
                f_para = json.loads(tool.function.arguments)
            except Exception as e:
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': '工具参数错误'})
                continue
            func = available_tools[f_name]
            if func:
                result = func(f_para)
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': result})
            else:
                messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': f'未知工具: {f_name}'})

        try:
            message = send_message(messages)
            print(f'第二次返回的message：{message}')
        except Exception as e:
            print(f'调用模型失败：{e}')
            # 出错了，整轮作废，回退到备份点之前，若要保存用户消息则是backup_len
            messages[:backup_len-1]
             #代码健壮性修改5：用continue的话，message因为send_message失败，没有被第二次返回的正确message覆盖，
             # 因此还是那个带tool_calls的message，在下一轮while循环判断时候依然会进循环，导致死循环
            break
    #代码健壮性修改6：加了一层守卫，若代码正常执行进入else，若while被break出来的话，证明本轮作废，没有assistant输出
    else:
        messages.append({'role': 'assistant', 'content': message.content})
        print(f'Model:\t{message.content}')

    #写法二：出错后保存到正确的那步，并手动构造一轮模型回复作为给用户和模型的情况说明
    #这种改法会导致用户收不到模型的最后一句回复（因为send_message失败），messages里少一轮模型的回复，
    #但前面写入的数据并不是“脏数据”，因为磁盘里真的保存了用户要保存的这条笔记（save函数已被成功执行，messages里
    # while message.tool_calls:
    #     messages.append(message)
    #     for tool in message.tool_calls:
    #         tool_id = tool.id
    #         f_name = tool.function.name
    #         f_para = json.loads(tool.function.arguments)
    #         func = available_tools.get(f_name)
    #         if func:
    #             result = func(f_para)
    #             messages.append({'role': 'tool', 'tool_call_id': tool_id, 'content': result})
    #         else:
    #             messages.append({'role': 'tool',  'tool_call_id': tool_id, 'content':f'未知工具：{f_name}'})        
    #     try:
    #         message = send_message(messages)
    #         print(f'第2次返回的message：{message}')
    #     except Exception as e:
    #         print(f'工具调用后模型回复失败：{e}')
    #         messages.append({'role': 'assistant', 'content': '抱歉，处理您的请求时遇到错误。如果刚进行了保存操作，可能已完成，请勿重复保存。'})
    #         print('Model:\t' + messages[-1]['content'])
    #         #代码健壮性修改3：用continue的话，message因为send_message失败，没有被第二次返回的正确message覆盖，因此还是那个带tool_calls的message，在下一轮while循环判断时候依然会进循环，导致死循环
    #         break
    # else:
    #     messages.append({'role': 'assistant', 'content': message.content})
    #     print(f'Model:\t{message.content}')


    #写法三：废弃
    #这种改法会导致主历史中messages里这一轮只会留下最终那句回复(第 45 行那条),中间的 tool_calls、tool 结果全留在 messages1 里被丢弃了。
    # messages1 = messages.copy()
    # while message.tool_calls:
    #     messages1.append(message)
    #     for tool in message.tool_calls:
    #         tool_id = tool.id
    #         f_name = tool.function.name
    #         f_para = json.loads(tool.function.arguments)
    #         func = available_tools.get(f_name)
    #         if func:
    #             result = func(f_para)
    #             messages1.append({'role': 'tool', 'tool_call_id': tool_id, 'content': result})
    #         else:
    #             messages1.append({'role': 'tool',  'tool_call_id': tool_id, 'content':f'未知工具：{f_name}'})        
    #     try:
    #         message = send_message(messages1)
    #         print(f'第2次返回的message：{message}')
    #         # messages.append(messages1.copy())  这一行不该要，这是把一整个 list 塞进去当一条消息——下一轮 send 时 API 直接报格式错误崩掉。append 进去的得是消息，不是消息列表。
    #     except Exception as e:
    #         print(f'调用模型失败：{e}')
            #用continue的话，message因为send_message失败，没有被第二次返回的正确message覆盖，因此还是那个带tool_calls的message，在下一轮while循环判断时候依然会进循环，导致死循环
    #         break 
    # messages.append({'role': 'assistant', 'content': message.content})
    # print(f'Model:\t{message.content}')


