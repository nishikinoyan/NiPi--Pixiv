import requests
import re
import time
from bs4 import BeautifulSoup
from picture_info import original_picture_info
import os
import json
import datetime
import threading

login_sessions = None
ranking_start_url = None
ranking_model_url = None
picture_dir = None
picture_dir_backup = None
wait_time = 1  #每张图发请求的等待时间，建议1S



def strfomat_date(reduce_date):
    today_date = datetime.datetime.now()
    last_date = today_date + datetime.timedelta(days=reduce_date)
    last_date_format = last_date.strftime('%Y%m%d')
    return last_date_format

def now_hour():
    return time.strftime('%H', time.localtime(time.time()))

def picture_catch_date():
    today_date = datetime.datetime.now()
    last_date = today_date + datetime.timedelta(days=0)
    last_date_format = last_date.strftime('%Y%m%d%H%M%S')
    return last_date_format


def login_pixiv(login_pixiv_id,login_pixiv_passwd):

    start_url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
    login_url = 'https://accounts.pixiv.net/api/login?lang=zh'

    login_headers = {
        'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
        'Origin': 'https://accounts.pixiv.net',
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    }

    post_key_page = login_sessions.get(start_url,headers=login_headers).content #post_key的获取必须要在同一个session里，否则会登陆错误！！！！！！！！
    post_key_page_code = BeautifulSoup(post_key_page, 'lxml')
    post_key = post_key_page_code.find('input')['value']      #查找登陆的post_key码

    print('post_key:' + post_key)

    login_data = {
        'pixiv_id': login_pixiv_id,
        'password': login_pixiv_passwd,
        'return_to': 'https://www.pixiv.net/',
        'post_key': post_key
    }

    try:
        login_page = login_sessions.post(login_url,headers=login_headers,data=login_data,timeout=10)
        return login_page

    except Exception as e:
        print('登陆错误')
        print(e)

def rangking_page_get(ranking_url):      #排行页面获取
    ranking_headers = {
        'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
        'Origin': 'https://accounts.pixiv.net',
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    }
    try:
        ranking_page = login_sessions.get(ranking_url, headers = ranking_headers, timeout = 10).content
        return ranking_page
    except Exception as e:
        print('页面获取错误')
        print(e)

def original_page_get(original_url, headers):
    try:
        original_page = login_sessions.get(original_url, headers = headers, timeout = 10)
        return original_page
    except Exception as e:
        '''
        print('原图页面获取错误')
        print(e)
        '''
        pass


