#! user/bin/env python
# encoding: utf-8
"""
    @author:易兮尘
    @file:qqmail_weather2.0.py
    @time:2020/8/7   2022/02/03--02/08
    @function: 爬取今日天气和美文发送给指定邮箱
            2.0 将天气转化为图片发送出去
"""
import io
import re
import time
import json
import requests
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from PIL import Image, ImageDraw, ImageFont  # 导入绘图模块
from email.mime.text import MIMEText
from email.header import Header
from random_User_Agent import User_Agent


# 爬取信息
class Spider:
    def __init__(self):
        self.weather_city = input('请输入天气城市(最小到县/市级)：')
        self.file = 'cities.text'
        # 天气API的url（post请求）
        self.weather_url = 'http://apis.juhe.cn/simpleWeather/query'
        # 美文的API url（get请求）
        self.meiwen_url = 'https://apis.juhe.cn/fapig/soup/query?key=88d46841bfe05da9c3a6d548f49c06a8'
        self.headers = {
            'User-Agent': User_Agent()}

    def cheek_city(self):
        with open(self.file, 'r', encoding='utf-8') as fp:
            while self.weather_city not in fp.read():
                self.weather_city = input('该城市的天气暂时无法查询，请输入另外的城市：')

    def get_weather(self):
        self.cheek_city()
        data = {
            "city": self.weather_city,
            "key": "2557a0ef9a6a58b91e78cd5e2a0edd6d"
        }
        response = requests.post(self.weather_url, headers=self.headers, data=data).text
        result = json.loads(response)["result"]
        weather = "                           建始近5日天气：\n_________________________________________________________________________________\n"
        future_result = result["future"]
        today = re.findall("'date': '(.*?)'", str(future_result[0]))[0]
        today_temperature = result["realtime"]["temperature"] + '℃'  # 今日气温
        if '/' not in today_temperature:
            today_temperature = '-/' + today_temperature
        today_humidity = result["realtime"]["humidity"]  # 今日湿度
        today_info = result["realtime"]["info"]  # 今日天气
        today_direct = result["realtime"]["direct"]  # 今日风向
        today_power = result["realtime"]["power"]  # 今日风级
        today_aqi = result["realtime"]["aqi"]  # 今日api指数
        today_weather = '气温：{} | 湿度：{} | 天气：{} | 风向：{} | 风级：{} | aqi指数：{}'.format(today_temperature, today_humidity,
                                                                                  today_info, today_direct, today_power,
                                                                                  today_aqi)
        weather1 = '今日({})天气状况：\n{}'.format(today, today_weather)
        weather2 = '\n后几天的天气状况：'
        for x in range(len(future_result) - 1):
            date = re.findall("'date': '(.*?)'", str(future_result[x + 1]))[0]
            temperature = re.findall("'temperature': '(.*?)'", str(future_result[x + 1]))[0]
            info = re.findall("'weather': '(.*?)'", str(future_result[x + 1]))[0]
            direct = re.findall("'direct': '(.*?)'", str(future_result[x + 1]))[0]
            content = '  '.join([date, temperature, info, direct])
            weather2 = weather2 + '\n' + content
        weather = weather + weather1 + weather2
        print('获取天气完成！')
        return weather

    def get_meiwen(self):
        i = 0
        b = []
        response = requests.get(self.meiwen_url, headers=self.headers).text
        resp = json.loads(response)
        content0 = resp["result"]["text"]  # 返回的美文内容
        meiwen = '今日美句：' + content0
        while True:
            c = list(meiwen)[i:i + 40]
            b.append(''.join(c))
            if len(c) < 40:
                break
            i += 40
        content1 = '\n'.join(b)  # 最终分行的美文内容
        print('获取美文完成！')
        return content1


# 发送邮件
class Mail:
    def __init__(self, _buf, _sender, _receivers):
        # 第三方 SMTP 服务
        # self.content = weather__content + '\n\n励志美文，每日一篇，总有你喜欢的！\n' + _meiwen
        self.mail_host = "smtp.qq.com"  # 设置服务器:这个是qq邮箱服务器，直接复制就可以
        self.mail_pass = "wfqtdiyocbrbbaeb"  # 刚才我们获取的授权码
        self.sender = '1198858349@qq.com'  # 你的邮箱地址
        self.receivers = _receivers  # 收件人的邮箱地址，可设置为你的QQ邮箱或者其他邮箱，可多个
        self.buf = _buf  # 调用缓存

    def send(self):
        from_name = input('请输入发件人：')
        to_name = input('请输入收件人：')
        print('开始发送天气邮件...')
        message = MIMEMultipart('related')
        message['From'] = Header(from_name, 'utf-8')
        message['To'] = Header(to_name, 'utf-8')
        subject = '每日天气'  # 发送的主题，可自由填写
        message['Subject'] = Header(subject, 'utf-8')
        content = MIMEText('<html><body><img src="cid:imageid" alt="imageid"></body></html>', 'html', 'utf-8')
        message.attach(content)
        # # 将图片保存在文件中并调用
        # file = open("weather.png", "rb")
        # img_data = file.read()
        # file.close()

        # 图片保存在缓存中
        img_data = self.buf.getvalue()
        img = MIMEImage(img_data)
        img.add_header('Content-ID', 'imageid')
        message.attach(img)
        try:
            smtpObj = smtplib.SMTP_SSL(self.mail_host, 465)
            smtpObj.login(self.sender, self.mail_pass)
            smtpObj.sendmail(self.sender, self.receivers, message.as_string())
            smtpObj.quit()
            print('邮件发送成功！')
        except smtplib.SMTPException as e:
            print('邮件发送失败，具体原因：' + str(e))


# 将天气生成为图片并存在缓存中
def weather_pic(weather):
    wide = 950
    height = 500
    # 构造字体对象
    font = ImageFont.truetype(r'SongTi.otf', 20)
    img = Image.new('RGB', (wide, height), '#00ffff')
    # 创建画笔对象
    draw = ImageDraw.Draw(img)
    draw.text((30, 10), weather, font=font, fill='black')
    del draw
    buf = io.BytesIO()
    # 将图片保存在内存中,文件类型为png
    img.save(buf, "PNG")
    # img.show()
    img.save('weather.png')  # 存在文件中
    return buf


def main():
    sender = input('请输入你的QQ邮箱地址：').lower()
    while not re.search(r'\w[-\w.+]*@qq.com', sender):
        sender = input('您输入的QQ邮箱地址有误，请重新输入：').lower()
    receivers = input('请输入收件人的邮箱地址：').lower()
    while not re.search(r'\w[-\w.+]*@qq.com', receivers):
        receivers = input('您输入的QQ邮箱地址有误，请重新输入：').lower()
    spider = Spider()
    weather_content = spider.get_weather()
    meiwen_content = spider.get_meiwen()
    text = weather_content + '\n========================================================================\n' + meiwen_content
    buf = weather_pic(text)
    mail = Mail(buf, _sender=sender, _receivers=receivers)
    mail.send()
    time.sleep(5)


if __name__ == '__main__':
    main()
