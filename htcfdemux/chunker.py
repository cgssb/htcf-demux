#!/usr/bin/env python3

import argparse
import logging
import math
import os
import re
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
    Chunker:  Provide (offset, length) of file chunks of roughly <chunksize> split on <search> boundaries.

    >>> record = r'^@.*\n.*\n\+\n.*$'
    >>> c = Chunker(myfile, chunksize=1024*1024*200, search=record)
    >>> print(c.num_chunks)
    >>> 
    >>> for i in range(c.num_chunks):
    >>>     c.get_chunk(i)
    >>> 
    >>> for (offset, length) in c.chunks():
    >>>     # do something
    >>> 
    """

    BUFSIZE = 1024*1024
    CHUNKSIZE = 1024*1024*200

    def __init__(self, fname, chunksize=None, searchlen=1024*100, search='>', debug=False):
        if chunksize is None:
            self._csize = self.CHUNKSIZE
        else:
            self._csize = chunksize
        self.fsize = os.stat(fname).st_size
        self._searchlen = searchlen # maxsize 
        self._search = search
        self._debug = debug
        assert(self._csize > self._searchlen)
        self._f = open(os.path.realpath(fname), 'r')

    @property
    def num_chunks(self):
        if not getattr(self, '_num_chunks', None):
            i = int(math.ceil(self.fsize / self._csize) - 1)  # i might be the last index
            if self._get_start(i) is None:              # nope, it's just a small piece of the previous chunk
                i -= 1
            # Sanity Check
            for x in range(i):
                try:
                    self._get_start(x)
                except:
                    raise Exception("Could not find 'start' in chunk %d (offset %d)" % (x,i))

            self._num_chunks = i + 1 

        return self._num_chunks

    def chunks(self):
        for i in range(self.num_chunks):
            yield self.get_chunk(i)

    def get_chunk(self, index):
        start = self._get_start(index)
        if start is None: return None
        stop = self._get_start(index+1) or self.fsize
        return (start, stop-start)

    def _get_start(self, index):
        """find the start boundary for chunk"""
        start = index * self._csize
        if start >= self.fsize: return None  # This is off the end of the file.
        self._f.seek(start)
        s = self._f.read(self._searchlen)
        match = re.search(self._search, s, re.MULTILINE)
        if match:
            i = match.span()[0]
        else:
        #i = s.find(self._search)
        #if i == -1: 
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

class FastqChunker(Chunker):
    def __init__(self, *args, **kwargs):
        super(FastqChunker, self).__init__(*args, **kwargs)
        self._search = r'^@.*\n.*\n\+\n.*$'

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('fastq')
    p.add_argument('-r', '--read_chunk', type=int)
    p.add_argument('-c', '--chunk_size', default=None, type=int)
    #p.add_argument('-s', '--search_len', default=None, type=int)
    p.add_argument('-d', '--debug', action="store_true")
    args = p.parse_args()
    c = FastqChunker(args.fastq, args.chunk_size, debug=args.debug)
    if args.read_chunk:
        c.read_chunk(args.read_chunk-1)
    else:
        for x in c.chunks():
            print(x)

if __name__ == '__main__':
    parse_args()
