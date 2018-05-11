# coding: utf-8
import os
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter 
from requests import Session, exceptions

import logging
_logger = logging.getLogger(__name__)

def download(url, path, question_id):
    try:
        status_code = None
        url = url.strip()
        spider = Session()
        spider.mount("https://", HTTPAdapter(
                 max_retries = Retry(total = 2, status_forcelist = [500, 502, 503, 504]))
        )
        res = spider.get(url, timeout = 2)
        status_code = res.status_code
        # 如果内容完全正确 
        if status_code == 200:
            # 判断大小是否一致
            if ('Content-Length' in res.headers) and int(res.headers['Content-Length']) != len(res.content):
                _logger.error('Content-Length: %s\t question_id: %s\t Response length: %d\turl: %s', res.headers['Content-Length'], question_id, len(res.content), url)
            else:
                # 如果不存在则建立目录
                _logger.info("question_id:  %s; save to: %s downloaded!", question_id, path)
                # print("question id :   %s" % (question_id))
                dir = os.path.dirname(path)
                if not os.path.exists(dir):
                    os.makedirs(os.path.dirname(path))
                with open(path, 'wb') as img:
                    img.write(res.content)
        # 否则记录状态码和URL
        else:
            _logger.error('question_id: %s\tstatus code: %d\turl: %s', question_id, status_code, url)
    except Exception as e:
        _logger.error(e)
        _logger.error('question_id: %s\t url: %s', question_id, url, exc_info=True)
    
    return status_code
