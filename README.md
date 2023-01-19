# greedysub

![](https://img.shields.io/badge/version-1.2.4-blue)
[![PyPI downloads](https://static.pepy.tech/personalized-badge/greedysub?period=total&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/greedysub)

The `greedysub` command-line program selects a subset of input data such that no retained items are closely related ("neighbors"). 

![](https://github.com/agormp/greedysub/raw/main/maxindset.png?raw=true)

## Overview

One use case for `greedysub` is to select a non-redundant subset of DNA- or protein-sequences, i.e., a subset where all pairwise sequence identities are below a given threshold. However, the program can be used to find representative subsets for any other type of items also, or, more generally, to find a ["maximal independent set"](#theory) on a graph. 

The program requires a list of pairwise similarities (or distances) as input, along with a cutoff specifying when two items are considered to be neighbors.

Reducing sequence redundancy is helpful, e.g., when using cross-validation for estimating the predictive performance of machine learning methods, such as neural networks, in order to avoid spuriously high performance estimates: if similar items (sequences) are present in both training and test sets, then the method will appear to be good at generalisation, when it may just have been overtrained to recognize items (sequences) similar to those in the training set. 

The program implements two different [greedy](https://en.wikipedia.org/wiki/Greedy_algorithm) heuristics for solving the problem: "greedy-max" and "greedy-min". On average the "min" algorithm will be best (giving the largest subset). See section "Theory" for details on the algorithms, and for comments on the non-optimality of the heuristics for this problem.


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

## Primary Dependencies

* [pandas](https://pandas.pydata.org) (automatically installed when using pip to install greedysub)

## Usage

```
usage: greedysub    [-h] [--algo ALGORITHM] [--val VALUETYPE] [-c CUTOFF] [-k KEEPFILE]
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

**Note:** The input file must contain one line for *each possible pair of items*.

### Output file

The results are written to the OUTFILE, which will contain a list of names (one name per line) of sequences (items) that should be retained: 

```
yfg1
klp2
...
```

**Note:** It is guaranteed that no two items in the resulting subset are neighbors.
The program aims to find the maximally sized set of non-adjacent items (but see section Theory for why this is hard and not guaranteed).


### Keepfile

Using the option `-k <PATH TO KEEPFILE>` the user can specify a list of names for items that must be retained in the subset no matter what (even if some of them are neighbors). This KEEPFILE should be a text file listing one name to be retained per line

```
abc1
def3
...
```

### Usage examples

#### Select items such that pairwise *similarity* is less than 0.75, using "greedy-min" algorithm

```
greedysub --algo min --val sim -c 0.75 simfile.txt resultfile.txt
```

#### Select items such that pairwise *distance* is at least 10, using "greedy-min" algorithm

```
greedysub --algo min --val dist -c 10 distfile.txt resultfile.txt
```

#### Select items with pairwise *distance* at least 3, while keeping items in keeplist.txt, using "greedy-max"

```
greedysub --algo max --val dist -c 3 -k keeplist.txt simfile.txt resultfile.txt
```

### Summary info written to stdout

Basic information about the original and reduced data sets will be printed to stdout. 

#### Example output

```

	Names in reduced set written to tests/outfile.txt

	Number in original set:      1,414
	Number in reduced set:         509

	Node degree original set:
	    min:       1
	    max:       9
	    ave:       3.03

	Node distances original set:
	    ave:       5.12
	    cutoff:    0.95

```

Here, the `node degree` of an item is the number of neighbors it has (i.e., the number of other items that are closer to the item than the cutoff value).


## Theory

### Equivalence to "maximum independent set problem" and other problems

Finding the largest subset of non-neighboring sequences (items) from a list of pairwise similarities (or distances) is equivalent to the following problems:

* ["Maximum independent set problem"](https://en.wikipedia.org/wiki/Independent_set_(graph_theory)) from graph-theory: find the largest set of nodes on a graph, such that none of the nodes are adjacent.
* ["Maximum clique problem"](https://en.wikipedia.org/wiki/Clique_problem#Finding_maximum_cliques_in_arbitrary_graphs): if a set of nodes constitute a maximum independent set, then the same nodes form a maximum [clique](https://en.wikipedia.org/wiki/Clique_(graph_theory)) on the [complement graph](https://en.wikipedia.org/wiki/Complement_graph).
* ["Minimum vertex cover problem"](https://en.wikipedia.org/wiki/Vertex_cover): a vertex cover is a set of nodes that includes at least one endpoint of all edges of the graph. A minimum vertex cover is the smallest possible such set. A minimum vertex cover is the complement of a maximum independent set.

### Computational intractibility of problem

This problem is [strongly NP-hard](https://en.wikipedia.org/wiki/Strong_NP-completeness) and it is also
[hard to approximate](https://projecteuclid.org/journals/acta-mathematica/volume-182/issue-1/Clique-is-hard-to-approximate-within-n1ε/10.1007/BF02392825.full). There are therefore no efficient, exact algorithms, although [there are exact algorithms with much better time complexity than the worst-case complexity of a naive, exhaustive search](https://arxiv.org/abs/1312.6260). 

### Implemented algorithms

**Note:** of the two implemented, greedy algorithms, `greedy-min` has the best guaranteed performance. However, performance can be much better than the minimum guaranteed one, and occasionally `greedy-max` may find a larger set (this depends on the specific graph).

#### Greedy-min algorithm

Given a graph G, and an empty set S:

* While there are still edges in G:
	* Select a node $\nu$ of *minimum* degree in G
	* Add $\nu$ to S
	* Remove $\nu$ and its neighbors from G
* Output the set of nodes in S

**Performance ratio:** On a graph with maximum node degree $\Delta$, it [has been shown ](https://link.springer.com/article/10.1007/BF02523693) that the greedy-min algorithm yields solutions that are within a factor $3 / (\Delta + 2)$ of the optimal solution. For instance, for $\Delta=4$ the algorithm is guaranteed to be no worse than $3 / (4 + 2) = 0.5$ times the optimal solution (i.e., the found solution will be at least half the size of the optimal one).

#### Greedy-max algorithm

Given a graph G:

* While there are still edges in G:
	* Select a node $\nu$ of *maximum* degree in G
	* Remove $\nu$
* Output set of nodes left in G

**Performance ratio:** On a graph with maximum node degree $\Delta$, it [has been shown ](https://www.sciencedirect.com/science/article/pii/S0166218X02002056?via%3Dihub) that the greedy-max algorithm yields solutions that are within a factor $1 / (\Delta + 1)$ of the optimal solution. For instance, for $\Delta=4$ the algorithm is guaranteed to be no worse than $1 / (4 + 1) = 0.2$ times the optimal solution (i.e., the found solution will be at least 20% the size of the optimal one).

**Note:** the greedy-max algorithm is the same as algorithm 2 from the following paper, and has also been implemented in the [`hobohm` program](https://github.com/agormp/hobohm) (but the algorithm has been described in the context of graph theory prior to this work): Hobohm et al.: ["Selection of representative protein data sets", Protein Sci. 1992. 1(3):409-17](https://pubmed.ncbi.nlm.nih.gov/1304348/).

### Computational performance:

The program has been optimized to run reasonably fast with limited memory usage, and to be able to handle large input files (also larger than available RAM). A known (current) limitation is that the neighbor graph (the dictionary keeping track of which nodes connect to which other nodes) has to be small enough to fit in memory.

The table below shows examples of run times (wall-clock time) on a 2021 M1 Macbook Pro (64 GB memory), for different sizes of input files.


Cutoffs were chosen such that inputs were reduced to approximately 500 names regardless of starting size (except for the smallest file where the cutoff was chosen such that the input was reduced to a third of its initial size).

| Size of input file  | Size of input file: lines | No. names, original | No. names, reduced | Peak memory     |Wall-clock time |
|      :-----:        |       :-----:             |        -----:       |     -------:       |   -------:      |  -------:      |
|      1.6 MB         |       100 K (1E5)         |         447         |       151          |    43 MB        |   0.36 s       |
|      18 MB          |       1 mill (1E6)        |        1,414        |       509          |    88 MB        |   0.52 s       |
|      91 MB          |       5 mill (5E6)        |        3,162        |       500          |    97 MB        |   1.23 s       |
|      181 MB         |       10 mill (1E7)       |        4,472        |       501          |    102 MB       |   2.23 s       |
|      2.0 GB         |       100 mill (1E8)      |        14,142       |       505          |    310 MB       |   21.3 s       |
|      20 GB          |       1 bill (1E9)        |        44,721       |       501          |    6.7 GB       |   4:12 m:s     |      
          

<!---

Cutoffs were chosen such that inputs were reduced to approximately 500 names regardless of starting size (except for the smallest file where the cutoff was chosen such that the input was reduced to a third of its initial size).

| Size of input file  | Size of input file: lines | No. names, original | No. names, reduced | Time         |
|      :-----:        |       :-----:             |        -----:       |     -------:       |   -------:   |
|      1.6 MB         |       100 K (1E5)         |         447         |   c 1      151     |    0.36 s    |
|      18 MB          |       1 mill (1E6)        |        1,414        |   c 0.95   509     |    0.52 s    |
|      91 MB          |       5 mill (5E6)        |        3,162        |   c 1.75   500     |    1.23 s    |
|      181 MB         |       10 mill (1E7)       |        4472         |   c 2.16   501     |    2.23 s    |
|      2.0 GB         |       100 mill (1E8)      |        14142        |   c 3.65   505     |    21.3 s    |
|      20 GB          |       1 bill (1E9)        |        44721        |   c 5.38   501     |                 |               |
          
-->
