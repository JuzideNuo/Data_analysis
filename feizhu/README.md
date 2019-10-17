# 爬取飞猪各地旅游景点销售记录进行分析

## 1 爬取

毫无疑问 飞猪的网页还是没那么容易直接爬取的  观察一下吧 = =

![1571291940112](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_2.png)

点清除 然后点一个城市 直接就发现了目标 看来还是虚晃一招而已 是一个json数据 

![1571292129096](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_3.png)![1571292158748](C:\Users\ADMINI~1\AppData\Local\Temp\1571292158748.png)

看请求的URL 对应下面的data就发现这一堆编码其实就是城市 这样把各个城市输入就OK

OK 爬取回来了 = =

![1571293946921](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_7.png)

```Python
import requests
import pandas as pd
from pymongo import MongoClient
import time


class DataCrawler(object):
    def __init__(self):
        # 这个城市可以手打 我把全国的城市都弄到一个文件里面的
        self.cities = list(pd.read_csv('city_data.csv')['city'])
        client = MongoClient(host='localhost')
        db = client.Laborday
        self.col = db.ticket

    def get_city_trip(self):
        for city in self.cities:
            print('正在爬取城市:{}的数据!'.format(city))
            res = requests.get('https://travelsearch.fliggy.com/async/queryItemResult.do?searchType='
                               'product&keyword={}&category=SCENIC&pagenum=1'.format(city))
            data = res.json()
            itemPagenum = data['data']['data'].get('itemPagenum')
            if itemPagenum is not None:
                page_count = itemPagenum['data']['count']

                data_list = data['data']['data']['itemProducts']['data']['list'][0]['auctions']
                for ticket in data_list:
                    ticket['city'] = city
                    self.col.insert_one(ticket)
                print('成功爬取城市:{}的第{}页数据!'.format(city, 1))
                time.sleep(3)  # 为了防止防止在防止 还是3秒吧 慢就慢点 当然大神一般都是弄IP池的= =
                if page_count > 1:
                    for page in range(2, page_count+1):
                        res = requests.get('https://travelsearch.fliggy.com/async/queryItemResult.do?searchType='
                                           'product&keyword={}&category=SCENIC&pagenum={}'.format(city, page))
                        data = res.json()
                        data_list = data['data']['data']['itemProducts']['data']['list'][0]['auctions']
                        for ticket in data_list:
                            ticket['city'] = city
                            self.col.insert_one(ticket)
                        print('成功爬取城市:{}的第{}页数据!'.format(city, page))

if __name__ == '__main__':
    data_crawler = DataCrawler()
    data_crawler.get_city_trip()
```

前面试过MySQL 这次试试mongdb  json数据还是很好解析的 就当做一个字典嵌套就行

把数据库的数据弄出来变成CSV吧  谷歌了一下做分析还是直接存在CSV好一点 `data.to_csv('data1.csv', index=False)`

```Python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
from pandas.io.json import json_normalize

plt.style.use('ggplot')
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']  #解决seaborn中文字体显示问题
plt.rc('figure', figsize=(10, 10))  #把plt默认的图片size调大一点
plt.rcParams["figure.dpi"] =mpl.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题
%matplotlib inline
conn = MongoClient(host='127.0.0.1', port=27017)  # 实例化MongoClient
db = conn.get_database('Laborday')  

col = db.get_collection('ticket') # 连接到集合ticket
mon_data = col.find()  # 查询这个集合下的所有记录
```

得到一堆nan = = 清洗清洗   一看 50000+景点 我的电脑内存要顶不住了....

![1571299087920](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_8.png)

查看索引、数据类型和内存信息 `.info()`

表头 `columns`  索引`iloc[]`

![1571292954904](C:\Users\ADMINI~1\AppData\Local\Temp\1571292954904.png)

![1571299823874](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_9.png)

第一次弄那么多数据 刺激= =

### 1寻找我们需要的数据

```Python
fz_demo = ['city', 'fields.comment', 'fields.discountPrice', 'fields.features', 'fields.itemId',
           'fields.itemTotalScore', 'fields.latitude', 'fields.longitude', 'fields.price',
           'fields.shortInfo', 'fields.sold365', 'fields.soldRecentNum', 'fields.tagList', 
            'fields.title', 'trip_main_busness_type']
fz = fz[fz_demo]
fz.head()
```

