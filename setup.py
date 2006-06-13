#!/usr/bin/env python
#
# To build and/or install PyNGL:
#
#   python setup.py install
#
# There are three environment variables, that if set, will change
# the behavior of this script:
#
#    USE_NUMPY     - Create a Numpy version of PyNGL
#    USE_CVS         Use CVS to get the latest version of the pynglex files.
#    INCLUDE_PYNIO - Copy over PyNIO files from PyNIO installed location.
#
import sys,os
import shutil
import fileinput
import re
import tempfile

from distutils.core import setup, Extension

#
# Determine whether we want to build a Numeric or Numpy version
# of PyNGL.
#
try:
  path = os.environ["USE_NUMPY"]
  HAS_NUM = 2
except:
  HAS_NUM = 1

#
# Should we copy over the PyNIO files?
#
try:
  path = os.environ["INCLUDE_PYNIO"]
  include_pynio = True
except:
  include_pynio = False

#
# Should we use CVS for getting the latest pynglex examples?
#
try:
  path = os.environ["USE_CVS"]
  use_cvs = True
except:
  use_cvs = False
   
# Get version info.

execfile('pyngl_version.py')
pyngl_version = version

if HAS_NUM == 2:
  DMACROS =  [('NeedFuncProto', None),('USE_NUMPY',None)]
  print '====> building with numpy/arrayobject.h'
else:
  DMACROS =  [('NeedFuncProto',None)]
  print '====> building with Numeric/arrayobject.h'

#
# Get the root of where PyNGL will live, and where the extra PyNGL
# data files (fontcaps, graphcaps, map databases, example
# scripts, etc) will be installled.
#
pkgs_pth        = os.path.join(sys.prefix, 'lib', 'python'+sys.version[:3],
                               'site-packages')
python_bin_dir  = os.path.join(sys.prefix,'bin')
pyngl_dir       = os.path.join(pkgs_pth, os.path.join('PyNGL'))
pynio_dir       = os.path.join(pkgs_pth, os.path.join('PyNIO'))
pyngl_ncarg_dir = os.path.join(pyngl_dir, os.path.join('ncarg'))
pyngl_data_dir  = os.path.join(pyngl_ncarg_dir, 'data')

#
#
# Get root and various other directories of installed files.
#
ncl_root      = os.getenv("NCARG_ROOT")
ncl_bin       = os.path.join(ncl_root,'bin')
ncl_lib       = os.path.join(ncl_root,'lib')
ncl_inc       = [os.path.join(ncl_root,'include')]
ncl_ncarg_dir = os.path.join(ncl_lib,'ncarg')
ncl_data_dir  = os.path.join(ncl_ncarg_dir,'data')

#
# Get the list of pynglex *.py and *.res files. You have a choice of
# checking out a new directory from CVS, or using the "examples" directory.
# If you use the "examples" directory, make sure it doesn't have 
# any extraneous files.
#
pynglex_dir = "Scripts"
os.system("/bin/rm -rf " + pynglex_dir)
if use_cvs:
  os.system("cvs co pynglex")
  pynglex_files = os.listdir(pynglex_dir)
#
# Remove everything but *.py and *.res files from the list of files.
#
  pynglex_files.remove("yMakefile")
  pynglex_files.remove("CVS")
  pynglex_files.remove("pynglex")
else:
#
# Create a Scripts directory and copy the .py and .res files
# from the ../examples directory into the Scripts directory.
# The executable ../examples/pynglex must also be copied.
#
  all_pynglex_files = os.listdir("../examples")
  os.system("mkdir Scripts")
  pynglex_files = []
  for file in all_pynglex_files:
    if (file[-3:] == ".py" or file[-4:] == ".res"):
      pynglex_files.append(file)
      os.system("cp ../examples/" + file + " Scripts")
  os.system("cp ../examples/pynglex Scripts")

#
# Prepend the full directory path leading to files.
#
for i in xrange(len(pynglex_files)):
  pynglex_files[i] = os.path.join(pynglex_dir,pynglex_files[i])

