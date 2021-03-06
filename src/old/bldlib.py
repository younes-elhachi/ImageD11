

"""
We started using some intrinsics in the C code to make it run faster
when processors support specific instructions.  This makes it less
portable and harder to build. These notes explain how things could 
work. 

If a CPU has some feature (sse2, avx2, fma, etc) then we will want
to use it in specific places that we are aware of. We might as well
also let the compiler use those instructions everywhere else where
we have not written specific things too. That means:

- compile everything as avx2 -> avx2 version
- compile everything as sse2 -> sse2 version
- compile everything as ansi -> ansi version

So we are going to build a series of extensions and use #ifdef inside
them.

-- May 2020 - all that gets to be a horrific mess.
We have a "generic" build that takes the regular python option
and a host platform build that take -mhost=native flags.

Which one we get is determined by the cImageD11.py module.
"""

import os, sys, platform
import setuptools
import distutils.ccompiler

need_build = True

sources = ("blobs.c cdiffraction.c cimaged11utils.c closest.c connectedpixels.c"+
 " darkflat.c localmaxlabel.c sparse_image.c splat.c").split()

plat = platform.system()
bits = platform.architecture()[0]
mach = platform.machine()
vers = "%d.%d"%(sys.version_info[:2])
tmpdir = "%s_%s_%s_%s"%(plat, bits, mach, vers)
# Hopefully this keeps thing separate for ppc vs AMD64 etc in a build folder.
safelibname = "cImageD11_"+tmpdir+"_safe"
fastlibname = "cImageD11_"+tmpdir+"_fast"

compiler = None
for a in sys.argv:
    if "mingw32" in a:
        compiler = "mingw32"

def getfastarg(args):
    cc = distutils.ccompiler.new_compiler( verbose=1 , compiler=compiler )
    with open("dummy.c","w") as cfile:
        cfile.write("\n")
    farg = []
    if platform.machine in ("x86_64", "AMD64"):
        poss = ("-mavx2", "-mtune=native" )
    else:
        poss = ("-mtune=native",)
    for a in (
        try:
            cc.compile(["dummy.c",], output_dir=".",extra_preargs=args+[a,])
            farg.append(a)
        except:
            pass
    print("Fast args are",farg)
    return farg
    
        
if plat == "Linux" or compiler == "mingw32":
    arg=["-O2", "-fopenmp", "-fPIC", "-std=c99" ]
    fa =  getfastarg(arg)
    fastarg = arg + fa
    # link args
    lfastarg = arg + fa
elif plat == "Windows": # Needs to be MSVC for now. 
    arg=["/O2", "/openmp" ]
    # the /arch switches are ignored by the older MSVC compilers
    fastarg = arg + ["/arch:AVX2",]
    lfastarg = arg + ["/arch:AVX2",]
else:
    fastarg = lfastarg = arg = [ ]

def run_cc( cc, flags, libname ):
    objs = cc.compile( sources , 
                       output_dir=libname.replace("cImageD11_",""),
                       extra_preargs = flags )
    ok = cc.create_static_lib( objs, libname, output_dir="." )
    return libname

def write_docs( inp, outf ):
    """ One single block of !DOC per item, first word is key
    """
    with open(inp , "r") as pyf:
        fname = None
        docs = {}
        for line in pyf.readlines():
            if line.startswith("!DOC"):
                if fname is not None:
                    docs[fname] += line[5:] 
                else:
                    words = line.split()
                    fname = words[1]
                    docs[fname] = " ".join(words[2:]) + "\n"
            else:
                fname = None
    with open(outf, "w") as docf:
        docf.write('\n"""Autogenerated by src/bldlib.py. Edit in src/cImageD11_interface.pyf please"""\n')
        keys = list(docs.keys())
        keys.sort()
        for fname in keys:
            docf.write( '%s = """%s"""\n'%(fname, docs[fname]))
        docf.write("__all__ = [\n" + ",\n".join(['    "%s"'%(k) for k in keys ])+  "]")
        

def make_pyf( inp, name ):
    out = open(name+".pyf", "w")
    out.write("python module %s\n"%(name))
    pyf = open(inp , "r").read() 
    out.write( pyf )
    out.write("end python module %s\n"%(name))
    out.close()

def docs():
    write_docs( "cImageD11_interface.pyf", os.path.join("..","ImageD11src", "cImageD11_docstrings.py"))


def main():
    cc = distutils.ccompiler.new_compiler( verbose=1 , compiler=compiler )
    cc.add_include_dir( "." )
    docs()
    make_pyf( "cImageD11_interface.pyf", "cImageD11_safe")
    safelib = run_cc(cc, arg, safelibname )
    make_pyf( "cImageD11_interface.pyf", "cImageD11_fast")
    fastlib = run_cc(cc, fastarg, fastlibname )
    return 0


if __name__=="__main__":
    main()
