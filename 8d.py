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

from effects import apply_effects

def minmax_norm(arr: np.ndarray, a: float=1.0, b: float=None) -> np.ndarray:
    """min-max feature scaling to normalize panning values between 'a' and 'b'"""
    if not b:
        b = abs(a)
        a = -b
    x_min = np.min(arr)
    x_max = np.max(arr)
    return np.array(list(map(lambda x: a + ((x-x_min)*(b-a)) / (x_max - x_min), arr)))

def to_8d(infile: str, outfile: str, effect_set: str, normalize: bool):
    """
    converts audio to 8d audio
    """
    filetype = os.path.splitext(infile)[1].replace(".","").lower()
    audio = AudioSegment.from_file(infile, format=filetype)
    file = mutagen_info(infile)
    bitrate = str(file.info.bitrate)

    # init 8d audio file:
    shrooms = AudioSegment.empty()

    pan_amounts = apply_effects(effect_set)
    if normalize or (np.min(pan_amounts) < -1 or np.max(pan_amounts) > 1):
        print(f"normalizing {effect_set=}: pan amounts exceed bounds")
        pan_amounts = minmax_norm(pan_amounts, 1.0)


    pan_limit = len(pan_amounts) - 1

    # integrate pan into audio
    chunks = list(enumerate(audio[::1]))
    for i, chunk in tqdm(chunks, ascii="->=", desc="Processing 8d Chunks", unit="chunks", total=len(chunks)):
        if i > pan_limit:
            i = -1
        shrooms = shrooms + chunk.pan(pan_amounts[i])

    shrooms.export(outfile, format=filetype, bitrate=bitrate)
    
if __name__ == "__main__":
    parser = ArgumentParser(description="Add ear-to-ear panning to audio file")
    parser.add_argument("-i", "--input", required=True, type=str, help="input file")
    parser.add_argument("-o", "--output", required=True, type=str, help="output file")
    parser.add_argument("-e", "--effect", required=True, type=str, help="set of pan effects to use from effects.json")
    parser.add_argument("-n", "--normalize", action="store_true", help="normalize pan matrix to extend to -1 and 1 as bounds. Performed automatically for matrices that exceed (-1,1)")
    args = parser.parse_args()
    to_8d(args.input, args.output, args.effect, args.normalize)

