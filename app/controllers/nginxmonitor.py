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
import memcache
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
        MEMCACHE_HOST_TEST = "127.0.0.1:11211"
        str_xml = web.data()
        xml = ET.fromstring(str_xml)
        
        #获取用户的输入
        keyWord = xml.find("Content").text.strip()
        msgType = xml.find("MsgType").text
        fromUser= xml.find("FromUserName").text
        toUser  = xml.find("ToUserName").text

        mc = memcache.Client([MEMCACHE_HOST_TEST],debug=0)
        
        result = ""
        print re.findall("运通|\d+",keyWord),keyWord
        #用户输入空
        if keyWord.strip()=="":
            result = "小主~聊点什么吧~"

        elif re.findall("clear",keyWord.strip(),re.IGNORECASE):
            result = "清除完毕,可开始新的查询~"
            mc.set(fromUser,"done")

        elif re.findall("运通|^\d+",keyWord):
            if (not mc.get(fromUser)) or (mc.get(fromUser) == "done"):
                busId  = bus.requestRouteId(keyWord)
                busList = bus.requestStationInfo(busId)
                retDict = json.loads(busList)
                routeIdList = []
                for routeId in retDict:
                    result += "车次ID（{0}）: {1}\n".format(routeId,retDict[routeId])
                    routeIdList.append(str(routeId))
                result += "请输入待查询车次ID号以查看具体的站点信息\n如：863\n【结束此次查询请输入clear】"
                mc.set(fromUser,"getBusList,{0}".format(",".join(routeIdList)))

            elif re.findall("getBusList",mc.get(fromUser)):
                busId  = int(keyWord)
                busIdList = mc.get(fromUser).split(",")[1:]
                print busIdList
                if keyWord not in busIdList:
                    result = "抱歉，输入车次ID不符合上次查询结果！请确认！\n【结束此次查询请输入clear】"
                    return render.reply_text(fromUser,toUser,int(time.time()),result)
                stationList = bus.requestStations(busId)
                result = []
                stationIdList = []
                for station in stationList:
                    result.append(str(station["index"])+": "+station["station_name"])
                    stationIdList.append(str(station["index"]))
                result.append("请输入待查询站点ID号以查看实时公交信息\n如：3\n【结束此次查询请输入clear】")
                result = "\n".join(result)
                mc.set(fromUser,"getRealBus,{0},{1}".format(busId,",".join(stationIdList)))

            elif re.findall("getRealBus",mc.get(fromUser)):
                routeId = int(mc.get(fromUser).split(",")[1])
                stationIdList = mc.get(fromUser).split(",")[2:]
                if keyWord not in stationIdList:
                    result = "抱歉，输入站点ID不符合上次查询结果！请确认！\n【结束此次查询请输入clear】"
                    return render.reply_text(fromUser,toUser,int(time.time()),result)
                stationId = int(keyWord)
                result  = bus.requestBusInfo(routeId,stationId)
                mc.set(fromUser,"done")

        else:
            result = "亲~我暂时还不能理解你的话哟"

        print fromUser,toUser
        return render.reply_text(fromUser,toUser,int(time.time()),result)
