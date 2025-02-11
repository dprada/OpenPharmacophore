from openpharmacophore.pharmacophoric_point import PharmacophoricPoint
import pyunitwizard as puw
import numpy as np
import re

def read_pharmagist(file_name, pharmacophore_index=None):
    """ Loads pharmacophores from a pharmagist mol2 file.

        Parameters
        ----------
        file_name : str
            Name of the file containing the pharmacophore.

        pharmacophore_index : int, optional
            If given, returns the pharmacophore which index is provided. 
            Else, all the pharmcophores from the file will be returned.

        Returns
        -------
        pharmacophores : list of openpharmacophore.LigandBasedPharmacophores
            A list of ligand based pharmacophores.
        
        elements : list of openpharmacophore.PharmacophoricPoint
            A list of pharmacophoric points from a single pharmacophore.
    """
    # dictionary to map pharmagist feature names to openpharmacophore elements
    pharmagist_element_name = { 
        "AR": "aromatic ring",
        "HYD": "hydrophobicity",
        "ACC": "hb acceptor",
        "DON": "hb donor",
        "CAT": "positive charge",
        "ANI": "negative charge",
    }
    
    pharmacophores = []
    pattern = r"[A-Z]{2,3} "
    with open(file_name, "r") as f:
        for line in f.readlines():
            match = re.search(pattern, line)
            if "@<TRIPOS>ATOM" in line:
                points = []
            if match:
                point_line = [p for p in line.split(" ") if p != ""]
                feat_type = pharmagist_element_name[point_line[1]]
                center = [float(coord) for coord in point_line[2: 5]] # convert coordinates to float
                center = puw.quantity(center, "angstroms")
                element = PharmacophoricPoint(
                    feat_type=feat_type,
                    center=center, 
                    radius=puw.quantity(1.0, "angstroms"))
                points.append(element)
            if "@<TRIPOS>BOND" in line:
                pharmacophores.append(points)
    pharmacophores = [ph for ph in pharmacophores if len(ph) > 0] # filter empty lists
    
    if pharmacophore_index is None:
        from openpharmacophore.ligand_based import LigandBasedPharmacophore
        pharmacophores = [LigandBasedPharmacophore(ph) for ph in pharmacophores]
        return pharmacophores

    elements = pharmacophores[pharmacophore_index]
    return elements

def to_pharmagist(pharmacophores, file_name):
    """ Save pharmacophores to pharmagist mol2 format

        Parameters
        ----------
        pharmacophores : list of openpharmacophore.Pharmacophore or openpharmacophore.Pharmacophore
            Pharmacophore or pharmacophores that will be saved.

        file_name : str
            Name of the file containing the pharmacophore.

        Notes
        -------
        Nothing is returned. A new file is written.
    """
    doc = _pharmagist_file_info(pharmacophores)
    with open(file_name, "w") as f:
        f.writelines(doc)

def _pharmagist_file_info(pharmacophores):
    """ Get necessary info to create a pharmagist mol2 file to store pharmacophores.

        Parameters
        ----------
        pharmacophores : list of openpharmacophore.Pharmacophore or openpharmacophore.Pharmacophore
            Pharmacophore or pharmacophores that will be saved

        Returns
        -------
        doc : list of list
            List where each sublist contains a pharmacophore represented as a mol2 string.
    """
    pharmagist_element_name = { 
        "aromatic ring": "AR ",
        "hydrophobicity": "HYD",
        "hb acceptor": "ACC",
        "hb donor": "DON",
        "positive charge": "CAT",
        "negative charge": "ANI",
        }

    pharmagist_element_specs = { 
            "aromatic ring": "AR ",
            "hydrophobicity": "HYD",
            "hb acceptor": "HB ",
            "hb donor": "HB ",
            "positive charge": "CHG",
            "negative charge": "CHG",
    }

    if not isinstance(pharmacophores, list):
        pharmacophores = [pharmacophores]

    doc = [] # list to store all pharmacophores
    for pharmacophore in pharmacophores:
        lines = ["@<TRIPOS>MOLECULE\n", "@<TRIPOS>ATOM\n"] # list to store all lines for a single pharmacophore
        line = ""
        for i, element in enumerate(pharmacophore.elements):
            element_inx = str(i + 1)
            line += element_inx.rjust(7)
            try:
                feat_name = pharmagist_element_name[element.feature_name]
            except:
                continue
            line += " " + feat_name
            # Get point coordinates
            center = np.around(puw.get_value(element.center, to_unit="angstroms"), 4)
            # Pad coordinates with zeros to the right. Number of zeros depends on sign
            if center[0] < 0:
                x = str(center[0]).ljust(7,"0").rjust(16)
            else:
                x = str(center[0]).ljust(6,"0").rjust(16)
            if center[1] < 0:
                y = str(center[1]).ljust(7,"0").rjust(10)
            else:
                y = str(center[1]).ljust(6,"0").rjust(10)
            if center[2] < 0:
                z = str(center[2]).ljust(7,"0").rjust(10)
            else:
                z = str(center[2]).ljust(6,"0").rjust(10)
            line += x + y + z + " "
            line += pharmagist_element_specs[element.feature_name].rjust(5)
            line += str(i).rjust(5)
            line += pharmagist_element_specs[element.feature_name].rjust(6)
            line += "0.0000\n".rjust(12)
            lines.append(line)
            line = ""

        lines.append("@<TRIPOS>BOND\n")
        for l in lines:
            doc.append(l)
        
    return doc