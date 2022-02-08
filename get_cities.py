# encoding: utf-8
"""
    @author:易兮尘
    @file:get_cities.py
    @time:2022/2/8
    @function:获取可查看天气的城市列表
"""
import json
import re
import requests
from random_User_Agent import User_Agent


def main():
    headers = {
        'user-agent': User_Agent()
    }
    response = requests.get('http://apis.juhe.cn/simpleWeather/cityList?key=2557a0ef9a6a58b91e78cd5e2a0edd6d', headers=headers).text
    file = 'cities.text'
    fp = open(file, 'w', encoding='utf-8')
    fp.write(' '.join(re.findall("'district': '(.*?)'", str(json.loads(response)["result"]))))
    fp.close()
    print('城市列表已创建成功！')


if __name__ == '__main__':
    main()
