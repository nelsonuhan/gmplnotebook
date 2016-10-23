from setuptools import setup

setup(
    name='gmplnotebook',
    version='0.1',
    description='A GNU MathProg (GMPL) kernel for Jupyter',
    url='http://nelson.uhan.me',
    author='Nelson Uhan',
    author_email='nelson@uhan.me',
    packages=['gmplnotebook'],
    package_data={
        '': ['kernel.js'],
    },
    install_requires=['glpk>=0.4.2', 'metakernel'],
)
