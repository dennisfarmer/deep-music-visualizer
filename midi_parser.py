#!/usr/bin/env python
# Dennis Farmer - October 8, 2021
# Midi Parser that retrieves timemarks for each measure of music within a midi file

from mido import MidiFile, tempo2bpm
from numpy import linspace, floor, ceil, ndarray
from function import Function
from typing import Union

class MeasureNumber:
    def __init__(self, mm: int=None):
        self.mm = mm
    def update(self, mm: int=None):
        self.mm = mm
    def __str__(self):
        return f"[{mm}]"
    def __eq__(self, other):
        if isinstance(other, MeasureNumber):
            return self.mm == other.mm
        else: return False

class Tempo:
    def __init__(self, bpm: int=None, _type="quarter"):
        self.bpm = bpm
        if _type == "quarter":
            self.type = "\u2669"
    def update(self, bpm: int=None, _type="quarter"):
        self.bpm = bpm
        if _type == "quarter":
            self.type = "\u2669"
    def __str__(self):
        return f"{self.type}={self.bpm}"
    def __eq__(self, other):
        if isinstance(other, Tempo):
            return (self.bpm == other.bpm) and (self.type == other.type)
        else: return False

class TimeSignature:
    def __init__(self, num: int=None, den: int=None):
        self.upper = num
        self.lower = den
    def update(self, num: int=None, den: int=None):
        self.upper = num
        self.lower = den
    def __str__(self):
        return f"{self.upper}/{self.lower}"
    def __eq__(self, other):
        if isinstance(other, TimeSignature):
            return self.upper == other.upper and self.lower == other.lower
        else: return False

# TODO: store amount of time one quarter note takes
# for wave time calculations
class Measure:
    def __init__(self, mm: MeasureNumber, bpm: Tempo, tsig: TimeSignature, t_0: float=None, t_f: float=None):
        self.mm = mm
        self.bpm = bpm
        self.tsig = tsig
        self.t_0 = t_0
        self.t_f = t_f
        self.beats = linspace(self.t_0, self.t_f, (self.tsig.upper*(self.tsig.lower/4) + 1 ))[:-1]

    def time_per_beat(self):
        t = 1/(self.bpm.bpm/60)
        if self.tsig.lower == 8:
            t/=2
        return t

    def beat(self, num):
        if num > self.tsig.upper*(self.tsig.lower/4) + 1 or num < 0:
            raise ValueError("beat number cannot be larger than number of beats, or less than zero")
        elif num == self.tsig.upper + 1:
            return self.t_f
        else:
            return self.beats[num-1] + (self.time_per_beat() * (num - np.floor(num)))

    def __str__(self):
        return f"{self.mm}: {self.tsig} @{self.bpm} t_0={self.t_0:.2f} -> t_f={self.t_f:.2f}"

    def __len__(self):
        return self.tsig.upper

