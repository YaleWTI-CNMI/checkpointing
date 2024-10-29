# Checkpointing Python library 

The checkpointing library (cpl) is designed to facilitate checkpointing for Python code running on a SLURM cluster. 
## Installation

```{bash}
pip install cpl@git+https://github.com/YaleWTI-CNMI/checkpointing
```

## Configuration File `cpl.yml`

By default, no email and log is configured. The default checkpointing file is `model_checkpoint.pt`, 
and there is no delay to start running user checkpointing function when a signal is caught.
All of these can be customized in the user configurable file `cpl.yml`.
```{bash}
email_server: mail.yale.edu
email_address: ping.luo@yale.edu
email_types:
  signal_caught: True
  user_handle_done: True

logfile: cpl.log
loglevel: INFO

delay: 50   # in minutes
checkpoint_fn: model_checkpoint.pt
```
## Class CPL

### Initialization

```{python}
from cpl import cpl
mycpl = cpl.CPL(sig=SIGTERM)
```
The `sig` parameter specifies the signal value that CPL will catch and process. The default value is `SIGTERM`. 

### Methods

```{python}
check(self, handle=_cpl_handler, delay=60, back=True, **kwargs)
```
**Description**

Check if a signal watched by the CPL instance is caught. If yes, process the signal. 

**Parameters**
- handler: a pointer, specifies a user function that will handle the signal. The default value is an internal handle that does nothing.
- delay: an integer, specifies for how long the CPL instance must wait after a signal is caught to call the user function.
- back: a bool, specifies if the control should return back to the caller immediately after the user function (the handler) is called, or it should stay until the process of the python program is terminated. 
- kwargs: a special parameter used in Python to pass a keyworded, variable-length argument list. It is used to pass arguments to the user function defined in the parameter `handle`. 

```{python}
get_checkpoint_fn()
```
**Description**

Get the checkpoint filename. 

```{python}
reset(self)
```
**Description**

Reset the private variable `_preempted` to zero. This is useful for debugging when multiple signals need to be caught. 

### Use Cases
[A basic use case](examples/example1)

[Email notification](examples/example2)

[Delayed checkpointing](examples/example3)

[Automatic checkpointing and restarting](examples/example4)

