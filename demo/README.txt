Setting PYTHONPATH
==================

Before running any scripts in the Roundup project, 
ensure that the PYTHONPATH environment variable includes the directory containing the `roundup` package. 
This is necessary for proper module imports. You can set the PYTHONPATH as follows:

```bash
export PYTHONPATH=/path/to/Roundup:$PYTHONPATH