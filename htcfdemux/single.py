#!/usr/bin/env python

import argparse
import datetime
import os
import threading
from htcfdemux import chunker
from mpi4py import MPI

comm = MPI.COMM_WORLD

TAG_INIT = 0
TAG_CHUNK = 1
TAG_WRITE = 2
TAG_RESPONSE = 3
TAG_DONE = 4

class Handler(threading.Thread):
    def __init__(self, file1, bcfile, outdir):
        threading.Thread.__init__(self)
        self.file1 = file1
        self.bcfile = bcfile
        self.outdir = outdir

    def prep(self):
        if not os.path.isdir(self.outdir):
            os.mkdir(self.outdir)
        self.barcodes = {}
        for name,bc in [l.strip().split() for l in open(self.bcfile)]:
            fname1 = os.path.join(self.outdir, name+'.fastq')
            open(fname1, 'w') # create and ensure empty files
            self.barcodes[bc] = {'name': name, 'pos': 0, 'filename': fname1 }

        self.chunker = chunker.Chunker(self.file1, chunksize=1024*1024*500)
        self.chunklist = [self.chunker.get_chunk(id) for id in range(self.chunker.num_chunks)]

    def run(self):
        while 1:
            send_data = None
            s = MPI.Status()
            data = comm.recv(status=s)
            if s.tag == TAG_DONE:
                break
            elif s.tag == TAG_INIT:
                send_data = {'file1': self.file1, 'barcodes': self.barcodes}
            elif s.tag == TAG_CHUNK:
                if len(self.chunklist) > 0:
                    send_data = self.chunklist.pop(0)
                else:
                    send_data = None
            elif s.tag == TAG_WRITE:
                bc_key = data['bc_key']
                send_data = self.barcodes[bc_key]['pos']
                self.barcodes[bc_key]['pos'] += data['size']
    
            comm.send(send_data, s.source, tag=TAG_RESPONSE)

