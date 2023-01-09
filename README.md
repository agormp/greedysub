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

## Dependencies

There are no dependencies.

## Overview

The main purpose of the `greedysub` program is to select a non-redundant subset of DNA- or protein-sequences, i.e., a subset where the pairwise sequence identity is below a given threshold. However, the program can be used to find representative subsets for any other type of items, for which pairwise similarities (or distances) are known. The subset is found using a [greedy](https://en.wikipedia.org/wiki/Greedy_algorithm) algorithm (hence the name).

Input:
    
* A file containing, on each line, the names of two items (sequences) and their pairwise similarity (sequence identity):
	* `name1 name2 similarity`
* It is also possible to provide the pairwise distance instead:
	* `name1 name2 distance`
* A cutoff for deciding when two items are too similar. Two items are "neighbors" if:
	* similarity > cutoff
* or:
	* distance < cutoff

Output:

* A file containing, on each line, the name of an item (sequence) that should be retained in the non-redundant subset.
* It is guaranteed that no two items in the set are neighbors.
* The program aims to find the maximally sized set of non-adjacent items (but see section Theory for why this is hard and not guaranteed).

Reducing sequence redundancy is useful, e.g., when using cross-validation for estimating the performance of machine learning methods, such as neural networks, in order to avoid spuriously high performance estimates: if similar items (sequences) are present in training and test sets respectively, then the method will appear to be good at generalisation, when it may just have been overtrained on the items (sequences) in the training set. 

The program implements two related greedy heuristics for solving the problem: "max" and "min". On average the "min" algorithm will be best (giving the largest subset). See section "Theory" for details on the algorithms, and for comments on the non-optimality of the heuristics for this problem.

## Theory

### Equivalence to "maximum independent set problem" and other problems

Finding the largest subset of non-neighboring items from a list of pairwise similarities (or distances) is equivalent to the following problems:

* ["Maximum independent set problem"](https://en.wikipedia.org/wiki/Independent_set_(graph_theory)) from graph-theory: find the largest set of nodes on a graph, such that none of the nodes are adjacent.
* ["Maximum clique problem"](https://en.wikipedia.org/wiki/Clique_problem#Finding_maximum_cliques_in_arbitrary_graphs): if a set of nodes constute a maximum independent set, then the same nodes form a maximum [clique](https://en.wikipedia.org/wiki/Clique_(graph_theory)) on the [complement graph](https://en.wikipedia.org/wiki/Complement_graph).
* ["Minimum vertex cover problem"](https://en.wikipedia.org/wiki/Vertex_cover): a minimum vertex cover is the smallest set of nodes that include an endpoint of all edges of the graph. This is the complement of a maximum independent set.

### Computational intractibility of problem

This problem is ![strongly NP-complete](https://en.wikipedia.org/wiki/Strong_NP-completeness) 



## Overview

### Input:

#### Option -s: pairwise similarities

(1) A text file containing pairwise *similarities*, one pair per line. All pairs of names must be listed. The similarity matrix is assumed to be symmetric, and it is only necessary to list one direction for each pair of names.

```
name1 name2 similarity
name1 name3 similarity
...
```

(2) A cutoff value. Pairs of items that are *more similar* than this cutoff are taken to be redundant, and at least one of them will be removed in the final output.

#### Option -d: pairwise distances

(1) A text file containing pairwise *distances*, one pair per line. All pairs of names must be listed. The distance matrix is assumed to be symmetric, and it is only necessary to list one direction for each pair of names.

```
name1 name2 distance
name1 name3 distance
...
```

(2) A cutoff value. Pairs of items that are *less distant* than this cutoff are taken to be redundant, and at least one of them will be removed in the final output.

### Output:

A list of names of items that should be kept in the representative subset, written to stdout. This set contains no pairs of items that are more similar (less distant) than the cutoff. The algorithm aims at making the set the maximal possible size. This can occassionally fail if there are multiple items with the same number of "neighbors" and the order of removal of items has an impact.

### Checking validity of input data

By default the program assumes that input data are valid, i.e., that there are entries for all pairs of names, and that listed values are consistent (A B value == B A value). Using the option `--check`, it is possible to explicitly check this. If an error is found, the program will stop with an error message. If data are OK, the program will finish  and print results.

**Note:** Using this option requires storing all values in memory, and takes longer time to run.

### Performance:

The program has been optimized to run reasonably fast with limited memory usage. For instance: 100 million lines of pairwise distance info (about 2.3 GB) was analyzed in 52 seconds, using about 1 GB of memory, on a 2018 Macbook Pro.

**Note:** Using the option `--check` to verify validity of input data is costly in terms of memory and runtime.

## Usage

```
usage: hobohm [-h] [-s | -d] [-c CUTOFF] [-k KEEPFILE] [--check] PAIRFILE

Selects representative subset of data based on list of pairwise similarities (or
distances), such that no retained items are close neighbors

positional arguments:
  PAIRFILE     file containing the similarity (option -s) or distance (option -d) for each
               pair of items: name1 name2 value

options:
  -h, --help   show this help message and exit
  -s           values in PAIRFILE are similarities (larger values = more similar)
  -d           values in PAIRFILE are distances (smaller values = more similar)
  -c CUTOFF    cutoff for deciding which pairs are neighbors
  -k KEEPFILE  file with names of items that must be kept (one name per line)
  --check      Check validity of input data: Are all pairs listed? Are A B distances the
               same as B A? If yes: finish run and print results. If no: abort run with
               error message
  ```

## Usage examples

### Select items such that max pairwise similarity is 0.65

```
hobohm -s -c 0.65 pairsims.txt > nonredundant.txt
```

### Select items such that minimum pairwise distance is 10

```
hobohm -d -c 10 pairdist.txt > nonredundant.txt
```

### Select items such that max pairwise similarity is 0.3, while keeping items in keeplist.txt

```
hobohm -s -c 0.3 -k keeplist.txt pairsims.txt > nonredundant.txt
```
