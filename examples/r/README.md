# Software Centre

RStudio is available in the Software Centre on YOYO computers. This software has the ability to install and manage R packages.

To make virtual environments, use [renv](https://rstudio.github.io/renv/).

# Virtual environment

Create a Conda virtual environment with the prerequisite packages:

```bash
conda create --name airbodsr r-base r-essentials r-RPostgres r-keyring --channel conda-forge
conda install rstudio
```

