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
__version__ = "1.0.1"
__email__ = "vkhomenko@qubell.com"

from random import randrange
import time
import os

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
