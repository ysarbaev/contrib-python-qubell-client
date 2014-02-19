# Copyright (c) 2013 Qubell Inc., http://qubell.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import re
import time

import logging
from requests import sessions, api


__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__email__ = "vkhomenko@qubell.com"


def requests_patch():
    """
    This method provides logging of elapsed time for routes
    """
    logger = logging.getLogger("qubell.routes")

    def nicer(url):
        """
        Converts 'https://express.qubell.com/organizations/52f0f242e4b0defa5da4808e/environments/52f0f242e4b0defa5da4808f.json'
        To '/organizations/__/environments/__.json'
        """
        withoutdomain = url[url.find("/", 8):]  # 8 == len("https://")
        id_pattern = "[A-Fa-f0-9]{24}"
        snips = re.split(id_pattern, withoutdomain)
        return "__".join(snips)


    def request_with_info(method, url, **kwargs):
        session = sessions.Session()
        start = time.time()
        cache = session.request(method=method, url=url, **kwargs)
        end = time.time()
        elapsed = int((end - start) * 1000.0)

        logfun = logger.info
        if 1000 < elapsed <= 10000:
            logfun = logger.warn
        elif elapsed > 10000:
            logfun = logger.error

        logfun(' {0} {1} took {2} ms'.format(method.upper(), nicer(url), elapsed))
        return cache

    api.request = request_with_info


requests_patch()