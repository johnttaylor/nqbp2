NQBP stands for (N)ot (Q)uite (B)env - (P)ython.

NQBP (Gen2) is a multi-host build engine designed for:

    - C, C++, and assembler builds
    - Embedded development (but not limited to)
    - Minimal overhead to the developer, i.e. no makefiles required
    - Speed.  Uses [Ninja](https://ninja-build.org/) as the underlying build system
    - Full dependency checking and incremental builds
    - Command line based
    - Supporting many Compiler toolchains
    - Source code resusablilty, i.e. NQBP assumes that code is/will be shared across many projects.
    - Resusablilty of Compiler toolchains, i.e once a particular compiler toolchain has been created/defined - it can be reused across an unlimited number of projects.
    - Very effective on small to medium size projects
    - Supports building in Outcast [http://www.integerfox.com/outcast]

Gen2 NQBP was created to specially address the lack of dependency checking in _classic_
[NQBP](https://github.com/johnttaylor/nqbp).

Documentation is located in the top/ directory and/or available at: http://www.integerfox.com/nqbp2.

NQBP is licensed with a BSD licensing agreement (see the `top/` directory).
