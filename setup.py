import setuptools
import pypandoc

long_description = pypandoc.convert('README.md', 'rst')

setuptools.setup(
    name='gmplnotebook',
    version='0.1.2',
    description='A GMPL/MathProg kernel+extension for Jupyter',
    long_description=long_description,
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