![1571299933792](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_10.png)

`fz = fz.fillna(0)` 将所有的NaN 变成0.0

### 2 去重

![1571299998128](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_11.png)

重复居然那么多 

`fz.dtypes` 看一下各个字段的数据类型对不对 = 

![1571300031798](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_12.png)

转换一下

![1571300543331](C:\Users\ADMINI~1\AppData\Local\Temp\1571300543331.png)

`new_fz = fz`  拿新的分析 不然改不对就要重头运行一下 麻烦死 = =

### 清洗 三个字段的数据 这样才能分析

- fields.features
- fields.sold365
- fields.tagList

#### 清洗fields.features

```Python
def get_fea(data):
    if len(data) > 0:
        return data[0]['text']
    else:
        return None

new_fz['fields.features'] = new_fz['fields.features'].apply(get_fea)
new_fz.head()
```

![1571300646796](C:\Users\ADMINI~1\AppData\Local\Temp\1571300646796.png)

```Python
def get_sold365(new_fz):
    if new_fz != 0:
        if "万" in new_fz:
            return float(new_fz[new_fz.find('售')+1:new_fz.find('万')]) * 10000
        else:
            return float(new_fz[new_fz.find('售')+1:new_fz.find('笔')])

    
new_fz['fields.sold365'] = new_fz['fields.sold365'].apply(get_sold365)
new_fz.sample(5)
```

转换成销售的笔数

![1571301315051](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_14.png)

### fields.tagList 清洗

![1571301547026](C:\Users\ADMINI~1\AppData\Local\Temp\1571301547026.png)

拿出之前存的全城市

```Python
city_data = pd.read_csv('city_data.csv')
display(city_data.shape,city_data.head())
```

![1571301672796](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_15.png)

将对于的省份加进来

![1571301801386](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_17.png)

OK 到这里就差不多 开始做可视化分析

# 哪些城市/省份的旅游选择最多？



### 哪些城市/省份的旅游选择最多？ 

![1571302019421](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\image_18.png)

### 城市选择

![1571302420323](C:\Users\ADMINI~1\AppData\Local\Temp\1571302420323.png)

![全国各省份旅游选择数量图](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\全国各省份旅游选择数量图.png)

越红代表越多人去= =

### 最近一个月售出门票Top10省份

![1571302744159](C:\Users\ADMINI~1\AppData\Local\Temp\1571302744159.png)

![最近一个月售出门票Top10城市](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\最近一个月售出门票Top10城市.png)

### 最近一个月热爱去的地方-->词云

![1571303101107](C:\Users\ADMINI~1\AppData\Local\Temp\1571303101107.png)

![词云](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\词云.png)

### 最热门的景点

![1571303252399](C:\Users\ADMINI~1\AppData\Local\Temp\1571303252399.png)

```Python
most_popular = ['灵隐飞来峰', '上海迪士尼', '广州长隆', '故宫博物院',
               '珠海长隆', '上海野生动物园', '东方明珠', '乌镇', '上海海昌海洋公园']
most_popular_values = [96759+95234, 158493, 54497+37687, 63733,
                      51782, 24831, 32285, 33989, 24963]

bar = Bar("最热门的10个景点", width = 700,height=600)
bar.add("", most_popular, most_popular_values, is_stack=True, 
       xaxis_label_textsize=16, yaxis_label_textsize=14, is_label_show=True,
       xaxis_rotate=25)
bar
```

![最热门的10个景点](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\最热门的10个景点.png)

### 各个景区门票价格

```Python
level = ['A', 'AA', 'AAA', '4A景区', '5A景区']
level_data = city.groupby('fields.tagList')['fields.price'].mean()[level]
bar = Bar("各级别景区的门票价格", width = 500,height=500)
bar.add("", level_data.index, np.round(level_data.values,0), is_stack=True, 
       xaxis_label_textsize=18, yaxis_label_textsize=14, is_label_show=True)
bar
```

![各级别景区的门票价格](E:\Jupyter_save\shujufenxi\飞猪旅游分析\image\各级别景区的门票价格.png)

