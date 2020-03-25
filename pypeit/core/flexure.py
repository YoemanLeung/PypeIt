""" Module for flexure routines

.. include common links, assuming primary doc root is up one directory
.. include:: ../links.rst
"""
import inspect

import numpy as np
import copy
from matplotlib import pyplot as plt
from matplotlib import gridspec

from astropy import stats
from astropy import units

from linetools.spectra import xspectrum1d

from pypeit import msgs
from pypeit import utils
from pypeit.core import arc
from pypeit import ginga
from pypeit.core import qa

from IPython import embed


def spat_flexure_shift(sciimg, slits, debug=False):
    """
    Calculate a rigid flexure shift in the spatial dimension
    between the slitmask and the science image.

    It is *important* to use original=True when defining the
    slitmask as everything should be relative to the initial slits

    Otherwise, the WaveTilts could get out of sync with science images

    Args:
        sciimg (`np.ndarray`_):
        slits (:class:`pypeit.slittrace.SlitTraceSet`):

    Returns:
        float:  The spatial flexure shift relative to the initial slits

    """
    #slitmask = pixels.tslits2mask(tslits_dict)
    # TODO -- Add in short slits too
    slitmask = slits.slit_img(initial=True) #, short_slits=True
    onslits = (slitmask > -1)
    corr_slits = (onslits.astype(float)).flatten()
    #corr_roll = np.roll(corr_slits, 10, axis=1).astype(float)

    # Compute
    (mean_sci, med_sci, stddev_sci) = stats.sigma_clipped_stats(sciimg[onslits])
    thresh =  med_sci + 5.0*stddev_sci
    corr_sci = np.fmin(sciimg.flatten(), thresh)


    maxlag = 20
    lags, xcorr = utils.cross_correlate(corr_sci, corr_slits, maxlag)
    xcorr_denom = np.sqrt(np.sum(corr_sci*corr_sci)*np.sum(corr_slits*corr_slits))
    xcorr_norm = xcorr / xcorr_denom
    tampl_true, tampl, pix_max, twid, centerr, ww, arc_cont, nsig = arc.detect_lines(xcorr_norm, sigdetect=3.0,
                                                                                     fit_frac_fwhm=1.5, fwhm=5.0,
                                                                                     cont_frac_fwhm=1.0, cont_samp=30,
                                                                                     nfind=1, debug=debug)
    # No peak? -- e.g. data fills the entire detector
    if len(tampl) == 0:
        msgs.warn('No peak found in spatial flexure.  Assuming there is none..')
        return 0.

    # Find the peak
    xcorr_max = np.interp(pix_max, np.arange(lags.shape[0]), xcorr_norm)
    lag_max = np.interp(pix_max, np.arange(lags.shape[0]), lags)
    msgs.info('Spatial flexure measured: {}'.format(lag_max[0]))

    if debug:
        # Interpolate for bad lines since the fitting code often returns nan
        plt.figure(figsize=(14, 6))
        plt.plot(lags, xcorr_norm, color='black', drawstyle='steps-mid', lw=3, label='x-corr', linewidth=1.0)
        plt.plot(lag_max[0], xcorr_max[0], 'g+', markersize=6.0, label='peak')
        plt.title('Best shift = {:5.3f}'.format(lag_max[0]) + ',  corr_max = {:5.3f}'.format(xcorr_max[0]))
        plt.legend()
        plt.show()

    #tslits_shift = trace_slits.shift_slits(tslits_dict, lag_max)
    # Now translate the tilts

    #slitmask_shift = pixels.tslits2mask(tslits_shift)
    #slitmask_shift = slits.slit_img(flexure=lag_max[0])
    if debug:
        # Now translate the slits in the tslits_dict
        _, _ = slits.select_edges(flexure=lag_max[0])
        viewer, ch = ginga.show_image(sciimg)
        ginga.show_slits(viewer, ch, slits.left_flexure, slits.right_flexure)#, slits.id) #, args.det)
        embed(header='83 of flexure.py')
    #ginga.show_slits(viewer, ch, tslits_shift['slit_left'], tslits_shift['slit_righ'])
    #ginga.show_slits(viewer, ch, tslits_dict['slit_left'], tslits_dict['slit_righ'])

    return lag_max[0]



