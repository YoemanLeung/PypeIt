=============
Spec2D Output 
=============

.. index:: spec2d

Overview
========

During the data reduction proceess, PypeIt creates a series
of 2D spectral images prior to extraction of 1D spectra.
And, of course, several of these 2D images may have greater
value for analysis than the 1D spectra.  For each on-source
exposure, PypeIt outputs a series of these images, with the
number set by the :ref:`outputs-reduction-mode`.

The following table describes the standard products:

============  ====================================
2D Spec Type  Description
============  ====================================
PROCESSED     Bias-subtracted, flat-fielded image
IVARRAW       Inverse variance image; sky+detector
SKY           Sky-subtracted, processed image
OBJ           Model of the object(s) flux
IVARMODEL     Model of the inverse variance image; sky+detector
MASK          Mask image
============  ====================================

There will be a set of these images for each detector
processed.

Naming
======

The 2D spectra files have names like::

    spec2d_b27-J1217p3905_KASTb_2015May20T045733.560.fits

The model is::

    Prefix_frame-objname_spectrograph_timestamp.fits

Viewing
=======

You can open this image in ds9 and play around.
But we highly recommend using the `pypeit_show_2dspec`_ script
which interfaces with *ginga*.

.. _pypeit-2dspec:

pypeit_show_2dspec
------------------

This script displays the sky-subtracted 2D image for a single
detector in a *ginga* RC viewer.  It also overlays the slits and
any objects extracted.  It should be called from the reduction
directory, i.e. above the *Science/* folder where the spec2d image
is located.

Here is the usage (possibly out of date;  use *pypeit_show_2dspec -h*)::

    usage: pypeit_show_2dspec [-h] [--list] [--det DET] [--showmask]
                          [--removetrace] [--embed]
                          file

    Display sky subtracted, spec2d image in a Ginga viewer. Run above the Science/
    folder

    positional arguments:
      file           PYPIT spec2d file

    optional arguments:
      -h, --help     show this help message and exit
      --list         List the extensions only? (default: False)
      --det DET      Detector number (default: 1)
      --showmask     Overplot masked pixels (default: False)
      --removetrace  Do not overplot traces in the skysub, sky_resid and resid
                     channels (default: False)
      --embed        Upon completion embed in ipython shell (default: False)

Before running, you need to launch a *ginga* RC viewer with::

    ginga --modules=RC

Here is a typical call::

    pypeit_show_2dspec Science/spec2d_c17_60L._LRISb_2017Mar20T055336.211.fits


This opens 4 tabs for the:

 - Procesed image (sciimg-det##)
 - Sky subtracted image (skysub-det##)
 - Sky residual image (sky_resid-det##)
 - Full residual image which removes the object too (resid-det##)

Red/green lines indicate slit edges.  Orange lines (if present)
indicate object traces.

As you mouse around, the x-values shown at the bottom indicate
the wavelength.

Coming Soon
===========

A better description of the data model.
