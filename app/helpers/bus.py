#!/usr/bin/evn python
#!coding: utf-8

import os
import time
import json
import uuid
import xmltodict
import urllib
import urllib2
import hashlib
import subprocess
from collections import OrderedDict
from datetime import datetime
from pytz import timezone

E_BUS_STATION = "http://apprealtimebus.bjbus.com/app/app/getStationInfosByRouteId"
E_BUS_ROUTE = "http://apprealtimebus.bjbus.com/app/app/getRouteAndStationInfosByKeywords"
E_BUS_INFO  = "http://apprealtimebus.bjbus.com/app/app/getBusStatusInfosByRouteId"

common_header = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.0.2; MI 2SC MIUI/6.3.24)',
        'Host': 'apprealtimebus.bjbus.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
        'Content-Type': 'application/x-www-form-urlencoded',
}

def getBusMD5(params):
    origin = ""
    for key in params:
        origin += key+"="+str(params[key])
    origin += "client_credentialsf8:a4:5f:11:21:79"
    print origin
    return hashlib.md5(origin).hexdigest()
     
def generateMD5(key,msg):
    m_key = hashlib.md5()
    m_key.update(key+msg)
    return m_key.hexdigest()

def sendMsg(id,key,msg):
    url = "https://ops.ms.netease.com/sendtask"
    key_md5 = generateMD5(key,msg)
    postData = {
        "id":id,
        "msg":msg,
        "key_md5":key_md5
    }
    postData = urllib.urlencode(postData)
    req = urllib2.Request(url,postData)
    r = urllib2.urlopen(req)

def clear(paths):
    for path in paths:
        if os.path.exists(path):
            os.remove(path)

def requestRouteId(keyWord):
    params = OrderedDict([
        ('device_id','f8:a4:5f:11:21:79'),
        ('is_exact',0),
        ('keywords',keyWord),
        ('timestamp',"2016-03-31 15:39:00"),
    ])
    sign = getBusMD5(params)
    print params,sign
    params = dict(params,**{"sign":sign})

    params = urllib.urlencode(params)
    req    = urllib2.Request(E_BUS_ROUTE,params,common_header)
    response = urllib2.urlopen(req)

    uuidNum = str(uuid.uuid1())
    fileGz = "tmpfile{0}.gz".format(uuidNum)
    if response.info()["Content-Encoding"]=="gzip":
        resHtml = open(fileGz,"w")
        resHtml.write(response.read())
        resHtml.close()
        cmd = "gunzip -d "+fileGz
        subprocess.call(cmd,shell=True)

    id = ""
    with open("tmpfile{0}".format(uuidNum),"r") as fileHandler:
        result = json.loads(fileHandler.readline())
        if result and isinstance(result,dict) and "data" in result and result["data"]["datas"]["route_infos"]:
            id = result["data"]["datas"]["route_infos"][0]["route_id"]
    clear(["tmpfile{0}".format(uuidNum),"tmpfile{0}.gz".format(uuidNum)])
    return id

def requestStations(id):
    if id=="":
        return "暂不支持此公交"
    params = OrderedDict([
        ('device_id','f8:a4:5f:11:21:79'),
        ('index',1),
        ('is_change',0),
        ('route_id',id),
        ('timestamp',"2016-03-31 15:39:02"),
        ('type',0),
    ])

    sign = getBusMD5(params)
    params = dict(params,**{"sign":sign})

    params = urllib.urlencode(params)
    req    = urllib2.Request(E_BUS_STATION,params,common_header)
    response = urllib2.urlopen(req)

    uuidNum = str(uuid.uuid1())
    fileGz = "tmpfile{0}.gz".format(uuidNum)
    if response.info()["Content-Encoding"]=="gzip":
        resHtml = open(fileGz,"w")
        resHtml.write(response.read())
        resHtml.close()
        cmd = "gunzip -d "+fileGz
        subprocess.call(cmd,shell=True)

    with open("tmpfile{0}".format(uuidNum),"r") as fileHandler:
        result = json.loads(fileHandler.read())
    clear(["tmpfile{0}".format(uuidNum),"tmpfile{0}.gz".format(uuidNum)])

    return result["data"]["station_infos"]["datas"]