def load_sky_spectrum(sky_file):
    """
    Load a sky spectrum into an XSpectrum1D object

    Args:
        sky_file: str

    Returns:
        sky_spec: XSpectrum1D
          spectrum
    """
    sky_spec = xspectrum1d.XSpectrum1D.from_file(sky_file)
    return sky_spec


def spec_flex_shift(obj_skyspec, arx_skyspec, mxshft=20):
    """ Calculate shift between object sky spectrum and archive sky spectrum

    Args:
        obj_skyspec (:class:`linetools.spectra.xspectrum1d.XSpectrum1d`):
            Spectrum of the sky related to our object
        arx_skyspec (:class:`linetools.spectra.xspectrum1d.XSpectrum1d`):
            Archived sky spectrum
        mxshft (float, optional):
            Maximum allowed shift from flexure;  note there are cases that
            have been known to exceed even 30 pixels..

    Returns:
        dict: Contains flexure info
    """

    # TODO None of these routines should have dependencies on XSpectrum1d!

    # Determine the brightest emission lines
    msgs.warn("If we use Paranal, cut down on wavelength early on")
    arx_amp, arx_amp_cont, arx_cent, arx_wid, _, arx_w, arx_yprep, nsig = arc.detect_lines(arx_skyspec.flux.value)
    obj_amp, obj_amp_cont, obj_cent, obj_wid, _, obj_w, obj_yprep, nsig_obj= arc.detect_lines(obj_skyspec.flux.value)

    # Keep only 5 brightest amplitude lines (xxx_keep is array of
    # indices within arx_w of the 5 brightest)
    arx_keep = np.argsort(arx_amp[arx_w])[-5:]
    obj_keep = np.argsort(obj_amp[obj_w])[-5:]

    # Calculate wavelength (Angstrom per pixel)
    arx_disp = np.append(arx_skyspec.wavelength.value[1]-arx_skyspec.wavelength.value[0],
                         arx_skyspec.wavelength.value[1:]-arx_skyspec.wavelength.value[:-1])
    #arx_disp = (np.amax(arx_sky.wavelength.value)-np.amin(arx_sky.wavelength.value))/arx_sky.wavelength.size
    obj_disp = np.append(obj_skyspec.wavelength.value[1]-obj_skyspec.wavelength.value[0],
                         obj_skyspec.wavelength.value[1:]-obj_skyspec.wavelength.value[:-1])
    #obj_disp = (np.amax(obj_sky.wavelength.value)-np.amin(obj_sky.wavelength.value))/obj_sky.wavelength.size

    # Calculate resolution (lambda/delta lambda_FWHM)..maybe don't need
    # this? can just use sigmas
    arx_idx = (arx_cent+0.5).astype(np.int)[arx_w][arx_keep]   # The +0.5 is for rounding
    arx_res = arx_skyspec.wavelength.value[arx_idx]/\
              (arx_disp[arx_idx]*(2*np.sqrt(2*np.log(2)))*arx_wid[arx_w][arx_keep])
    obj_idx = (obj_cent+0.5).astype(np.int)[obj_w][obj_keep]   # The +0.5 is for rounding
    obj_res = obj_skyspec.wavelength.value[obj_idx]/ \
              (obj_disp[obj_idx]*(2*np.sqrt(2*np.log(2)))*obj_wid[obj_w][obj_keep])
    #obj_res = (obj_sky.wavelength.value[0]+(obj_disp*obj_cent[obj_w][obj_keep]))/(
    #    obj_disp*(2*np.sqrt(2*np.log(2)))*obj_wid[obj_w][obj_keep])

    if not np.all(np.isfinite(obj_res)):
        msgs.warn('Failed to measure the resolution of the object spectrum, likely due to error '
                   'in the wavelength image.')
        return None
    msgs.info("Resolution of Archive={0} and Observation={1}".format(np.median(arx_res),
                                                                     np.median(obj_res)))

    # Determine sigma of gaussian for smoothing
    arx_sig2 = np.power(arx_disp[arx_idx]*arx_wid[arx_w][arx_keep], 2)
    obj_sig2 = np.power(obj_disp[obj_idx]*obj_wid[obj_w][obj_keep], 2)

    arx_med_sig2 = np.median(arx_sig2)
    obj_med_sig2 = np.median(obj_sig2)

    if obj_med_sig2 >= arx_med_sig2:
        smooth_sig = np.sqrt(obj_med_sig2-arx_med_sig2)  # Ang
        smooth_sig_pix = smooth_sig / np.median(arx_disp[arx_idx])
        arx_skyspec = arx_skyspec.gauss_smooth(smooth_sig_pix*2*np.sqrt(2*np.log(2)))
    else:
        msgs.warn("Prefer archival sky spectrum to have higher resolution")
        smooth_sig_pix = 0.
        msgs.warn("New Sky has higher resolution than Archive.  Not smoothing")
        #smooth_sig = np.sqrt(arx_med_sig**2-obj_med_sig**2)

    #Determine region of wavelength overlap
    min_wave = max(np.amin(arx_skyspec.wavelength.value), np.amin(obj_skyspec.wavelength.value))
    max_wave = min(np.amax(arx_skyspec.wavelength.value), np.amax(obj_skyspec.wavelength.value))

    #Smooth higher resolution spectrum by smooth_sig (flux is conserved!)