####################################################################
#                                                                  #
#  Begin code for mods to the example sources for NumPy support.   #
#                                                                  #
####################################################################
#
# Modify the example sources appropriately if NumPy support is
# requested.  For all examples except "metrogram.py," "scatter1.py," 
# and "ngl09p.py" this is just a matter of replacing "import Numeric"
# with "import numpy as Numeric".  The cases of "meteogram.py"
# and "ngl09p.py" are handled as special cases in the if block below; 
# "scatter1.py" is then handled separately.
#
if (HAS_NUM == 2):
  for line in fileinput.input(pynglex_files,inplace=1):
    if (re.search("^import Numeric",line) != None):
      print "import numpy as Numeric"
    elif (os.path.basename(fileinput.filename()) == "meteogram.py" and  \
        re.search("typecode()",line) != None):
      print line.replace("typecode()","dtype.char"),
    elif (os.path.basename(fileinput.filename()) == "ngl09p.py" and     \
        re.search("import MA",line) != None):
      print line.replace("import MA","import numpy.core.ma as MA"),
    elif (os.path.basename(fileinput.filename()) == "ngl09p.py" and     \
        re.search("MA.Float0",line) != None):
      print line.replace("MA.Float0","dtype=float"),
    else:
      print line,
  for file in pynglex_files:
    if (os.path.basename(file) == "scatter1.py"):
      scatter_src = open(file,"r")
      scatter_new = tempfile.TemporaryFile()

      while(1):
        line = scatter_src.readline()
        if (line == ""):
          break
        elif (re.search("From Scientific import",line) != None):
          while (re.search("^from",line) == None):
            line = scatter_src.readline()
          line = scatter_src.readline()
        elif (re.search("Put the data",line) != None):
          while (re.search("^plot =",line) == None):
            line = scatter_src.readline()
          line = scatter_src.readline()
          scatter_new.write("""#
#  Do a quadratic least squares fit.
#
npoints = len(x)
a = Numeric.zeros([npoints,3],Numeric.Float32)
for m in xrange(npoints):
  a[m,0] = 1.
  for j in xrange(1,3):
    a[m,j] = x[m]*a[m,j-1]
c = (Numeric.linalg.lstsq(a,y,rcond=1.e-15))[0]

#
#  Draw the least squares quadratic curve.
#
num  = 301
delx = 1000./num
xp    = Numeric.zeros(num,Numeric.Float0)
yp    = Numeric.zeros(num,Numeric.Float0)
for i in xrange(num):
  xp[i] = float(i)*delx
  yp[i] = c[0]+c[1]*xp[i]+c[2]*xp[i]*xp[i]
plot = Ngl.xy(wks,xp,yp,resources) # Draw least squares quadratic.

""")
        scatter_new.write(line)

#
#  Write the new NumPy source back over the Numeric source.
#
      scatter_src.close()
      scatter_src = open(file,"w+")
      scatter_new.seek(0)
      for line in scatter_new.readlines():
        scatter_src.write(line)
      scatter_src.close()
      scatter_new.close()
########################################################
#                                                      #
#  End of mods to example sources for NumPy support.   #
#                                                      #
########################################################

#
# Gather up the executables we want to install as part of PyNGL.
# Get the NCAR Graphics executables from the installed location
# ($NCARG_ROOT).
#
bin_files  = ["ctrans","med","psplit"]
for i in xrange(len(bin_files)):
  bin_files[i] = os.path.join(ncl_bin,bin_files[i])
bin_files.append(os.path.join(pynglex_dir,'pynglex'))

#
# Location of system and NCARG include files and libraries.
#
# To include additional libraries, you can add them here, or, on
# the UNIX command line, you can type something like:
#
#  python setup.py build_ext -L/sw/lib
#
# You will then have to type "python setup.py install" separately to
# install the package.
#
ncl_and_sys_lib_paths = [ncl_lib, "/usr/X11R6/lib"]

if sys.platform == "darwin":
    ncl_and_sys_lib_paths.append('/sw/lib')

#
# List all the extra files that need to be installed with PyNGL.
# These files include example PyNGL scripts, data for the scripts,
# fonts, map databases, colormaps, and other databases.
#
# os.listdir doesn't include the relative directory path
#
# We need a way to recursively list all files in the "ncarg"
# directory, rather than having to list each directory 
# individually. I think "os.walk" might be something to look into
# here.
#
asc_files      = os.listdir(os.path.join(ncl_data_dir,'asc'))
dbin_files     = os.listdir(os.path.join(ncl_data_dir,'bin'))
cdf_files      = os.listdir(os.path.join(ncl_data_dir,'cdf'))
grb_files      = os.listdir(os.path.join(ncl_data_dir,'grb'))
colormap_files = os.listdir(os.path.join(ncl_ncarg_dir,'colormaps'))
fontcap_files  = os.listdir(os.path.join(ncl_ncarg_dir,'fontcaps'))
graphcap_files = os.listdir(os.path.join(ncl_ncarg_dir,'graphcaps'))
database_files = os.listdir(os.path.join(ncl_ncarg_dir,'database'))
if os.path.exists(os.path.join(ncl_ncarg_dir,'database','rangs')):
  database_files.remove("rangs")

#
# os.listdir doesn't include the relative directory path, so add it
# back here.
#
for i in xrange(len(asc_files)):
  asc_files[i] = os.path.join(ncl_data_dir,'asc',asc_files[i])

for i in xrange(len(dbin_files)):
  dbin_files[i] = os.path.join(ncl_data_dir,'bin',dbin_files[i])

for i in xrange(len(cdf_files)):
  cdf_files[i] = os.path.join(ncl_data_dir,'cdf',cdf_files[i])

for i in xrange(len(grb_files)):
  grb_files[i] = os.path.join(ncl_data_dir,'grb',grb_files[i])

for i in xrange(len(colormap_files)):
  colormap_files[i] = os.path.join(ncl_ncarg_dir,'colormaps',colormap_files[i])

for i in xrange(len(database_files)):
  database_files[i] = os.path.join(ncl_ncarg_dir,'database',database_files[i])

