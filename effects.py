#!/usr/bin/env python
from midi_parser import MeasureArray
import json

def apply_effects(effect_set: str="vibes", json_file: str="effects.json", midi_file: str="media/measures.midi"):
    with open(json_file) as f:
        data = json.load(f)
    verify_json(data)
    m = MeasureArray(filename=midi_file)
    arr = []
    for e in data[effect_set]:
        arr.extend(m.apply_effect(e))
    return arr

def verify_json(data: dict):
    for s in data:
        prev_m = data[s][0]["m2"]
        prev_b = data[s][0]["b2"]
        for e in data[s][1:]:
            if e["m1"] != prev_m:
                raise ValueError(f"json error in {s}, measure {e['m1']}:\nmeasure number {e['m1']} != {prev_m}")
            elif e["b1"] != prev_b:
                raise ValueError(f"json error in {s}, measure {e['m1']}:\nbeat number {e['b1']} != {prev_b}")
            prev_m = e["m2"]
            if "b2" in e:
                prev_b = e["b2"]
            else:
                break



