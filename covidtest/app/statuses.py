from enum import Enum

class SampleStatus(Enum):
    PRINTED = 'PRINTED'
    WAIT = 'WAIT'
    LAMPPOS = 'LAMPPOS'
    LAMPINC = 'LAMPINC'
    LAMPNEG = 'LAMPNEG'
    LAMPFAIL = 'LAMPFAIL'
    PCRPOS = 'PCRPOS'
    PCRNEG = 'PCRNEG'
    UNDEF = 'UNDEF'
    INFO = 'INFO'