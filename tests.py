from retry_install import *
import subprocess

def test_package_resolution_rate():
    subprocess.run(['sudo', 'apt', 'update'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    pkgs = ['zlib.h', 'gmp.h', 'sys/capability.h', 'X11/Xlib.h', 'bits/libc-header-start.h', 'jemalloc/jemalloc.h', 'jpeglib.h', 'libnetfilter_queue/libnetfilter_queue.h', 'event.h', 'zmq.h', 'readline/readline.h', 'SDL2/SDL.h', 'lmdb.h', 'openssl/rand.h', 'portaudio.h', 'xcb/xcb_event.h', 'libavcodec/avcodec.h', 'bits/wordsize.h', 'SDL.h', 'lua.h', 'sndfile.h', 'curses.h', 'pcap.h', "cannot execute 'f951': execvp", 'librpitx/librpitx.h', 'openssl/bio.h', 'windows.h', 'openssl/ssl.h', 'cuda_runtime.h', 'fuse.h', 'sys/sysctl.h', 'histedit.h', 'bfd.h', 'openssl/sha.h', 'ncurses.h']
    good = 0
    total = 0

    for pkg in pkgs:
        total += 1
        res = can_package_name_be_resolved(get_package_name(pkg))
        if res:
            good += 1

        # if not res: print in red color
        if not res:
            print(f"\033[91m{pkg} -> {get_package_name(pkg)} -> {res}\033[00m")
        else:
            print(f"{pkg} -> {get_package_name(pkg)} -> {res}")
    print(f"{good/total}")
    print("Successful resoluitions: ", good)
    print("Total resoluitions: ", total)

test_package_resolution_rate()
