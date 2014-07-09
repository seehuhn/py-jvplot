"""distutils/setuptools configuration for the jvplot package"""

from setuptools import setup

import jvplot

setup(
    name='JvPlot',
    version=jvplot.__version__,
    packages=['jvplot'],

    install_requires=['cairocffi'],
    setup_requires=['nose>=1.0'],

    # metadata for upload to PyPI
    author='Jochen Voss',
    author_email='voss@seehuhn.de',
    description='programmatically generate plots using Cairo',
    keywords='cairo graphics plotting',
    url='http://github.com/seehuhn/jvplot',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 or later' +
        ' (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Scientific/Engineering :: Visualization',
    ]
)