#    if np.median(obj_res) >= np.median(arx_res):
#        msgs.warn("New Sky has higher resolution than Archive.  Not smoothing")
        #obj_sky_newflux = ndimage.gaussian_filter(obj_sky.flux, smooth_sig)
#    else:
        #tmp = ndimage.gaussian_filter(arx_sky.flux, smooth_sig)
#        arx_skyspec = arx_skyspec.gauss_smooth(smooth_sig_pix*2*np.sqrt(2*np.log(2)))
        #arx_sky.flux = ndimage.gaussian_filter(arx_sky.flux, smooth_sig)

    # Define wavelengths of overlapping spectra
    keep_idx = np.where((obj_skyspec.wavelength.value>=min_wave) &
                         (obj_skyspec.wavelength.value<=max_wave))[0]
    #keep_wave = [i for i in obj_sky.wavelength.value if i>=min_wave if i<=max_wave]

    #Rebin both spectra onto overlapped wavelength range
    if len(keep_idx) <= 50:
        msgs.warn("Not enough overlap between sky spectra")
        return None
    else: #rebin onto object ALWAYS
        keep_wave = obj_skyspec.wavelength[keep_idx]
        arx_skyspec = arx_skyspec.rebin(keep_wave)
        obj_skyspec = obj_skyspec.rebin(keep_wave)
        # Trim edges (rebinning is junk there)
        arx_skyspec.data['flux'][0,:2] = 0.
        arx_skyspec.data['flux'][0,-2:] = 0.
        obj_skyspec.data['flux'][0,:2] = 0.
        obj_skyspec.data['flux'][0,-2:] = 0.

    # Normalize spectra to unit average sky count
    norm = np.sum(obj_skyspec.flux.value)/obj_skyspec.npix
    obj_skyspec.flux = obj_skyspec.flux / norm
    norm2 = np.sum(arx_skyspec.flux.value)/arx_skyspec.npix
    arx_skyspec.flux = arx_skyspec.flux / norm2
    if (norm < 0.):
        msgs.warn("Bad normalization of object in flexure algorithm")
        msgs.warn("Will try the median")
        norm = np.median(obj_skyspec.flux.value)
        if (norm < 0.):
            msgs.warn("Improper sky spectrum for flexure.  Is it too faint??")
            return None
    if (norm2 < 0.):
        msgs.warn('Bad normalization of archive in flexure. You are probably using wavelengths '
                   'well beyond the archive.')
        return None

    # Deal with bad pixels
    msgs.work("Need to mask bad pixels")

    # Deal with underlying continuum
    msgs.work("Consider taking median first [5 pixel]")
    everyn = obj_skyspec.npix // 20
    bspline_par = dict(everyn=everyn)
    mask, ct = utils.robust_polyfit(obj_skyspec.wavelength.value, obj_skyspec.flux.value, 3,
                                    function='bspline', sigma=3., bspline_par=bspline_par)
    obj_sky_cont = utils.func_val(ct, obj_skyspec.wavelength.value, 'bspline')
    obj_sky_flux = obj_skyspec.flux.value - obj_sky_cont
    mask, ct_arx = utils.robust_polyfit(arx_skyspec.wavelength.value, arx_skyspec.flux.value, 3,
                                        function='bspline', sigma=3., bspline_par=bspline_par)
    arx_sky_cont = utils.func_val(ct_arx, arx_skyspec.wavelength.value, 'bspline')
    arx_sky_flux = arx_skyspec.flux.value - arx_sky_cont

    # Consider sharpness filtering (e.g. LowRedux)
    msgs.work("Consider taking median first [5 pixel]")

    #Cross correlation of spectra
    #corr = np.correlate(arx_skyspec.flux, obj_skyspec.flux, "same")
    corr = np.correlate(arx_sky_flux, obj_sky_flux, "same")

    #Create array around the max of the correlation function for fitting for subpixel max
    # Restrict to pixels within maxshift of zero lag
    lag0 = corr.size//2
    #mxshft = settings.argflag['reduce']['flexure']['maxshift']
    max_corr = np.argmax(corr[lag0-mxshft:lag0+mxshft]) + lag0-mxshft
    subpix_grid = np.linspace(max_corr-3., max_corr+3., 7)

    #Fit a 2-degree polynomial to peak of correlation function. JFH added this if/else to not crash for bad slits
    if np.any(np.isfinite(corr[subpix_grid.astype(np.int)])):
        fit = utils.func_fit(subpix_grid, corr[subpix_grid.astype(np.int)], 'polynomial', 2)
        success = True
        max_fit = -0.5 * fit[1] / fit[2]
    else:
        fit = utils.func_fit(subpix_grid, 0.0*subpix_grid, 'polynomial', 2)
        success = False
        max_fit = 0.0
        msgs.warn('Flexure compensation failed for one of your objects')


    #Calculate and apply shift in wavelength
    shift = float(max_fit)-lag0
    msgs.info("Flexure correction of {:g} pixels".format(shift))
    #model = (fit[2]*(subpix_grid**2.))+(fit[1]*subpix_grid)+fit[0]

    flex_dict = dict(polyfit=fit, shift=shift, subpix=subpix_grid,
                     corr=corr[subpix_grid.astype(np.int)],
                     sky_spec=obj_skyspec,
                     arx_spec=arx_skyspec,
                     corr_cen=corr.size/2, smooth=smooth_sig_pix, success=success)
    # Return
    return flex_dict


