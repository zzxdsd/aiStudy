import string

#分词replace split
def file2List(s):
    for p in string.punctuation:
        s = s.replace(p, '')
    s = s.lower()
    l = s.split() #比 split(' ') 更健壮，可以处理多个空格
    return l

def calWords():
    #读文件open read，记得手动关闭或者让with来处理
    with open('test.txt', 'r') as f:
        l = file2List(f.read())

    #计数 dict
    d = {}
    for word in l:  #下标思维是java/C的
        d[word] = d.get(word, 0) + 1
    #     if word not in d:
    #         d[word] =1
    #     else:
    #         d[word] += 1
        
    
    #dict是无序的，所以要转为list
    l2 = list(d.items())
    
    #排序 sorted
    l3 = sorted(l2, key = lambda item: item[1], reverse = True)
    print(l3)

    #列表生成式输出前十项tuple的key
    print([item[0] for item in l3[:10]])
    return None

calWords()
    