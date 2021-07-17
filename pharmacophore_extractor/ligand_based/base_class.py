import molsysmt as msm
import numpy as np

class LigandBasedExtractor():

    def __init__(self, negative_charge=None, positive_charge=None,
                 hb_donor=None, hb_acceptor=None, included_volume=None, excluded_volume=None,
                 hydrophobity=None, aromatic_ring=None, check=True):

        self.method_name = None
        self.check=check

        self.negative_charge = negative_charge
        self.positive_charge = positive_charge
        self.hb_donor = hb_donor
        self.hb_acceptor = hb_acceptor
        self.included_volume = included_volume
        self.excluded_volume = excluded_volume
        self.hydrophobicity = hydrophobicity
        self.aromatic_ring = aromatic_ring


    def extract(self, molecular_system, selection='all', frame_indices='all'):

        ligand = msm.extract(molecular_system, selection=selection, frame_indices=frame_indices)

        if self.check:
            n_molecules, molecule_types = msm.get(ligand, target='molecule', n_molecules=True, molecule_type=True)
            if (n_molecules>1) or (molecule_types[0]!='small molecule'):
                raise ValueError('A single small molecule needs to be provided')

        n_frames = msm.get(ligand, target='system', n_frames=True)
        output = []

        for frame_index in range(n_frames):
            tmp_ligand = msm.extract(ligand, frame_indices=frame_index)
            pharmacophore = self._workflow(ligand)
            pharmacophore.extractor = self
            pharmacophore.molecular_system = ligand
            output.append(pharmacophore)

        if n_frames==1:
            output = output[0]

        return output

