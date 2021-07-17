from openpharmacophore.pharmacophore_extractor.ligand_based.base_class import LigandBasedMethod
from openpharmacophore.pharmacophore import Pharmacophore

class Pharmer(LigandBasedMethod):

    def __init__(self):

        super().__init__(positive_charge='sphere', negative_charge='sphere', hb_donor='sphere and vector',
                         hb_acceptor='sphere and vector', aromatic_ring='sphere')

    def _workflow(ligand):

        pharmacophore = Pharmacophore()

        center = puw.quantity([1,1,0],'nm')
        radius = puw.quantity(1.0,'nm')
        element = oph.pharmacophoric_elements.PositiveChargeSphere(center, radius)
        pharmacophore.add_element(element)

        center = puw.quantity([0,-1,0],'nm')
        radius = puw.quantity(1.0,'nm')
        element = oph.pharmacophoric_elements.NegativeChargeSphere(center, radius)
        pharmacophore.add_element(element)

        center = puw.quantity([0,-1,-3],'nm')
        radius = puw.quantity(1.0,'nm')
        direction = [1,1,1]
        element = oph.pharmacophoric_elements.HBAcceptorSphereAndVector(center, radius, direction)
        pharmacophore.add_element(element)

        center = puw.quantity([2,-2,2],'nm')
        radius = puw.quantity(1.0,'nm')
        element = oph.pharmacophoric_elements.AromaticRingSphere(center, radius)
        pharmacophore.add_element(element)

        center = puw.quantity([-2,1,1],'nm')
        sigma = puw.quantity(1.0,'nm')
        element = oph.pharmacophoric_elements.HydrophobicGaussianKernel(center, sigma)
        pharmacophore.add_element(element)

        return pharmacophore

