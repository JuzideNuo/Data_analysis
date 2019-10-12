# 爬取前途无忧进行Python招聘数据分析

```Python
# -*- coding:utf-8 -*-
import urllib.request
import re
import xlwt  # 用来创建excel文档并写入数据

# 获取原码


def get_content(page):
    url = 'http://search.51job.com/list/000000,000000,0000,00,9,99,python,2,' + \
        str(page) + '.html'
    a = urllib.request.urlopen(url)  # 打开网址
    html = a.read().decode('gbk')  # 读取源代码并转为unicode
    return html


def get(html):
    reg = re.compile(
        r'class="t1 ">.*? <a target="_blank" title="(.*?)".*? <span class="t2"><a target="_blank" title="(.*?)".*?<span class="t3">(.*?)</span>.*?<span class="t4">(.*?)</span>.*? <span class="t5">(.*?)</span>',
        re.S)  # 匹配换行符
    items = re.findall(reg, html)
    return items


def excel_write(items, index):

    # 爬取到的内容写入excel表格
    for item in items:  # 职位信息
        for i in range(0, 5):
            # print item[i]
            ws.write(index, i, item[i])  # 行，列，数据
        print(index)
        index += 1


newTable = "qt_python.xls"  # 表格名称
wb = xlwt.Workbook(encoding='utf-8')  # 创建excel文件，声明编码
ws = wb.add_sheet('sheet1')  # 创建表格
headData = ['招聘职位', '公司', '地址', '薪资', '日期']  # 表头部信息
for colnum in range(0, 5):
    ws.write(0, colnum, headData[colnum], xlwt.easyxf('font: bold on'))  # 行，列

for each in range(1, 20):
    index = (each - 1) * 50 + 1
    excel_write(get(get_content(each)), index)
wb.save(newTable)
```

![1570881266423](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_10.png?raw=true)

将爬取回来的数据存放在`excel`中用`jupyter notebook`分析一下爬取回来的招聘数据

![1570881367225](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_11.png?raw=true)

数据妥妥的收到了 然后进行简单的处理 将薪资提取出来 

先进行去空处理

```Python
# 去除没有的字段
qt = qt.dropna(axis=0,how='any')
qt.shape
```

![1570881605614](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_12.png?raw=true)

```Python
# 将薪资分配  依次添加千.万.万/年
qt_q = qt[qt['薪资'].str.contains('千/月')]
qt_q['薪资'] = qt_q['薪资'].str.split('千/月').str[0]
s_min, s_max = qt_q['薪资'].str.split('-',1).str

qt_min = pd.DataFrame(s_min)
qt_min.columns = ['薪资_min']
qt_max = pd.DataFrame(s_max)
qt_max.columns = ['薪资_max']


new_qt1 = pd.concat([qt_q, qt_min, qt_max], axis=1)
new_qt1['薪资_min'] = pd.to_numeric(new_qt1['薪资_min'])*1000
new_qt1['薪资_max'] = pd.to_numeric(new_qt1['薪资_max'])*1000

new_qt1.head()
```

![1570881673933](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_13.png?raw=true)

将转化的数据合并`(inner-->并集   outer-->交集)`

![1570881769733](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_18.png?raw=true)

处理一下地址并将评价薪资弄出来 方便等下操作

![1570881807052](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_14.png?raw=true)

将工作岗位地址进行汇总

```Python
# 可视化处理
demo_list=[]
demo_city=[]
demo_data=[]
for index in qt_city.index:
    value=qt_city.loc[index]
    a=(index,value)
    demo_list.append(a)
    demo_city.append(index)
    demo_data.append(value)
# 删除掉异地招聘
del demo_list[7]
print(demo_data)
```

```Python
from pyecharts import Geo 
geo = Geo("职位分布", title_color="red",
          title_pos="center", width=1000,
          height=600, background_color='#404a59')
attr, value = geo.cast(demo_list)
geo.add("", attr, value, type="effectScatter",visual_range=[0, 171], maptype='china',visual_text_color="#FF0000", geo_normal_color="#6E6E6E",geo_emphasis_color='#F5D0A9',
        symbol_size=8, effect_scale=5, is_visualmap=True)
#symbol_size 样式大小
geo
```

调用`pyecharts`  --> 下载`pip install pyecharts==0.5.11 `不然会下新版本的 新版本还需要练习

### 地图样式

![1570882062657](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_15.png?raw=true)

越红 说明职位需求越高

### 饼图

```Python
from pyecharts import Pie,configure
configure(output_image=True)
pie =Pie('饼图',background_color = 'white',width=1600,height=1400)
pie.add('',demo_city,demo_data,is_label_show = True)
pie
```

![饼图](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/%E9%A5%BC%E5%9B%BE.png?raw=true)

### 玫瑰花环图

```Python

configure(output_image=True)
pie =Pie('圆环中的玫瑰图',background_color = 'white',width=1600,height=1400)
attr = demo_city
v1 = demo_data
pie.add( '',attr,v1,radius=[65, 75],center=[50, 50],is_label_show=True,geo_title_size=25)
pie.add('',attr,v1,radius=[0, 60],center=[50, 50],rosetype='area',is_label_show=True)
pie.render(path='玫瑰花环图.html')
pie

```



![职位分布玫瑰花环图](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/%E8%81%8C%E4%BD%8D%E5%88%86%E5%B8%83%E7%8E%AB%E7%91%B0%E8%8A%B1%E7%8E%AF%E5%9B%BE.png?raw=true)



```Python
# 得到各地区的职位平均薪资的平均薪资
mean = new_qt.pivot_table(columns='地址').loc['平均薪资']
mean = mean.drop('异地招聘')
mean


diqu = mean.index
diqu
money = []
for i in mean:
    money.append(int(i))
money
```

![1570882239394](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_16.png?raw=true)

```Python
from pyecharts import Bar
mybar = Bar('地区薪资',width=1800,height=800)
# new_g = g.sort_values(by = 'counts',ascending = False)
attr = diqu
value = money
mybar.add('平均薪资',attr,value,mark_line = ['min', 'max'],mark_point = ['average'],is_label_show=True,is_datazoom_show=True,is_stack=True)
mybar.render(path='地区薪资.html')
mybar
# 可以滑动的 贼好玩
```

![1570882310157](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/10.12_17.png?raw=true)

```Python
from pyecharts import Geo

def geo_formatter(params):
    return params.name + ' : '+ params.value[2]
geo = Geo("平均工资", title_color="red",
          title_pos="center", width=1500,title_text_size=30,
          height=1000, background_color='#404a59')
geo.add("", 
        diqu, money,maptype='china', 
        is_visualmap=True, 
        is_label_show=True,
        symbol_size=20, effect_scale=15,
        visual_range=[min(value), max(value)],
       label_formatter=geo_formatter, # 重点在这里，将函数直接传递为参数。
       )
geo.render(path='地图版地区薪资.html')
geo
```

地图版

![各地平均招聘工资](https://github.com/JuzideNuo/Data_analysis/blob/master/qiantu/image/%E5%90%84%E5%9C%B0%E5%B9%B3%E5%9D%87%E6%8B%9B%E8%81%98%E5%B7%A5%E8%B5%84.png?raw=true)
