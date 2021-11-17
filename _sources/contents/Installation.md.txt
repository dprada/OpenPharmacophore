# Installation

OpenPharmacophore requires ChemBl webresource client to be installed:

```bash
pip install chembl_webresource_client==0.10.7
```

The latest "stable" version of OpenPharmacophore can be installed from the UIBCDF Anaconda channel:

```bash
conda -c uibcdf openpharmacophore
```

If you want to work with the not so tested last beta version, the installation command is the following:

```bash
conda install -c uibcdf/label/dev openpharmacophore
```

The former beta version is nothing but a quenched version from the main github repository of this project which it is done from time to time with few scruples. The raw code fully alive can be installed from this github repo as follows:

```bash
git clone https://github.com/uibcdf/openpharmacophore.git
cd OpenPharmacophore
python setup.py develop
```

In the first two cases, OpenPharmacophore can be uninstalled with conda:

```bash
conda remove openpharmacophore
```

But if you installed it straight from its github central repository, do the following to uninstall it:

```bash
pip uninstall openpharmacophore
```

