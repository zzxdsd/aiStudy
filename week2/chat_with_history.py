import json
import os
from openai import OpenAI

api_key = os.environ.get('DEEPSEEK_API_KEY')
if not api_key:
    print('环境变量出错')
    exit(1)

client = OpenAI(
    api_key= api_key,
    base_url= "https://api.deepseek.com"
)

print('下面开始对话', '-'*30)

#读历史对话
#json知识点：json.load()把json文件反序列化为python对象
#           json.loads() 把json字符串反序列化为python对象
if os.path.exists('history.json'):
    with open('history.json', 'r', encoding= 'utf-8') as f:
        content= f.read()
        # print(f'历史对话为：{content}')
        # messages = json.load(f)  read()函数会把指针移到文件末尾，所以会出现空文件报错
        messages = json.loads(content)
else:
    messages = []

while True:
    user_input = input('\n你: ').strip()
    if not user_input:
        continue
    if user_input.lower() in ['quit', 'exit']:
        break

    messages.append({'role': 'user', 'content': user_input})
    req = client.chat.completions.create(
        model = 'deepseek-v4-pro',
        messages = messages,
        stream = False
    )

    reply = req.choices[0].message.content
    messages.append({'role': 'assistant', 'content': reply})

    #写入新一轮对话进history
    #知识点1：ensure_ascii=False 非 ASCII 字符全部转成 \uXXXX 编码，决定 json 模块生成的字符串里是中文还是 \u 编码
    #        encoding= 'utf-8'  决定字符串怎么存到文件字节里
    #        indent = 2 表示缩进
    #知识点2：json.dump() 把python对象序列化为json格式，作用于文件
    with open('history.json', 'w', encoding= 'utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    print(f'\n回复：{reply}')

