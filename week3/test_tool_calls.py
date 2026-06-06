from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url='https://api.deepseek.com'
)

def send_messages(messages):
    response = client.chat.completions.create(
        model = 'deepseek-v4-pro',
        messages = messages,
        tools = tools 
    )

    return response.choices[0].message

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'get_weather',
            'description': 'Get weather of a location, the user should supply a location first.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'location': {
                        'type': 'string',
                        'description': 'The city and state, e.g. San Francisco, CA'
                    }
                },
                'required': ['location']
            }
        }
    }
]

#1、程序将用户说的话发送给模型
messages = [{'role': 'user', 'content': 'How\'s the weather in Hangzhou, Zhejiang?'}]
#2、模型返回message对象，里面包含模型想调用的function信息（tool_calls)
message = send_messages(messages)
print(f"User>\t {messages[0]['content']}")


tool = message.tool_calls[0]
#这步append必须，模型最后拿到的messages必须包含完整的流程，否则历史断裂（模型没有记忆）
messages.append(message)

#3、程序从message里取出要调用的函数，并调用它
pass

#4、程序将函数调用结果和完整的四步流程发给模型，模型生成最终回复
messages.append({'role': 'tool', 'tool_call_id': tool.id, 'content': '24℃'})
message = send_messages(messages)
print(f'Model>\t {message.content}')