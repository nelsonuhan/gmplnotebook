# GMPL Notebook: A GMPL/MathProg Kernel for Jupyter

## Usage

Take a look at these [example notebooks](https://github.com/nelsonuhan/gmplnotebookexamples) for details on how to use GMPL Notebook &mdash; no installation required, thanks to [Binder](http://mybinder.org)!


## Dependencies

GMPL Notebook has been tested with

* Jupyter 4.2.0 
* Python 3.5.2
* MetaKernel 0.14
* PyGLPK 0.4.2, available from [@bradfordboyle](https://github.com/bradfordboyle/pyglpk)
* GLPK 4.60

## Installation

First, make sure you have a working installation of GLPK. For example, on macOS, this can be accomplished with [Homebrew](http://brew.sh) by:

```
brew update
brew tap homebrew/science
brew install glpk
```

(I will eventually include instructions on how to install GLPK on other operating systems.)

Next, install PyGLPK - note that the version on PyPI is outdated:

```
pip install https://github.com/bradfordboyle/pyglpk/zipball/master
```

Then, install GMPL Notebook:

```
pip install gmplnotebook
python -m gmplnotebook install --user
```

GMPL/MathProg should now appear as an option when creating new notebooks in Jupyter.