#!/usr/bin/python3
import collections

batches=collections.defaultdict(set)
with open("barcodes.csv", 'r') as f:
  for line in f:
    barcode1,barcode2,timestamp,batch = line.rstrip().split(";")
    batches[batch].add(barcode1)
    batches[batch].add(barcode2)

instructions=collections.defaultdict(set)
with open('instruction.csv', 'r') as fi:
    for line in fi:
        batch, inst, date1, date2 = line.rstrip().split(';')
        instructions[batch].add(inst)

bcode = "CSKRBN"
for s in batches:
    if bcode in batches[s]:
        print(instructions[s])
