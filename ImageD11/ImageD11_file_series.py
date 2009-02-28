
"""
To be moved to fabio sometime
"""

import fabio.file_series
import fabio.fabioimage
import fabio.openimage
import numpy

def get_options(parser):

    parser.add_option("-5","--hdf5",action="store", type="string",
                      dest = "hdf5", default = None,
                      help = "hdf file containing input image series")
    # or, eventually:
    # stem, first, last, format, (omegas better be in the headers)
    parser.add_option("-n","--stem",action="store", type="string",
                      dest = "stem", default = None,
                      help = "stem name for input image series")
    parser.add_option("-f","--first",action="store", type="int",
                      dest = "first", default = None,
                      help = "first number for input image series")
    parser.add_option("-l","--last",action="store", type="int",
                      dest = "last", default = None,
                      help = "last number for input image series")
    parser.add_option("--ndigits", action="store", type="int",
                      dest = "ndigits", default = 4,
                      help = "Number of digits in file numbering [4]")
    parser.add_option("-P", "--padding", action="store",
                      type="choice", choices=["Y","N"], 
                      default="Y", dest="padding",
                      help="Is the image number to padded Y|N, e.g. "\
                          "should 1 be 0001 or just 1 in image name, default=Y")
    parser.add_option("-F","--format",action="store", type="string",
                      dest = "format", default = ".edf",
                      help = "format [.edf] for input image series")

    parser.add_option("-O", "--flood", action="store", type="string",
                      dest = "flood", default = None,
                      help = "Flood")
    
    parser.add_option("-d", "--dark", action="store", type="string",
                      dest = "dark", default = None,
                      help = "Dark image")
    return parser


def get_series_from_hdf( hdf_file, dark = None, flood = None ):
    groups = hdf_file.listnames()
    for group in groups:
        imagenames = hdf_file[group].listnames()
        for image in imagenames:
            im = hdf_file[group][image]
            om = float(im.attrs['Omega'])
            data = im[:,:]
            if (dark, flood) is not (None, None):
                data = data.astype(numpy.float32)
            if dark != None:
                numpy.subtract( data, dark, data )
            if flood != None:
                numpy.divide( data, flood, data )
            yield fabio.fabioimage.fabioimage( data = data,
                                               header = {
                    'Omega': om } )

def series_from_fabioseries( fabioseries, dark=None, flood=None ):
    for filename in fabioseries:
        fim = fabio.openimage.openimage(filename)
        if (dark, flood) is not (None, None):
            fim.data = fim.data.astype(numpy.float32)
        if dark != None:
            numpy.subtract( fim.data, dark, fim.data )
        if flood != None:
            numpy.divide( fim.data, flood, fim.data )
        fim.header['Omega'] = float(fim.header['Omega'])
        yield fim
        


def get_series_from_stemnum( options, args, dark = None, flood = None ):
    """
    Returns a file series thing - not a fabio one
    """
    if options.format in ['bruker', 'BRUKER', 'Bruker']:
        extn = ""
    elif options.format == 'GE':
        extn = ""
    else:
        extn = options.format
        
    fso = fabio.file_series.numbered_file_series(
        options.stem,
        options.first,
        options.last,
        extn,
        digits = options.ndigits,
        padding = options.padding )
    return series_from_fabioseries( fso , dark, flood )
    

def get_series_from_options( options, args ):
    """
    Returns a file series thing - not a fabio one

    This gives back a fabioimage object with dark and flood
    corrected data
    """

    try:
        if options.dark is not None:
            dark = fabio.openimage.openimage( options.dark ).data
        else:
            dark = None
    except:
        print "Problem with your dark",options.dark
        raise
    
    try:
        if options.flood is not None:
            flood = fabio.openimage.openimage( options.flood ).data
        else:
            flood = None
    except:
        print "Problem with your flood",options.flood
        raise
        

    if len(args) > 0 :
        # We assume unlabelled arguments are filenames 
        fso = fabio.file_series.file_series(args)
        return series_from_fabioseries( fso, dark, flood )

    if options.hdf5 is not None:
        hf = h5py.File(options.hdf5)
        # print "Getting images from",options.hdf5
        return get_series_from_hdf( hf, dark, flood )
    
    return get_series_from_stemnum( options, args,
                                     dark, flood) 
    