def requestStationInfo(id):
    if id=="":
        return "暂不支持此公交"
    #{ID1:(a->b),ID2:(b->a)}
    retDict = {}
    params  = []
    params.append(OrderedDict([
        ('device_id','f8:a4:5f:11:21:79'),
        ('index',1),
        ('is_change',0),
        ('route_id',id),
        ('timestamp',"2016-03-31 15:39:02"),
        ('type',0),
    ]))
    params.append(OrderedDict([
        ('device_id','f8:a4:5f:11:21:79'),
        ('index',1),
        ('is_change',1),
        ('route_id',id),
        ('timestamp',"2016-03-31 15:39:02"),
        ('type',0),
    ]))
    for param in params:
        sign = getBusMD5(param)
        param = dict(param,**{"sign":sign})

        param = urllib.urlencode(param)
        req    = urllib2.Request(E_BUS_STATION,param,common_header)
        response = urllib2.urlopen(req)

        uuidNum = str(uuid.uuid1())
        fileGz = "tmpfile{0}.gz".format(uuidNum)
        if response.info()["Content-Encoding"]=="gzip":
            resHtml = open(fileGz,"w")
            resHtml.write(response.read())
            resHtml.close()
            cmd = "gunzip -d "+fileGz
            subprocess.call(cmd,shell=True)

        with open("tmpfile{0}".format(uuidNum),"r") as fileHandler:
            result = json.loads(fileHandler.read())
        clear(["tmpfile{0}".format(uuidNum),"tmpfile{0}.gz".format(uuidNum)])

        routeID = result["data"]["route_detail"]["id"]
        start   = result["data"]["route_detail"]["start_station"]
        end     = result["data"]["route_detail"]["end_station"]
        retDict[routeID] = start+" 至 "+end

    print "$$$$$$$$$$$$$$$$$bus$$$$$$$$$$$$$$$$",retDict
    return json.dumps(retDict)

def requestBusInfo(busId,stationId):
    params = OrderedDict([
        ('bus_num',9999),
        ('device_id','f8:a4:5f:11:21:79'),
        ('index',stationId),
        ('route_id',busId),
        ('show_all',1),
        #'timestamp': datetime.now().strftime("%F %T")
        ('timestamp',"2016-03-31 15:39:08"),
    ])
    sign = getBusMD5(params)
    params = dict(params,**{"sign":sign})

    params = urllib.urlencode(params)
    req    = urllib2.Request(E_BUS_INFO,params,common_header)
    response = urllib2.urlopen(req)

    uuidNum = str(uuid.uuid1())
    fileGz = "tmpfile{0}.gz".format(uuidNum)
    if response.info()["Content-Encoding"]=="gzip":
        resHtml = open(fileGz,"w")
        resHtml.write(response.read())
        resHtml.close()
        time.sleep(4.2)
        cmd = "gunzip -d "+fileGz
        subprocess.call(cmd,shell=True)

    with open("tmpfile{0}".format(uuidNum),"r") as fileHandler:
        result = json.loads(fileHandler.read())
    clear(["tmpfile{0}".format(uuidNum),"tmpfile{0}.gz".format(uuidNum)])
    retList = result["data"]["datas"]["bus_list_before"]
    if not isinstance(retList,list):
        return "抱歉，该车次暂无实时信息"
    retStr  = "有{0}辆车将到来：\n".format(len(retList))
   
    for result in retList:
        stationName = result["station_wstation"]
        busMeter    = int(result["bus_meter"])
        busTime     = int(result["bus_time"])
        if busTime<=60:
            busTime = 1
        else:
            busTime = busTime/60
        retStr += "位于【{0}】的车辆还有{1}米,预计{2}分钟内到达\n".format(stationName,busMeter,busTime)

    return retStr

if __name__=="__main__":
    #lineName = raw_input("请输入名称:")
    #getLineId(lineName)
    #sendMsg(2,"6pf7t1zr","Hello")
    RouteId = requestRouteId()
    #requestStations(RouteId)
    requestBusInfo(RouteId)
