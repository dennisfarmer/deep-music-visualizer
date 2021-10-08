#!/usr/bin/env python
# Dennis Farmer - October 1, 2021
# 8d audio generator (audio moving ear to ear / inside head illusion)

import numpy as np
from tqdm import tqdm
from pydub import AudioSegment
from argparse import ArgumentParser
import os
import sys
from mutagen import File as mutagen_info

def minmax_norm(arr: np.array, a: float=1.0, b: float=None) -> np.array:
    """min-max feature scaling to normalize panning values between 'a' and 'b'"""
    if not b:
        b = abs(a)
        a = -b
    x_min = min(arr)
    x_max = max(arr)
    return np.array(list(map(lambda x: a + ((x-x_min)*(b-a)) / (x_max - x_min), arr)))

def to_8d(infile: str, outfile: str, period_ms: int, depth: float, wavelength: float, normalize: bool):
    """
    converts audio to 8d audio
        For custom pan functions outside of sin(x), use:
            echo "-0.5*sin(3*x/4)" | python 8d.py ... --wavelength 4.188790204  # 4pi/3
    """
    stdin_exists = not sys.stdin.isatty()
    filetype = os.path.splitext(infile)[1].replace(".","").lower()
    audio = AudioSegment.from_file(infile, format=filetype)
    file = mutagen_info(infile)
    bitrate = str(file.info.bitrate)

    # init 8d audio file:
    shrooms = AudioSegment.empty()

    if stdin_exists:
        function = sys.stdin.read()
        if isinstance(function, str):
            f = parse_np_string(function.strip("\n"))
        else: raise TypeError("stdin is not in a parsable format, try:\n\techo \"sin(x)\" | python 8d.py ...")
    else:
        f = np.sin
        wavelength = 2*np.pi

    pan_amounts = depth*f(np.linspace(0, wavelength, period_ms))
    if normalize or (min(pan_amounts) < -1 or max(pan_amounts) > 1):
        pan_amounts = minmax_norm(pan_amounts, 1.0)

    # integrate pan into audio
    chunks = list(enumerate(audio[::100]))
    for i, chunk in tqdm(chunks, ascii="->=", desc="Processing 8d Chunks", unit="chunks", total=len(chunks)):
        if len(chunk) < 100:
            continue
        shrooms = shrooms + chunk.pan(pan_amounts[i % period_ms])

    shrooms.export(outfile, format=filetype, bitrate=bitrate)
    
if __name__ == "__main__":
    parser = ArgumentParser(description="Add ear-to-ear panning to audio file")
    parser.add_argument("-i", "--input", required=True, type=str, help="input file")
    parser.add_argument("-o", "--output", required=True, type=str, help="output file")
    parser.add_argument("-p", "--period", type=int, default=200, help="panning period in miliseconds (default: 200, Recommended: >=200)")
    parser.add_argument("-d", "--depth", type=float, default=0.9, help="depth of pan (0,1] (default: 0.9)")
    parser.add_argument("-w", "--wavelength", type=float, default=2*np.pi, help="period of pan generating function (use desmos/algebra to figure it out lol)")
    parser.add_argument("-n", "--normalize", action="store_true", help="normalize pan matrix to extend to -1 and 1 as bounds. Performed automatically for matrices that exceed (-1,1)")
    args = parser.parse_args()
    to_8d(args.input, args.output, args.period, args.depth, args.wavelength, args.normalize)

