
import os, os.path, sys, traceback, threading

class tsdict:
    def __init__(self,lock=threading.RLock):
        self._lock = lock()
        self._dict = dict()
    def acquire(self):
        self._lock.acquire()
    def release(self):
        self._lock.release()
    def dump(self,handle=sys.stderr):
        self.acquire()
        try:
            for k,v in sorted(self._dict.items()):
                print >>handle, k,"=",v
        finally:
            self.release()
    def get(self,key,default=None):
        self.acquire()
        try:
            return self._dict.get(key,default)
        finally:
            self.release()
    def set(self,key,value):
        self.acquire()
        try:
            self._dict[key] = value
        finally:
            self.release()
    def setif(self,key,value,value0=None):
        self.acquire()
        try:
            if self._dict.get(key,None) != value0:
                return False
            self._dict[key] = value
            return True
        finally:
            self.release()
    def inc(self,key):
        self.acquire()
        try:
            if not key in self._dict:
                self._dict[key] = 1
            else:
                self._dict[key] += 1
            return self._dict[key]
        finally:
            self.release()
    def dec(self,key):
        self.acquire()
        try:
            self._dict[key] -= 1
            return self._dict[key]
        finally:
            self.release()
    def copy(self):
        self.acquire()
        try:
            return copy.copy(self._dict)
        finally:
            self.release()
