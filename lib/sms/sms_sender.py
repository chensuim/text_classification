# coding: utf-8
import json
import top.api
import logging

class SmsSender(object):
    def __init__(self, appkey=None, secret=None):
        self._logger = logging.getLogger(__name__)
        self._appkey = appkey or '23454907'
        self._secret = secret or 'e5a615af3df3d20e5f78c75065d515c3'
        self._url = 'gw.api.taobao.com'
        self._sms_free_sign_name = '神算子教育'

    def send_alarm(self, phone, name, message):
        """发送告警信息"""
        req = top.api.AlibabaAliqinFcSmsNumSendRequest(self._url)
        req.set_app_info(top.appinfo(self._appkey, self._secret))
    
        req.extend = ''
        req.sms_type = 'normal'
        req.sms_free_sign_name = self._sms_free_sign_name
        req.sms_param = json.dumps({'name': name, 'message': message})
        req.rec_num = phone
        req.sms_template_code = "SMS_42185030"
        resp = None
        try:
            resp = req.getResponse()
            self._logger.info(resp)
            result = resp
        except Exception as e:
            self._logger.error('Sms error: ', exc_info=True)
        return resp
    
