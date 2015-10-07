import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from lsst.sims.photUtils import Bandpass, Sed, PhotometricParameters, LSSTdefaults, SignalToNoise
import bandpassUtils as bu
import sedUtils as su

filterlist = ('u', 'g', 'r', 'i', 'z', 'y')
filtercolors = {'u':'b', 'g':'c', 'r':'g',
                'i':'y', 'z':'r', 'y':'m'}


def calcM5s(hardware, system, atmos, title='m5'):
    photParams = PhotometricParameters()
    lsstDefaults = LSSTdefaults()
    darksky = Sed()
    darksky.readSED_flambda(os.path.join(os.getenv('SYSENG_THROUGHPUTS_DIR'), 'siteProperties', 'darksky.dat'))
    flatSed = Sed()
    flatSed.setFlatSED()
    m5 = {}
    sourceCounts = {}
    skyCounts = {}
    skyMag = {}
    gamma = {}
    for f in system:
        m5[f] = SignalToNoise.calcM5(darksky, system[f], hardware[f], photParams, seeing=lsstDefaults.seeing(f))
        fNorm = flatSed.calcFluxNorm(m5[f], system[f])
        flatSed.multiplyFluxNorm(fNorm)
        sourceCounts[f] = flatSed.calcADU(system[f], photParams=photParams)
        # Calculate the Skycounts expected in this bandpass.
        skyCounts[f] = darksky.calcADU(hardware[f], photParams=photParams) * photParams.platescale**2
        # Calculate the sky surface brightness.
        skyMag[f] = darksky.calcMag(hardware[f])
        # Calculate the gamma value.
        gamma[f] = SignalToNoise.calcGamma(system[f], m5[f], photParams)
    print title
    print 'Filter m5 SourceCounts SkyCounts SkyMag Gamma'
    for f in ('u', 'g' ,'r', 'i', 'z', 'y'):
        print '%s %.2f %.1f %.2f %.2f %.6f' %(f, m5[f], sourceCounts[f], skyCounts[f], skyMag[f], gamma[f])

    # Show what these look like individually (add sky & m5 limits on throughput curves)
    plt.figure()
    ax = plt.gca()
    # Add dark sky
    ax2 = ax.twinx()
    plt.sca(ax2)
    skyab = -2.5*np.log10(darksky.fnu) - darksky.zp
    ax2.plot(darksky.wavelen, skyab,
             'k-', linewidth=0.8, label='Dark sky mags')
    ax2.set_ylabel('AB mags')
    ax2.set_ylim(24, 10)
    plt.sca(ax)
    # end of dark sky
    handles = []
    for f in filterlist:
        plt.plot(system[f].wavelen, system[f].sb, color=filtercolors[f], linewidth=2)
        myline = mlines.Line2D([], [], color=filtercolors[f], linestyle='-', linewidth=2,
                               label = '%s: m5 %.1f (sky %.1f)' %(f, m5[f], skyMag[f]))
        handles.append(myline)
    plt.plot(atmos.wavelen, atmos.sb, 'k:', label='Atmosphere, X=1.2')
    # Add legend for dark sky.
    myline = mlines.Line2D([], [], color='k', linestyle='-', label='Dark sky AB mags')
    handles.append(myline)
    # end of dark sky legend line
    plt.legend(loc=(0.01, 0.69), handles=handles, fancybox=True, numpoints=1, fontsize='small')
    plt.ylim(0, 1)
    plt.xlim(300, 1100)
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Fractional Throughput Response')
    if title == 'Vendor combo':
        title = ''
    plt.title('System total response curves %s' %(title))
    if title == '':
        plt.savefig('throughputs.png', format='png', dpi=600)
    return m5


if __name__ == '__main__':

    defaultDirs = bu.setDefaultDirs()
    addLosses = True

    allPlots = False

    photParams = PhotometricParameters()
    lsstDefaults = LSSTdefaults()

    # Build the detectors.
    qevendors = {}
    qevendors[1] = bu.buildVendorDetector(os.path.join(defaultDirs['detector'], 'vendor1'), addLosses)
    qevendors[2] = bu.buildVendorDetector(os.path.join(defaultDirs['detector'], 'vendor2'), addLosses)
    qevendors['combo'] = bu.buildGenericDetector(defaultDirs['detector'], addLosses)
    if allPlots:
        bu.plotBandpasses(qevendors, title='Vendor Detector Responses')

    # Build the other components.
    lens1 = bu.buildLens(defaultDirs['lens1'], addLosses)
    lens2 = bu.buildLens(defaultDirs['lens2'], addLosses)
    lens3 = bu.buildLens(defaultDirs['lens3'], addLosses)
    filters = bu.buildFilters(defaultDirs['filters'], addLosses)
    mirror1 = bu.buildMirror(defaultDirs['mirror1'], addLosses)
    mirror2 = bu.buildMirror(defaultDirs['mirror2'], addLosses)
    mirror3 = bu.buildMirror(defaultDirs['mirror3'], addLosses)
    atmosphere = bu.buildAtmosphere(defaultDirs['atmosphere'])

    # Plot all components.
    if allPlots:
        plt.figure()
        plt.plot(qevendors['combo'].wavelen, qevendors['combo'].sb, 'k-', linewidth=2, label='Detector')
        plt.plot(lens1.wavelen, lens2.sb, 'g-', linewidth=2, label='L1')
        plt.plot(lens2.wavelen, lens2.sb, 'r-', linewidth=2, label='L2')
        plt.plot(lens3.wavelen, lens3.sb, 'b-', linewidth=2, label='L3')
        for f in ['u', 'g', 'r', 'i', 'z', 'y']:
            plt.plot(filters[f].wavelen, filters[f].sb, linestyle=':', linewidth=5, label=f)
        plt.plot(mirror1.wavelen, mirror1.sb, 'g-.', linewidth=2, label='M1')
        plt.plot(mirror2.wavelen, mirror2.sb, 'r--', linewidth=2, label='M2')
        plt.plot(mirror3.wavelen, mirror3.sb, 'b--', linewidth=2, label='M3')
        plt.plot(atmosphere.wavelen, atmosphere.sb, 'k:', linewidth=2, label='X=1.2')
        plt.legend(loc=(0.96, 0.2), numpoints=1, fontsize='smaller', fancybox=True)
        plt.xlim(300, 1100)
        plt.ylim(0, 1)
        plt.title('Throughput components')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Fractional Throughput Response')

    hardware = {}
    system = {}
    m5 = {}
    # Combine components (and individual combination for each detector vendor) by hand.
    for detector in ['combo', 1, 2]:
        core_sb = qevendors[detector].sb * lens1.sb * lens2.sb * lens3.sb * mirror1.sb * mirror2.sb * mirror3.sb
        hardware[detector] = {}
        system[detector] = {}
        m5[detector] = {}
        for f in filters:
            hardware[detector][f] = Bandpass()
            system[detector][f] = Bandpass()
            wavelen = filters[f].wavelen
            hw_sb = core_sb * filters[f].sb
            hardware[detector][f].setBandpass(wavelen, hw_sb)
            system[detector][f].setBandpass(wavelen, hw_sb*atmosphere.sb)
        m5[detector] = calcM5s(hardware[detector], system[detector], atmosphere, title='Vendor %s' %detector)

    plt.show()
