import json
import os
from openai import OpenAI

api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    print('环境变量出错')
    exit(1)

# api_key = '0' #测试异常处理
#这一段只是创建一个客户端对象,把参数存到对象里,没有发任何网络请求，所以根本不会抛异常，没必要用try except捕获
client = OpenAI(
    api_key= api_key,
    base_url= "https://api.deepseek.com"
)

#读历史对话
#json知识点：json.load()把json文件反序列化为python对象
#           json.loads() 把json字符串反序列化为python对象
def load_history():
    if not os.path.exists('history.json'):
        return []
    try: 
        with open('history.json', 'r', encoding= 'utf-8') as f:
            content= f.read()
            # print(f'历史对话为：{content}')
            # messages = json.load(f)  read()函数会把指针移到文件末尾，所以会出现空字符串报错
            return json.loads(content)
    except json.JSONDecodeError as e:
        print(f'历史文件损坏/格式不正确：{e}')
        return []

#写入新一轮对话进history
#知识点1：ensure_ascii=False 非 ASCII 字符全部转成 \uXXXX 编码，决定 json 模块生成的字符串里是中文还是 \u 编码
#        encoding= 'utf-8'  决定字符串怎么存到文件字节里
#        indent = 2 表示缩进
#知识点2：json.dump() 把python对象序列化为json格式，作用于文件
def save_histroty(messages):
    with open('history.json', 'w', encoding= 'utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

#主流程
messages = load_history()
print('下面开始对话', '-'*30)

while True:
    user_input = input('\n你: ').strip()
    if not user_input:
        continue
    if user_input.lower() in ['quit', 'exit']:
        #退出时统一保存一次messages，不用在结尾每轮对话都写一次文件
        save_histroty(messages) 
        break

    #先判断quit再append，不会将quit/exit保存进history
    messages.append({'role': 'user', 'content': user_input})
    try:
        req = client.chat.completions.create(
            model = 'deepseek-v4-pro',
            messages = messages,
            stream = False
        )
    except Exception as e:
        print(f'调用API出错: {e}')
        # exit(1)  不能直接退出，会导致整个程序崩掉、之前的对话上下文全丢
        messages.pop() #撤回刚才那条没成功的 user 消息
        continue

    reply = req.choices[0].message.content
    messages.append({'role': 'assistant', 'content': reply})

    print(f'\n回复：{reply}')

