# -*- coding: utf8 -*-

import os
import pickle
import re
import time
import requests

UserAgent = 'Mozilla/5.0 (Linux; Android 10; Redmi Note 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.101 Mobile Safari/537.36'

GOODJOB_USER = os.environ.get('GOODJOB_USER')
GOODJOB_PWD = os.environ.get('GOODJOB_PWD')
JOB51_COOKIE = os.environ.get('JOB51_COOKIE')
JOB51_ReSumeID = os.environ.get('JOB51_ReSumeID')


session = requests.Session()
session.timeout = 5
session.cookies.update({'51job': JOB51_COOKIE})

_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def load_cookie(cookie_name: str) -> bool:
    """
    从 cookie.pkl 文件中读取 cookie_name 的 Cookie 并检验是否过期
    """
    if (os.path.exists('cookie.pkl')):
        try:
            with open('cookie.pkl', 'rb') as fr:
                session.cookies = pickle.load(fr)
                expires = next(x for x in session.cookies if x.name ==
                               cookie_name).expires
        except (StopIteration, EOFError):
            return True
        if (int(expires) <= int(time.time())):
            print("Cookie 已过期，重新登录!")
            return True
        else:
            print("使用 Cookie 登录!")
            return False
    else:
        return True


def goodjob_refresh():
    headers = {
        'Host': 'm.goodjob.cn',
        'Connection': 'keep-alive',
        'Content-Length': '42',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'DNT': '1',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': UserAgent,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://m.goodjob.cn',
        'Referer': 'http://m.goodjob.cn/Login',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh,zh-CN;q=0.9',
    }

    def login():
        data = {
            'UserName': GOODJOB_USER,
            'UserPwd': GOODJOB_PWD
        }

        # 登录, cookie 生存时间 1h
        response = session.post('http://m.goodjob.cn/ajax/Login.ashx',
                                headers=headers, data=data)
        res = response.json()
        if (res['code'] == -1):
            print(f"{_time} 登录失败！")
            return
        if (res['code'] == 1):
            print(f"{_time} 登录成功")

    # 刷新简历
    # if (load_cookie('.goodjobcnmanage')):
    login()
    headers['Content-Length'] = '0'
    headers['Referer'] = 'http://m.goodjob.cn/Manage/index.aspx'
    response = session.post(
        'http://m.goodjob.cn/ajax/RefreshResume.ashx', headers=headers)
    if (response.status_code == 200):
        print(f"{_time} 刷新成功")


def job51_refresh():
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Origin': 'https://login.51job.com',
        'Upgrade-Insecure-Requests': '1',
        'DNT': '1',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://login.51job.com/login.php?lang=c',
        'Accept-Language': 'zh,zh-CN;q=0.9',
    }

    response = session.get(
        'https://m.51job.com/my/my51job.php', headers=headers)
    response.encoding = 'utf-8'
    # print(response.text)
    if ("$_CONFIG['islogin'] = '1';" in response.text):
        print(f"{_time} 登录成功！")
    else:
        print(f"{_time} Cookie 已过期！")
        return
    params = (
        ('0.2743062077884375', ''),
        ('jsoncallback',
         f'jQuery18304990121686218256_{int(time.time() * 1000)}'),
        ('ReSumeID', JOB51_ReSumeID),
        ('lang', 'c')
    )
    response = session.get('https://i.51job.com/resume/ajax/refresh_resume.php',
                           headers=headers, params=params, )
    msg = re.search(r'{.+}', response.text)
    if (msg):
        msg = msg.group()
    print(response.text)


def save_cookie():
    with open('cookie.pkl', 'wb') as fw:
        pickle.dump(session.cookies, fw)


def main(event, context):
    goodjob_refresh()
    job51_refresh()
    # save_cookie()


if __name__ == '__main__':
    main('', '')
