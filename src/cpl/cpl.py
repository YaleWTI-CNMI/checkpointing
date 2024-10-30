import signal
import smtplib
import logging
import yaml
import sys
import os
from email.message import EmailMessage
from datetime import datetime, timedelta
from pathlib import Path

SIGTERM = 15

class CPL:

    """
    sig: an integer, specifies the signal number the cpl instance will catch.
    email: a valid email address where notifications will be sent when a signal is caught.
    logfile
    loglevel
    """
    def __init__(self, sig=SIGTERM):
        self._sig = sig
        self._checkpoint_fn = "checkpoint.pt"
        self._email_server = None
        self._email_address = None
        self._delay = 0
        self._preempted = False
        self._emailed = False
        self._email_signal_caught = False
        self._email_checkpoint_handler_done = False
        self._log_enabled = False

        _cfg_fn = 'cpl.yml'
        file_path = Path(_cfg_fn)
        if file_path.exists():
            with open(_cfg_fn) as _cfg_f:
                _config = yaml.safe_load(_cfg_f)
            
            if _config["logfile"]:
                self._log_enabled = True
                logging.basicConfig(filename=_config["logfile"], 
                                    encoding='utf-8', 
                                    level=_config["loglevel"], 
                                    format='%(asctime)s %(levelname)s:%(message)s')

            if _config["email_server"]:
                self._email_server = _config["email_server"]
            if _config["email_address"]:
                self._email_address = _config["email_address"]
            if _config["email_types"]:
                self._email_signal_caught = _config["email_types"]["signal_caught"]
                self._email_checkpoint_handler_done = _config["email_types"]["checkpoint_handler_done"]

            if _config["checkpoint_fn"]:
                self._checkpoint_fn = _config["checkpoint_fn"]

        signal.signal(self._sig, self._signal_handler)
            
    def _signal_handler(self, sig, frame):
        self._preempted = True
        self._time_of_preemption = datetime.now()

    def _cpl_handler(self, **kwargs):
        return

    def _email(self, email_server, email_address, subject, message):
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = email_address
        msg['To'] = email_address

        s = smtplib.SMTP(email_server)
        s.send_message(msg)
        s.quit()

    def _get_jobid(self):
        # check if $SLURM_JOB_ID exist
        jobid = os.getenv("SLURM_JOB_ID")
        return jobid

    """
    delay: postpone 'delay' minutes to return a true value of self._preempted to the caller. 
    checkpoint_handler: a handler for a user defined checkpointing and cleanup callback function.
    back: after the user handle is done, if 'back' is False, then stay in 'check.'
          If back is True, go back to the caller function. 'back' must be False to have a job requeued.
    """
    def check(self, checkpoint_handler=_cpl_handler, back=True, **kwargs):
        if self._preempted == True:
            if self._email_address != None and not self._emailed and self._email_signal_caught: 
                # when the signal is caught, email the user immediately
                jobid = self._get_jobid()
                if jobid:
                    _subject = f"Signal caught in job {jobid}"
                    _message = f"Signal {self._sig} is caught in job {jobid}."
                else:
                    _subject = f"Signal caught"
                    _message = f"Signal {self._sig} is caught."
                self._email(self._email_server, self._email_address, _subject, _message)
                self._emailed = True

                if self._log_enabled:
                    if jobid:
                        logging.info(f"Signal {self._sig} is caught in job {jobid}. Notification is sent to {self._email_address}")
                    else:
                        logging.info(f"Signal {self._sig} is caught. Notification is sent to {self._email_address}")

            if datetime.now() < self._time_of_preemption + timedelta(minutes=self._delay):
                return False

            if self._log_enabled:
                if jobid:
                    logging.info(f"Before calling the checkpoint handler in job {jobid}.")
                else:
                    logging.info(f"Before calling the checkpoint handler.")
            checkpoint_handler(kwargs)
            if self._log_enabled:
                if jobid:
                    logging.info(f"After calling the checkpoint handler in job {jobid}.")
                else:
                    logging.info(f"After calling the checkpoint handler.")
            if self._email_address != None and self._email_checkpoint_handler_done:
                jobid = self._get_jobid()
                if jobid:
                    _subject = f"Checkpoint handler done in job {jobid}"
                    _message = f"Checkpoint handler is done in job {jobid}."
                else:
                    _subject = f"Checkpoint handler done"
                    _message = f"Checkpoint handler is done."
                self._email(self._email_server, self._email_address, _subject, _message)

            if back == False:
                # loop until job is preempted. This is necessary if the job has --requeue
                while True:
                    pass

        return self._preempted
        
    def reset(self):
        self._preempted = False

    def get_checkpoint_fn(self):
        return self._checkpoint_fn
