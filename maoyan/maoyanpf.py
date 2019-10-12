import urllib.request
from fontTools.ttLib import TTFont
from lxml import etree
from math import sqrt
import re
import pandas as pd


def create_request():
    url = 'http://piaofang.maoyan.com/movie/246082/boxshow?wkwebview=1'
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
    pd.DataFrame(demo_dict).to_csv('maoyansj-xlt.csv')


def main():
    # 创建请求
    content = create_request()

    # 解析数据 -->破解文字加密
    new_html = decryption(content)

    parse_new(new_html)


if __name__ == "__main__":
    main()