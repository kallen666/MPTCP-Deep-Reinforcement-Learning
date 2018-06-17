from distutils.core import setup, Extension

setup(name='mpsched',
      ext_modules=[
          Extension('mpsched',
                    ['mpsched.c'],
                    include_dirs=['/usr/src/linux-headers-4.4.110-mptcp+/include/uapi', '/usr/src/linux-headers-4.4.110-mptcp+/include', '/usr/include/python3.5m'],
                    define_macros=[('NUM_SUBFLOWS', '2'), ('SOL_TCP', '6')]
                    )
      ])
