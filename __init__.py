import os
import json
import random
import string
import builtins
import tempfile
import subprocess
from io import IOBase
from types import NoneType
from typing import Callable, Dict, Any
from string import templatelib
from threading import Thread

try: from .randName import randName
except ImportError: from randName import randName

if os.name == "nt":
    try: from . import clipboard
    except ImportError: import clipboard

    cb = clipboard.generic
    cbmod = clipboard.mod
    cbundo = clipboard.undo

try: from .extras import *
except ImportError:
    try: from extras import *
    except ImportError: pass # Running without extras.


# --------------------------- HEX STUFF ---------------------------

# hex string to normalized hex str (ex. "01 00 04 06 70" -> "0100040670")
def hexs2s(hexstr: str, sep="") -> str:
    normalized = hexstr.strip().replace(" ", "").replace("-", "").replace(":", "").replace("\n", "").upper()
    return sep.join([normalized[(i*2):(i+1)*2] for i in range((len(normalized)+1)//2)])

# hex string to int (ex. "12 34 56 78" -> 305419896)
def hexs2i(hexstr: str) -> int:
    return int(hexs2s(hexstr), 16)

# hex string to bytes (ex. "deadbeef" -> b'\xde\xad\xbe\xef')
def hexs2b(hexstr: str) -> bytes:
    hexint = hexs2i(hexstr)
    return hexint.to_bytes(((hexint.bit_length()+7)//8 or 1))

# int to hex string (ex. 262254561 -> 'FA1AFE1')
def hexi2s(hexint: int, sep="") -> str:
    if not sep: return "{:0X}".format(hexint)
    _hex = ["", "0"][((hexint.bit_length()+3)//4 or 1)%2] + "{:0X}".format(hexint)
    return sep.join([c1+c2 for c1,c2 in zip(_hex[::2],_hex[1::2])])

# bytes to hex string (ex. b'\x01#Eg\x89' -> '123456789')
def hexb2s(hexbytes: bytes, sep="") -> str:
    return hexi2s(int.from_bytes(hexbytes), sep)

# int to bytes (ex. 7106407 -> b'log')
def hexi2b(hexint: int) -> bytes:
    return hexint.to_bytes(((hexint.bit_length()+7)//8 or 1))

# bytes to int, where hexb2i(hexi2b(x)) == x
hexb2i = int.from_bytes


# ------------------------- MAC ADDR STUFF ------------------------

# mac string to integer (ex. 68-05-CA-75-16-4A, 00:50:56:c0:00:03, 000C294805ED)
def macs2i(mac: str) -> int:
    return int((mac if len(mac) == 12 else "".join([mac[i*3:i*3+2] for i in range(6)])), 16)

# mac string to bytes
def macs2b(mac: str) -> bytes:
    return macs2i(mac).to_bytes(6)

# compare 2 mac strings 
def macscmp(mac1: str, mac2: str) -> bool:
    return macs2i(mac1) == macs2i(mac2)

# mac integer to string (ex. 11111822610015 -> 0A:1B:2C:3D:4E:5F)
# NOTE: truncates on numbers above 2**(6*8)-1
def maci2s(mac: int) -> str:
    return ('00:00:00:00:00:' + hexi2s(mac, ":"))[-17:]

# mac string to string (normalize mac string to canonical form)
def macs2s(mac: str) -> str:
    return maci2s(macs2i(mac))

macNull = maci2s(0) # "00:00:00:00:00:00"
macBroad = maci2s(2**48-1) # "FF:FF:FF:FF:FF:FF"


# ------------------------- IP ADDR STUFF -------------------------

# ip integer (ex. 0xC0A8D302) to string
def ipi2s(ip: int) -> str:
    return ".".join([str(x) for x in ip.to_bytes(4)])

# ip network-order integer (ex. 0xC0A8D302) to string
def ipni2s(ip: int) -> str:
    return ".".join([str(x) for x in ip.to_bytes(4, byteorder="little")])

# ip string (ex. 192.168.1.32) to integer
def ips2i(ip: str) -> int:
    return int.from_bytes(bytes([int(x) for x in ip.split(".")]))

# ip string (ex. 192.168.1.32) to network-order integer
def ips2ni(ip: str) -> int:
    return int.from_bytes(bytes([int(x) for x in ip.split(".")]), byteorder="little")

ipNull = ipi2s(0) # "0.0.0.0"
ipBroad = ipi2s(2**32-1) # "255.255.255.255"


# ------------------------------ MISC -----------------------------

# Not intended to be used, just as a factoid to be used in other functions
# fastestCeilDiv = lambda numerator, denominator: numerator+(denominator-1) // denominator


# Return groups of size number of members where the final group may be less than size
def splitBy(obj, size: int):
    return [obj[(i*size):(i+1)*size] for i in range((len(obj)+(size-1))//size)]


# Reverse an object, avoids having to unravel a "reversed" object
rev = lambda obj: obj[::-1]


# Swap "cur" with whichever of "obj1" and "obj2" it's not
swap = lambda cur, obj1, obj2: (obj1, obj2)[cur==obj1]


# Define new call-ambiguous exit for older/incompatible REPLs
exit = type("", tuple(), {"__repr__": exit, "__call__": exit})()


# Get first element of an iterable, useful for unindexable objects, such as dict.keys
def get1st(i):
    for x in i: return x


# Rename a function, if a different name makes more sense where it is used than where it is defined
def func_rename(func, name):
    func.__name__ = name
    func.__qualname__ = name
    return func


# Generate a random "name" (ASCII compliant, no spaces, no number-start)
def randStrId(charCount: int) -> str:
    if charCount <= 0: return ""

    # make first character a non-number
    firstChar = string.printable[random.randint(10, 61)]
    
    return firstChar + "".join([
        string.printable[random.randint(0, 61)] for x in range(charCount-1)
        ])


# Generate bytes where each digit represents the position it occupies
def dbgPayload(totSize):
    try: return [b"", b"1", b".2"][totSize]
    except IndexError: pass
    
    payload = b""
    while len(payload) < totSize:
        payload = b"." + str(totSize - len(payload)).encode() + payload
        
    payload = b"1." + payload[(len(payload)-totSize+2):]
        
    return payload


# Return number of bytes needed to represent int
def sizeofInt(i: int) -> int:
    return (i.bit_length()+7)//8 or 1


# Reverse byte-order of integer, where n2h(n2h(i)) == i
def n2h(i: int, size=0) -> int:
    return int.from_bytes(int.to_bytes(i, size or sizeofInt(i), "little"))
h2n = n2h

# Convenience functions for quickly "disabling" a n2h/h2n
h2h = lambda i: i
n2n = h2h


# Convert any type to a string, where x2s(x) is x when isinstance(x, str)
x2s = lambda x: x if isinstance(x, str) else repr(x)


# Return "obj" if "obj" is "primitive", otherwise return json.dumps(obj)
def to_primitive(obj):
    if isinstance(obj, (str, int, float, bytes, NoneType)):
        return obj
    return json.dumps(obj)


# Format a number into binary format, comparable to bin()
# Padding for `padFor` number *bytes*, or 0 for auto
# Separate every nibble (4bits) in the byte by by `nibbleSep`
# Separate every byte (8bits) by `byteSep`
def binex(i: int, padFor=0, nibbleSep=" ", byteSep=" | ") -> str:
    padFor = padFor or sizeofInt(i)
    padded = ("0"*64 + bin(i)[2:])[-padFor*8:]
    return byteSep.join([padded[x:x+4]+nibbleSep+padded[x+4:x+8] for x in range(0, padFor*8, 8)])


# Read a file (.read() style) and return result
def file2s(fileName: str) -> str:
    file = open(fileName)
    content = file.read()
    file.close()
    return content


# Open a string in notepad (tempfile)
def notepad(s, pause=True):
    if pause:
        s = s if isinstance(s, bytes) else s.encode(errors="replace")
        with tempfile.TemporaryFile("wb", delete_on_close=False) as fp:
            fp.write(s)
            fp.close()
            subprocess.run(["notepad", fp.name])
        return

    def _tmp():
        # Guard if non-blocking so we don't spawn a million
        if subprocess.run(["tasklist", "/FI", "IMAGENAME eq notepad.exe", "/FO", "CSV", "/NH"], stdout=subprocess.PIPE).stdout.count(b"\n") > 13: return
        notepad(s)
        
    Thread(target=_tmp).start()


# Return a dict that maps prefixed functions' unprefixed name to itself
# Ex (assuming prefix="GET_"): def GET_user(): ... -> {"user": GET_user}
def funcMap(prefix: str, scopeDict: dict[str, Any]) -> Dict[str, Callable[..., Any]]:
    return {
        key[len(prefix):]: val 
        for key, val in scopeDict.items()
        if (key.startswith(prefix) and callable(val))
        }


# Return current value of `buf` and prepare it for subsequent writes
def consumeBuf(buf: IOBase) -> Any:
    data = buf.getvalue()
    buf.__init__()
    return data


# Find all non-ASCII characters in string
def _findNonASCII(content: str):
    for i, char in enumerate(content):
        # also filters tab ("\t")
        if 9 > ord(char) > 126:
            print(i, char)


# Find all non-ASCII characters in file
def findNonASCII(fileName: str):
    _findNonASCII(file2s(fileName))


# Rid (or replace) "obj" of instances "x", preserving type(obj)
def rid(obj, x, *replaceWith):
    try: return {
            str:   lambda: (obj.replace(x, replaceWith[0] if replaceWith else "")),
            bytes: lambda: (obj.replace(x, replaceWith[0] if replaceWith else b"")),
            }[type(obj)]()
    except KeyError: pass
    
    if not replaceWith:
        return type(obj)([i for i in obj if i != x])
    else:
        return type(obj)([(i if i != x else replaceWith[0]) for i in obj])
        

# return True randomly with odds 1/n
def iRollA(n: int) -> bool:
    return not random.randint(0, n-1)


# Truncate a string, ensuring the returned string is always <= cut
def trunc(s: str, cut: int = 10, ellipsis: str = "…"):
    if len(ellipsis) > cut: return ellipsis[:cut] # edge case
    return s[:cut-len(ellipsis)]+ellipsis if len(s) > cut else s


# Provide a quick view of the object
def qview(obj, width: int = 50, depth: int = 1, _indent=0, _offset=0):
    if (width-_indent) < 4:
        print(r"\/"*(width//2))
        return
    
    print(trunc(f"{type(obj)}: {repr(obj)}", width-_offset))
    if not isinstance(obj, dict):
        if isinstance(obj, str): return
        if hasattr(obj, "__iter__"):
            _counter = -1
            obj = {(_counter := (_counter+1)): x for x in obj}
        else: return
        
    # Now we have a dict to work with
    for key in obj:
        if hasattr(obj[key], "__iter__") and depth > 1:
            # The value itself is iterable
            if isinstance(obj[key], dict) or (
                    any(map(
                        lambda x: hasattr(x, "__iter__") and not isinstance(x, str),
                        obj[key]
                        )) and True
                    
                    #getattr(obj[key], "__len__",  lambda: 0)() != 0 and
                    #type(obj[key]) != type(obj[key][0])
                ):
                prefix = trunc(f"{' '*_indent}{key}: ", width)
                print(prefix, end="")
                qview(obj[key], width, depth-1, _indent+2, len(prefix))
                continue
        print(trunc(f"{' '*_indent}{repr(key)}: {repr(obj[key])}", width))
        

# Fix whatever broken string you've copied from termux terminal
def fixMyNewlines(raw: str):
    raw+="P"
    while (start := raw.find(" "*5)) != -1:        
        end = start + 1
        while raw[end] == " ":
            end+=1
        raw = raw.replace(" "*(end-start), "\n", 1)
           
    return raw[:-1]


# Create a category separator (as found in this file)
def catSep(name: str, prefix: str="", lineLen: int=67) -> str:
    tot = lineLen - (2 + len(prefix) + len(name))
    print( prefix + "-"*int(tot/2 + 0.5) + f" {name} " + "-"*(tot//2) )

catSepCode = lambda name: catSep(name, "# ")
catSepTxt = lambda name: catSep(name)


# Given a string "s", return an object "obj" where next(obj) == s
def str2iter(s: str):
    return type("", tuple(), {"__next__": lambda _: s})()


# Print statement with built-in arg-caching
_printData = {}
def print(*args, **kwargs):
    key = " ".join([(arg if isinstance(arg, str) else repr(arg)) for arg in args])
    _printData[key] = (args)
    builtins.print(key, **kwargs)

def getPrint(key=None):
    if key is None: return _printData

    # Traverse items in reverse, for most-recent first
    for iterKey, value in reversed(_printData.items()):
        if key in iterKey: return value


# Parse input to return a list of ints
def parseInts(s: str) -> list[int]:
    intArr = []

    for line in s.strip().splitlines():
        for part in line.split(","):
            parsedPart = part.strip()
            if parsedPart.isalnum():
                intArr.append(int(parsedPart, 0))
    return intArr


# Dump ints in binary format to stdout, largest value first
def binCmpDmp(arr: list[int]):
    nums = tuple(sorted(arr, reverse=True))
    numBytes = sizeofInt(nums[0])
    [print(binex(num, numBytes)) for num in nums]


# Create a versatile string (vstr)
def vstr(ts: templatelib.Template):
    retStr = ""
    objDict = {}
    noIter = False

    # Resolve dynamic objects in ts
    for dynObj in ts.values:
        if isinstance(dynObj, str):
            objDict[dynObj] = str2iter(dynObj)
        elif "__iter__" in dynObj.__dir__():
            objDict[dynObj] = iter(dynObj)
        else:
            objDict[dynObj] = dynObj

    if not objDict: return print("No iterators found")

    # Build string
    try:
        while True:
            block = ""
            for obj in ts:
                if isinstance(obj, templatelib.Interpolation):
                    block+= str(next(objDict[obj.value]))
                    continue
                block+= obj
            retStr+= block+"\n"
            
    except StopIteration:
        return retStr[:-1]


