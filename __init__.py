import os
import sys
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


if __file__.endswith("jotils.py"):
    # We are in the "fake/proxy" jotils file, nothing in this file will actually be loaded.
    pass
else:
    sys.path.append(__file__[:-len("x__init__.py")])
    from randName import randName

    if os.name == "nt":
        import clipboard

        cb = clipboard.generic
        cbmod = clipboard.mod
        cbundo = clipboard.undo

    try: from .extras import *
    except ImportError: pass # Running without extras.


# --------------------------- HEX STUFF ---------------------------

def hexs2s(hexstr: str, sep="") -> str:
    "hex string to normalized hex str (ex. '01 00 04 06 70' -> '0100040670')"
    normalized = hexstr.strip().replace(" ", "").replace("-", "").replace(":", "").replace("\n", "").upper()
    return sep.join([normalized[(i*2):(i+1)*2] for i in range((len(normalized)+1)//2)])

def hexs2i(hexstr: str) -> int:
    "hex string to int (ex. '12 34 56 78' -> 305419896)"
    return int(hexs2s(hexstr), 16)

def hexs2b(hexstr: str) -> bytes:
    "hex string to bytes (ex. 'deadbeef' -> b'\xde\xad\xbe\xef')"
    hexint = hexs2i(hexstr)
    return hexint.to_bytes(((hexint.bit_length()+7)//8 or 1))

def hexi2s(hexint: int, sep="") -> str:
    "int to hex string (ex. 262254561 -> 'FA1AFE1')"
    if not sep: return "{:0X}".format(hexint)
    _hex = ["", "0"][((hexint.bit_length()+3)//4 or 1)%2] + "{:0X}".format(hexint)
    return sep.join([c1+c2 for c1,c2 in zip(_hex[::2],_hex[1::2])])

def hexb2s(hexbytes: bytes, sep="") -> str:
    "bytes to hex string (ex. b'\x01#Eg\x89' -> '123456789')"
    return hexi2s(int.from_bytes(hexbytes), sep)

def hexi2b(hexint: int) -> bytes:
    "int to bytes (ex. 7106407 -> b'log')"
    return hexint.to_bytes(((hexint.bit_length()+7)//8 or 1))

# bytes to int, where hexb2i(hexi2b(x)) == x
hexb2i = int.from_bytes


# ------------------------- MAC ADDR STUFF ------------------------

def macs2i(mac: str) -> int:
    "mac string to integer (ex. 68-05-CA-75-16-4A, 00:50:56:c0:00:03, 000C294805ED)"
    return int((mac if len(mac) == 12 else "".join([mac[i*3:i*3+2] for i in range(6)])), 16)

def macs2b(mac: str) -> bytes:
    "mac string to bytes"
    return macs2i(mac).to_bytes(6)

def macscmp(mac1: str, mac2: str) -> bool:
    "compare 2 mac strings "
    return macs2i(mac1) == macs2i(mac2)

# NOTE: truncates on numbers above 2**(6*8)-1
def maci2s(mac: int) -> str:
    "mac integer to string (ex. 11111822610015 -> 0A:1B:2C:3D:4E:5F)"
    return ('00:00:00:00:00:' + hexi2s(mac, ":"))[-17:]

def macs2s(mac: str) -> str:
    "mac string to string (normalize mac string to canonical form)"
    return maci2s(macs2i(mac))

macNull = maci2s(0) # "00:00:00:00:00:00"
macBroad = maci2s(2**48-1) # "FF:FF:FF:FF:FF:FF"


# ------------------------- IP ADDR STUFF -------------------------

def ipi2s(ip: int) -> str:
    "ip integer (ex. 0xC0A8D302) to string"
    return ".".join([str(x) for x in ip.to_bytes(4)])

def ipni2s(ip: int) -> str:
    "ip network-order integer (ex. 0xC0A8D302) to string"
    return ".".join([str(x) for x in ip.to_bytes(4, byteorder="little")])

def ips2i(ip: str) -> int:
    "ip string (ex. 192.168.1.32) to integer"
    return int.from_bytes(bytes([int(x) for x in ip.split(".")]))

def ips2ni(ip: str) -> int:
    "ip string (ex. 192.168.1.32) to network-order integer"
    return int.from_bytes(bytes([int(x) for x in ip.split(".")]), byteorder="little")

ipNull = ipi2s(0) # "0.0.0.0"
ipBroad = ipi2s(2**32-1) # "255.255.255.255"


# ------------------------------ MISC -----------------------------

# Not intended to be used, just as a factoid to be used in other functions
# fastestCeilDiv = lambda numerator, denominator: numerator+(denominator-1) // denominator


def splitBy(obj, size: int):
    "Return groups of size number of members where the final group may be less than size"
    return [obj[(i*size):(i+1)*size] for i in range((len(obj)+(size-1))//size)]


def rev(obj):
    "Reverse an object, avoids having to unravel a 'reversed' object"
    return obj[::-1]


def swap(cur, obj1, obj2):
    "Swap 'cur' with whichever of 'obj1' and 'obj2' it's not"
    return (obj1, obj2)[cur==obj1]


# Define new call-ambiguous exit for older/incompatible REPLs
exit = type("", tuple(), {"__repr__": exit, "__call__": exit})()


def get1st(i):
    "Get first element of an iterable, useful for unindexable objects, such as dict.keys"
    for x in i: return x


def func_rename(func, name):
    "Rename a function, if a different name makes more sense where it is used than where it is defined"
    func.__name__ = name
    func.__qualname__ = name
    return func


def randStrId(charCount: int) -> str:
    "Generate a random 'name' (ASCII compliant, no spaces, no number-start)"
    if charCount <= 0: return ""

    # make first character a non-number
    firstChar = string.printable[random.randint(10, 61)]
    
    return firstChar + "".join([
        string.printable[random.randint(0, 61)] for x in range(charCount-1)
        ])


def dbgPayload(totSize):
    "Generate bytes where each digit represents the position it occupies"
    try: return [b"", b"1", b".2"][totSize]
    except IndexError: pass
    
    payload = b""
    while len(payload) < totSize:
        payload = b"." + str(totSize - len(payload)).encode() + payload
        
    payload = b"1." + payload[(len(payload)-totSize+2):]
        
    return payload


def sizeofInt(i: int) -> int:
    "Return number of bytes needed to represent int"
    return (i.bit_length()+7)//8 or 1


def n2h(i: int, size=0) -> int:
    "Reverse byte-order of integer, where n2h(n2h(i)) == i"
    return int.from_bytes(int.to_bytes(i, size or sizeofInt(i), "little"))
h2n = n2h

# Convenience functions for quickly "disabling" a n2h/h2n
h2h = lambda i: i
n2n = h2h


def x2s(x):
    "Convert any type to a string, where x2s(x) is x when isinstance(x, str)"
    return x if isinstance(x, str) else repr(x)


def isPrimitive(obj):
    "Return True if 'obj' is a primitive type, False otherwise"
    return isinstance(obj, (str, int, float, bytes, NoneType))


def x2primitive(obj):
    "Return 'obj' if 'obj' is 'primitive', otherwise return json.dumps(obj)"
    return obj if isPrimitive(obj) else json.dumps(obj)


def binex(i: int, padFor=0, nibbleSep=" ", byteSep=" | ") -> str:
    """Format a number into binary format, comparable to bin()

    Padding for `padFor` number *bytes*, or 0 for auto
    Separate every nibble (4bits) in the byte by by `nibbleSep`
    Separate every byte (8bits) by `byteSep`"""

    padFor = padFor or sizeofInt(i)
    padded = ("0"*64 + bin(i)[2:])[-padFor*8:]
    return byteSep.join([padded[x:x+4]+nibbleSep+padded[x+4:x+8] for x in range(0, padFor*8, 8)])


def file2s(fileName: str) -> str:
    "Read a file (.read() style) and return result"
    file = open(fileName)
    content = file.read()
    file.close()
    return content


def notepad(s, pause=True):
    "Open a string in notepad (tempfile)"
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


def funcMap(prefix: str, scopeDict: dict[str, Any]) -> Dict[str, Callable[..., Any]]:
    """Return a dict that maps prefixed functions' unprefixed name to itself
    
    Ex (assuming prefix="GET_"): def GET_user(): ... -> {"user": GET_user}"""

    return {
        key[len(prefix):]: val 
        for key, val in scopeDict.items()
        if (key.startswith(prefix) and callable(val))
        }


def consumeBuf(buf: IOBase) -> Any:
    "Return current value of `buf` and prepare it for subsequent writes"
    data = buf.getvalue()
    buf.__init__()
    return data


def _findNonASCII(content: str):
    "Find all non-ASCII characters in string"
    for i, char in enumerate(content):
        # also filters tab ("\t")
        if 9 > ord(char) > 126:
            print(i, char)


def findNonASCII(fileName: str):
    "Find all non-ASCII characters in file"
    _findNonASCII(file2s(fileName))


def rid(obj, x, *replaceWith):
    "Rid (or replace) 'obj' of instances 'x', preserving type(obj)"
    try: return {
            str:   lambda: (obj.replace(x, replaceWith[0] if replaceWith else "")),
            bytes: lambda: (obj.replace(x, replaceWith[0] if replaceWith else b"")),
            }[type(obj)]()
    except KeyError: pass
    
    if not replaceWith:
        return type(obj)([i for i in obj if i != x])
    else:
        return type(obj)([(i if i != x else replaceWith[0]) for i in obj])
        

def iRollA(n: int) -> bool:
    "return True randomly with odds 1/n"
    return not random.randint(0, n-1)


def trunc(s: str, cut: int = 10, ellipsis: str = "…"):
    "Truncate a string, ensuring the returned string is always <= cut"
    if len(ellipsis) > cut: return ellipsis[:cut] # edge case
    return s[:cut-len(ellipsis)]+ellipsis if len(s) > cut else s


def dictify(obj):
    "Return an 'obj.__dict__' style object"
    return {name: getattr(obj, name) for name in dir(obj)}


def _qview(obj, depth: int = 1, height: int = 20, width: int = 80, _indent=0, _offset=0):
    height-= 1

    if not height:
        return print("\n"+r"\/"*(width//2))
    
    if (width-_indent) < 4:
        print("\n"+r"\/"*(width//2))
        return height
    
    print(trunc(f"{type(obj)}: {repr(obj)}", width-_offset))
    if not isinstance(obj, dict):
        if isPrimitive(obj): return height
        elif hasattr(obj, "__iter__"):
            _counter = -1
            obj = {(_counter := (_counter+1)): x for x in obj}
        elif hasattr(obj, "__dict__"):
            obj = obj.__dict__
        else:
            obj = dictify(obj)
        
    # Now we have a dict to work with
    for key in obj:
        if hasattr(obj[key], "__iter__") and depth > 1:
            # The value itself is iterable. If this value is an iterable of "primitive" values, we
            # don't need to recurse into it, otherwise we do.
            if any(x for x in obj[key] if (not isPrimitive(x)) or hasattr(x, "__iter__")):
                # If any of the values are not primitive, or it contains a dict, we
                # recurse into the value.
                prefix = trunc(f"{' '*_indent}{key}: ", width)
                print(prefix, end="")
                height = _qview(obj[key], depth=depth-1, height=height, width=width, _indent=_indent+2, _offset=len(prefix))
                if not height: return
                continue
        
        print(trunc(f"{' '*_indent}{repr(key)}: {repr(obj[key])}", width))
        height-= 1

        if not height:
            return print(r"\/"*(width//2))

    return height


def qview(obj, depth: int = 1, height: int = 20, width: int = 78):
    "Provide a quick view of the object"
    if height == 1:
        print(trunc(f"{type(obj)}: {repr(obj)}", width))
    _qview(obj, depth=depth, height=height, width=width, _indent=0, _offset=0)
        

def fixMyNewlines(raw: str):
    "Fix whatever broken string you've copied from termux terminal"
    raw+="P"
    while (start := raw.find(" "*5)) != -1:        
        end = start + 1
        while raw[end] == " ":
            end+=1
        raw = raw.replace(" "*(end-start), "\n", 1)
           
    return raw[:-1]


def catSep(name: str, prefix: str="", lineLen: int=67) -> str:
    "Create a category separator (as found in this file)"
    tot = lineLen - (2 + len(prefix) + len(name))
    print( prefix + "-"*int(tot/2 + 0.5) + f" {name} " + "-"*(tot//2) )

catSepCode = lambda name: catSep(name, "# ")
catSepTxt = lambda name: catSep(name)


def str2iter(s: str):
    "Given a string 's', return an object 'obj' where next(obj) == s"
    return type("", tuple(), {"__next__": lambda _: s})()


# Print statement with built-in arg-caching
_printData = {}
def print(*args, **kwargs):
    key = " ".join([(arg if isinstance(arg, str) else repr(arg)) for arg in args])
    _printData[key] = (args)
    builtins.print(key, **kwargs)

def getPrint(key=None):
    "Return all args passed to the most recent print containing 'key'♣"
    if key is None: return _printData

    # Traverse items in reverse, for most-recent first
    for iterKey, value in reversed(_printData.items()):
        if key in iterKey: return value


def parseInts(s: str) -> list[int]:
    "Parse input to return a list of ints"
    intArr = []

    for line in s.strip().splitlines():
        for part in line.split(","):
            parsedPart = part.strip()
            if parsedPart.isalnum():
                intArr.append(int(parsedPart, 0))
    return intArr


def binCmpDmp(arr: list[int]):
    "Dump ints in binary format to stdout, largest value first"
    nums = tuple(sorted(arr, reverse=True))
    numBytes = sizeofInt(nums[0])
    [print(binex(num, numBytes)) for num in nums]


def vstr(ts: templatelib.Template):
    "Create a versatile string (vstr)"
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
    

def localJotils():
    "Make a link to *this* file from wherever this is called from"
    global jotilsFile, my_module

    def syncFile():
        realFile = file2s(jotilsFile)
        warningText = f"# DON'T MODIFY ME: This file is a proxy to {jotilsFile}\n\njotilsFile={repr(jotilsFile)}\n\n"
        realFile = warningText + realFile
    
        with open("jotils.py", "w+") as file:
            file.write(realFile)

    if __file__.endswith("jotils.py"):
        # We are inside the fake "jotils.py"
        syncFile()
        # If the "real lib" has been updated, *this* instance of the file
        # is "old", so we need to import the real lib just in case.
        # This is so damn ugly I wanna puke.
        import importlib.util
        spec = importlib.util.spec_from_file_location("jotils", jotilsFile)
        my_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(my_module)

        for var in dir(my_module):
            setattr(sys.modules[__name__], var, getattr(my_module, var))

    else:
        # We are inside the real jotils lib (__init__.py)
        jotilsFile = __file__
        syncFile()