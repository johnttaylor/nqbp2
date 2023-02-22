NQBP stands for (N)ot (Q)uite (B)env - (P)ython.

NQBP (Gen2) is a multi-host build engine designed for:

- C, C++, and assembler builds
- Embedded development (but not limited to)
- Minimal overhead to the developer, i.e. no makefiles required
- Speed.  Uses [Ninja](https://ninja-build.org/) as the underlying build system
- Full dependency checking and incremental builds
- Command line based
- Supporting many Compiler toolchains
- Source code resusablilty, i.e. NQBP assumes that code is/will be shared across many rojects.
- Resusablilty of Compiler toolchains, i.e once a particular compiler toolchain has beencreated/defined - it can be reused across an unlimited number of projects.
- Very effective on all sizes of projects


Gen2 NQBP was created to specially address the lack of dependency checking in _classic_
[NQBP](https://github.com/johnttaylor/nqbp).  This was done by incorporating the
[__Ninja__](https://ninja-build.org/) build tool to perform the actual builds.

Documentation is located in the top/ directory and/or available at: http://www.integerfox.com/nqbp2.

NQBP is licensed with a BSD licensing agreement (see the `top/` directory).

## Differences between NQBP classic and NQBP Gen2
### Front End
The __front end has not__ change. How to specify what source code to build 
(e.g `libdirs.b`, `sources.b`, etc.) and how project specific build flags and options 
are specified (e.g. `mytoolchain.py`) has not changed.

### Compatibility
NQBP Gen2 is __mostly backwards compatible__ with NQBP classic.  In this case 
_mostly_ means that any existing project/test that uses NQBP classic can use
NQBP Gen2 __without__ modifying any of the files NQBP files (e.g. `nqbp.py`,
`mytoolchain.py`, `libdirs.b`, etc.) in a project/test directory.  All that
this is required is that the `NQBP_BIN` path be set to point to the NQBP Gen2
directory.  __However__, you will be required to port your custom toolchain files
to work with NQBP Gen2.

__Note__: You will need to install [ninja](https://ninja-build.org/) on your PC 
and update the command path to include the ninja directory.  Binaries are
available [here](https://github.com/ninja-build/ninja/releases)

To port an existing custom toolchain you will need to be familiar with _ninja_
tool and how it works (but you don't need to be expert or even advanced user
of ninja).  

Here is list of variables in the toolchain _class_ that have changed in their
usage and/or expected content.
```
self._ar_out
self._ar_opts
self._link_output
self._base_release.cflags   // Need to remove -D BUILD_TIME_UTC
self._rm                    // New
self._shell                 // New
```

Use the following Gen2 toolchains as a reference for when porting your toolchain.
- [Visual Studio](https://github.com/johnttaylor/nqbp2/blob/main/nqbplib/toolchains/windows/vc12/console_exe.py)
- [ARM Cortex M0 (Windows Host)](https://github.com/johnttaylor/nqbp2/blob/main/nqbplib/toolchains/windows/arm_gcc_rp2040/stdio_serial.py)

### Derived Object
NQBP Gen2 now generates/locates __all__ build/derived artifacts (e.g. `.o`, 
`.a`, `.exe`, `.bin`, etc.) under the build variant directory (e.g. `_win32`, `_posix64`, `_pico`, etc.).  

NQBP classic only stored the final outputs (`.exe`, `.bin`) in the build variant 
directory. It stored/located the object files and libraries in the project 
directory itself or in source-path-specific sub-directories.

### Performance
NQBP Gen2 is faster on a build-all than NQBP classic.  In my test Gen2 averages 
around ~25% faster.  The caveat here is that I don't any _really big_ projects to
determine if the speed improvement is due to less console IO for Gen2 or that `ninja` 
really is just faster.

### TODO
The toolchains listed below have been ported to NQBP Gen2 - but I have not verified
the toolchains (I no longer have the compilers installed on my PC).

- `nqbp2\nqbplib\toolchains\windows\arm_m4_arduino\nrf52_feather52.py`
- `nqbp2\nqbplib\toolchains\windows\avr_gcc_arduino\atmega328p_uno.py`