class MeasureArray:
    def __init__(self, filename=None, arr=None):
        if arr:
            self.arr = arr
        else:
            self.gen_measures(filename)

    def next_beat(self, m, b):
        if m > len(self.arr):
            raise ValueError(f"next_beat({m=}, {b=}): requested index out of bounds")
        curr_measure = self.arr[m-1]
        if (b // len(curr_measure)) > 0):
            return (m+1, 1)
        return (m, b+1)

    def delta_quarternotes(self, m1: int, b1: int, m2: int, b2: int):
        found = False
        count = 0
        error_threshold = 999

        for b in [b1, b2]:
            if floor(b) != b:
                raise ValueError(f"delta_quarternotes({m1=}, {b1=}, {m2=}, {b2=}): beat {b} must be an integer")
        
        if m1 > m2:
            temp = m1,b1
            m1,b1 = m2,b2
            m2,b2 = temp
        elif m1 == m2:
            if b1 > b2:
                temp = b1
                b1 = b2
                b2 = temp
            elif b1 == b2:
                return 0

        while not found:
            m1, b1 = self.next_beat(m1,b1)
            if self.arr[m1-1].tsig.lower == 4:
                count += 1
            elif self.arr[m1-1].tsig.lower == 8:
                count += 0.5
            elif self.arr[m1-1].tsig.lower == 16:
                count += 0.25
            else:
                raise ValueError(f"measure ({m1}) has incompatable measure format")

            if (m1,b1) == (m2,b2):
                return count
            if count > error_threshold:
                raise ValueError(f"delta_quarternotes({m1}, {b1=}, {m2=}, {b2=}): count limit reached ({error_threshold} repetitions)")


    def calculate_measure_lengths(self, meta_events: 'list[MetaEvent]') -> [Measure]:
        prev = {"time": 0, "tsig": TimeSignature(), "bpm": Tempo()}
        curr = {"time": 0, "tsig": TimeSignature(), "bpm": Tempo()}
        e = 0  # index of current meta_event
        epsilon = 1e-3
        measures = []
        for e in meta_events:
            curr = prev.copy()
            curr["time"] = e.time
            if e.type == "time_signature":
                curr["tsig"] = e.data
            elif e.type == "set_tempo":
                curr["bpm"] = e.data

            # assuming that all tempo changes are on the first beat of the measure
            # num_measures = (delta_time * bpm) / (60 * time_signature.numerator)
            delta_t = curr["time"] - prev["time"]
            # Check if tempo and time sig. change occur on the same beat
            if abs(delta_t) > epsilon:  # if delta_t ~!= 0
                num_beats = (prev["bpm"].bpm * delta_t ) / 60
                if prev["tsig"].lower == 8:
                    num_beats*=2
                num_measures =  round(num_beats / prev["tsig"].upper)
                num_beats = round(num_beats)
                # time_dist[-1]: end time of last measure in chunk 
                time_dist = linspace(prev["time"], curr["time"], num_measures+1)
                for i in range(num_measures):
                    mm = len(measures) + 1
                    measures.append(Measure(mm, bpm=prev["bpm"], tsig=prev["tsig"], t_0=time_dist[i], t_f=time_dist[i+1]))

            prev = curr.copy()
        return measures

    def gen_measures(self, filename: str, quiet: bool=False) -> [Measure]:
        mid = MidiFile(filename)
        t = 0
        events = []

        class MetaEvent:
            def __init__(self, time: float, _type: str, data: Union[TimeSignature, Tempo]):
                self.time=time
                self.type=_type
                self.data=data
            def __str__(self):
                return f"t={self.time:.4f}: {self.data.__str__()}"

        for msg in mid:
            t += msg.time
            if msg.type == 'time_signature':
                events.append(MetaEvent(t, msg.type, TimeSignature(msg.numerator, msg.denominator)))
            elif msg.type == 'set_tempo':
                events.append(MetaEvent(t, msg.type, Tempo(round(tempo2bpm(msg.tempo)))))

        measures = self.calculate_measure_lengths(events)
        if not quiet:
            #for e in events:
                #print(e)
            for m in measures:
                print(m)
        # Son't forget to adjust last measure to have a differnt end time to account for reverb
        self.arr = measures

    def straight_line(self, ear_i, ear_f=None, time_ms=0):
        if ear_f is None:
            return repeat(ear_i, time_ms)
        slope = ear_f - ear_i
        func = Function("linear", a=ear_i, b=slope)
        return func.f(linspace(0,1,time_ms))

    def whole_cosine_line(self, ear_i, ear_mid, time_ms):
        amplitude = (ear_mid-ear_i)/2
        offset = ear_mid-amplitude
        func = Function("cosine", o=offset, a=amplitude, p=1)
        return func.f(linspace(0,1,time_ms))

    # similar to whole_cosine, starts and ends steeper
    def half_sine_line(self, ear_i, ear_mid, time_ms):
        func = Function("sine", o=ear_i, a=ear_mid-ear_i p=2)
        return func.f(linspace(0,1,time_ms))

    def half_cosine_line(self, ear_i, ear_f, time_ms):
        amplitude = (ear_f-ear_i)/2
        offset = ear_f-amplitude
        func = Function("cosine", o=offset, a=amplitude, p=2)
        return func.f(linspace(0,1,time_ms))

    # similar to half_cosine, starts without a gradual climb/decline
    # (more steep at start)
    def quarter_sine_line(self, ear_i, ear_f, time_ms):
        amplitude = ear_f - ear_i
        offset = ear_f - amplitude
        func = Function("sine", o=offset, a=amplitude, p=4)
        return func.f(linspace(0,1,time_ms))

    # applies a sawtooth line multiple times within the given time interval
    def sawtooth_line(self, ear_i, ear_f, time_ms, cycles=4):
        amplitude = (ear_f - ear_i)/2
        offset = amplitude + ear_i
        func = Function("sawtooth", o=offset, a=amplitude, p=1/cycles)
        return func.f(linspace(0,1,time_ms))

    def get_time(self, m1: int, b1: Union[int, float], m2: int=None, b2: Union[int, float]=None, end: bool=False, delta: bool=True):
        m -= 1
        t1 = self.arr[m1-1].beat(b1)
        t = 0,0
        # calculate time between m1,b1 and end of piece
        if end:
            m2 = self.arr[-1].mm
            b2 = self.arr[-1].beat(len(self.arr[-1]) + 1)
        if m2 and b2:
            m2 -= 1
            t2 = self.arr[m2-1].beat(b2)
            t = t1, t2
            if delta:
                return abs(t[1] - t[0])
            return t
        return t1

    def apply_effect(self, effect: str=None, m1: int=None, b1: Union[int, float]=None, m2: int=None, b2: Union[int, float]=None, ear_i: float=None, ear_mid: float=None, ear_f: float=None, cycles: Union[int, str]=None, clip_effect: bool=True, _json: dict=None) -> np.ndarray:

        if _json:
            try:
                effect = _json["effect"]
                m1 = _json["m1"]
                b1 = _json["b1"]
                m2 = _json["m2"]
            except KeyError as e:
                print(f"KeyError: {str(e)}")
                raise KeyError(e)
            if "b2" in _json:
                b2 = _json["b2"]
            if b2 is None and str(m2) != "end":
                raise ValueError(f"apply_effect({str(_json)}): missing required \"b2\" argument")
            if "ear_i" in _json:
                ear_i = _json["ear_i"]
            if "ear_mid" in _json:
                ear_mid = _json["ear_mid"]
            if "ear_f" in _json:
                ear_f = _json["ear_f"]
            if "cycles" in _json:
                cycles = _json["cycles"]

        if str(m2) == "end":
            time_ms = np.floor(self.get_time(m1, b1, end=True, delta=True) * 100)
        else:
            if b2 is None:
                raise ValueError(f"apply_effect(): missing required \"b2\" argument"
            time_ms = np.floor(self.get_time(m1, b1, m2, b2, delta=True) * 1000)

        # crop effect by one millisecond so that proceeding effect
        # is alligned correctly
        if clip_effect:
            time_ms -= 1

        if effect == "whole_cosine":
            return self.whole_cosine_line(ear_i, ear_mid, time_ms)

        elif effect == "half_sine":
            return self.half_sine_line(ear_i, ear_mid, time_ms)

        elif effect == "quarter_sine":
            return self.quarter_sine_line(ear_i, ear_f, time_ms)

        elif effect == "half_cosine":
            return self.half_cosine_line(ear_i, ear_f, time_ms)

        elif effect == "none":
            return self.straight_line(0, time_ms=time_ms)

        elif effect == "straight":
            if ear_f is None or ear_i == ear_f:
                return self.straight_line(ear_i, time_ms=time_ms)
            else:
                return self.straight_line(ear_i, ear_f, time_ms)

        elif effect == "sawtooth":
            if str(cycles) == "per_beat" or str(cycles) == "per beat":
                try:
                    cycles = self.delta_quarternotes(m1, b1, m2, b2)
                except ValueError as e:
                    print(e)
                    return self.straight_line(ear_i, time_ms=time_ms)
            return self.sawtooth_line(ear_i, ear_f, time_ms, int(cycles))

        else:
            raise ValueError(f"improper effect format: {effect}")
        
    def get_time_inverse(self, t_sec):
        epsilon = 1e-5
        for i, m in enumerate(self.arr):
            if m.t_f > t_sec:
                continue
            elif abs(m.t_f - t_sec) < epsilon:
                return i+2,1
            else:
                for j, beat in enumerate(m.beats):
                    if t_sec > beat:
                        continue
                    elif abs(t_sec - beat) < epsilon:
                        return i+1,j+1
                    elif t_sec < beat:
                        return i+1,j+0.5
                return -1,-1
        return -1,-1
                


if __name__ == "__main__":
    m = gen_measures()

