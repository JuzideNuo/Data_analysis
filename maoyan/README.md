## 猫眼电影爬取并做预测分析:

**记得加Cookie 不然是登录验证网页**

## 字体:

这个字体是加密的 所以我们需要用智慧破解(网上的破解方法好像都过期了)

![1570016310986](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.2_1.png)

每次刷新就会出现不一样的字体, 我们双击他就可以下载到字体文件 然后把文件放进-->[这个网站](http://fontstore.baidu.com/static/editor/) 当然 也可以下载应用

> FontCreator安装：
>
> 安装包下载地址 ：链接：<https://pan.baidu.com/s/1zKIr7EcGlMSSF6e9Z6IZmw> 提取码：d4gm （如果无效的话自己百度下） -->[这个是大神的链接](https://blog.csdn.net/weixin_43145520/article/details/89631403)

```python
from fontTools.ttLib import TTFont
font=TTFont('maoyan.ttf')    #打开本地字体文件01.ttf
font.saveXML('maoyan.xml')   #将ttf文件转化成xml格式并保存到本地，主要是方便我们查看内部数据结构
```



![1570016490077](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.2_2.png)

![1570016504042](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.2_3.png)

坐标大致都一样 就是有点小弯曲的区别 但是就是这些区别...导致后面的都不一样

> 网上的很多方法都是说他们的坐标是一样的。可以直接进行比较，相等的就是目标字符。可能是我打开的姿势不对吧。。。。。。这不是坐标不一样这么简单，这是连坐标数量都不一样。。。。。。 

怎么办呢 在观察观察 xml里面

![1570036742965](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.3_1.png)

![1570036758179](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.3_2.png)

感觉`x,y` 密密麻麻的 参考了这位大神的思路 每一个数字其实就是微小的变化而已,我们就把相差最小的平均值视为我们模板数字这样就可以映射替换了,--->>[求平均值](https://blog.csdn.net/xing851483876/article/details/82928607)

```python
def average(list):
    d = 0
    for point in list:
        x1, x2 = point
        # 最小平均距离 x-x的平方+y-y的平方 在开放 初中学过的 = =
        d = d + sqrt(pow(x1[0]-x2[0], 2) + pow(x1[1]-x2[1], 2))
    d = d / len(list)
    return d
```

现在需要我们用我们下的模板字体库和新的字体库进行对比映射,替换掉加密的字体

```python
def decryption(content):
    base_data = {
        'uniF5DD': '7',
        'uniF855': '4',
        'uniF7BD': '1',
        'uniEDFA': '8',
        'uniE559': '9',
        'uniE521': '3',
        'uniEC35': '2',
        'uniE77C': '6',
        'uniE06A': '5',
        'uniEC1C': '0'
    }

    # 提取网页中被加密的字符
    reg_num = re.compile(r'&#x(.*?);')
    # 提取字符并去重，减少计算量
    encryption_num = list(set(reg_num.findall(content)))
    # 混进去了一个3D
    encryption_num.remove('3D')

    # 模板字体库信息
    base_font = TTFont('maoyan_5.woff')
    # 提取出uni字段
    base_list = base_font.getGlyphOrder()[2:]

    # 新字体库信息
    replace_demo = re.findall(r'src:url\((.*)\) ', content)[0]
    file_name = './maoyan_new.woff'
    urllib.request.urlretrieve(replace_demo, file_name)
    font_new = TTFont('maoyan_new.woff')

    # 字体解密
    dec_num = {}
    num = {}
    # 遍历每个要计算的字符
    for item in encryption_num:
        # 把glyf里面的所有x,y坐标弄出来
        target = font_new['glyf']['uni'+item.upper()].coordinates
        dist_min = 10000  # 一般最小距离是 不会大于200的
        # 遍历模板每个字符
        for index in base_list:
            template = base_font['glyf'][index].coordinates
            # 因为每个字体库的相同字体，坐标点数量会不一样

            # 所以需要做一个判断，坐标数量相差少于10个，也起到筛选作用
            # 根据实际情况自己设，7-9我觉得最好,偶尔会报错，因为(8,0,9,5,6)这这里数的坐标比较接近没完全匹配出来，所以这里改成10
            if abs(len(target) - len(template)) < 10:
                # 对满足条件的字符进行计算  因为是元组所以要变成列表
                dist = average(list(zip(target, template)))
                # 找出最小平均距离的字符，嗯，答案就是最小的它了
                if dist < dist_min:
                    dist_min = dist
                    num[item] = index
    # 构建两个字体库的新映射 便于拿回解析的数据之后替换成我们的数据
    for index_new in encryption_num:
        dec_num['&#x'+index_new+';'] = base_data[num[index_new]]
	# 替换
    for i in dec_num:
        content = content.replace(i, str(dec_num[i]))
    new_html = content
    return new_html
```

![1570096624885](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.3_3.png)

![1570096648732](C:\Users\Administrator\Desktop\爬虫\爬虫日志\10.3_4.png)

OK 完全正确 可以提取我们需要的数据了

把数据库打开然后把我们爬取回来的数据存进去

完整代码:

```python
import urllib.request
from fontTools.ttLib import TTFont
from lxml import etree
from math import sqrt
import re
import pandas as pd


def create_request():
    url = 'http://piaofang.maoyan.com/movie/248700/boxshow?wkwebview=1'
    headers = {
        "Cookie": "_lxsdk_cuid=16d85aaafc5c8-099267df6a243a-5a13331d-1fa400-16d85aaafc5c8;isid=3A689751DB3BA983E11A94399CE576BC; token=ePqIUnmzA9_cctXbldqtWzlNaPcAAAAAJQkAAFXT9eB8vcPZ3I8yyeZziy9TqXMQNuzxC1Po7_7sq5VFyyL_iGs_YB9NGqA0fIkEMg; theme=moviepro; _lxsdk=A9949710E46811E9903AEB67D3AA605F2E20D933308D42FB94FE3DEBF15A25DB;__mta=47126168.1569947379525.1569947379525.1569947482122.2; __mta=47126168.1569947379525.1569947482122.1569947733482.3; _lxsdk_s=16d8b98f88c-080-a57-38%7C%7C6",

        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.87 Safari/537.36",
    }
    req = urllib.request.Request(url=url, headers=headers)
    res = urllib.request.urlopen(req)
    content = res.read().decode('utf-8')
    return content

    # return new_font

    # base_list = font_1.getGlyphOrder()[2:]
    # print(base_list)
    # print(replace_demo)


# 计算两个字符间的平均距离
def average(list):
    d = 0
    for point in list:
        x1, x2 = point
        d = d + sqrt(pow(x1[0] - x2[0], 2) + pow(x1[1] - x2[1], 2))
    d = d / len(list)
    return d


# 字体解密
def decryption(content):
    base_data = {
        'uniF5DD': '7',
        'uniF855': '4',
        'uniF7BD': '1',
        'uniEDFA': '8',
        'uniE559': '9',
        'uniE521': '3',
        'uniEC35': '2',
        'uniE77C': '6',
        'uniE06A': '5',
        'uniEC1C': '0'
    }

    # 提取网页中被加密的字符
    reg_num = re.compile(r'&#x(.*?);')
    # 提取字符并去重，减少计算量
    encryption_num = list(set(reg_num.findall(content)))
    # 混进去了一个3D
    encryption_num.remove('3D')

    # 模板字体库信息
    base_font = TTFont('maoyan_5.woff')
    # 提取出uni字段
    base_list = base_font.getGlyphOrder()[2:]

    # 新字体库信息
    replace_demo = re.findall(r'src:url\((.*)\) ', content)[0]
    file_name = './maoyan_new.woff'
    urllib.request.urlretrieve(replace_demo, file_name)
    font_new = TTFont('maoyan_new.woff')

    # 字体解密
    dec_num = {}
    num = {}
    # 遍历每个要计算的字符
    for item in encryption_num:
        # 把glyf里面的所有x,y坐标弄出来
        target = font_new['glyf']['uni' + item.upper()].coordinates
        dist_min = 10000  # 一般最小距离是 不会大于200的
        # 遍历模板每个字符
        for index in base_list:
            template = base_font['glyf'][index].coordinates
            # 因为每个字体库的相同字体，坐标点数量会不一样

            # 所以需要做一个判断，坐标数量相差少于10个，也起到筛选作用
            # 根据实际情况自己设，7-9我觉得最好,偶尔会报错，因为(8,0,9,5,6)这这里数的坐标比较接近没完全匹配出来，所以这里改成10
            if abs(len(target) - len(template)) < 10:
                # 对满足条件的字符进行计算  因为是元组所以要变成列表
                dist = average(list(zip(target, template)))
                # 找出最小平均距离的字符，嗯，答案就是最小的它了
                if dist < dist_min:
                    dist_min = dist
                    num[item] = index
    # 构建两个字体库的新映射 便于拿回解析的数据之后替换成我们的数据
    for index_new in encryption_num:
        dec_num['&#x' + index_new + ';'] = base_data[num[index_new]]

    for i in dec_num:
        content = content.replace(i, str(dec_num[i]))
    new_html = content
    return new_html


def parse_new(new_html):
    # soup_path = '//div[@class="t-change"]//div[@class="t-row"]//i/text()'
    soup_path = '//div[@class="t-change"]//div[@class="t-row"]'
    soup_day = '//div[@class="t-main-col"]//div[@class="t-col"]//b/text()'
    tree = etree.HTML(new_html)
    # print(tree)
    soup_name = '//div[@class="info-title-bar"]/text()'
    html_name = tree.xpath(soup_name)[0].replace("\n", "").replace(" ", "")
    demo_dict = {}
    html_data = tree.xpath(soup_path)
    html_day = tree.xpath(soup_day)
    demo_list = []
    demo_day = []
    for i in range(len(html_data)):
        data = html_data[i].xpath('.//i/text()')
        day = html_day[i]
        demo_list.append(data[-3])
        demo_day.append(day)
    demo_dict[html_name] = demo_list
    demo_dict['日期'] = demo_day
    pd.DataFrame(demo_dict).to_csv('maoyansj-ssy.csv')


def main():
    # 创建请求
    content = create_request()

    # 解析数据 -->破解文字加密
    new_html = decryption(content)

    parse_new(new_html)


if __name__ == "__main__":
    main()
```

这样就能得到很多的票房信息了 主要修改一下`url` -->注意 不能同时一大批爬取 超过3个就会出现错误!

`ConnectionResetError: [WinError 10054] 远程主机强迫关闭了一个现有的连接`

 我懒得修改了 毕竟我用就下几个电影的票房数据做分析而已

大概有十个吧  如果爬取数据大的话需要设置一下时间延迟 和短暂关闭requese

具体看-->[猛戳这里](https://blog.csdn.net/IllegalName/article/details/77164521)

然后简单弄回来一些数据开始做图

![1570814642482](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_4.png)

先清洗一下数据 把 -- 去掉,然后切片 从上映到结束票房 也就90天.

打开刚保存的csv

![1570814684100](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_5.png)

这第一列是什么魔鬼 删掉删掉

![1570814708984](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_6.png)

`my = my.replace('--',0)` 将--替换成0  

`my.dtypes`  看一下数据类型 确保没错

然后

```python
name = my.columns.tolist()
plt.figure(figsize=(22,12))  # --> 改变图像大小
plt.xlabel('天数',fontsize=15)
plt.ylabel('票房(万)')

for i in range(9):
    plt.subplot(3, 3, i+1)
    y = my[name[i]].dropna().tolist()
    x = [i for i in range(len(y))]
    plt.title(name[i])
    plt.plot(x,y)
plt.show()
```

![1570815047723](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_7.png)

```python
# 拟合曲线
def draw_fit(my):
    x = np.array(range(len(my)))
    # print(np.polyfit(x,my,10))
    z = np.poly1d(np.polyfit(x,my,10)) # 传入票房得出一个多项式
    plt.plot(x,z(x), 'r-') # 红色曲线形状
    return z

plt.figure(figsize=(22,12))
func_fits = []

for i in range(9):
    plt.subplot(3, 3, i+1)
    y = my[name[i]].dropna().tolist()
    x = [i for i in range(len(y))]
    plt.title(name[i])
    plt.plot(x,y)
    z = draw_fit(y)  # 绘制拟合曲线
    func_fits.append(z)
plt.show()
```

![1570817068792](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_8.png)

然后创建一个 拟合函数

```python
# 拟合函数
z = func_fits[0]
def func(x,p):
    A,k = p
    return A * z(x)
func(5,[1,1])
# 误差函数
def residuals(p,y,x):
    return y - func(x,p)
```

读取新的数据

```python
# 读取新数据
data_nz = pd.read_csv('demo_movi.csv',sep=',',encoding='utf8')
title = data_nz.columns.tolist()
y2 = data_nz[title[1]].dropna().tolist()
x2 = np.array(range(len(y2)))
```

```python
# 最小二乘法
from scipy.optimize import leastsq
p0 = [1,1]
plsq = leastsq(residuals,p0,args=(y2,x2))
x3 = np.array(range(len(y2)))
plt.figure(figsize=(8,6))
plt.xticks()
plt.xlabel('',fontsize=14)
plt.ylabel('票房(万)')

plt.title(title[0])
plt.plot(x2,y2)

y3 = func(x3,plsq[0])
plt.plot(x3,y3,'r-')
plt.show()
print('总票房估计:%.f 万'%np.sum(y3))
```

![1570818153886](C:\Users\Administrator\Desktop\笔记\数据分析\10.12_9.png)

为啥预测得不太准确= = 估计是前面高峰期哪里低得太多了= =