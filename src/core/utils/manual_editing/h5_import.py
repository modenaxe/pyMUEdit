import h5py
import numpy as np
import scipy.io as sio
import time
import numpy as np


class h5py_convert:
    
    def h5py_to_dict(self, h5obj):

        """
        Convert h5py.File, Group, or Dataset into nested dict/native Python structures.
        """
        # If it's a Group, recursively convert all its children
        if isinstance(h5obj, h5py.Group):
            return {name: self.h5py_to_dict(h5obj[name])
                    for name in h5obj.keys()}

        # If it's a Dataset, extract the data and check if dereferencing is needed
        elif isinstance(h5obj, h5py.Dataset):
            data = h5obj[()]
            # Arrays with object dtype (typically references) need special handling
            if data.dtype == object:
                return self._resolve_references(data, h5obj.file)

            # Numeric values, strings, or matrices: convert directly to native Python types
            else:
                return data

        else:
            # For unexpected types, extend as needed
            return None

    def _resolve_references(self, arr, h5file):
        """
        Replace HDF5 references in numpy.ndarray with actual data.
        arr    : ndarray with dtype=object, elements are h5py.Reference
        h5file : h5py.File handle used for dereferencing
        """
        # Scalar reference
        if isinstance(arr, h5py.Reference):
            return self._follow_reference(arr, h5file)
        
        if isinstance(arr, np.ndarray) and arr.dtype == object:
            if arr.ndim == 0:
                return self._resolve_references(arr.item(), h5file)

            res = [self._resolve_references(x, h5file) for x in arr]
            return res
        
        return arr


    def _follow_reference(self, ref, h5file):
        """
        Given an h5py.Reference, return the actual data it points to (or nested dict).
        """
        # Dereference using the file handle
        obj = h5file[ref]
        
        if isinstance(obj, h5py.Dataset):
            data = obj[()]
            if isinstance(data, np.ndarray) and data.dtype == object:
                return self._resolve_references(data, h5file)
            
            if isinstance(data, np.ndarray) and data.ndim == 2 and data.shape[1] == 1:
                data = data[:, 0]    
            return data.tolist()
        return obj
    
