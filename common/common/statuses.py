from enum import Enum

class SampleStatus(Enum):
    PRINTED = 'PRINTED'
    WAIT = 'WAIT'
    LAMPPOS = 'LAMPPOS'
    LAMPINC = 'LAMPINC'
    LAMPNEG = 'LAMPNEG'
    PCRPOS = 'PCRPOS'
    PCRNEG = 'PCRNEG'
    UNDEF = 'UNDEF'