def rangking_page_more_get(more_ranking_url):      #排行页面获取
    ranking_headers = {
        'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
        'Origin': 'https://accounts.pixiv.net',
        'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    }
    try:
        ranking_page = login_sessions.get(more_ranking_url, headers = ranking_headers, timeout = 10).content
        return ranking_page
    except Exception as e:
        print('更多页面获取错误')
        print(e)



def first_page_analysis_picture_info(rangking_page):        #第一页解析排行榜图片信息，提取原图链接
    picture_items = []#图片信息列表数组

    rangking_page_soup = BeautifulSoup(rangking_page, 'lxml')

    global tt
    tt = rangking_page_soup.select('#wrapper > footer > div > ul > li')[0].select('form > input')[1]['value']  #下一页爬虫需要的参数

    picture_all_info = rangking_page_soup.select(
        '#wrapper > div.layout-body > div > div.ranking-items-container > div.ranking-items.adjust > section.ranking-item')

    for picture_temp in picture_all_info:
        linkUrl = picture_temp.select('div.ranking-image-item > a')[0]['href']
        illust_id = picture_temp['data-id']
        thumbnailUrl = picture_temp.select('div.ranking-image-item > a > div > img')[0]['data-src']
        title = picture_temp['data-title']
        author = picture_temp['data-user-name']
        browse = picture_temp['data-view-count']
        score = picture_temp['data-rating-count']
        date = picture_temp['data-date']
        originalUrl = thumbnailUrl.replace('c/240x480/img-master', 'img-master')
        picture_items.append(original_picture_info.save_original_picture_info(title, illust_id, author, date, browse, score, linkUrl,
                               thumbnailUrl, originalUrl))

    return picture_items




def first_page_get_original_picture_info(page_info):    #第一页信息解析
    print('第一页数据')

    picture_items = first_page_analysis_picture_info(page_info)
    for picture_items_temp in picture_items:
        try:
            time.sleep(wait_time)

            picture_detail_page_link = 'https://www.pixiv.net' + picture_items_temp.linkUrl  #详细页链接
            picture_original_link = picture_items_temp.originalUrl                           #原图链接
            picture_name = picture_items_temp.title
            picture_id = picture_items_temp.illust_id

            re_str = r"[\/\\\:\*\?\'\"\<\>\|]"  # '/ \ : * ? " < > |'    <------去掉文件中非法的字符
            picture_name = re.sub(re_str, "_", picture_name)
            picture_name = picture_name + ' id~ ' + str(picture_id)

            picture_write_thread = threading.Thread(target=get_original_picture_download,args=(picture_detail_page_link,picture_original_link,picture_name))
            picture_write_thread.start()
        except Exception as e:
            print('第一页错误' + str(e))
            pass
        continue





def get_original_picture_download(picture_detail_page_link,picture_original_link,picture_name):
    get_originnal_headers = {
        'Referer': ranking_model_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    }

    picture_detail_page = original_page_get(picture_detail_page_link,get_originnal_headers)  #进入图片详细链接
    original_picture_page = original_page_get(picture_original_link,get_originnal_headers)   #原图链接访问

    picture_name = picture_name + picture_original_link[-4:]

    if(original_picture_page.status_code == 200):
        try:
            with open(os.path.join(picture_dir, picture_name), 'wb')as o:
                o.write(original_picture_page.content)
                print('下载图片： ' + picture_name)

        except Exception as e:
            print('写入图片错误' + str(e))
            pass

def more_page_get_original_picture_info(json_info):    #json信息解析
    items = []

    picture_json = json.loads(json_info)['contents']

    for picture_json_temp in picture_json:
        linkUrl = picture_json_temp['url']
        illust_id = picture_json_temp['illust_id']
        thumbnailUrl = picture_json_temp['url']  #缩略图链接

        author = picture_json_temp['user_name']
        browse = picture_json_temp['view_count']
        score = picture_json_temp['rating_count']
        date = picture_json_temp['date']
        title = picture_json_temp['title']

        originalUrl = thumbnailUrl.replace('c/240x480/img-master', 'img-master')

        items.append(original_picture_info.save_original_picture_info(title, illust_id, author, date, browse, score, linkUrl,
                               thumbnailUrl, originalUrl))

    return items


def get_more_picture(p,format,rangking_tt):
    #https://www.pixiv.net/ranking.php?mode=monthly&p=2&format=json&tt=71c100ffe639954a7c560dd45901e1d1
    #print('p:' + str(p) + 'format:' + format + 'tt:' + tt)

    more_ranking_url = ranking_model_url + '&' + 'p=' + str(p) + '&' + 'format=' + format + '&' + 'tt=' + rangking_tt
    print('json请求网址:' + more_ranking_url)
    rangking_page_more_page = rangking_page_more_get(more_ranking_url)
    picture_json_item = more_page_get_original_picture_info(rangking_page_more_page)

    for picture_json_item_temp in picture_json_item:
        time.sleep(wait_time)

        try:
            picture_json_detail_page_link = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(picture_json_item_temp.illust_id)  # 详细页链接
            picture_json_original_link = picture_json_item_temp.originalUrl  # 原图链接
            picture_json_name = picture_json_item_temp.title
            picture_json_id = picture_json_item_temp.illust_id

            re_str = r"[\/\\\:\*\?\'\"\<\>\|]"  # '/ \ : * ? " < > |'    <------去掉文件中非法的字符
            picture_json_name = re.sub(re_str, "_", picture_json_name)
            picture_json_name = picture_json_name + ' id~ ' + str(picture_json_id)


            picture_json_write_thread = threading.Thread(target=get_original_picture_download,args=(picture_json_detail_page_link,picture_json_original_link,picture_json_name))
            picture_json_write_thread.start()
        except Exception as e:      #下载图片时发生错误继续执行
            pass
        continue


if __name__ == "__main__":

    print('账号')
    pixiv_account = input()
    print('密码')
    pixiv_passwd = input()
    print('路径')
    picture_dir = input()
    print('要爬多少天（往后爬多少天）')
    catch_day = input()

    max_page_num = 0

    login_sessions = requests.session()
    login_after_page = login_pixiv(pixiv_account, pixiv_passwd)  # 登陆后的页面
    print('登陆代码：' + str(login_after_page.status_code))

    picture_dir_backup = picture_dir

    ranking_start_url = 'https://www.pixiv.net/ranking.php'

    catch_type_items = ['?mode=daily', '?mode=weekly', '?mode=monthly', '?mode=rookie', '?mode=original']

    print()
    if(int(now_hour())>12):#    P站过了12点才能爬昨天的图片，12点之前都是前天的
        print('当前小时：' + now_hour())
        day_sum = -1
        print('昨天')
    else:
        print('当前小时：' + now_hour())
        day_sum = -2
        print('前天')

    catch_day_temp = 0

    while(catch_day_temp < int(catch_day)):
        print()
        print('当前日期：' + strfomat_date(day_sum))

        picture_dir = picture_dir_backup + '/' + strfomat_date(day_sum)
        picture_dir_date_backup = picture_dir
        if not os.path.exists(picture_dir):
            os.mkdir(picture_dir)


        for catch_type_temp in catch_type_items:
            print()
            print('爬取类型：' + catch_type_temp[6:])
            picture_dir = picture_dir_date_backup + '/' + catch_type_temp[6:]
            if not os.path.exists(picture_dir):
                os.mkdir(picture_dir)

            ranking_model_url = ranking_start_url + catch_type_temp + '&date=' +strfomat_date(day_sum)
            print('开始链接：' + ranking_model_url)
            rangking_page = rangking_page_get(ranking_model_url)
            first_page_get_original_picture_info(rangking_page)

            if(catch_type_temp[6:] == 'rookie' or catch_type_temp[6:] == 'original'):#原创和新人只有6页图片
                max_page_num = 6
            else:
                max_page_num = 10   #日，周，月排行都有10页

            p = 2
            format = 'json'
            print('tt:' + tt)

            while p <= max_page_num:
                print('第' + str(p) + '页###########################################################')
                get_more_picture(p, format, tt)
                p = p + 1

            time.sleep(15)

        day_sum = day_sum - 1
        catch_day_temp = catch_day_temp + 1


