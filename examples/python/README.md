You'll need to install Python, which is available via the Software Centre on YOYO computers.

# Create virtual environment

## Conda

See the [Conda docs](https://docs.conda.io/en/latest/). Create a new environment and install the necessary packages:

```bash
conda create --name airbods pandas sqlalchemy
conda activate airbods
```

## venv

See the Python documentation [Virtual Environments and Packages](https://docs.python.org/3/tutorial/venv.html).

```bash
# Create new environment
python3 -m venv airbods
# Activate the environment
source airbods/bin/activate
python -m pip install pandas sqlalchemy
```

# Usage

```bash
python airbods.py
```

