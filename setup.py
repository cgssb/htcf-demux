from distutils.core import setup

setup(
    name='HTCF Demux',
    version='0.1',
    packages=['htcfdemux',],
    license='MIT',
    scripts=('htcfdemux/htcf-demux',),
    #long_description=open('README.txt').read(),
)
