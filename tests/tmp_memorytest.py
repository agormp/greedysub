import dask.dataframe as dd

ddf = dd.read_csv("pairdist_100mio.txt",
                  delimiter=" ",
                  names=["name1", "name2", "val"],
                  dtype={"name1":str, "name2":str, "val":float})

valuesum = ddf["val"].values.sum()
valuesum = valuesum.compute(num_workers=3)
