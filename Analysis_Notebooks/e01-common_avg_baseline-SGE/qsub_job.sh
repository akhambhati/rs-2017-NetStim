#!/bin/zsh

#qsub -t 1-50000 ./e01-Measure_Adjacency.py
qsub -t 50001-100000 ./e01-Measure_Adjacency.py
#qsub -t 100001-154994 ./e01-Measure_Adjacency.py

