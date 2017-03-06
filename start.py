#!/usr/bin/env python
# coding: utf-8
# 工程启动主文件
# Author: dlgao

import os
import sys
import web

urls = (
    '/functiontest', 'app.controllers.nginxmonitor.Monitor',
)

# 切换工作目录
cur_path = os.path.dirname(__file__)
sys.path.append(cur_path)
os.chdir(cur_path)

# 处理中文编码
default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

# 启动应用
app = web.application(urls, globals())
application = app.wsgifunc()