class Worker(object):
    def __init__(self, comm):
        self.comm = comm
        self.logfile = open('rank%d.log' % comm.rank, 'w')

    def log(self, msg):
        self.logfile.write('%s %s\n' % (datetime.datetime.now(), msg))
        self.logfile.flush()

    def prep(self):
        data = self.comm.sendrecv(None, 0, sendtag=TAG_INIT, recvtag=TAG_RESPONSE)
        self.f1 = open(data['file1'], 'rb')
        self.barcodes = data['barcodes']
        for key,attrs in self.barcodes.items():
            attrs['file'] = open(attrs['filename'], 'r+b')

    def cleanup(self):
        for b, attrs in self.barcodes.items():
            self.write_seq(b, force=True)
            attrs['file'].close()

    def start(self):
        self.prep()
        while 1:
            self.log("getting chunk")
            chunk = self.comm.sendrecv(None, 0, sendtag=TAG_CHUNK, recvtag=TAG_RESPONSE)
            self.log("got chunk %s" % (str(chunk)))
            if chunk is None: break
            self.log("starting chunk %s" % (str(chunk)))
            self.process_chunk(chunk)
            self.log("ending chunk %s" % (str(chunk)))
        self.cleanup()


    def write_seq(self, key, seq=None, force=False):
        bc_attrs = self.barcodes[key]
        if not bc_attrs.get('buffer', None):
            bc_attrs['buffer'] = bytearray()
        buf = bc_attrs['buffer']
        if seq:
            buf.extend(b"%s" % seq)
        length = len(buf)
        if (not force) and length < 1024*1024*10:
            return
        pos =  self.comm.sendrecv({'bc_key': key, 'size': length} , 0, sendtag=TAG_WRITE, recvtag=TAG_RESPONSE)
        bc_attrs['file'].seek(pos)
        bc_attrs['file'].write(buf)
        bc_attrs['buffer'] = None

    def process_chunk(self,chunk):
        offset,length = chunk
        self.f1.seek(offset)
    
        nonmatching_headers_count = 0    
        total_reads = 0
        matching_bcs = 0
        mismatched_bcs = 0
        #left = length
        #while left:
        #    size = self.buffsize
        #    if left - size < 0:
        #        size = left
        #    self.f1.read(size)
        #    self.f2.read(size)
        #    left = left-size
        #return
        pos = 0
    
        for line in self.f1:
            pos += len(line)
            if pos > length:
                break
            # If it's a header line
            if line.startswith(b'@'):
                total_reads += 1
                
                read = self.f1.readline()
                pos += len(read)

                # Get the barcodes from the sequences (assumes 8 bp)
                read_bc = read[0:8].decode('utf-8')
                
                #Skip the '+' line in the fastq
                delim = self.f1.readline()
                pos += len(delim)
                
                # Read the qual lines
                read_qual = self.f1.readline()
                pos += len(read_qual)
                
                
                key = (read_bc)
                # Check that the barcode was in the barcode file.
                if key in self.barcodes:
                #     Increment the counts for that barcode
                #    bc_forthisread = bcseq_hash[read1_bc]
                #    bc_readcounts[bc_forthisread] += 1
                #    
                #    # Print these to the appropriate files (if those files exist).
                #    bc_id = bcseq_hash[read1_bc]
                #    
                #    bc_r1_outpath = outpath + '/' + bc_id + '_r1.fastq'
                #    bc_r2_outpath = outpath + '/' + bc_id + '_r2.fastq'
                #    
                         
                     self.write_seq(key, b"%s%s+\n%s" % (line, read, read_qual))
                #    if os.path.exists(bc_r1_outpath):
                #        tempout = filebuffers[bc_r1_outpath]
                #        tempout.write(r1_line)
                #        tempout.write(read1)
                #        tempout.write('+\n')
                #        tempout.write(read1_qual)
                #    
                #        
                #    if os.path.exists(bc_r2_outpath):
                #        tempout2 = filebuffers[bc_r2_outpath]
                #        tempout2.write(r2_line)
                #        tempout2.write(read2)
                #        tempout2.write('+\n')
                #        tempout2.write(read2_qual)
                
        #percent_matched = (float(matching_bcs)/float(total_reads))*100
        #percent_mismatched = (float(mismatched_bcs)/float(total_reads))*100
        #percent_nonmatchingheaders = (float(nonmatching_headers_count)/float(total_reads))*100
   # 
   #     # Print out the summary statistics
   #     summarypath = outpath + '/split_barcodes_summary.log'
   #     summary = open(summarypath, 'w')
   #     summary.write('Read 1 file:\t' + r1_path + '\n')
   #     summary.write('Read 2 file:\t' + r2_path + '\n')
   #     summary.write('Total Reads:\t' + str(total_reads) + '\n')
   #     summary.write('Reads with matching barcodes:\t' + str(matching_bcs) + '\n')
   #     summary.write('Percent with matching barcodes:\t' + str(percent_matched) + '\n')
   #     summary.write('Reads with mismatched barcodes:\t' + str(mismatched_bcs) + '\n')
   #     summary.write('Percent with mismatched barcodes:\t' + str(percent_mismatched) + '\n')
   #     summary.write('Reads with mismatched headers:\t' + str(nonmatching_headers_count) + '\n')
   #     summary.write('Percent with mismatched headers:\t' + str(percent_nonmatchingheaders) + '\n')
   #     
   #     # Print the summary stats for each barcode
   # 
   #     summary.write('\n\n')
   #     summary.write('Barcode\tCount\tPercent of matching barcodes\n')
   #     for item in bc_readcounts:
   #         count = bc_readcounts[item]
   #         percent_item = ( float(count) / float(matching_bcs) ) * 100
   #         itemline = item + '\t' + str(count) + '\t' + str(percent_item) + '\n'
   #         summary.write(itemline)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('seqfile')
    p.add_argument('bcfile')
    p.add_argument('outdir')
    return p.parse_args()

if __name__ == '__main__':
    
    w = Worker(comm)
    w.log("Started worker")
    if comm.rank == 0:
        args = parse_args()
        handler = Handler(args.seqfile, args.bcfile, args.outdir)
        handler.prep()
        handler.start()

    comm.Barrier()
    w.log("Starting work")
    w.start()
    w.log("Waiting for everyone to be done.")
    comm.Barrier()
    w.log("Done with work")

    if comm.rank == 0:
        comm.send(None, 0, tag=TAG_DONE)
        for t in threading.enumerate():
            if t != threading.current_thread():
                t.join()