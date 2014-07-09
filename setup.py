# setup.py - distutils/setuptools configuration for the JvPlot package
# Copyright (C) 2014 Jochen Voss <voss@seehuhn.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

"""distutils/setuptools configuration for the JvPlot package"""

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
    url='http://github.com/seehuhn/py-jvplot',
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
