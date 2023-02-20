#!/usr/bin/python3
""" Top level entry point for NQBP (i.e. called by the project-being-built's mk.py) """

#=============================================================================
# ENVIRONMENT VARIABLES
# ---------------------
#   REQUIRED:
#     NQBP_BIN          Path to the directory of where (and/or which version)
#                       of the NQBP Python package to be used
#
#   OPTIONAL:
#=============================================================================

#
from json import tool
import sys   
import os
import logging
import time

#
from .docopt.docopt import docopt
from .base import ToolChain
from .output import Printer
from .ninja_synatx import Writer

from . import base
from . import utils
import multiprocessing

    
# Globals
from .my_globals import NQBP_WORK_ROOT
from .my_globals import NQBP_PKG_ROOT
from .my_globals import NQBP_TEMP_EXT
from .my_globals import NQBP_VERSION
from .my_globals import NQBP_PRJ_DIR
from .my_globals import NQBP_WRKPKGS_DIRNAME
from .my_globals import NQBP_NAME_SOURCES
from .my_globals import NQBP_PRE_PROCESS_SCRIPT
from .my_globals import NQBP_PRE_PROCESS_SCRIPT_ARGS
from .my_globals import NQBP_NAME_LIBDIRS



# 
usage = """ 
(N)ot (Q)uite (B)env/(P)ython Build Script
===============================================================================
Usage: nqbp [options] [-b variant] 
       nqbp [options] [-b variant] -d DIR
       nqbp [options] [-b variant] -f FILE
       nqbp [options] [-b variant] -s DIR [-e DIR]
       nqbp [options] [-b variant] -m [-d DIR | -f FILE]

Arguments:
  -b variant       Builds the specified configuration/variant instead of the 
                   release build. What 'variants' are available is Toolchain 
                   specific. The default is variant is determined by the
                   mytoolchain.py script.
  --try variant    Same as the '-b' option, except that if the variant does not
                   exist - the script does not report a failure on exit.
  --bld-all        Builds all variants.  Does NOT build variants that start 
                   with a leading '_'.
  -g               Debug build (default is release build.
  -v               Display Compiler/linker options.
  --bldnum M       Passes 'M' as build number information for the build. 
                   [Default: 0].          
  --def1 SYM1      Defines (as a compiler option) the preprocessor 'SYM1'.
  --def2 SYM2      Defines (as a compiler option) the preprocessor 'SYM2'.
  --def3 SYM3      Defines (as a compiler option) the preprocessor 'SYM3'.
  --def4 SYM4      Defines (as a compiler option) the preprocessor 'SYM4'.
  --def5 SYM5      Defines (as a compiler option) the preprocessor 'SYM5'.
  -z, --clean-all  Cleans ALL files for ALL build configurations and then exits
  --debug          Enables debug info internally to NQBP.
  --qry            Outputs the current project directory (does nothing else)
  --qry-and-clean  Combines '--qry' and '--clean-all' options into a single 
                   operation.
  --qry-blds       Displays the build 'variants' supported by the toolchain 
                   (no build is performed).
  --qry-dirs       Displays the list of directories (in order, for the selected
                   build variant) referenced in the libdirs.b file.
  --qry-dirs2      Same as --qry-dirs with the addition of the any source file
                   include/exclude info
  -h,--help        Display help.
  --version        Display version number.

"""

ninja_fname = "build.ninja"

