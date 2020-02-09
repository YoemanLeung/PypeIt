"""
Module for generating a Bar image to map constant spatial locations

.. include common links, assuming primary doc root is up one directory
.. include:: ../links.rst
"""
import numpy as np
import os
from IPython import embed

from pypeit import msgs
from pypeit import masterframe
from pypeit.par import pypeitpar
from pypeit.images import calibrationimage
from pypeit.images import pypeitimage


class BarFrame(calibrationimage.CalibrationImage, masterframe.MasterFrame):
    """
    Class to generate/load the bar image

    This class is primarily designed to generate a Bar frame to map constant
    spatial locations.  It also contains I/O methods for the Master frames
    of PypeIt.  The build_master() method will return a simple command
    (str) if that is the specified parameter (`par['useframe']`).

    Args:
        spectrograph (:class:`pypeit.spectrographs.spectrograph.Spectrograph`):
            Spectrograph used to take the data.

        files (:obj:`list`, optional):
            List of filenames to process.
        det (:obj:`int`, optional):
            The 1-indexed detector number to process.
        par (:class:`pypeit.par.pypeitpar.FrameGroupPar`, optional):
            The parameters used to process the frames.  If None, set
            to::

                pypeitpar.FrameGroupPar('bar')

        master_key (:obj:`str`, optional):
            The string identifier for the instrument configuration.  See
            :class:`pypeit.masterframe.MasterFrame`.
        master_dir (:obj:`str`, optional):
            Path to master frames
        reuse_masters (:obj:`bool`, optional):
            Load from disk if possible
    """

    # Frame type is a class attribute
    frametype = 'bar'
    master_type = 'Bar'

    @classmethod
    def from_master_file(cls, master_file, par=None):
        """
        Instantiate from a master file

        Args:
            master_file (str):
            par (:class:`pypeit.par.pypeitpar.FrameGroupPar`, optional):

        Returns:
            barframe.BarFrame:
                The PypeItImage is loaded into self.pypeitImage

        """
        # Spectrograph
        spectrograph, extras = masterframe.items_from_master_file(master_file)
        head0 = extras[0]
        # Master info
        master_dir = head0['MSTRDIR']
        master_key = head0['MSTRKEY']
        # Instantiate
        slf = cls(spectrograph, par=par, master_dir=master_dir, master_key=master_key,
                  reuse_masters=True)
        slf.pypeitImage = slf.load(ifile=master_file)
        # Return
        return slf

    # Keep order same as processimages (or else!)
    def __init__(self, spectrograph, files=None, det=1, par=None, master_key=None,
                 master_dir=None, reuse_masters=False):

        # Parameters
        self.par = pypeitpar.FrameGroupPar(self.frametype) if par is None else par

        # Start us up
        calibrationimage.CalibrationImage.__init__(self, spectrograph, det, self.par['process'], files=files)

        # MasterFrames: Specifically pass the ProcessImages-constructed
        # spectrograph even though it really only needs the string name
        masterframe.MasterFrame.__init__(self, self.master_type, master_dir=master_dir,
                                         master_key=master_key, reuse_masters=reuse_masters)

        # Processing steps
        self.process_steps = []
        if self.par['process']['overscan'].lower() != 'none':
            self.process_steps.append('subtract_overscan')
        self.process_steps += ['trim']
        self.process_steps += ['orient']

    def build_image(self, overwrite=False, trim=True):
        """
        Grab the bar files (as needed) and then process the input bar
        frames with :func:`pypeit.processimages.ProcessImages.process`.

        Args:
            overwrite: (:obj: `bool`, optional):
                Regenerate the combined image
            trim (:obj:`bool`, optional):
                If True, trim the image

        Returns:
            `numpy.ndarray`_: Combined, processed image.
        """
        if self.nfiles == 0:
            msgs.info("No bar frames provided.  No bar image will be generated or used")
            return None
        # Build
        self.pypeItImage = super(BarFrame, self).build_image(ignore_saturation=True)
        self.pypeitImage.ivar = None  # Zero this out as it non-sensical
        # Return
        return self.pypeItImage

    def save(self, outfile=None, overwrite=True):
        """
        Save the bar master data.

        Args:
            outfile (:obj:`str`, optional):
                Name for the output file.  Defaults to
                :attr:`file_path`.
            overwrite (:obj:`bool`, optional):
                Overwrite any existing file.
        """
        # Some checks
        if self.pypeitImage is None:
            msgs.warn('No MasterBar to save!')
            return
        if not self.pypeitImage.validate():
            msgs.warn('MasterBar is not a proper image.')
            return
        # Proceed
        _outfile = self.master_file_path if outfile is None else outfile
        # Check if it exists
        if os.path.exists(_outfile) and not overwrite:
            msgs.warn('Master file exists: {0}'.format(_outfile) + msgs.newline()
                      + 'Set overwrite=True to overwrite it.')
            return
        # Save
        hdr = self.build_master_header(steps=self.process_steps, raw_files=self.file_list)
        self.pypeitImage.write(_outfile, hdr=hdr, iext='BAR')
        msgs.info('Master frame written to {0}'.format(_outfile))
        #super(BarFrame, self).save(self.pypeitImage, 'BAR', outfile=outfile, overwrite=overwrite,
        #                            raw_files=self.file_list, steps=self.process_steps)

    def load(self, ifile=None):
        """
        Load the bar frame according to how par['useframe'] is set.

        Args:
            ifile (:obj:`str`, optional):
                Name of the master frame file.  Defaults to
                :attr:`file_path`.

        Returns:
            Returns either the `numpy.ndarray`_ with the bar image
            or None if no bar is to be subtracted.
        """
        # Check on whether to reuse and whether the file exists
        master_file = self.chk_load_master(ifile)
        if master_file is None:
            return
        else:  # Load
            self.pypeitImage = pypeitimage.PypeItImage.from_file(master_file)
            return self.pypeitImage
        #return super(BarFrame, self).load('BAR', ifile=ifile, is_pypeitImage=True)