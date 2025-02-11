# OpenPharmacophore
from openpharmacophore.databases import chembl, pubchem
from openpharmacophore.screening.alignment import apply_radii_to_bounds, transform_embeddings
from openpharmacophore._private_tools.exceptions import BadShapeError, MissingParameters, OpenPharmacophoreValueError
from openpharmacophore._private_tools.screening_arguments import check_virtual_screening_kwargs, is_3d_pharmacophore
# Third Party
import matplotlib.pyplot as plt
import numpy as np
from rdkit import Chem, RDConfig, DataStructs
from rdkit.Chem import ChemicalFeatures, rdDistGeom
from rdkit.Chem.Pharm2D import Gobbi_Pharm2D
from rdkit.Chem.Pharm2D.Generate import Gen2DFingerprint
from rdkit.Chem.Pharm3D import EmbedLib
from tqdm.auto import tqdm
# Standard library
from collections import namedtuple
from operator import itemgetter
import os

class RetrospectiveScreening():
    """ Class for performing retrospective virtual screening. 
    
        This class expects molecules classified as actives and inactives. 
        With this class pharmacophore models can be validated.

    Parameters
    ----------

    Attributes
    ----------

    """
    def __init__(self, pharmacophore, **kwargs):
        
        if is_3d_pharmacophore(pharmacophore):
            self.scoring_metric = "SSD"
            self._screen_fn = self._align_molecules
        elif isinstance(pharmacophore, DataStructs.SparseBitVect): # For pharmacophore fingerprints
            self.scoring_metric = "Similarity"
            self.similarity_fn, _ = check_virtual_screening_kwargs(**kwargs)
            self.similarity_cutoff = 0.0
            self._factory = Gobbi_Pharm2D.factory
            self._screen_fn = self._fingerprint_similarity
        else:
            raise TypeError("pharmacophore must be of type Pharmacophore, StructuredBasedPharmacophore, "
                "LigandBasedPharmacophore, or rdkit.DataStructs.SparseBitVect")
        
        self.n_actives = 0
        self.n_inactives = 0
        self.bioactivities = None
        self.molecules = []
        self.n_molecules = 0
        self.pharmacophore = pharmacophore
             
    def from_chembl_target_id(self, target_id, pIC50_threshold=6.3):
        """ Retrospective screening from bioactivity data fetched from chembl.
           
           Parameters
           ----------
           target_id : str
                ChemBl target id.
           
           pIC50_threshold : float, default=6.3
                The cuttoff value from which a molecule is considered active.
           
           """
        smiles, activity = chembl.get_training_data(target_id, pIC50_threshold)
        
        self.db = "PubChem"
        self.from_bioactivity_data(smiles, activity)

    def from_bioactivity_data(self, smiles, activity):
        """ Retrospective screening from a set of molecules classified as active or inactive.
        
            Parameters
            ----------
            smiles : List of 2-tuples
                A list with the molecules for screening. Each element of the list is 
                a tuple, where the first elements is the compound id and the second 
                the smiles of the molecule.

            activity : numpy.ndarray 
                Array with the labels of each molecule; 1 corresponds to an active molecule
                and 0 to an inactive one. An array of rank 1 where the first dimension is 
                equal to the length of the smiles list is expected. 
        
        """
        if len(activity.shape) > 1:
            raise BadShapeError("activity must be an array of rank 1")
        if len(smiles) != activity.shape[0]:
            raise OpenPharmacophoreValueError("smiles and activity must contain the same number of entries")

        self.n_actives = np.sum(activity)
        self.n_inactives = activity.shape[0] - self.n_actives
        self.bioactivities = activity

        molecules = []
        for id, smi in smiles:
            mol = Chem.MolFromSmiles(smi)
            mol.SetProp("_Name", str(id))
            molecules.append(mol)

        if self.scoring_metric == "Similarity":
            self._fingerprint_similarity(molecules)
        elif self.scoring_metric == "SSD":
            self._align_molecules(molecules)
        else:
            raise NotImplementedError

    def from_pubchem_bioassay_id(self, bioassay_id):
        """ Retrospective screening from a pubchem bioassay.

            Parameters
            ----------
            bioassay_id : int
                PubChem bioassay id. 
        """
        pubchem_client = pubchem.PubChem()
        smiles, activity = pubchem_client.get_assay_training_data(bioassay_id)
        self.db = "Pubchem"
        self.from_bioactivity_data(smiles, activity)

    def confusion_matrix(self, threshold=None):
        """ Compute a confusion matrix
        
            Parameters
            ----------
            threshold : float, optional
                The scoring value from which a molecule will be considered as active.
                Required if the screening was done with fingerprints.
            
            Returns
            -------
            cf_matrix: np.ndarray of shape (2, 2)
                The confusion matrix.

        """
        if self.scoring_metric == "Similarity" and threshold is None:
            raise MissingParameters("Expected a threshold value.")
        
        if self.scoring_metric == "SSD":
            threshold = 0.0
            
        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0
        
        for ii, mol in enumerate(self.molecules):
            if self.bioactivities[ii] == 1 and mol.score > threshold:
                true_positives += 1
            elif self.bioactivities[ii] == 1 and mol.score <= threshold:
                false_negatives += 1
            elif self.bioactivities[ii] == 0 and mol.score > threshold:
                false_positives += 1
            elif self.bioactivities[ii] == 0 and mol.score <= threshold:
                true_negatives += 1
        
        cf_matrix = np.array([[true_positives, false_positives],
                              [false_negatives, true_negatives]])
        
        assert np.sum(cf_matrix, axis=None) == self.n_molecules
        
        return cf_matrix

    def AUC(self):
        """ Calculate ROC area under the curve.
        
            Returns
            -------
            area : float
                The value of the area under the curve.

            References
            ----------
            Fawcett, T. An Introduction to ROC Analysis. Pattern Recognition Letters 2006, 27, 861−874
        """
        def trapezoid_area(x1, x2, y1, y2):
            """ Calculate the area of a trapezoid.
            """
            base = abs(x1 - x2)
            # average height
            height = abs(y1 + y2) / 2
            return base * height

        scores = [x[0] for x in self.molecules]
        scores = np.array(scores)

        # Sort scores in descending order and then sort labels
        indices = np.argsort(scores)[::-1]
        scores = np.sort(scores)[::-1] 
        labels = self.bioactivities[indices]

        n_positives = self.n_actives
        n_negatives = self.n_inactives

        false_positives = 0
        true_positives = 0
        false_pos_prev = 0
        true_pos_prev = 0

        area = 0
        score_prev = -10000000

        i = 0
        while i < labels.shape[0]:

            if scores[i] != score_prev:
                area += trapezoid_area(false_positives, false_pos_prev, 
                                        true_positives, true_pos_prev)
                score_prev = scores[i]
                false_pos_prev = false_positives
                true_pos_prev = true_positives
            
            if labels[i] == 1:
                true_positives += 1
            else:
                false_positives += 1

            i += 1

        area += trapezoid_area(n_negatives, false_pos_prev, n_positives, true_pos_prev)
        # Scale area from n_negatives * n_positives onto the unit square
        area = area / (n_negatives * n_positives)

        assert area >= 0 and area <= 1

        return area

    def ROC_plot(self, ax=None, label="", random_line=True):
        """ Plot the ROC curve. 
        
            Parameters
            ----------
            ax : matplotlib.axes._subplots.AxesSubplot, optional (Default = None)
                An axes object where the plot will be drawn.

            random_line : bool, default=True
                Whether to plot the line corresponding to a random classifier.

            Returns
            ----------
            ax : matplotlib.axes._subplots.AxesSubplot, optional (Default = None)
                An axes object whith the plot.

            References
            ----------
            Fawcett, T. An Introduction to ROC Analysis. Pattern Recognition Letters 2006, 27, 861−874

        """

        scores = [x[0] for x in self.molecules]
        scores = np.array(scores)

        # Sort scores in descending order and then sort labels
        indices = np.argsort(scores)[::-1]
        scores = np.sort(scores)[::-1] 
        labels = self.bioactivities[indices]

        n_positives = self.n_actives
        n_negatives = self.n_inactives
        
        false_positives = 0
        true_positives = 0
        x = []
        y = []
        score_prev = -10000000

        # Calculate points for the ROC plot
        i = 0
        while i < labels.shape[0]:

            if scores[i] != score_prev:
                x.append(false_positives/n_negatives)
                y.append(true_positives/n_positives)
                score_prev = scores[i]

            if labels[i] == 1:
                true_positives += 1
            else:
                false_positives += 1

            i += 1

        # Append point (1, 1)
        x.append(false_positives/n_negatives)
        y.append(true_positives/n_positives)

        # Plot the curve

        if ax is None:
            fig, ax = plt.subplots()
        ax.plot(x, y, label=label)
        if random_line:
            ax.plot([0, 1], [0, 1], color="black", linestyle="dashed", label="Random")
        
        ax.set_xlabel("Sensitivity")
        ax.set_ylabel("1 - Specificity")
        if label or random_line:
            ax.legend()   

        return ax

    def enrichment_factor(self, percentage):
        """ Calculate enrichment factor for the x% of the screened database 

            Parameters
            ----------
            percentage : float
                Percentage of the screened database. Must be between 0 and 100
            
            Returns
            -------
            float
                The enrichment factor
        """
        if percentage < 0 or percentage > 100:
            raise OpenPharmacophoreValueError("percentage must be a number between 0 and 100")

        screened_percentage, percentage_actives_found = self._enrichment_data()
        screened_percentage = np.array(screened_percentage)
        percentage_actives_found = np.array(percentage_actives_found)

        indices_screen_per = screened_percentage <= percentage / 100
        max_enrichment_idx = np.argsort(screened_percentage[indices_screen_per])[-1]

        return percentage_actives_found[max_enrichment_idx] * 100

    def ideal_enrichment_factor(self, percentage):
        """ Calculate ideal enrichment factor for the x% of the screened database 

            Parameters
            ----------
            percentage : float
                Percentage of the screened database. Must be between 0 and 100
            
            Returns
            -------
            float
                The idal enrichment factor"""
    
        percentage = percentage / 100

        n_molecules = self.bioactivities.shape[0]
        ratio_actives = self.n_actives / n_molecules
        if percentage <= ratio_actives:
            return (100 / ratio_actives) * percentage
        else:
            return 100.0
    
    def enrichment_plot(self, ax=None, label="", random_line=True, ideal=False):
        """ Create an enrichment plot 
            
            Parameters
            ----------
            ax : matplotlib.axes._subplots.AxesSubplot, optional (Default = None)
                An axes object where the plot will be drawn.

            random_line : bool, default=True
                Whether to plot the line corresponding to a random classifier.

            ideal : bool, defaul=False
                Whether to plot the ideal enrichmnent curve
            
            Returns
            ----------
            ax : matplotlib.axes._subplots.AxesSubplot, optional (Default = None)
                An axes object whith the plot.
        
        """
        screened_percentage, percentage_actives_found = self._enrichment_data()
        n_molecules = self.bioactivities.shape[0]

        if ax is None:
            fig, ax = plt.subplots()
        ax.plot(screened_percentage, percentage_actives_found, label=label)
        if random_line:
            ax.plot([0, 1], [0, 1], color="black", linestyle="dashed", label="Random")
        if ideal:
            n_molecules = self.bioactivities.shape[0]
            ratio_actives = self.n_actives / n_molecules
            ax.plot([0, ratio_actives, 1], [0, 1, 1], color="red", linestyle="dashed", label="Ideal")
        
        ax.set_xlabel("% Database Screened")
        ax.set_ylabel("% Actives")   
        ax.legend()

        return ax
     
    def _enrichment_data(self):
        """ Get enrichment data necessary for enrichment plot and enrichment factor calculation.

            Returns
            --------
            screened_percentage : list of float
                The percentage of the database screened.
            
            percentage_actives_found: list of float
                The percentage of actives found.

        """
        scores = [x[0] for x in self.molecules]
        scores = np.array(scores)

        # Sort scores in descending order and then sort labels
        indices = np.argsort(scores)[::-1]
        scores = np.sort(scores)[::-1] 
        bioactivities = self.bioactivities[indices]

        n_molecules = bioactivities.shape[0]
        n_actives = self.n_actives

        # Calculate % number of active molecules found in the x% of the screened database
        percentage_actives_found = [0]
        screened_percentage = [0]
        actives_counter = 0
        for ii in range(n_molecules):
            if bioactivities[ii] == 1:
                actives_counter += 1
            percentage_actives_found.append(actives_counter / n_actives)
            screened_percentage.append(ii / n_molecules)
        
        return screened_percentage, percentage_actives_found
    
    def _align_molecules(self, molecules):
        """ Align a list of molecules to a given pharmacophore.

        Parameters
        ----------
        molecules : list of rdkit.Chem.mol
            List of molecules to align.

        Note
        -------
        Does not return anything. The attribute molecules is updated with the scored molecules.
        """
        self.n_molecules += len(molecules)

        rdkit_pharmacophore, radii = self.pharmacophore.to_rdkit()
        apply_radii_to_bounds(radii, rdkit_pharmacophore)

        fdef = os.path.join(RDConfig.RDDataDir,'BaseFeatures.fdef')
        featFactory = ChemicalFeatures.BuildFeatureFactory(fdef)
        
        MolScore = namedtuple("MolScore", ["score", "id", "mol"])
        
        for mol in tqdm(molecules):

            bounds_matrix = rdDistGeom.GetMoleculeBoundsMatrix(mol)
            can_match, all_matches = EmbedLib.MatchPharmacophoreToMol(mol, featFactory, rdkit_pharmacophore)
            if can_match:
                failed, _ , matched_mols, _ = EmbedLib.MatchPharmacophore(all_matches, 
                                                                          bounds_matrix,
                                                                          rdkit_pharmacophore, 
                                                                          useDownsampling=True)
                if failed:
                    matched_mol = MolScore(0.0, mol.GetProp("_Name"), mol)
                    self.molecules.append(matched_mol)
                    continue
            else:
                matched_mol = MolScore(0.0, mol.GetProp("_Name"), mol)
                self.molecules.append(matched_mol)
                continue
            atom_match = [list(x.GetAtomIds()) for x in matched_mols]
            
            try:
                mol_H = Chem.AddHs(mol)
                _, embeddings, _ = EmbedLib.EmbedPharmacophore(mol_H, atom_match, rdkit_pharmacophore, count=10)
            except:
                continue
            
            SSDs = transform_embeddings(rdkit_pharmacophore, embeddings, atom_match) 
            if len(SSDs) == 0:
                matched_mol = MolScore(0.0, mol.GetProp("_Name"), mol)
                self.molecules.append(matched_mol)
                continue
            best_fit_index = min(enumerate(SSDs), key=itemgetter(1))[0]
            
            score = 1 / SSDs[best_fit_index]
            matched_mol = MolScore(score, mol.GetProp("_Name"), embeddings[best_fit_index])
            self.molecules.append(matched_mol)
    
    def _fingerprint_similarity(self, molecules):
        """ Compute fingerprints and similarity values for a list of molecules. 

        Parameters
        ----------
        molecules : list of rdkit.Chem.mol
            List of molecules whose similarity to the pharmacophoric fingerprint will be calculated.
        
        Note
        -----
        Does not return anything. The attribute molecules is updated with the scored molecules.

        """
        if self.similarity_fn == "tanimoto":
            similarity_fn = DataStructs.TanimotoSimilarity
        elif self.similarity_fn == "dice":
            similarity_fn = DataStructs.DiceSimilarity
       
        self.n_molecules = len(molecules)
        MolScore = namedtuple("MolScore", ["score", "id", "mol"])
        
        for mol in tqdm(molecules):
            fingerprint = Gen2DFingerprint(mol, self._factory)
            similarity = similarity_fn(self.pharmacophore, fingerprint)
            mol_id = mol.GetProp("_Name")
            matched_mol = MolScore(similarity, mol_id, mol)
            self.molecules.append(matched_mol)
          
    def __repr__(self):
        return f"{self.__class__.__name__}(n_molecules={self.n_molecules})"