"""""""""""""""""""""""""""""""""""""""""""""
功能说明
1、梳理本地公众号目标清单
2、爬取近期文章记录并PUSH给指定用户
参考资料
1、python爬取微信公众号:https://www.cnblogs.com/xiao-apple36/p/9447877.html
2、Python 微信公众号发送消息:https://www.cnblogs.com/supery007/p/8136295.html
3、微信公众平台测试帐号申请地址：https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login
"""""""""""""""""""""""""""""""""""""""""""""
# -*- coding: utf-8 -*- 
from selenium import webdriver
import time
import json
import requests
import re
import random

#微信公众号账号与密码
user="luckyegg@139.com"
password="fangyi791021"
#设置要爬取的公众号列表
#gzlist=['湖州旅游','爱湖州','湖州银泰城','湖州微生活','南太湖优店']
gzlist=['湖州旅游']

#登录微信公众号，获取登录之后的cookies信息，并保存到本地文本中
def weChat_login():
    #定义一个空的字典，存放cookies内容
    post={}
    #用webdriver启动谷歌浏览器，打开微信公众号登录界面
    driver = webdriver.Chrome(executable_path='D:/WorkSpace/GZH-spider/chromedriver')
    driver.get('https://mp.weixin.qq.com/')
    time.sleep(5)
    
    #清空微信公众号登录账号和密码框中的内容并自动填入相应内容    
    driver.find_element_by_xpath("./*//input[@name='account']").clear()
    driver.find_element_by_xpath("./*//input[@name='account']").send_keys(user)
    driver.find_element_by_xpath("./*//input[@name='password']").clear()
    driver.find_element_by_xpath("./*//input[@name='password']").send_keys(password)
 
    # 在自动输完密码之后需要手动点一下记住我
    print("请在登录界面点击:记住账号")
    time.sleep(5)

    #自动点击登录按钮进行登录，拿手机扫二维码登录！
    driver.find_element_by_xpath("./*//a[@class='btn_login']").click()
    time.sleep(20)

    #重新载入公众号登录页，登录之后会显示公众号后台首页，从这个返回内容中获取cookies信息
    driver.get('https://mp.weixin.qq.com/')
    cookie_items = driver.get_cookies()

    #获取到的cookies是列表形式，将cookies转成json形式并存入本地名为cookie的文本中
    for cookie_item in cookie_items:
        post[cookie_item['name']] = cookie_item['value']
    cookie_str = json.dumps(post)
    with open('cookie.txt', 'w+', encoding='utf-8') as f:
        f.write(cookie_str)

#爬取微信公众号query的文章，并存在本地文本中
def get_content(query):
    url = 'https://mp.weixin.qq.com'
    #设置headers
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
        }

    #读取上一步获取到的cookies
    with open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
    cookies = json.loads(cookie)

    #登录之后的微信公众号首页url变化到公众号后台首页，从这里获取token信息
    response = requests.get(url=url, cookies=cookies)
    token = re.findall(r'token=(\d+)', str(response.url))[0]

    #搜索微信公众号的接口地址
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    #搜索微信公众号接口需要传入的参数，有三个变量：微信公众号token、随机数random、搜索的微信公众号名字
    query_id = {
        'action': 'search_biz',
        'token' : token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'query': query,
        'begin': '0',
        'count': '5'
        }
    #打开搜索微信公众号接口地址，需要传入相关参数信息如：cookies、params、headers
    search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)
    #取搜索结果中的第一个公众号
    lists = search_response.json().get('list')[0]
    #获取这个公众号的fakeid，后面爬取公众号文章需要此字段
    fakeid = lists.get('fakeid')

    #微信公众号文章接口地址
    appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    #搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
    query_id_data = {
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'action': 'list_ex',
        'begin': '0',#不同页，此参数变化，变化规则为每页加5
        'count': '5',
        'query': '',
        'fakeid': fakeid,
        'type': '9'
        }

    #打开搜索的微信公众号文章列表页
    appmsg_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
    #获取文章总数
    max_num = appmsg_response.json().get('app_msg_cnt')
    #每页至少有5条，获取文章总的页数，爬取时需要分页爬
    #num = int(int(max_num) / 5)
    num = 1
    #起始页begin参数，往后每页加5
    begin = 0
    while num + 1 > 0 :
        query_id_data = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin': '{}'.format(str(begin)),
            'count': '5',
            'query': '',
            'fakeid': fakeid,
            'type': '9'
            }
        print('正在翻页：--------------',begin)

        #获取每一页文章的标题和链接地址，并写入本地文本中
        query_fakeid_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
        fakeid_list = query_fakeid_response.json().get('app_msg_list')
        #print(fakeid_list)
        for item in fakeid_list:
            create_time=item.get('create_time')  
            content_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(create_time))
            content_link=item.get('link')
            content_title=item.get('title')
            fileName=query+'.txt'
            with open(fileName,'a',encoding='utf-8') as fh:
                #fh.write(otherStyleTime+"\n"+content_title+"\n"+content_link+"\n")   
                m_content = content_date+"\n"+content_title+"\n"+content_link+"\n"
                fh.write(m_content)  
                #sendmsg ('olGwn6-YCRvXwHPh4wUlF0LJh2j8',m_content)   
                sendmsg ('olGwn6wvUZTfO4D8QY6hqZPcW5Mo',m_content)   
        num -= 1
        begin = int(begin)
        #begin+=5
        begin+=1
        time.sleep(2)

def get_access_token():
    """
    获取微信全局接口的凭证(默认有效期俩个小时)
    如果不每天请求次数过多, 通过设置缓存即可
    """
    result = requests.get(
        url="https://api.weixin.qq.com/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": "wx9cf8011937eb104f",
            "secret": "aa71262af5c40b6c6f36c5cd225dc42d",
        }
    ).json()

    if result.get("access_token"):
        access_token = result.get('access_token')
    else:
        access_token = None
    return access_token

def sendmsg(openid,msg):
    access_token = get_access_token()
    body = {
        "touser": openid,
        "msgtype": "text",
        "text": {
            "content": msg
        }
    }
    #query_fakeid_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
    response = requests.post(
        url="https://api.weixin.qq.com/cgi-bin/message/custom/send",
        params={
            'access_token': access_token
            },
        data=bytes(json.dumps(body, ensure_ascii=False), encoding='utf-8')
    )
    # 这里可根据回执code进行判定是否发送成功(也可以根据code根据错误信息)
    result = response.json()
    print(result)

if __name__=='__main__':
    try:
        #登录微信公众号，获取登录之后的cookies信息，并保存到本地文本中
        weChat_login()
        #登录之后，通过微信公众号后台提供的微信公众号文章接口爬取文章
        for query in gzlist:
            #爬取微信公众号文章，并存在本地文本中
            print("开始爬取公众号："+query)
            get_content(query)
            print("爬取完成")  
    except Exception as e:
        print(str(e))
