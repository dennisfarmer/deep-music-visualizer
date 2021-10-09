#!/usr/bin/env python
# Dennis Farmer - October 8, 2021
# Midi Parser that retrieves timemarks for each measure of music within a midi file

from mido import MidiFile, tempo2bpm
from numpy import linspace

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
        self.tsig = (num, den)
    def update(self, num: int=None, den: int=None):
        self.tsig = (num, den)
    def __str__(self):
        return f"{self.tsig[0]}/{self.tsig[1]}"
    def __eq__(self, other):
        if isinstance(other, TimeSignature):
            return self.tsig == other.tsig
        else: return False

class Measure:
    def __init__(self, mm: MeasureNumber, bpm: Tempo, tsig: TimeSignature, t_0: float=None, t_f: float=None):
        self.mm = mm
        self.bpm = bpm
        self.tsig = tsig
        self.t_0 = t_0
        self.t_f = t_f
    def __str__(self):
        return f"{self.mm}: {self.tsig} @{self.bpm} t_0={self.t_0:.2f} -> t_f={self.t_f:.2f}"

class MetaEvent:
    def __init__(self, time: float, _type: str, data):
        self.time=time
        self.type=_type
        self.data=data
    def __str__(self):
        return f"t={self.time:.4f}: {self.data.__str__()}"

def calculate_measure_lengths(meta_events) -> [Measure]:
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
            if prev["tsig"].tsig[1] == 8:
                num_beats*=2
            num_measures =  round(num_beats / prev["tsig"].tsig[0])
            num_beats = round(num_beats)
            # time_dist[-1]: end time of last measure in chunk 
            time_dist = linspace(prev["time"], curr["time"], num_measures+1)
            for i in range(num_measures):
                mm = len(measures) + 1
                measures.append(Measure(mm, bpm=prev["bpm"], tsig=prev["tsig"], t_0=time_dist[i], t_f=time_dist[i+1]))

        prev = curr.copy()
    return measures
                
def gen_measures(filename="./media/measures.midi", quiet=False) -> [Measure]:
    mid = MidiFile(filename)
    t = 0
    events = []
    for msg in mid:
        t += msg.time
        if msg.type == 'time_signature':
            events.append(MetaEvent(t, msg.type, TimeSignature(msg.numerator, msg.denominator)))
        elif msg.type == 'set_tempo':
            events.append(MetaEvent(t, msg.type, Tempo(round(tempo2bpm(msg.tempo)))))

    measures = calculate_measure_lengths(events)
    if not quiet:
        #for e in events:
            #print(e)
        for m in measures:
            print(m)
    # Son't forget to adjust last measure to have a differnt end time to account for reverb
    return measures

if __name__ == "__main__":
    m = gen_measures()

