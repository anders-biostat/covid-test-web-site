from enum import Enum


class SampleStatus(Enum):
    RECEIVED = "RECEIVED"
    LAMPPOS1 = "LAMPPOS1"
    LAMPPOS2 = "LAMPPOS2"
    LAMPPOS3 = "LAMPPOS3"
    LAMPNEG = "LAMPNEG"
    LAMPFAIL = "LAMPFAIL"
    UNDEF = "UNDEF"
    INFO = "INFO"
    MESSAGE = "MESSAGE"
    PRINTED = "PRINTED"
    WAIT = "WAIT"
    EXPIRED = "EXPIRED"