for i in xrange(len(fontcap_files)):
  fontcap_files[i] = os.path.join(ncl_ncarg_dir,'fontcaps',fontcap_files[i])

for i in xrange(len(graphcap_files)):
  graphcap_files[i] = os.path.join(ncl_ncarg_dir,'graphcaps',graphcap_files[i])

res_file = 'sysresfile'

#
# Gather up the *.py module files.
#
py_files= ['Ngl.py','hlu.py','__init__.py','pyngl_version.py']

#
# If INCLUDE_PYNIO is set, then make sure we include the PyNIO files.
#

pynio_files = []
if include_pynio:
  pynio_files = ['Nio.py', 'pynio_version.py', 'nio.so']
  for i in xrange(len(pynio_files)):
    pynio_files[i] = os.path.join(pynio_dir,pynio_files[i])

#
# List the extra arguments and libraries that we need on the load line.
#
EXTRA_LINK_ARGS = ""
LIBRARIES = ["nfpfort", "hlu", "ncarg", "ncarg_gks", "ncarg_c", "ngmath", "X11", "g2c"]
INCLUDE_PATHS = ncl_inc

if (HAS_NUM == 2):
  INCLUDE_PATHS.insert(0,os.path.join(pkgs_pth,"numpy/core/include"))

#
# The IRIX system is problematic, because distuils uses "-all" as one of the
# options to "ld".  This causes all objects from all archives to be linked
# in, and hence you get some undefined references from libraries like the
# Spherepack library, which you shouldn't need (yet). The solution around this
# is to use "-notall" in conjunction with "-all", but the "extra_link_args"
# parameter that you are supposed to use puts this at the *end* of the ld
# line, which doesn't work. It needs to be at the beginning.
#
# So, for now, on tempest, I'm having to build the darn *.so file
# by hand with:
#
# ld -64 -shared -all build/temp.irix64-6.5-2.4/Helper.o \
#   build/temp.irix64-6.5-2.4/hlu_wrap.o build/temp.irix64-6.5-2.4/gsun.o \
#  -L/fis/scd/home/ncargd/dev/opt/IRIX64_6.5_mips4_64/lib -L/usr/X11R6/lib \
#  -lnfpfort -lhlu -lncarg -lncarg_gks -lncarg_c -lngmath -lX11 -lftn -lm \
#  -o build/lib.irix64-6.5-2.4/PyNGL/_hlu.so -notall
#
# I use the build_on_irix64 script for this. Run the build_on_irix64 script
# instead of this setup.py script.
#

if sys.platform == "irix6-64":
    print "Warning: This setup.py file will not work on an irix6-64 system."
    print "Use 'build_on_irix64' instead."
#
# This is for later, if we ever get this to work under IRIX.
#
    LIBRARIES.remove('g2c')
    LIBRARIES.append('ftn')
    LIBRARIES.append('m')
    EXTRA_LINK_ARGS = ['-notall']

if sys.platform == "aix5":
    LIBRARIES.remove('g2c')
    LIBRARIES.append('xlf90')

#
# Here's the setup function.
#
setup (name = "PyNGL",
       version = pyngl_version,
       author="Fred Clare and Mary Haley",
       description = "2D visualization library",
       long_description = "PyNGL is a Python language module designed for publication-quality visualization of data. PyNGL stands for 'Python Interface to the NCL Graphics Libraries,' and it is pronounced 'pingle.'",
       url = "http://www.pyngl.ucar.edu/",
       package_dir = { 'PyNGL' : ''},
       data_files = [(os.path.join(pyngl_ncarg_dir,'pynglex'),pynglex_files),
                     (pkgs_pth,                ["PyNGL.pth"]),
                     (python_bin_dir,bin_files),
                     (os.path.join(pkgs_pth,'PyNGL'), py_files),
                     (os.path.join(pyngl_data_dir,'asc'), asc_files),
                     (os.path.join(pyngl_data_dir,'bin'), dbin_files),
                     (os.path.join(pyngl_data_dir,'cdf'), cdf_files),
                     (os.path.join(pyngl_data_dir,'grb'), grb_files),
                     (os.path.join(pyngl_ncarg_dir,'colormaps'),colormap_files),
                     (os.path.join(pyngl_ncarg_dir,'database'), database_files),
                     (os.path.join(pyngl_ncarg_dir,'fontcaps'), fontcap_files),
                     (os.path.join(pyngl_ncarg_dir,'graphcaps'),graphcap_files),
                     (pyngl_dir,pynio_files),
                     (pyngl_ncarg_dir, [res_file])],
       ext_package = 'PyNGL',
       ext_modules = [Extension('_hlu', 
                           ['Helper.c','hlu_wrap.c','gsun.c'],
                            define_macros = DMACROS,
                            extra_link_args = EXTRA_LINK_ARGS,
                            include_dirs = INCLUDE_PATHS,
                            library_dirs = ncl_and_sys_lib_paths,
                            libraries = LIBRARIES)]
      )
