#!/usr/bin/env python
from midi_parser import MeasureArray
import json

def apply_effects(effect_set: str="vibes"):
    jsonfile = "effects.json"
    f = open(jsonfile)
    data = json.load(f)
    f.close()
    m = MeasureArray(filename="./media/measures.midi")
    arr = []
    for e in data[effect_set]:
        arr.extend(m.apply_effect(_json=e))
    return arr


