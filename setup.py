from setuptools import setup

setup(
    name='gmplnotebook',
    version='0.1',
    description='A GMPL/MathProg kernel+extension for Jupyter',
    url='https://github.com/nelsonuhan/gmplnotebook',
    author='Nelson Uhan',
    author_email='nelson@uhan.me',
    license='GNU GPLv3',
    packages=['gmplnotebook'],
    package_data={
        '': ['kernel.js'],
    },
    install_requires=['glpk>=0.4.2', 'metakernel', 'jupyter'],
)
