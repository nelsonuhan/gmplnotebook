# GMPL Notebook: A GMPL/MathProg Kernel for Jupyter

## Usage

Take a look at these [example notebooks](https://github.com/nelsonuhan/gmplnotebookexamples) for details on how to use this kernel -- no installation required, thanks to [Binder](http://mybinder.org)!


## Dependencies

This kernel has been tested with

* Jupyter 4.2.0 with Python 3.5.2
* MetaKernel 0.14
* PyGLPK 0.4.2, available from [@bradfordboyle](https://github.com/bradfordboyle/pyglpk)
* GLPK 4.60

## Installation

First, install PyGLPK - note that the version on PyPI is outdated:

```
pip install https://github.com/bradfordboyle/pyglpk/zipball/master
```

PyGLPK depends on an existing installation of GLPK. On macOS, this can be accomplished by:

```
brew update
brew tap homebrew/science
brew install glpk
```

(I will post installation notes for other operating systems.)

Then, install this kernel:

```
pip install gmplnotebook
python -m gmplnotebook --user
```

GMPL/MathProg should now appear as an option when creating new notebooks in Jupyter.