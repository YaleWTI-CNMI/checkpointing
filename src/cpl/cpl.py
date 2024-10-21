import signal
from datetime import datetime, timedelta

SIGTERM = 15

class CPL:

    def __init__(self, sig=SIGTERM):
        self._preempted = False
        self._sig = sig
        signal.signal(self._sig, self._signal_handler)

    def _signal_handler(self, sig, frame):
        self._preempted = True
        self._time_of_preemption = datetime.now()

    def _cpl_handler(self, kwargs):
        return

    # delay: postpone 'delay' minutes to return a true value of self._preempted to the caller. 
    # handle: user defined checkpointing and cleaning function
    # back: after the user handle does its work, if back is False, then stay in 'check.'
    #       If back is True, go back to the caller function. 
    def check(self, handle=_cpl_handler, delay=60, back=True, **kwargs):
        if self._preempted == True:
            if datetime.now() < self._time_of_preemption + timedelta(minutes=delay):
                return False

            handle(kwargs)

            if back == False:
                # loop until job is preempted. This is necessary if the job has --requeue
                while True:
                    pass

        return self._preempted
        
    def reset(self):
        self._preempted = False
