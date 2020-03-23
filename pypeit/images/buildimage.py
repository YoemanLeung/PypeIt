""" Uber object for calibration images, e.g. arc, flat

.. include common links, assuming primary doc root is up one directory
.. include:: ../links.rst
"""

import os
import numpy as np

from pypeit import msgs
from pypeit.par import pypeitpar
from pypeit.images import combineimage
from pypeit.images import pypeitimage
from pypeit.core import procimg

from IPython import embed


class ArcImage(pypeitimage.PypeItImage):
    """
    Simple DataContainer for the Arc Image
    """
    # Peg the version of this class to that of PypeItImage
    version = pypeitimage.PypeItImage.version

    # I/O
    output_to_disk = ('ARC_IMAGE', 'ARC_FULLMASK', 'ARC_DETECTOR')
    hdu_prefix = 'ARC_'

    # Master fun
    master_type = 'Arc'
    file_format = 'fits'


class AlignImage(pypeitimage.PypeItImage):
    """
    Simple DataContainer for the Arc Image
    """
    # Peg the version of this class to that of PypeItImage
    version = pypeitimage.PypeItImage.version

    # I/O
    output_to_disk = ('ALIGN_IMAGE', 'ALIGN_FULLMASK', 'ALIGN_DETECTOR')
    hdu_prefix = 'ALIGN_'

    # Master fun
    master_type = 'Align'
    file_format = 'fits'


class BiasImage(pypeitimage.PypeItImage):
    """
    Simple DataContainer for the Tilt Image
    """
    # Set the version of this class
    version = pypeitimage.PypeItImage.version

    # Output to disk
    output_to_disk = ('BIAS_IMAGE', 'BIAS_DETECTOR')
    hdu_prefix = 'BIAS_'
    master_type = 'Bias'
    file_format = 'fits'


class TiltImage(pypeitimage.PypeItImage):
    """
    Simple DataContainer for the Tilt Image
    """

    # Peg the version of this class to that of PypeItImage
    version = pypeitimage.PypeItImage.version

    # I/O
    output_to_disk = ('TILT_IMAGE', 'TILT_FULLMASK', 'TILT_DETECTOR')
    hdu_prefix = 'TILT_'

    # Master fun
    master_type = 'Tiltimg'
    file_format = 'fits'


class TraceImage(pypeitimage.PypeItImage):
    """
    Simple DataContainer for the Trace Image
    """

    # Peg the version of this class to that of PypeItImage
    version = pypeitimage.PypeItImage.version

    # I/O
    output_to_disk = ('TRACE_IMAGE', 'TRACE_FULLMASK', 'TRACE_DETECTOR')
    hdu_prefix = 'TRACE_'

    # Master fun
    master_type = 'Trace'


def buildimage_fromlist(spectrograph, det, frame_par, file_list,
                        bias=None, bpm=None,
                        flatimages=None,
                        #pixel_flat=None, illum_flat_fit=None,
                        sigma_clip=False, sigrej=None, maxiters=5,
                        ignore_saturation=True, slits=None):
    """
    Build a PypeItImage from a list of files (and instructions)

    Args:
        spectrograph (:class:`pypeit.spectrographs.spectrograph.Spectrograph`):
            Spectrograph used to take the data.
        det (:obj:`int`):
            The 1-indexed detector number to process.
        frame_par (:class:`pypeit.par.pypeitpar.FramePar`):
            Parameters that dictate the processing of the images.  See
            :class:`pypeit.par.pypeitpar.ProcessImagesPar` for the
            defaults.
        file_list (list):
            List of files
        bpm (np.ndarray, optional):
            Bad pixel mask.  Held in ImageMask
        bias (np.ndarray, optional):
            Bias image
        pixel_flat (np.ndarray, optional):
            Flat image. If None, pixel-to-pixel response is not
            removed.
        illum_flat_fit (:class:`pypeit.bspline.bspline`, optional):
            if provided, use this bspline fit to construct an illumination flat
            If None, slit illumination profile is not removed.
        sigrej (int or float, optional): Rejection threshold for sigma clipping.
             Code defaults to determining this automatically based on the numberr of images provided.
        maxiters (int, optional):
        ignore_saturation (bool, optional):
            Should be True for calibrations and False otherwise

    Returns:
        :class:`pypeit.images.pypeitimage.PypeItImage`:  Or one of its children

    """
    # Check
    if not isinstance(frame_par, pypeitpar.FrameGroupPar):
        msgs.error('Provided ParSet for must be type FrameGroupPar.')
    process_steps = procimg.set_process_steps(bias, frame_par)
    #
    combineImage = combineimage.CombineImage(spectrograph, det, frame_par['process'], file_list)
    pypeitImage = combineImage.run(process_steps, bias, bpm=bpm,
                                   #pixel_flat=pixel_flat, illum_flat_fit=illum_flat_fit,
                                   flatimages=flatimages,
                                   sigma_clip=sigma_clip,
                                   sigrej=sigrej, maxiters=maxiters,
                                   ignore_saturation=ignore_saturation, slits=slits)
    #
    # Decorate according to the type of calibration
    #   Primarily for handling MasterFrames
    #   WARNING, any internals in pypeitImage are lost here
    if frame_par['frametype'] == 'bias':
        finalImage = BiasImage.from_pypeitimage(pypeitImage)
    elif frame_par['frametype'] == 'arc':
        finalImage = ArcImage.from_pypeitimage(pypeitImage)
    elif frame_par['frametype'] == 'tilt':
        finalImage = TiltImage.from_pypeitimage(pypeitImage)
    elif frame_par['frametype'] == 'trace':
        finalImage = TraceImage.from_pypeitimage(pypeitImage)
    elif frame_par['frametype'] in ['pixelflat', 'science', 'standard']:
        finalImage = pypeitImage
    else:
        finalImage = None
        embed(header='193 of calibrationimage')

    # Internals
    finalImage.process_steps = process_steps
    finalImage.files = file_list
    finalImage.rawheadlist = pypeitImage.rawheadlist
    finalImage.head0 = pypeitImage.head0

    # Return
    return finalImage
