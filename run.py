import random

from njupass import NjuUiaAuth
from dotenv import load_dotenv
import os
import json
import time
import logging
import datetime
from pytz import timezone

auth = NjuUiaAuth()


def notify(msg):
    with open('email.txt', 'a+') as f:
        f.write(msg + '\n')
    return


def get_normalization_date(username):
    today = datetime.datetime.now(timezone('Asia/Shanghai'))
    date = datetime.datetime(2022, 4, (4 + 1) + (int(username[-1]) + 4) % 5, 8, 30)
    while (today.replace(tzinfo=None) - date).days >= 5:
        date += datetime.timedelta(days=5)
    return date


def get_zjhs_time(method='YESTERDAY', username=None, last_time=None):
    today = datetime.datetime.now(timezone('Asia/Shanghai'))
    yesterday = today + datetime.timedelta(-1)
    if method == 'YESTERDAY':
        return yesterday.strftime("%Y-%m-%d %-H")
    elif method == 'LAST':
        return last_time
    elif method == 'NORMALIZATION':
        return get_normalization_date(username).strftime("%Y-%m-%d %-H")
    elif method == 'NORMALIZATION&LAST':
        if get_normalization_date(username) < datetime.datetime(
                int(last_time[:4]),
                int(last_time[5:7]),
                int(last_time[8:10]),
                int(last_time[11:13])
        ):
            date = last_time
        else:
            date = get_normalization_date(username).strftime("%Y-%m-%d %-H")
        return date
    elif method.startswith("STEP"):  # 根据起始时间和时间间隔计算上次核酸检测时间，例STEP::2022-10-07 17:00::2
        infos = method.split("::")
        start_date = infos[1]
        step = int(infos[2])

        today = datetime.datetime.now(timezone('Asia/Shanghai'))
        date = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
        while (today.replace(tzinfo=None) - date).days >= step:
            date += datetime.timedelta(days=step)
        return date
    else:
        raise Exception("核酸检测日期方式方式不正确")


def get_location(location_info_from, last_location):
    if location_info_from == 'CONFIG':
        return os.getenv('CURR_LOCATION')
    elif location_info_from == 'LAST':
        return last_location
    else:
        log.info('地址信息配置不正确，使用默认设置: LAST')
        return last_location


if __name__ == "__main__":
    load_dotenv(verbose=True)
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    log = logging.getLogger()

    username = os.getenv('NJU_USERNAME')
    password = os.getenv('NJU_PASSWORD')
    location_info_from = os.getenv('LOCATION_INFO_FROM')
    method = os.getenv('COVID_TEST_METHOD')
    random_sleep = os.getenv('SLEEP') == 'true'

    curr_location = ''
    zjhs_time = ''

    if location_info_from == '':
        location_info_from = 'LAST'
    if method == '':
        method = 'YESTERDAY'

    if username == '' or password == '' or (location_info_from == 'CONFIG' and curr_location == ''):
        log.error('账户、密码或地理位置信息为空！请检查是否正确地设置了 SECRET 项（GitHub Action）。')
        notify('账户、密码或地理位置信息为空！请检查是否正确地设置了 SECRET 项（GitHub Action）。')
        os._exit(0)

    log.info('尝试登录...')
    try:
        if not auth.setCookies(password):
            log.error('Cookies错误或失效')
            notify('Cookies错误或失效')
            os._exit(0)
    except Exception as e:
        log.error(e)
        notify(str(e))
        os._exit(0)
    log.info('登陆成功！')

    # 随机等待0-16.6667min
    if random_sleep:
        sleep_time = random.random()*1000
        log.info('随机等待，正在等待...(等待时间：%ds)' % sleep_time)
        time.sleep(sleep_time)
    else:
        log.info('延时10s...')
        time.sleep(10)

    for count in range(10):
        log.info('尝试获取打卡列表信息...')
        try:
            r = auth.getHistory()
            if r.status_code != 200:
                log.error('获取失败，一分钟后再次尝试...')
                time.sleep(60)
                continue
        except Exception as e:
            log.error(e)
            log.error('获取失败，一分钟后再次尝试...')
            time.sleep(60)
            continue
        dk_info = json.loads(r.text)['data']

        # 根据配置填写地址和核酸检测信息
        curr_location = get_location(location_info_from, dk_info[1]["CURR_LOCATION"])
        try:
            zjhs_time = get_zjhs_time(method, username, dk_info[1]['ZJHSJCSJ'])
        except Exception as e:
            log.error(e)
            log.error("最近核酸检测日期配置错误")
            notify("最近核酸检测日期配置错误")
            os._exit(0)


        if dk_info[0]['TBZT'] == "0":
            log.info('正在打卡...')
            try:
                auth.checkin(dk_info[0]['WID'], curr_location, zjhs_time)
                time.sleep(5)
            except Exception as e:
                log.error(e)
                log.error('打卡失败，一分钟后再次尝试...')
                time.sleep(60)
                continue
        else:
            log.info("打卡成功！")
            notify("打卡成功！")
            os._exit(0)

    log.error("打卡失败，请尝试手动打卡")
    notify("打卡失败，请手动打卡！")
    os._exit(0)
