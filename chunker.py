#!/usr/bin/env python3

import argparse
import math
import os
import sys

#class Chunk(object):
#    def __init__(self, fname, offset, length):
#        self.file = open(fname, 'rb')
#        self.seek(offset)
#        self.length = length
#
#    def tell(self):
#        actual_pos = self.file.tell()
#        if actual_pos > offset + length:
#            return length
#        elif actual_pos < offset:
#            return 0
#        else:
#            return actual_pos - offset
#
#    def read(self, size=None):
#        pos = self.tell()
#        if size is None or size > length - pos:
#            size = self.length - pos
#        elif size  
#        return 

class Chunker(object):
    """
    """
    BUFSIZE = 1024*1024

    def __init__(self, fname, chunksize=1024*1024*200, searchlen=512, search='@', debug=False):
        self.fsize = os.stat(fname).st_size
        self._csize = chunksize
        self._searchlen = searchlen
        self._search = search
        self._debug = debug
        assert(self._csize > self._searchlen)
        self._f = open(os.path.realpath(fname), 'r')

    @property
    def num_chunks(self):
        i = math.ceil(self.fsize / self._csize) - 1  # i might be the last index
        if self._get_start(i) is None:              # nope, it's just a small piece of the previous chunk
            i -= 1
        return i + 1

    def get_chunk(self, index):
        start = self._get_start(index)
        if start is None: return None
        stop = self._get_start(index+1) or self.fsize
        return (start, stop-start)

    def _get_start(self, index):
        start = index * self._csize
        if start >= self.fsize: return None  # This is off the end of the file.
        self._f.seek(start)
        s = self._f.read(self._searchlen)
        i = s.find(self._search)
        if i == -1: 
            if start+len(s) == self.fsize:  # No start, our search has gotten us to the end of the file.
                return None
            else:
                raise Exception("Search string not found. Is your search length too short?")
        return start + i

    def read_chunk(self, index):
        chunk = self.get_chunk(index)
        if chunk is None: return None
        if self._debug:
            sys.stderr.write("offset: %d\n" % chunk[0])
            sys.stderr.write("length: %d\n" % chunk[1])
        self._f.seek(chunk[0])
        left = chunk[1]
        while 1:
            if left > self.BUFSIZE:
                buf = self._f.read(self.BUFSIZE)
            else:
                buf = self._f.read(left)
            left -= len(buf)
            sys.stdout.write(buf)
            sys.stdout.flush()
            if left == 0:
                break

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('fastq')
    p.add_argument('-r', '--read_chunk', type=int)
    p.add_argument('-c', '--chunk_size', default=1000000000, type=int)
    p.add_argument('-d', '--debug', action="store_true")
    args = p.parse_args()
    c = Chunker(args.fastq, args.chunk_size, debug=args.debug)
    if args.read_chunk:
        c.read_chunk(args.read_chunk-1)
    else:
        print(c.num_chunks)

if __name__ == '__main__':
    parse_args()
