# htcf-demux
MPI Demultiplexer 

## Usage

Create an sbatch like so:

```bash
#!/bin/bash

#SBATCH --mem=1000M
#SBATCH -n 40
#SBATCH --tasks-per-node=1
 
module load mpich
module load htcf-demux
  
mpiexec single.py my.fastq barcodes.txt output_dir
```

