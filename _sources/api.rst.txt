API Documentation
=================

Pharmacophoric Point
-----------------------

.. autosummary::
   :toctree: _autosummary
   :template: custom-class-template.rst
   :recursive:

   openpharmacophore.PharmacophoricPoint

Features colorpalettes
**********************

.. autosummary::
   :toctree: _autosummary

   openpharmacophore.color_palettes.get_color_from_palette_for_feature


Pharmacophores
--------------

.. autosummary::
   :toctree: _autosummary
   :template: custom-class-template.rst
   :recursive:

   openpharmacophore.Pharmacophore
   openpharmacophore.LigandBasedPharmacophore
   openpharmacophore.StructuredBasedPharmacophore
   openpharmacophore.Dynophore


Virtual Screening
-----------------

.. autosummary::
   :toctree: _autosummary
   :template: custom-class-template.rst
   :recursive:

   openpharmacophore.VirtualScreening
   openpharmacophore.RetrospectiveScreening

IO
----
.. autosummary::
   :toctree: _autosummary

   openpharmacophore.io.from_ligandscout
   openpharmacophore.io.to_ligandscout
   openpharmacophore.io.from_pharmer
   openpharmacophore.io.to_pharmer
   openpharmacophore.io.from_moe
   openpharmacophore.io.to_moe
   openpharmacophore.io.read_pharmagist
   openpharmacophore.io.to_pharmagist
   openpharmacophore.io.load_mol2_file

Databases
---------

Zinc
****
.. autosummary::
   :toctree: _autosummary
    
   openpharmacophore.databases.zinc.download_zinc_subset

PubChem
*******
.. autosummary::
   :toctree: _autosummary

   openpharmacophore.databases.pubchem.get_assay_bioactivity_data
   openpharmacophore.databases.pubchem.get_compound_assay_summary

ChemBl
******
.. autosummary::
   :toctree: _autosummary

   openpharmacophore.databases.chembl.get_assay_bioactivity_data
   openpharmacophore.databases.chembl.get_bioactivity_dataframe
   openpharmacophore.databases.chembl.get_ro5_dataset



