#!/usr/bin/env python
# coding: utf-8
# 电商Nginx日志分析

import re
import os
import web
import json
import time
import hashlib
import datetime
import xml.etree.ElementTree as ET
from app.helpers import bus

render = web.template.render('app/templates/')

# 查询页面
class Monitor():
    def GET(self):
        i = web.input()
        signature = i.signature
        timestamp = i.timestamp
        nonce     = i.nonce
        token     = "lovekk"

        tmpArr    = [token, timestamp, nonce]
        tmpArr.sort()
        tmpArr    = ''.join(tmpArr)
        if hashlib.sha1(tmpArr).hexdigest() == signature:
            return i.echostr

    def POST(self):
        str_xml = web.data()
        xml = ET.fromstring(str_xml)
        
        #获取用户的输入
        keyWord = xml.find("Content").text.strip()
        msgType = xml.find("MsgType").text
        fromUser= xml.find("FromUserName").text
        toUser  = xml.find("ToUserName").text
        
        result = ""
        print re.findall("运通|\d+",keyWord),keyWord
        #用户输入空
        if keyWord.strip()=="":
            result = "小主~聊点什么吧~"

        elif re.findall("s \d+",keyWord):
            busId  = int(keyWord[2:])
            stationList = bus.requestStations(busId)

            result = []
            for station in stationList:
                result.append(str(station["index"])+": "+station["station_name"])
            result.append("查看实时公交信息请输入:r+空格+车次ID号+站点ID号\n如r 863 3")
            result = "\n".join(result)

        elif re.findall("r \d+ \d+",keyWord):
            allInfo = re.findall("r \d+ \d+",keyWord)
            routeId = int(allInfo[0].split()[1])
            stationId = int(allInfo[0].split()[2])
            
            result  = bus.requestBusInfo(routeId,stationId)

        elif re.findall("运通|\d+",keyWord):
            busId  = bus.requestRouteId(keyWord)
            busList = bus.requestStationInfo(busId)
            print "################nginxmonitor##################",busList
            retDict = json.loads(busList)
            for routeId in retDict:
                result += "车次ID（{0}）: {1}\n".format(routeId,retDict[routeId])
            result += "查看具体的站点信息请输入:s+空格+车次ID号\n如s 863"

        else:
            result = "亲~我暂时还不能理解你的话哟"

        print fromUser,toUser
        return render.reply_text(fromUser,toUser,int(time.time()),result)
