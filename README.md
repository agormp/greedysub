# greedysub: command line program for selecting representative, non-redundant subset of DNA or protein-sequences, based on list of pairwise sequence identities

[![PyPI downloads](https://static.pepy.tech/personalized-badge/greedureduce?period=total&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/greedureduce)
![](https://img.shields.io/badge/version-1.0.0-blue)

![](https://github.com/agormp/greedysub/raw/main/maxindset.png?raw=true)


## Availability

The `greedysub` source code is available on GitHub: https://github.com/agormp/greedysub. The executable can be installed from PyPI: https://pypi.org/project/greedysub/

## Installation

```
python3 -m pip install greedysub
```

Upgrading to latest version:

```
python3 -m pip install --upgrade greedysub
```

## Usage

```
usage: greedysub [-h] [--algo ALGORITHM] [--val VALUETYPE] [-c CUTOFF] [-k KEEPFILE]
                    INFILE OUTFILE

Selects subset of items, based on list of pairwise similarities (or distances), such that
no retained items are close neighbors

positional arguments:
  INFILE            input file containing similarity or distance for each pair of items:
                    name1 name2 value
  OUTFILE           output file contatining neighborless subset of items (one name per
                    line)

options:
  -h, --help        show this help message and exit
  --algo ALGORITHM  algorithm: min, max [default: min]
  --val VALUETYPE   specify whether values in INFILE are distances (--val dist) or
                    similarities (--val sim)
  -c CUTOFF         cutoff value for deciding which pairs are neighbors
  -k KEEPFILE       (optional) file with names of items that must be kept (one name per
                    line)
```

### Input file

The program requires an INFILE, which should be a textfile where each line contains the names of two sequences (items) and their pairwise similarity (option `--val sim`) or distance (option `--val dist`):

```
yfg1  yfg2  0.98
yfg1  klp2  0.67
yfg1  mcf9  0.87
...
```

### Output file

The results are written to the OUTFILE, which will contain a list of names (one name per line) of sequences that should be retained: 

```
yfg1
klp2
...
```

### Keep file

The user can specify a list of names for items that must be retained in the subset under all circumstances (also even some of them are neighbors). This KEEPFILE should be a text file listing one name to be retained per line

```
abc1
def3
...
```

### Usage examples

#### Select items such that max pairwise similarity is 0.75, using "greedy-min" algorithm

```
greedysub --algo min --val sim -c 0.75 simfile.txt resultfile.txt
```

#### Select items such that minimum pairwise distance is 10, using "greedy-min" algorithm

```
greedysub --algo min --val dist -c 10 distfile.txt resultfile.txt
```

#### Select items with max pairwise similarity 3, while keeping items in keeplist.txt

```
greedysub --algo max --val sim -c 3 -k keeplist.txt simfile.txt resultfile.txt
```

### Summary info written to stdout

Basic information about the original and reduced data sets will be printed to stdout. 

#### Example output

```

	Names in reduced set written to tests/outfile.txt

	Number in original set:      1,500
	Number in reduced set:       1,252

	Node degree original set:
	    min:       1
	    max:     170
	    ave:      11.67

	Node distances original set:
	    ave:     370.01
	    cutoff:   10.00

```

The `node degree` of an item is the number of neighbors it has (i.e., the number of other items that are closer to the item than the cutoff value).

## Overview

The main purpose of the `greedysub` program is to select a non-redundant subset of DNA- or protein-sequences, i.e., a subset where the pairwise sequence identity is below a given threshold. However, the program can be used to find representative subsets for any other type of items, for which pairwise similarities (or distances) are known. The subset is found using a [greedy](https://en.wikipedia.org/wiki/Greedy_algorithm) algorithm (hence the name).

**Input:**
    
* A file containing, on each line, the names of two items (sequences) and their pairwise similarity (sequence identity):
	* `name1 name2 similarity`
	* There must be a line for each possible pair of items
	* It is also possible to provide the pairwise distance instead of similarity
* A cutoff for deciding when two items are too similar. 
	* Two items are "neighbors" if:
		* similarity > cutoff
	* or:
		* distance < cutoff

**Output:**

* A file containing, on each line, the name of an item (sequence) that should be retained in the non-redundant subset.
* It is guaranteed that no two items in the set are neighbors.
* The program aims to find the maximally sized set of non-adjacent items (but see section Theory for why this is hard and not guaranteed).

Reducing sequence redundancy is useful, e.g., when using cross-validation for estimating the performance of machine learning methods, such as neural networks, in order to avoid spuriously high performance estimates: if similar items (sequences) are present in both training and test sets, then the method will appear to be good at generalisation, when it may just have been overtrained on the items (sequences) in the training set. 

The program implements two related greedy heuristics for solving the problem: "greedy-max" and "greedy-min". On average the "min" algorithm will be best (giving the largest subset). See section "Theory" for details on the algorithms, and for comments on the non-optimality of the heuristics for this problem.


## Theory

### Equivalence to "maximum independent set problem" and other problems

Finding the largest subset of non-neighboring items from a list of pairwise similarities (or distances) is equivalent to the following problems:

* ["Maximum independent set problem"](https://en.wikipedia.org/wiki/Independent_set_(graph_theory)) from graph-theory: find the largest set of nodes on a graph, such that none of the nodes are adjacent.
* ["Maximum clique problem"](https://en.wikipedia.org/wiki/Clique_problem#Finding_maximum_cliques_in_arbitrary_graphs): if a set of nodes constitute a maximum independent set, then the same nodes form a maximum [clique](https://en.wikipedia.org/wiki/Clique_(graph_theory)) on the [complement graph](https://en.wikipedia.org/wiki/Complement_graph).
* ["Minimum vertex cover problem"](https://en.wikipedia.org/wiki/Vertex_cover): a minimum vertex cover is the smallest set of nodes that include an endpoint of all edges of the graph. This is the complement of a maximum independent set.

### Computational intractibility of problem

This problem is [strongly NP-hard](https://en.wikipedia.org/wiki/Strong_NP-completeness) and
[hard to approximate](https://projecteuclid.org/journals/acta-mathematica/volume-182/issue-1/Clique-is-hard-to-approximate-within-n1ε/10.1007/BF02392825.full).  



### Checking validity of input data

By default the program assumes that input data are valid, i.e., that there are entries for all pairs of names, and that listed values are consistent (A B value == B A value). Using the option `--check`, it is possible to explicitly check this. If an error is found, the program will stop with an error message. If data are OK, the program will finish  and print results.

**Note:** Using this option requires storing all values in memory, and takes longer time to run.

### Performance:

The program has been optimized to run reasonably fast with limited memory usage. For instance: 100 million lines of pairwise distance info (about 2.3 GB) was analyzed in 52 seconds, using about 1 GB of memory, on a 2018 Macbook Pro.

**Note:** Using the option `--check` to verify validity of input data is costly in terms of memory and runtime.
