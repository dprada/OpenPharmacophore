## General Exceptions
class OpenPharmacophoreException(Exception):
    """ Base exception for openpharmacophore """
    def __init__(self, message, documentation_web=None):
        self.message = message
        if documentation_web is not None:
            message += f" Check the online documentation for more information {documentation_web}"
        super().__init__(self.message)

class MissingParameters(OpenPharmacophoreException):
    """ Exception raised when calling a function and not passing all required parameters.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


## Exceptions derived from value errors

class OpenPharmacophoreValueError(ValueError):
    """ Base value error exception for OpenPharmacophore
    """
    def __init__(self, message, documentation_web=None):
        self.message = message
        if documentation_web is not None:
            message += f" Check the online documentation for more information {documentation_web}"
        super().__init__(self.message)

class BadShapeError(OpenPharmacophoreValueError):
    """ Exception raised when an array has an incorrect shape."""
    pass

class PointWithNoColorError(OpenPharmacophoreValueError):
    """ Exception raised when a pharmacophoric point has no color"""
    pass

class NoConformersError(OpenPharmacophoreValueError):
    """ Exception raised when an rdkit molecule has no conformers and thus, no 3D coordinates.
    """
    def __init__(self, message="Molecule has no conformers." 
                                "Pharmacophoric points cannot be found without 3D coordinates.",
                        documentation_web=None):
        super().__init__(message, documentation_web)
    
class NoLigandsError(OpenPharmacophoreValueError):
    """ Exception raised when a pharmacophore contains no ligands."""
    pass

class NoMatchesError(OpenPharmacophoreValueError):
    """ Exception raised when a VirtualScreening object contains no matches."""
    pass

class InvalidFeatureError(OpenPharmacophoreValueError):
    """ Exception raised when trying to remove an invalid feature from a pharmacophore.
    """
    pass

class InvalidFileFormat(OpenPharmacophoreValueError):
    """ Exception raised when loading a file from an unsopported format.
    """
    pass

class WrongDimensionalityError(OpenPharmacophoreValueError):
    """ Exception raised when a quantity has the wrong dimensionality"""
    pass

## Exceptions derived from type errors

class OpenPharmacophoreTypeError(TypeError):
    """ Base exception for openpharmacophore type errors"""
    def __init__(self, message, documentation_web=None):
        self.message = message
        if documentation_web is not None:
            message += f" Check the online documentation for more information {documentation_web}"
        super().__init__(self.message)

class IsNotStringError(OpenPharmacophoreTypeError):
    """ Exception raised when passing an invalid argument to a function or class that expected a string"""
    pass

class IsNotQuantityError(OpenPharmacophoreTypeError):
    """ Exception raised when passing an invalid argument to a function or class that expected a quantity"""
    pass

class QuantityDataTypeError(OpenPharmacophoreTypeError):
    """ Exception raised when passing a quantity has an invalid data type"""
    pass

class NotArrayLikeError(OpenPharmacophoreTypeError):
    """ Exception raised when passing an invalid argument to a function or class that expected an 
        array like parameter."""
    pass

## Exceptions derived from IO errors

class OpenPharmacophoreIOError(IOError):
    """ Base exception for openpharmacophore IO related errors"""
    def __init__(self, message, documentation_web=None):
        self.message = message
        if documentation_web is not None:
            message += f" Check the online documentation for more information {documentation_web}"
        super().__init__(self.message)

class FetchError(OpenPharmacophoreIOError):
    """ Exception raised when fetching a file.
    """
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


## Not Implemented Exceptions

class OpenPharmacophoreNotImplementedError(NotImplementedError):

    def __init__(self, message=None, issues_web=None):
        if message is None:
            if issues_web is not None:
                message = ('It has not been implemeted yet. Write a new issue in'
                '{} asking for it.'.format(issues_web))

        super().__init__(message)