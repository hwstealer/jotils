# this is mostly frankensteined ChatGPT-4 code

import ctypes
from ctypes import wintypes
from string import printable

printableBytes = printable.encode()

# Load user32 and kernel32 DLLs
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# Define necessary functions
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID

kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL

user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE

user32.OpenClipboard.argtypes = [wintypes.HWND]
user32.OpenClipboard.restype = wintypes.BOOL

user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = wintypes.BOOL

user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = wintypes.BOOL

# Constants for clipboard formats, e.g., CF_TEXT
CF_TEXT = 1
# https://learn.microsoft.com/en-us/windows/win32/dataxchg/standard-clipboard-formats

##def enumerateClipboardFormats() -> list:
##    formats = []
##    format = 0  # Start with zero to find the first available format
##
##    # Open the clipboard
##    if not user32.OpenClipboard(0):
##        print("Failed to open the clipboard")
##        return formats
##
##    while True:
##        format = user32.EnumClipboardFormats(format)
##        if not format:
##            break
##        formats.append(format)
##
##    user32.CloseClipboard()
##    return formats


def getBytes() -> bytes:
    user32.OpenClipboard(0)
    handle = user32.GetClipboardData(CF_TEXT)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    lockedMem = kernel32.GlobalLock(handle)
    if not lockedMem:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        # Assuming the data is null-terminated text for simplicity
        data = ctypes.cast(lockedMem, ctypes.c_char_p).value
        return data
    
    finally:
        user32.CloseClipboard()
        if not kernel32.GlobalUnlock(handle):
            # It's okay if GlobalUnlock fails because memory might be unlocked already.
            pass


def setBytes(data: bytes) -> bool:
    bufferSize = len(data) + 1  # Size of buffer including the null terminator

    # Open the clipboard
    if not user32.OpenClipboard(0):
        return False

    try:
        # Empty the clipboard
        user32.EmptyClipboard()

        # Allocate global memory for the text; GMEM_MOVEABLE = 0x0002, GMEM_ZEROINIT = 0x0040
        hClipMem = kernel32.GlobalAlloc(0x2002 | 0x0040, bufferSize)
        if not hClipMem:
            return False

        # Lock the memory and get a pointer to it
        pClipMem = kernel32.GlobalLock(hClipMem)
        if not pClipMem:
            kernel32.GlobalFree(hClipMem)
            return False

        try:
            ctypes.memmove(pClipMem, data, bufferSize)

            # Set the clipboard data for text format; CF_TEXT = 1
            if not user32.SetClipboardData(1, hClipMem):
                # If setting data fails, free the allocated memory
                kernel32.GlobalFree(hClipMem)
                return False

            # Memory is now owned by the clipboard, do not free it.
            hClipMem = None

        finally:
            if pClipMem:
                kernel32.GlobalUnlock(hClipMem)

    finally:
        user32.CloseClipboard()

    return True



def get() -> str:
    raw = getBytes()
    try: return raw.decode()
    except UnicodeDecodeError:
        return bytes([c for c in raw if c in printableBytes]).decode()


def set(x) -> bool:
    return setBytes(x if isinstance(x, bytes) else (x if isinstance(x, str) else repr(x)).encode())


def generic(x=None):
    return get() if x is None else set(x)


# Modify clipboard by applying a chain of functions.
# Ex: `mod((int, 16), bin)` will be logically equivalent to set(bin(int(get(), 16)))
_undo = None
def mod(*args):
    global _undo
    _undo = get()
    
    res = _undo
    for arg in args:
        res = arg(res) if callable(arg) else arg[0](res, *arg[1:])
    set(res)


def undo():
    set(_undo)
