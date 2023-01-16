import pytest
import itertools
import random

############################################################################################

def pairfile_string_dist(nodes, pairs, cutoff):
    """Input: list of nodes, list of pair tuples, and cutoff value.
       Output: string that can be written in PAIRFILE, giving each pairwise dist"""
    stringlist = []
    for n1, n2 in itertools.combinations(nodes,2):
        if ((n1,n2) in pairs) or ((n2,n1) in pairs):
            stringlist.append("{} {} {}\n".format(n1,n2,cutoff/2))
        else:
            stringlist.append("{} {} {}\n".format(n1,n2,cutoff*2))
    return "".join(stringlist)

############################################################################################

def pairfile_string_sim(nodes, pairs, cutoff):
    """Input: list of nodes, list of pair tuples, and cutoff value.
       Output: string that can be written in PAIRFILE, giving each pairwise similarity"""
    stringlist = []
    for n1, n2 in itertools.combinations(nodes,2):
        if ((n1,n2) in pairs) or ((n2,n1) in pairs):
            stringlist.append("{} {} {}\n".format(n1,n2,cutoff*2))
        else:
            stringlist.append("{} {} {}\n".format(n1,n2,cutoff/2))
    return "".join(stringlist)

############################################################################################

def pairfile_string_euclideangrid(n, d):
    """Creates quadratic grid of nodes, and then returns all pairwise euclidean
    distances as string (can be put in pairfile).
    Note n^4/2 pairwise distances!!!
    n=number of nodes on each side of quadratic grid.
    d=distance between equally spaced nodes"""

    # Not using and not sure this is useful, but kept it just in case...

    coords = list(itertools.product(range(0, n*d, d), range(0, n*d, d)))
    nodes = [f"n{i}" for i in range(n**2)]
    stringlist = []
    for i1, i2 in itertools.combinations(range(n**2),2):
        n1 = nodes[i1]
        n2 = nodes[i2]
        x1,y1 = coords[i1]
        x2,y2 = coords[i2]
        dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        stringlist.append("{} {} {}\n".format(n1,n2,dist))
    return "".join(stringlist)

############################################################################################

@pytest.fixture()
def grid_pairfile_100nodes_dist1(tmp_path):
    distfile = tmp_path / "distfile.txt"
    n = 10
    d = 1
    distfile.write_text(pairfile_string_euclideangrid(n, d))
    nodes = [f"n{i}" for i in range(n**2)]
    return distfile, nodes

############################################################################################

@pytest.fixture()
def random_pairfile_50nodes(tmp_path):
    nodes = {f"n{i}" for i in range(50)}
    pairs = set()
    n_unpaired = 0
    for n1,n2 in itertools.combinations(nodes,2):
        if random.random() > 0.97:
            pairs.add((n1,n2))
        else:
            n_unpaired += 1
    if n_unpaired == 0:
        raise Exception("No unpaired nodes: tests are not covering all aspects")
    if n_unpaired == 50:
        raise Exception("All nodes are unpaired: tests are not covering all aspects")
    cutoff = random.random() * 100
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string_dist(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

@pytest.fixture()
def random_pairfile_50nodes_sim(tmp_path):
    nodes = {f"n{i}" for i in range(50)}
    pairs = set()
    n_unpaired = 0
    for n1,n2 in itertools.combinations(nodes,2):
        if random.random() > 0.97:
            pairs.add((n1,n2))
        else:
            n_unpaired += 1
    if n_unpaired == 0:
        raise Exception("No unpaired nodes: tests are not covering all aspects")
    if n_unpaired == 50:
        raise Exception("All nodes are unpaired: tests are not covering all aspects")
    cutoff = random.random() * 100
    simfile = tmp_path / "simfile.txt"
    simfile.write_text(pairfile_string_sim(nodes, pairs, cutoff))
    return simfile, nodes, pairs, cutoff

############################################################################################

@pytest.fixture()
def random_pairfile_no_neighbors_50nodes(tmp_path):
    nodes = {f"n{i}" for i in range(50)}
    pairs = set()
    cutoff = random.random() * 100
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string_dist(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

# Graph guaranteed to fail for reduce_from_top
@pytest.fixture()
def graph_example_01(tmp_path):
    nodes = {"n1", "n2", "n3", "n4", "n5", "n6", "n7"}
    pairs = {("n1", "n2"), ("n1", "n3"), ("n1", "n4"),
             ("n2", "n5"),
             ("n3", "n6"),
             ("n4", "n7")}
    cutoff = 5
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string_dist(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

# Graph guaranteed to fail for reduce_from_bottom
@pytest.fixture()
def graph_example_02(tmp_path):
    nodes = {"n1", "n2", "n3", "n4", "n5", "n6", "n7"}
    pairs = {("n1", "n2"), ("n1", "n3"), ("n1", "n4"),
             ("n2", "n5"), ("n2", "n6"), ("n2", "n7"),
             ("n3", "n5"), ("n3", "n6"), ("n3", "n7"),
             ("n4", "n5"), ("n4", "n6"), ("n4", "n7"),
             ("n5", "n6"), ("n5", "n7"),
             ("n6", "n7")}
    cutoff = 5
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string_dist(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

# Graph guaranteed to fail for reduce_from_bottom
@pytest.fixture()
def graph_example_03(tmp_path):
    nodes = {"n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "n10"}
    pairs = {("n1", "n2"), ("n1", "n3"), ("n1", "n4"), ("n1", "n5"), ("n1", "n6"), ("n1", "n10"),
             ("n2", "n3"), ("n2", "n6"),
             ("n3", "n6"),
             ("n4", "n8"), ("n4", "n9"),
             ("n5", "n7"), ("n5", "n8"),
             ("n5", "n7"), ("n5", "n8"),
             ("n7", "n8")}
    cutoff = 5
    distfile = tmp_path / "distfile.txt"
    distfile.write_text(pairfile_string_dist(nodes, pairs, cutoff))
    return distfile, nodes, pairs, cutoff

############################################################################################

@pytest.fixture()
def keepfile_n0_to_n9(tmp_path):
    keepfile = tmp_path / "keepfile.txt"
    keepset = {f"n{i}" for i in range(10)}
    with open(keepfile, "w") as outfile:
        for nodename in keepset:
            outfile.write(nodename + "\n")
    return keepfile, keepset

############################################################################################

@pytest.fixture()
def keepfile_n3_and_n5(tmp_path):
    keepfile = tmp_path / "keepfile.txt"
    keepset = {"n3", "n5"}
    with open(keepfile, "w") as outfile:
        for nodename in keepset:
            outfile.write(nodename + "\n")
    return keepfile, keepset


