# GMPL Notebook: A GMPL/MathProg Kernel for Jupyter

## Usage

Take a look at these [example notebooks]() for details on how to use this kernel.

## Dependencies

This kernel has been tested with 

* Jupyter 4.2.0 with Python 3.5.2
* MetaKernel 0.10
* PyGLPK 0.4.2, available from [@bradfordboyle](https://github.com/bradfordboyle/pyglpk)
* GLPK 4.60

## Installation

First, install PyGLPK - note that the version on PyPI is outdated:

```
pip install https://github.com/bradfordboyle/pyglpk/zipball/master
```

Then, install this kernel:

```
pip install https://github.com/nelsonuhan/gmplnotebook/zipball/master
python -m gmplnotebook --user
```

GMPL/MathProg should now appear as an option when creating new notebooks in Jupyter. 