## How to set package developer mode (also call editable mode on pip)

*After set this, we can directly test effect of editing a package files
without need to fully reinstall it.*

Turn on develop mode (add current package files to python path):

```bash
pip install --editable .
```
Turn off:

```bash
pip uninstall pyHMI
```
View the current python path:

```bash
python -c 'import sys; print(sys.path)'
```
