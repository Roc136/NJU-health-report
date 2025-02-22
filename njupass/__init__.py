"""
DESCRIPTION:
    Tools for getting Authorization websites of Nanjing University
PACKAGES:
    NjuUiaAuth
    NjuEliteAuth
"""
import execjs
import requests
import re
import os
from io import BytesIO
import njupass.ocr
import time

URL_NJU_UIA_AUTH = 'https://authserver.nju.edu.cn/authserver/index.do'
URL_NJU_ELITE_LOGIN = 'http://elite.nju.edu.cn/jiaowu/login.do'
URL_JKDK_INDEX = 'http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.do'
URL_JKDK_LIST = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/getApplyInfoList.do'
URL_JKDK_APPLY = 'http://ehallapp.nju.edu.cn/xgfw/sys/yqfxmrjkdkappnju/apply/saveApplyInfos.do'

MY_UA = "Mozilla/5.0 (Linux; Android 10; MAR-AL00 Build/HUAWEIMAR-AL00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/80.0.3987.99 Mobile Safari/537.36  cpdaily/8.2.7 wisedu/8.2.7"


class NjuUiaAuth:
    """
    DESCRIPTION:
        Designed for passing Unified Identity Authentication(UIA) of Nanjing University.
    """

    def __init__(self):
        self.cookies = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': MY_UA,
        })

        r = self.session.get(URL_NJU_UIA_AUTH)
        # self.lt = re.search(
        #     r'<input type="hidden" name="lt" value="(.*)"/>', r.text).group(1)
        # self.execution = re.search(
        #     r'<input type="hidden" name="execution" value="(.*)"/>', r.text).group(1)
        # self._eventId = re.search(
        #     r'<input type="hidden" name="_eventId" value="(.*)"/>', r.text).group(1)
        # self.rmShown = re.search(
        #     r'<input type="hidden" name="rmShown" value="(.*)"', r.text).group(1)
        # self.pwdDefaultEncryptSalt = re.search(
        #     r'var pwdDefaultEncryptSalt = "(.*)"', r.text).group(1)

    # def getCaptchaCode(self):
    #     """
    #     DESCRIPTION:
    #         Getting captcha code binded with IP
    #     RETURN_VALUE:
    #         captcha code image(ByteIO). Recommended using Image.show() in PIL.
    #     """
    #     url = 'https://authserver.nju.edu.cn/authserver/captcha.html'
    #     res = self.session.get(url, stream=True)
    #     return BytesIO(res.content)
    #
    # def parsePassword(self, password):
    #     """
    #     DESCRIPTION:
    #         Parsing password to encrypted form which can be identified by the backend sersver of UIA.
    #     ATTRIBUTES:
    #         password(str): Original password
    #     """
    #     with open(os.path.join(os.path.dirname(__file__), 'resources/encrypt.js')) as f:
    #         ctx = execjs.compile(f.read())
    #     return ctx.call('encryptAES', password, self.pwdDefaultEncryptSalt)
    #
    # def needCaptcha(self, username):
    #     url = 'https://authserver.nju.edu.cn/authserver/needCaptcha.html?username={}'.format(
    #         username)
    #     r = self.session.post(url)
    #     if 'true' in r.text:
    #         return True
    #     else:
    #         return False
    #
    # def tryLogin(self, username, password):
    #     """
    #     DESCRIPTION:
    #         Try to login using OCR to bypass captcha.
    #         Return true if login success, false otherwise
    #     """
    #     try_times = 3
    #     for _ in range(try_times):
    #         captchaText = ""
    #         if self.needCaptcha(username):
    #             captchaText = ocr.detect(self.getCaptchaCode())
    #         ok = self.login(username, password, captchaResponse=captchaText)
    #         if ok:
    #             return True
    #         time.sleep(5)
    #
    #     return False
    #
    # def login(self, username, password, captchaResponse=""):
    #     """
    #     DESCRIPTION:
    #         Post a request for logging in.
    #         Return true if login success, false otherwise
    #     ATTRIBUTES:
    #         username(str)
    #         password(str)
    #     """
    #     data = {
    #         'username': username,
    #         'password': self.parsePassword(password),
    #         'lt': self.lt,
    #         'dllt': 'userNamePasswordLogin',
    #         'execution': self.execution,
    #         '_eventId': self._eventId,
    #         'rmShown': self.rmShown,
    #         'captchaResponse': captchaResponse,
    #         "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit 537.36 (KHTML, like Gecko) Chrome"
    #     }
    #     r = self.session.post(URL_NJU_UIA_AUTH, data=data,
    #                           allow_redirects=False)
    #     return r.status_code == 302

    def setCookies(self, cookies):
        self.cookies = {item.split('=')[0]: item.split('=')[1] for item in cookies.split("; ")}
        self.session.headers.update({'User-Agent': MY_UA})
        self.session.get(URL_NJU_UIA_AUTH)
        for key, value in self.cookies.items():
            self.session.cookies.set(key, value)
        res = self.session.get(URL_NJU_UIA_AUTH, cookies=self.cookies).text
        if res.find('个人资料') != -1:
            return True
        return False

    def getHistory(self):
        self.session.get(URL_JKDK_INDEX)
        self.updateHeaders()
        return self.session.get(URL_JKDK_LIST)

    def checkin(self, wid, curr_location, zjhs_time):
        data = "?WID={}&IS_TWZC=1&CURR_LOCATION={}&ZJHSJCSJ={}&JRSKMYS=1&IS_HAS_JKQK=1&JZRJRSKMYS=1&SFZJLN=1".format(
            wid, curr_location, zjhs_time)
        url = URL_JKDK_APPLY + data
        self.updateHeaders()
        self.session.get(url)

    def updateHeaders(self):
        self.session.headers.update({
            'Host': 'ehallapp.nju.edu.cn',
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': MY_UA,
            'X-Requested-With': 'com.wisedu.cpdaily.nju',
            'Referer': 'http://ehallapp.nju.edu.cn/xgfw/sys/mrjkdkappnju/index.html',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        })
