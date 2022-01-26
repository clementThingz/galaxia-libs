import sys

file = open(sys.argv[1], "rb")

byte = file.read(1).hex()
s = ""
count=0
while byte:
    if count == 0:
        s+= "f.write(bytearray(b'"
    s += "\\x"+str(byte)
    count+=1
    byte = file.read(1).hex()
    if count == 20:
        count = 0
        s += "'))\r\n"
if count:
    s += "'))\r\n"

print(s)