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

__author__ = "Vasyl Khomenko"
__copyright__ = "Copyright 2013, Qubell.com"
__license__ = "Apache"
__version__ = "1.0.8"
__email__ = "vkhomenko@qubell.com"

from random import randrange
import time
import os
import logging as log

def rand():
    return str(randrange(1000, 9999))

def cpath(file):
    return os.path.join(os.path.dirname(__file__), file)

def retry(tries=5, delay=3, backoff=2):
    """
    Retry "tries" times, with initial "delay", increasing delay "delay*backoff" each time
    """

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            rv = f(*args, **kwargs)
            while mtries > 0:
                if rv is True:
                    return True
                mtries -= 1
                time.sleep(mdelay)
                mdelay *= backoff
                rv = f(*args, **kwargs)
            return False
        return f_retry
    return deco_retry

def waitForStatus(instance, final='Running', accepted=['Requested'], timeout=[20, 10, 1]):
    log.debug('Waiting status: %s' % final)
    import time #TODO: We have to wait, because privious status takes time to change to new one
    time.sleep(10)
    @retry(*timeout) # ask status 20 times every 10 sec.
    def waiter():
        cur_status = instance.status
        if cur_status in final:
            log.info('Got status: %s, continue' % cur_status)
            return True
        elif cur_status in accepted:
            log.info('Current status: %s, waiting...' % cur_status)
            return False
        else:
            log.error('Got unexpected instance status: %s' % cur_status)
            return True # Let retry exit

    waiter()
    # We here, means we reached timeout or got status we are waiting for.
    # Check it again to be sure

    cur_status = instance.status
    log.info('Final status: %s' % cur_status)
    if cur_status in final:
        return True
    else:
        return False