#-----------------------------------------------------------------------------
def build( argv, toolchain ):

    # ensure that I am executing in the project directory
    os.chdir( NQBP_PRJ_DIR() )

    # Append options from optional environment variable
    rawinput = sys.argv[1:]
    NQBP_CMD_OPTIONS = os.environ.get('NQBP_CMD_OPTIONS')
    if ( NQBP_CMD_OPTIONS != None ):
        rawinput.extend( NQBP_CMD_OPTIONS.split(' '))

    # Process command line args...
    arguments = docopt(usage, argv=rawinput, version=NQBP_VERSION() )

    # Create printer (and tell the toolchain about it)
    printer = Printer();
    toolchain.set_printer( printer )

    # Does the specified variant exist
    if ( arguments['--try'] != None ):
        if ( not arguments['--try'] in toolchain.get_variants() ):
            printer.output( "Tried (and failed) to build a non-existent variant: {}".format(arguments['--try'] ))  
            sys.exit()

        # If the variant exists--> set build variant option
        else:
            arguments['-b'] = arguments['--try']

    # Set default build variant 
    if ( not arguments['-b'] ):
        arguments['-b'] = toolchain.get_default_variant()
    
    # Pre-build steps
    pre_build_steps( printer, toolchain, arguments )
    printer.debug( str(arguments) )
    
    # Process 'non-build' options
    if ( arguments['--qry-blds'] ):
        toolchain.list_variants()
        sys.exit()
    
    if ( arguments['--qry'] ):
        printer.output( NQBP_PRJ_DIR() )
        sys.exit()
       
    if ( arguments['--qry-and-clean'] ):
        printer.output( NQBP_PRJ_DIR() )
        toolchain.clean_all( arguments, silent=True )
        printer.remove_log_file()
        sys.exit()
    
    if ( arguments['--clean-all'] ):
        toolchain.clean_all( arguments )
        sys.exit()
        
    # Validate Compiler toolchain is set properly (ONLY after non-build options have been processed, i.e. don't have to have an 'active' toolchain for non-build options to work)
    toolchain.validate_cc()
            
    # Start the selected build(s)
    if ( arguments['--bld-all'] ):
        for b in toolchain.get_variants():
            if ( not b.startswith("_") ):
                do_build( printer, toolchain, arguments, b )
    else: 
        do_build( printer, toolchain, arguments, arguments['-b'] )        
            
           

#-----------------------------------------------------------------------------
def do_build( printer, toolchain, arguments, variant ):

    # Create the Ninja writer and empty ninja build file
    with open(ninja_fname, 'w') as ninja_file:
        nwriter = Writer( ninja_file )
        toolchain.set_ninja_writer( nwriter )

        # Set the build variant (Note: The method constructs the libdirs.b directory list)
        toolchain.pre_build( variant, arguments )

        # Output start banner
        if ( arguments['--qry-dirs'] == False ):
            start_banner(printer, toolchain)
         
        # Spit out handy-dandy debug info
        printer.debug( '# NQBP version   = ' + NQBP_VERSION() )
        printer.debug( '# NQBP_BIN       = ' + os.path.dirname(os.path.abspath(__file__)) )
        printer.debug( '# NQBP_WORK_ROOT = ' + NQBP_WORK_ROOT() )
        printer.debug( '# NQBP_PKG_ROOT  = ' + NQBP_PKG_ROOT() )
        printer.debug( '# Project Dir    = ' + NQBP_PRJ_DIR() )
        
        # Display my full set of directories
        if ( arguments['--qry-dirs'] ):
            for dir, flag in toolchain.libdirs:
                d,s,sl = dir
                printer.output( "{:<5}  {}".format( str(flag), d)  )
            return

        # Display my full set of directories with Source include/exclude info
        if ( arguments['--qry-dirs2'] ):
            for dir, flag in toolchain.libdirs:
                d,s,sl = dir
                if ( s == None or sl == None ):
                    printer.output( "{:<5}  {}".format( str(flag), d)  )
                else:
                    printer.output( "{:<5}  {}  {}{}{} {} ".format( str(flag), d, s,s,s, sl)  )
            return
        
                            
        # Generate ninja content for each libdirs.b directory
        for d in toolchain.libdirs:
            build_single_directory( printer, arguments, toolchain, d[0], d[1], NQBP_PKG_ROOT(), NQBP_WORK_ROOT(), NQBP_WRKPKGS_DIRNAME(), NQBP_PRJ_DIR(), NQBP_PRE_PROCESS_SCRIPT(), NQBP_PRE_PROCESS_SCRIPT_ARGS() )

        # Generate ninja content for the Build project dir
        utils.run_pre_processing_script( printer, NQBP_PRJ_DIR(), NQBP_WORK_ROOT(), NQBP_PKG_ROOT(), NQBP_PRJ_DIR(), NQBP_PRE_PROCESS_SCRIPT(), NQBP_PRE_PROCESS_SCRIPT_ARGS(),  verbose=arguments['-v'] )
        files = utils.get_files_to_build( printer, toolchain, '.', NQBP_NAME_SOURCES() )
        toolchain._ninja_writer.newline()
        toolchain._ninja_writer.comment( "Project Directory:" )
        toolchain._ninja_writer.newline()
        objfiles = []
        for f in files:
            objfiles.append( toolchain.cc( arguments, '.' + os.sep + f, '.' ) )
        
        # Generate ninja content for the link
        #inf = open( NQBP_NAME_LIBDIRS(), 'r' )
        #link_libdirs = toolchain.pre_link( arguments, inf, 'local', variant )
        #inf.close()
        #toolchain.link( arguments, link_libdirs, 'local', variant )
                            
    # TODO: INVOKE NINJA

    # Output end banner
    end_banner(printer, toolchain)
     
