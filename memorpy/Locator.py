# Author: Nicolas VERDIER
# This file is part of memorpy.
#
# memorpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# memorpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with memorpy.  If not, see <http://www.gnu.org/licenses/>.

import copy
from Address import Address
from functools import reduce
import struct


class Locator(object):
    """ 
       take a memoryworker and a type to search
       then you can feed the locator with values and it will reduce the addresses possibilities
    """

    @staticmethod
    def get_typemap(value):
        # I think this thing can be extended with type sizes check (i.e. any int is between -2^15 and 2^15) 
        if (isinstance(value, int) or round(value) == value) and value < 0:
            return ['int', 'long', 'short', 'float', 'double']
        elif isinstance(value, float):
            return ['float', 'double']
        return ['uint', 'int', 'ulong', 'long', 'ushort', 'short', 'float', 'double']

    def __init__(self, mw, type = 'unknown', start = None, end = None):
        self.mw = mw
        self.type = type
        self.last_iteration = {}
        self.last_value = None
        self.start = start
        self.end = end

    def is_found(self):
        return len(set(reduce(lambda x, y: x + y, self.last_iteration.values()))) == 1

    def get_found(self):
        if self.is_found():
            return self.last_iteration.values()[0][0]
        return None

    def find(self, value, erase_last = True):
        return self.feed(value, erase_last)

    def feed(self, value, erase_last = True):
        self.last_value = value
        new_iter = copy.copy(self.last_iteration)
        all_types = Locator.get_typemap(value) if self.type == 'unknown' else [self.type]
        for type in all_types:
            if type not in new_iter:
                try:
                    new_iter[type] = [ Address(x, self.mw.process, type) for x in self.mw.mem_search(value, type, start_offset=self.start, end_offset=self.end) ]
                except struct.error:
                    new_iter[type] = []
            else:
                l = []
                for address in new_iter[type]:
                    try:
                        found = self.mw.process.read(address, type)
                        if int(found) == int(value):
                            l.append(Address(address, self.mw.process, type))
                    except Exception as e:
                        pass

                new_iter[type] = l

        if erase_last:
            del self.last_iteration
            self.last_iteration = new_iter
        return new_iter

    def get_addresses(self):
        return self.last_iteration

    def diff(self, erase_last = False):
        return self.get_modified_addr(erase_last)

    def get_modified_addr(self, erase_last = False):
        last = self.last_iteration
        new = self.feed(self.last_value, erase_last=erase_last)
        ret = {}
        for type, l in last.iteritems():
            typeset = set(new[type])
            for addr in l:
                if addr not in typeset:
                    if type not in ret:
                        ret[type] = []
                    ret[type].append(addr)

        return ret
