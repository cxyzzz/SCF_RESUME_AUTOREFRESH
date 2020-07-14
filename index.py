# -*- coding: utf8 -*-

import json
import os
import random
import pickle
import sys
import re
import time
import logging

import requests


UserAgent = 'Mozilla/5.0 (Linux; Android 10; Redmi Note 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.101 Mobile Safari/537.36'
UserAgent_Desktop = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'

GOODJOB_USER = os.environ.get('GOODJOB_USER')
GOODJOB_PWD = os.environ.get('GOODJOB_PWD')
JOB51_COOKIE = os.environ.get('JOB51_COOKIE')
ZHAOPING_COOKIE_AT = os.environ.get('ZHAOPING_COOKIE_AT')
QY_WEIXING_BOT_KEY = os.environ.get('QY_WEIXING_BOT_KEY')

ip = str(random.choice(list(range(255)))) + '.' + str(random.choice(list(range(255)))) + '.' + str(
    random.choice(list(range(255)))) + '.' + str(random.choice(list(range(255))))
session = requests.Session()
session.timeout = 5
session.headers = {'X-Client-IP': ip,
                   'X-Remote-IP': ip,
                   'X-Remote-Addr': ip,
                   'X-Originating-IP': ip,
                   'x-forwarded-for': ip, }

# session add 51job cookie
session.cookies.update({'51job': JOB51_COOKIE})

# session add zhaoping.com cookie
session.cookies.update({'at': ZHAOPING_COOKIE_AT, 'rt': 'a'})


_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


work_dir = os.path.dirname(sys.argv[0])
log_file = work_dir + os.sep + 'refresh.log'
cookie_file = work_dir + os.sep + 'cookie.pkl'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

date_fmt = '%Y-%m-%d %H:%M:%S'
msg_fmt = '%(asctime)s [%(filename)s:%(lineno)d] %(funcName)s %(levelname)s - %(message)s'

formatter = logging.Formatter(fmt=msg_fmt, datefmt=date_fmt)

fhl = logging.FileHandler(filename=log_file, mode='a')
fhl.setFormatter(formatter)
fhl.setLevel(logging.INFO)

shl = logging.StreamHandler()
shl.setFormatter(formatter)

logger.addHandler(fhl)
logger.addHandler(shl)


def push(title: str, msg: str):
    headers = {
        'Content-Type': 'application/json',
    }

    params = (
        ('key', QY_WEIXING_BOT_KEY),
    )

    data = {
        "msgtype": "text",
        "text": {
            "content": f"{title}\n{msg}"
        }
    }
    response = requests.post('https://qyapi.weixin.qq.com/cgi-bin/webhook/send',
                             headers=headers, params=params, data=json.dumps(data))
    logger.info(response.text)


def load_cookie(cookie_name: str) -> bool:
    """
    从 cookie.pkl 文件中读取 cookie_name 的 Cookie 并检验是否过期
    """
    if (os.path.exists(cookie_file)):
        func_name = sys._getframe(1).f_code.co_name
        try:
            with open(cookie_file, 'rb') as fr:
                cookies = pickle.load(fr)
                
                cookie = next(x for x in cookies if x.name ==
                               cookie_name)
        except (StopIteration, EOFError):
            return True
        if cookie.is_expired():
            logger.error(f"{func_name} Cookie 已过期，重新登录!")
            return True
        else:
            logger.info(f"{func_name} 使用 Cookie 登录!")
            session.cookies.set_cookie(cookie)
            return False
    else:
        logger.info("cookie 文件不存在!")
        return True


def save_cookie():
    with open(cookie_file, 'wb') as fw:
        pickle.dump(session.cookies, fw)


def goodjob_resume_refresh():
    headers = {
        'Host': 'm.goodjob.cn',
        'User-Agent': UserAgent,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://m.goodjob.cn',
        'Referer': 'http://m.goodjob.cn/Login',
    }
    session.headers.update(headers)

    def login():
        data = {
            'UserName': GOODJOB_USER,
            'UserPwd': GOODJOB_PWD
        }

        # 登录, cookie 生存时间 1h
        response = session.post('http://m.goodjob.cn/ajax/Login.ashx',
                                data=data)
        res = response.json()
        if (res['code'] == -1):
            logger.error(f"俊才网登录失败！[{res}]")
            return
        if (res['code'] == 1):
            logger.info("俊才网登录成功!")

    # 刷新简历
    session.get('http://m.goodjob.cn')
    if (load_cookie('.goodjobcnmanage')):
        login()
    session.headers.update(
        {'Content-Length': '0', 'Referer': 'http://m.goodjob.cn/Manage/index.aspx'})
    response = session.post(
        'http://m.goodjob.cn/ajax/RefreshResume.ashx')
    if (response.text == 'NotLogin'):
        logger.error(f"俊才网刷新失败![{response.text}]")
    else:
        logger.info("俊才网刷新成功")


def job51_resume_refresh():
    headers = {
        'Host': 'm.51job.com',
        'Origin': 'https://m.51job.com',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': UserAgent,
        'Referer': 'https://m.51job.com',
    }
    session.headers.update(headers)

    session.get('https://m.51job.com')
    response = session.get(
        'https://m.51job.com/resume/myresume.php')
    response.encoding = 'utf-8'
    if ("$_CONFIG['islogin'] = '1'" in response.text):
        logger.info("51job登录成功！")
        userid = re.search(r'userid=(\d+)', response.text)
        if (userid):
            userid = userid.group(1)
            logger.info(f"51job userid: {userid}")
        else:
          logger.error("51job userid not found!")
          return
    else:
        logger.error("51job Cookie 已过期！")
        return
    
    data = {
      'userid': userid
    }
    
    response = session.post('https://m.51job.com/ajax/resume/refreshresume.ajax.php', data=data)
    res = response.json()
    logger.info(res)


def zhaoping_resume_refresh():
    headers = {
        'Host': 'fe-api.zhaopin.com',
        'authority': 'fe-api.zhaopin.com',
        'accept': 'application/json, text/plain, */*',
        'User-Agent': UserAgent_Desktop,
        'origin': 'https://i.zhaopin.com',
        'referer': 'https://i.zhaopin.com/resume',
    }
    session.headers.update(headers)

    session.get('https://www.zhaopin.com')
    response = session.get(
        'https://fe-api.zhaopin.com/c/i/user/detail')
    res = response.json()
    if (res['code'] == 200):
        logger.info("智联招聘登录成功！")
    else:
        push('智联招聘简历刷新', 'Cookie 已过期')
        logger.error("智联招聘 Cookie 已过期")
        return

    data = {
        "resumeLanguage": res['data']['Resume']['LangueId'],
        "resumeNumber": res['data']['Resume']['ResumeNumber'],
        "resumeId": res['data']['Resume']['Id']
    }
    params = (
        ('at', session.cookies.get('at')),
        ('rt', session.cookies.get('rt')),
    )
    response = session.post('https://fe-api.zhaopin.com/c/i/resume/refresh',
                            params=params, data=json.dumps(data))
    res = response.json()
    if (res['code'] == 200):
        logger.info(res)
    else:
        logger.error(res)
        push('智联招聘简历刷新', 'Cookie 已过期')
        return


def main(event, context):
    time.sleep(random.randint(0, 60))
    goodjob_resume_refresh()
    job51_resume_refresh()
    zhaoping_resume_refresh()
    save_cookie()
    session.close()

if __name__ == '__main__':
    main('', '')
