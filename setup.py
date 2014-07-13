#-*- coding:utf-8 -*-
'''
Created on 10 juil. 2014

@author: youen
'''

from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='cukpab',
      version='0.1',
      description='simple backup manager',
      long_description=readme(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Backup :: Command Line',
      ],
      url='http://github.com/youen/cukpab',
      author='Youen Péron',
      author_email='youen.peron@gmail.com',
      license='MIT',
      packages=['cukpab'],
      install_requires=[
          'simplejson',
          'pyinotify',
          'pymongo'
      ],
      include_package_data=True,
      test_suite='nose.collector',
      tests_require=['nose'],
      entry_points = {
        'console_scripts': ['cukpab=cukpab.cli:main'],
      },
      zip_safe=False)