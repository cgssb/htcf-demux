[![Build Status](https://travis-ci.org/cgssb/htcf-demux.svg?branch=master)](https://travis-ci.org/cgssb/htcf-demux)

# htcf-demux
MPI Demultiplexer 

## Usage

Create an sbatch like so:

```bash
#!/bin/bash

# This will request a minimum of 10 and max of 40 processors
#SBATCH -n 40

# This may speed up the job but increase your wait time.
#SBATCH --tasks-per-node=1  
 
module load mpich
module load htcf-demux
  
mpiexec htcf-demux -o output_dir -b barcodes.txt myseq.fastq
```