def spec_flexure_obj(specobjs, maskslits, method, sky_file, mxshft=None):
    """Correct wavelengths for flexure, object by object

    Args:
        specobjs (:class:`pypeit.specobjs.Specobjs`):
        maskslits (`np.ndarray`_):
            True = masked slit
        method (:obj:`str`)
          'boxcar' -- Recommneded
          'slitpix' --
        sky_file (str):
            Sky file
        mxshft (int, optional):
            Passed to flex_shift()

    Returns:
        list:  list of dicts containing flexure results
            Aligned with specobjs
            Filled with a basically empty dict if the slit is skipped or there is no object
    """
    sv_fdict = None
    msgs.work("Consider doing 2 passes in flexure as in LowRedux")
    # Load Archive
    sky_spectrum = load_sky_spectrum(sky_file)

    nslits = len(maskslits)
    gdslits = np.where(~maskslits)[0]

    # Loop on objects
    flex_list = []

    # Slit/objects to come back to
    return_later_sobjs = []

    # Loop over slits, and then over objects here
    for slit in range(nslits):
        msgs.info("Working on flexure in slit (if an object was detected): {:d}".format(slit))
        # TODO -- This only will work for MultiSlit
        indx = specobjs.slitorder_indices(slit)
        this_specobjs = specobjs[indx]
        # Reset
        flex_dict = dict(polyfit=[], shift=[], subpix=[], corr=[],
                         corr_cen=[], spec_file=sky_file, smooth=[],
                         arx_spec=[], sky_spec=[])
        # If no objects on this slit append an empty dictionary
        if slit not in gdslits:
            flex_list.append(flex_dict.copy())
            continue
        for ss, specobj in enumerate(this_specobjs):
            if specobj is None:
                continue
            if specobj['BOX_WAVE'] is None: #len(specobj._data.keys()) == 1:  # Nothing extracted; only the trace exists
                continue
            msgs.info("Working on flexure for object # {:d}".format(specobj.OBJID) + "in slit # {:d}".format(specobj.SLITID))
            # Using boxcar
            if method in ['boxcar', 'slitcen']:
                sky_wave = specobj.BOX_WAVE #.to('AA').value
                sky_flux = specobj.BOX_COUNTS_SKY
            else:
                msgs.error("Not ready for this flexure method: {}".format(method))

            # Generate 1D spectrum for object
            obj_sky = xspectrum1d.XSpectrum1D.from_tuple((sky_wave, sky_flux))

            # Calculate the shift
            fdict = spec_flex_shift(obj_sky, sky_spectrum, mxshft=mxshft)
            punt = False
            if fdict is None:
                msgs.warn("Flexure shift calculation failed for this spectrum.")
                if sv_fdict is not None:
                    msgs.warn("Will used saved estimate from a previous slit/object")
                    fdict = copy.deepcopy(sv_fdict)
                else:
                    # One does not exist yet
                    # Save it for later
                    return_later_sobjs.append([slit, ss])
                    punt = True
            else:
                sv_fdict = copy.deepcopy(fdict)

            # Punt?
            if punt:
                break

            # Interpolate
            new_sky = specobj.flexure_interp(sky_wave, fdict)
            # Update dict
            for key in ['polyfit', 'shift', 'subpix', 'corr', 'corr_cen', 'smooth', 'arx_spec']:
                flex_dict[key].append(fdict[key])
            flex_dict['sky_spec'].append(new_sky)

        flex_list.append(flex_dict.copy())

        # Do we need to go back?
        for items in return_later_sobjs:
            if sv_fdict is None:
                msgs.info("No flexure corrections could be made")
                break
            # Setup
            slit, ss = items
            flex_dict = flex_list[slit]
            specobj = specobjs[ss]
            sky_wave = specobj.BOX_WAVE #.to('AA').value
            # Copy me
            fdict = copy.deepcopy(sv_fdict)
            # Interpolate
            new_sky = specobj.flexure_interp(sky_wave, fdict)
            # Update dict
            for key in ['polyfit', 'shift', 'subpix', 'corr', 'corr_cen', 'smooth', 'arx_spec']:
                flex_dict[key].append(fdict[key])
            flex_dict['sky_spec'].append(new_sky)

    return flex_list


