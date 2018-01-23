#!/bin/zsh

qsub -t 1-75000 ./ee02-Measure_Adjacency.py
#qsub -t 75000-150000 ./ee02-Measure_Adjacency.py
#qsub -t 150000-155000 ./ee02-Measure_Adjacency.py
