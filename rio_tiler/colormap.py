"""rio-tiler colormap functions."""

import pathlib
from typing import Dict, List, Sequence, Tuple, Union

import numpy

from .errors import ColorMapAlreadyRegistered, InvalidColorMapName, InvalidFormat

EMPTY_COLORMAP: Dict = {i: [0, 0, 0, 0] for i in range(256)}


_default_cmaps = list(pathlib.Path(__file__).parent.joinpath("cmap_data").glob("*.npy"))


def _update_alpha(cmap: Dict, idx: Sequence[int], alpha: int = 0) -> None:
    """Update the alpha value of a colormap index."""
    if isinstance(idx, int):
        idx = (idx,)
    for i in idx:
        cmap[i] = cmap[i][0:3] + [alpha]


def _remove_value(cmap: Dict, idx: Sequence[int]) -> None:
    """Remove value from a colormap dict."""
    if isinstance(idx, int):
        idx = (idx,)

    for i in idx:
        cmap.pop(i, None)


def _update_cmap(cmap: Dict, values: Dict) -> None:
    """Update a colormap dict."""
    for i, color in values.items():
        if len(color) == 3:
            color += [255]
        cmap[i] = color


# From https://github.com/mojodna/marblecutter/blob/5b9040ba6c83562a465eabdbb6e8959e6a8bf041/marblecutter/utils.py#L35
def make_lut(colormap: Dict) -> numpy.ndarray:
    """
    Create a lookup table numpy.ndarray from a GDAL RGBA Color Table dictionary.

    Attributes
    ----------
    colormap : dict
        GDAL RGBA Color Table dictionary.

    Returns
    -------
    lut : numpy.ndarray
        colormap lookup table

    """
    lut = numpy.zeros(shape=(256, 4), dtype=numpy.uint8)
    for i, color in colormap.items():
        lut[int(i)] = color

    return lut


def apply_cmap(
    data: numpy.ndarray, colormap: Dict
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Apply colormap on tile data.

    Attributes
    ----------
    data : numpy ndarray
        1D image array to translate to RGB.
    colormap : dict
        GDAL RGBA Color Table dictionary.

    Returns
    -------
    data : numpy.ndarray
        RGB data.
    mask: numpy.ndarray
        Alpha band.

    """
    if data.shape[0] > 1:
        raise InvalidFormat("Source data must be 1 band")

    lookup_table = make_lut(colormap)
    data = lookup_table[data[0], :]

    data = numpy.transpose(data, [2, 0, 1])

    return data[:-1], data[-1]


def apply_discrete_cmap(
    data: numpy.ndarray, colormap: Dict
) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Apply discrete colormap.

    Note: This method is not used by default and left
          to users to use within custom render methods.

    Attributes
    ----------
    data : numpy ndarray
        1D image array to translate to RGB.
    color_map: dict
        Discrete ColorMap dictionary
        e.g:
        {
            1: [255, 255, 255],
            2: [255, 0, 0]
        }

    Returns
    -------
    arr: numpy.ndarray

    """
    res = numpy.zeros((data.shape[1], data.shape[2], 4), dtype=numpy.uint8)

    for k, v in colormap.items():
        res[data[0] == k] = v

    data = numpy.transpose(res, [2, 0, 1])

    return data[:-1], data[-1]


class ColorMaps(object):
    """Default Colormaps holder."""

    def __init__(self):
        """Load default CMAP names in a dict."""
        self._data = {f.stem: str(f) for f in _default_cmaps}

    def get(self, name: str) -> Dict:
        """Fetch a colormap."""
        cmap = self._data.get(name)
        if cmap is None:
            raise InvalidColorMapName(f"Invalid colormap name: {name}")

        if isinstance(cmap, str):
            cmap = numpy.load(cmap)
            assert cmap.shape == (256, 4)
            assert cmap.dtype == numpy.uint8
            return {idx: value.tolist() for idx, value in enumerate(cmap)}
        else:
            return cmap

    def list(self) -> List[str]:
        """List registered Colormaps."""
        return list(self._data.keys())

    def register(self, name: str, custom_cmap: Union[Dict, str], force: bool = False):
        """
        Register a custom colormap.

        Attributes
        ----------
        name : str
            Name of the colormap.
        custom_cmap: dict or str
            A dict or a path to a numpy file
        force: bool
            Overwrite existing colormap with same key (default: False)

        """
        if not force and name in self._data.keys():
            raise ColorMapAlreadyRegistered(
                f"{name} is already registered. Use force=True to overwrite."
            )

        self._data[name] = custom_cmap


cmap = ColorMaps()  # noqa