#-----------------------------------------------------------------------------
def pre_build_steps(printer, toolchain, arguments ):

    # Enable verbose logging (if selected)
    if ( arguments['-v'] ):
        printer.enable_verbose()
    
    # Enable debugging logging (if selected) note: order is important here -->must follow enable.verbose()    
    if ( arguments['--debug'] ):
        printer.enable_debug()
        
        
            
#-----------------------------------------------------------------------------
def start_banner(printer, toolchain):

    # 
    start = int( toolchain.get_build_time() ) 
    printer.output('')
    printer.output( '=' * 80 );
    printer.output( '= START of build for:  {}'.format( toolchain.get_final_output_name()) )
    printer.output( '= Project Directory:   {}'.format( NQBP_PRJ_DIR() ))
    printer.output( '= Toolchain:           {}'.format( toolchain.get_ccname()) )
    printer.output( '= Build Configuration: {}'.format( toolchain.get_build_variant()) )
    printer.output( '= Begin (UTC):         {}'.format( time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())) )
    printer.output( '= Build Time:          {:d} ({:x})'.format( start, start ) )
    printer.output( '=' * 80 );

        
#-----------------------------------------------------------------------------
def end_banner(printer, toolchain):

    # Calculate elasped time in hhh mm ss    
    elasped = int(time.time() - toolchain.get_build_time()) 
    mm      = (elasped // 60) % 60
    hhh     = elasped // (60*60)
    ss      = elasped % 60
    
    # 
    printer.output( '=' * 80 );
    printer.output( '= END of build for:    {}'.format( toolchain.get_final_output_name()) )
    printer.output( '= Project Directory:   {}'.format( NQBP_PRJ_DIR() ))
    printer.output( '= Toolchain:           {}'.format( toolchain.get_ccname()) )
    printer.output( '= Build Configuration: {}'.format( toolchain.get_build_variant()) )
    printer.output( '= Elapsed Time (hh mm:ss): {:02d} {:02d}:{:02d}'.format(hhh, mm, ss) )
    printer.output( '=' * 80 );

    
#-----------------------------------------------------------------------------
def build_single_directory( printer, arguments, toolchain, dir, entry, pkg_root, work_root, pkgs_dirname, prj_dirname, preprocess_script, preprocess_args ):
   
    srcpath, display, dir = utils.derive_src_path( pkg_root, work_root, pkgs_dirname, entry, dir )

    # Banner 
    printer.output( "=====================" )
    printer.output( "= Building Directory: " + display )

    # Debug info
    printer.debug( "#   entry  = {}".format( entry ) )
    printer.debug( "#   objdir = {}".format( dir[0] ) )
    printer.debug( "#   srcdir = {}".format( srcpath ) )

    
    # verify source directory exists
    if ( not os.path.exists( srcpath ) ):
        printer.output( "")
        printer.output( "ERROR: Build Failed - directory does not exist: " )
        printer.output( "" )
        sys.exit(1)
        
    # Check/run the PreProcessing script
    utils.run_pre_processing_script( printer, srcpath, work_root, pkg_root, prj_dirname, preprocess_script, preprocess_args, verbose=arguments['-v'] )

    # Get/Construct the source file list and filter it (if needed) for the specified directory
    files = utils.get_and_filter_files_to_build( printer, toolchain, dir, srcpath, NQBP_NAME_SOURCES() )
    
    toolchain._ninja_writer.newline()
    toolchain._ninja_writer.comment( f"Directory: {srcpath}" )
    toolchain._ninja_writer.newline()

    # compile 
    objfiles = []
    for f in files:
        objfiles.append( toolchain.cc( arguments, srcpath + os.sep + f, dir[0] ) )

    # build archive
    toolchain.ar( arguments, objfiles, dir[0]  )
        