# TODO I don't see why maskslits is needed in these routine, since if the slits are masked in arms, they won't be extracted
#  AND THIS IS WHY THE CODE IS CRASHING
def spec_flexure_qa(specobjs, maskslits, basename, det, flex_list,
               slit_cen=False, out_dir=None):
    """

    Args:
        specobjs:
        maskslits (np.ndarray):
        basename (str):
        det (int):
        flex_list (list):
        slit_cen:
        out_dir:

    """
    plt.rcdefaults()
    plt.rcParams['font.family']= 'times new roman'

    # Grab the named of the method
    method = inspect.stack()[0][3]
    #
    gdslits = np.where(np.invert(maskslits))[0]

    # Loop over slits, and then over objects here
    for slit in gdslits:
        indx = specobjs.slitorder_indices(slit)
        this_specobjs = specobjs[indx]
        this_flex_dict = flex_list[slit]

        # Setup
        if slit_cen:
            nobj = 1
            ncol = 1
        else:
            nobj = np.sum(indx)
            ncol = min(3, nobj)
        #
        if nobj == 0:
            continue
        nrow = nobj // ncol + ((nobj % ncol) > 0)
        # Outfile, one QA file per slit
        outfile = qa.set_qa_filename(basename, method + '_corr', det=det,slit=(slit + 1), out_dir=out_dir)
        plt.figure(figsize=(8, 5.0))
        plt.clf()
        gs = gridspec.GridSpec(nrow, ncol)
        for iobj, specobj in enumerate(this_specobjs):
            if specobj is None or (specobj.BOX_WAVE is None and specobj.OPT_WAVE is None):
                continue
            # Correlation QA
            ax = plt.subplot(gs[iobj//ncol, iobj % ncol])
            # Fit
            fit = this_flex_dict['polyfit'][iobj]
            xval = np.linspace(-10., 10, 100) + this_flex_dict['corr_cen'][iobj] #+ flex_dict['shift'][o]
            #model = (fit[2]*(xval**2.))+(fit[1]*xval)+fit[0]
            model = utils.func_val(fit, xval, 'polynomial')
            mxmod = np.max(model)
            ylim_min = np.min(model/mxmod) if np.isfinite(np.min(model/mxmod)) else 0.0
            ylim = [ylim_min, 1.3]
            ax.plot(xval-this_flex_dict['corr_cen'][iobj], model/mxmod, 'k-')
            # Measurements
            ax.scatter(this_flex_dict['subpix'][iobj]-this_flex_dict['corr_cen'][iobj],
                       this_flex_dict['corr'][iobj]/mxmod, marker='o')
            # Final shift
            ax.plot([this_flex_dict['shift'][iobj]]*2, ylim, 'g:')
            # Label
            if slit_cen:
                ax.text(0.5, 0.25, 'Slit Center', transform=ax.transAxes, size='large', ha='center')
            else:
                ax.text(0.5, 0.25, '{:s}'.format(specobj.NAME), transform=ax.transAxes, size='large', ha='center')
            ax.text(0.5, 0.15, 'flex_shift = {:g}'.format(this_flex_dict['shift'][iobj]),
                    transform=ax.transAxes, size='large', ha='center')#, bbox={'facecolor':'white'})
            # Axes
            ax.set_ylim(ylim)
            ax.set_xlabel('Lag')
        # Finish
        plt.tight_layout(pad=0.2, h_pad=0.0, w_pad=0.0)
        plt.savefig(outfile, dpi=400)
        plt.close()

        # Sky line QA (just one object)
        if slit_cen:
            iobj = 0
        else:
            iobj = 0
            specobj = this_specobjs[iobj]

        if len(this_flex_dict['shift']) == 0:
            return

        # Repackage
        sky_spec = this_flex_dict['sky_spec'][iobj]
        arx_spec = this_flex_dict['arx_spec'][iobj]

        # Sky lines
        sky_lines = np.array([3370.0, 3914.0, 4046.56, 4358.34, 5577.338, 6300.304,
                              7340.885, 7993.332, 8430.174, 8919.610, 9439.660,
                              10013.99, 10372.88])*units.AA
        dwv = 20.*units.AA
        gdsky = np.where((sky_lines > sky_spec.wvmin) & (sky_lines < sky_spec.wvmax))[0]
        if len(gdsky) == 0:
            msgs.warn("No sky lines for Flexure QA")
            return
        if len(gdsky) > 6:
            idx = np.array([0, 1, len(gdsky)//2, len(gdsky)//2+1, -2, -1])
            gdsky = gdsky[idx]

        # Outfile
        outfile = qa.set_qa_filename(basename, method+'_sky', det=det,slit=(slit + 1), out_dir=out_dir)
        # Figure
        plt.figure(figsize=(8, 5.0))
        plt.clf()
        nrow, ncol = 2, 3
        gs = gridspec.GridSpec(nrow, ncol)
        if slit_cen:
            plt.suptitle('Sky Comparison for Slit Center', y=1.05)
        else:
            plt.suptitle('Sky Comparison for {:s}'.format(specobj.NAME), y=1.05)

        for ii, igdsky in enumerate(gdsky):
            skyline = sky_lines[igdsky]
            ax = plt.subplot(gs[ii//ncol, ii % ncol])
            # Norm
            pix = np.where(np.abs(sky_spec.wavelength-skyline) < dwv)[0]
            f1 = np.sum(sky_spec.flux[pix])
            f2 = np.sum(arx_spec.flux[pix])
            norm = f1/f2
            # Plot
            ax.plot(sky_spec.wavelength[pix], sky_spec.flux[pix], 'k-', label='Obj',
                    drawstyle='steps-mid')
            pix2 = np.where(np.abs(arx_spec.wavelength-skyline) < dwv)[0]
            ax.plot(arx_spec.wavelength[pix2], arx_spec.flux[pix2]*norm, 'r-', label='Arx',
                    drawstyle='steps-mid')
            # Axes
            ax.xaxis.set_major_locator(plt.MultipleLocator(dwv.value))
            ax.set_xlabel('Wavelength')
            ax.set_ylabel('Counts')

        # Legend
        plt.legend(loc='upper left', scatterpoints=1, borderpad=0.3,
                   handletextpad=0.3, fontsize='small', numpoints=1)

        # Finish
        plt.savefig(outfile, dpi=400)
        plt.close()
        #plt.close()

    plt.rcdefaults()

    return
