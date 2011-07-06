"""
A module for controlling and receiving data from a CASPER_N correlator.

Implements interfaces for controlling a CASPER_N correlator and verifying correct operation.
Used primarily for by the PAPER array project.

Author: Jason Manley, Aaron Parsons
Email: jason_manley at hotmail.com, aparsons at astron.berkeley.edu
Revisions:
ver0.4.2: 2010-04-02
    *) tgtap call in katcp_wrapper now takes another parameter to allow naming of tap devices. *NOT BACKWARDS COMPATIBLE*
    *) antenna numbering now correct off F engines.
    *) cn_tx.py replaced by corr_tx.py
    *) cleanup of some functions.

"""
import cn_conf, sim_cn_data, katcp_wrapper, log_handlers, corr_functions
