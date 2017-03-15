#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/3/13 18:02
# @Author  : klk
# @Site    : 
# @File    : getproxy.py
# @Software: PyCharm
import random

import requests
import time
from lxml import etree
import pytesseract
from io import BytesIO
from PIL import Image
from sqlalchemy import Column, Integer, String, UniqueConstraint, Float, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()
mysqlengine_wb = create_engine("mysql+pymysql://username:passwd@hostname:port/db?charset=utf8mb4")

### 创建存储proxy 数据库表
class ProxyIpFree(Base):
    __tablename__ = 'ip_table'
    id = Column(Integer, primary_key=True)
    ip = Column(String(50))
    port = Column(String(50))
    cls = Column(String(50))
    anonymous = Column(String(50))
    address = Column(String(50))
    operator = Column(String(50))
    restime = Column(String(50))
    speed = Column(Float)
    vertime = Column(DateTime, unique=True)
    addtime = Column(DateTime(timezone=True), default=func.now())
    retry_num = Column(Integer,default=0)
Session = sessionmaker(bind=mysqlengine_wb)
session = Session()
Base.metadata.create_all(mysqlengine_wb)

### 获得代理
def getProxyIps(offset,limit):
    ips = session.query(ProxyIpFree.ip, ProxyIpFree.port).order_by(ProxyIpFree.vertime.desc()).offset(offset).limit(limit).all()
    ipstrs = ["http://" + ip.ip + ":" + ip.port for ip in ips]
    return ipstrs

### 发送请求
def getResponse(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux X86; U; Debian SID; it; rv:1.9.0.1) Gecko/2008070208 Debian IceWeasel/3.0.1',
    }
    proxies = {}
    status = 500
    req = None
    try:
        req = requests.get(url, headers=headers)
        status = req.status_code
    except Exception,e:
        pass
    get_num = 0
    limit = 10
    ips = []
    while status != 200:
        if len(ips) < 1:
            ips = getProxyIps(get_num*limit,limit)
            get_num += 1
        ip = random.choice(ips)
        proxies["http"] = ip
        try:
            req = requests.get(url, headers=headers, proxies=proxies,timeout=5)
            status = req.status_code
            if status != 200 and ip in ips:
                ips.remove(ip)
        except Exception,e:
            status = 500
            if ip in ips:
                ips.remove(ip)

    return req

### 获得代理ip
def getIps():

    urls = ["http://proxy.mimvp.com/free.php?proxy=in_tp", "http://proxy.mimvp.com/free.php?proxy=in_hp"]
    ips = []
    for url in urls:
        req = getResponse(url)
        htmlparse = etree.HTMLParser()
        root = etree.fromstring(req.text, htmlparse)
        rows = root.xpath("//tbody/td")
        ip = []
        for index, row in enumerate(rows):
            if index % 10 == 1:
                ip.append(row.xpath("./text()")[0])
            if index % 10 == 2:
                ip.append(row.xpath("./img/@src")[0])
            if index % 10 == 3:
                ip.append(row.xpath("./text()")[0])
            if index % 10 == 4:
                ip.append(row.xpath("./text()")[0])
            if index % 10 == 5:
                ip.append(row.xpath("./font/text()")[0])
            if index % 10 == 6:
                ip.append(row.xpath("./text()")[0])
            if index % 10 == 7:
                ip.append(row.xpath("./@title")[0])
            if index % 10 == 8:
                ip.append(row.xpath("./@title")[0])
            if index % 10 == 9:
                ip.append(row.xpath("./text()")[0])
            if index % 10 == 0 and index / 10 > 0:
                ips.append(ip)
                ip = []
    ips_dict = []
    for ip in ips:
        req = getResponse("http://proxy.mimvp.com/"+ip[1])
        time.sleep(2)
        img = Image.open(BytesIO(req.content))
        try:
            text = pytesseract.image_to_string(img, config="-psm 6 digits").strip()
            ip_dict = {"ip": ip[0],
                       "port": text,
                       "cls": ip[2],
                       "anonymous": ip[3],
                       "address": ip[4],
                       "operator": ip[5],
                       "restime": ip[6],
                       "speed": ip[7],
                       "vertime": ip[8],
                       }
            if ip_dict not in ips_dict:
                ips_dict.append(ip_dict)
        except:
            pass
    return ips_dict


def main():
	###入库
    for ip in getIps():
        try:
            session.merge(ProxyIpFree(**ip))
            session.commit()
        except Exception as e:
            session.rollback()


main()
