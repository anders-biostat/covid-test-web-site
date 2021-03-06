from enum import Enum


class SampleStatus(Enum):
    RECEIVED = "RECEIVED"
    LAMPREPEAT = "LAMPREPEAT"
    LAMPPOS = "LAMPPOS"
    LAMPNEG = "LAMPNEG"
    LAMPFAIL = "LAMPFAIL"
    LAMPINC = "LAMPINC"
    PCRPOS = "PCRPOS"
    PCRNEG = "PCRNEG"
    UNDEF = "UNDEF"
    INFO = "INFO"
    MESSAGE = "MESSAGE"
    PRINTED = "PRINTED"
    WAIT = "WAIT"
