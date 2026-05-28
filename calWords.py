#分词replace split
def file2List(s):
    s = s.replace(',', '')
    s = s.replace('.', '')
    s = s.lower()
    l = s.split(' ')
    return l

def calWords():
    #读文件open read
    f = open('test.txt', 'r')
    l = file2List(f.read())

    #计数 dict
    d = {}
    for i in range(len(l)):
        if l[i] not in d:
            d[l[i]] =1
        else:
            d[l[i]] += 1
    
    #dict是无序的，所以要转为list
    l2 = list(d.items())
    
    #排序 sorted
    l3 = sorted(l2, key = lambda item: item[1], reverse = True)
    print(l3)

    #列表生成式输出前五项tuple的key
    print([item[0] for item in l3[:5]])
    return None

calWords()
    