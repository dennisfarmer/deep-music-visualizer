#!/usr/bin/env python
# Dennis Farmer - October 1, 2021

#import numpy as np  # used within NumpyTemplate class
from argparse import ArgumentParser
from string import Template
import sys

class NumpyTemplate(Template):
    def __init__(self, name: str, template: str, default: dict={}):
        self.name = name
        self.default = default
        self.params = list(self.default.keys())
        super(NumpyTemplate, self).__init__(template)

    def mapping(self, mapping):
        default_mapping = self.default.copy()
        default_mapping.update(mapping)
        return default_mapping

    def rename(self, new_name: str):
        if isinstance(new_name, str):
            self.name = name
        else: raise TypeError("Incorrect name type; should be string")

    def copy(self, default: dict=None):
        new = NumpyTemplate(self.name, self.template, self.default)
        if default:
            new.update(default)
        return new
    
    def update(self, new_default: dict=None, **kwargs):
        if new_default:
            self.default.update(new_default)
        self.default.update(kwargs)
        self.params = list(self.default.keys())

    def substitute(self, mapping=None, **kwargs):
        return super(NumpyTemplate, self).substitute(self.mapping(mapping or {}), **kwargs)

    def safe_substitute(self, mapping=None, **kwargs):
        return super(NumpyTemplate, self).safe_substitute(self.mapping(mapping or {}), **kwargs)

    def def_str(self):
        args = ""
        if self.params:
            for p in self.params:
                args += f", {p}={self.default[p]}"
        expr = self.template.replace("$", "")
        return f"def f(t{args}):\n\treturn {expr}"

    def lambda_str(self):
        args = ""
        if self.params:
            for p in self.params:
                args += f", {p}={self.default[p]}"
        expr = self.template.replace("$", "")
        return f"f = lambda t{args}: {expr}"

    def __str__(self):
        return f"# {self.name} function:\n{self.def_str()}"

class Function:
    def __init__(self, function_name: str, np_string: str=None, np_template: NumpyTemplate=None, **kwargs):
        self.default = {"p": "2*pi", "a": "1"}
        self.sawtooth = NumpyTemplate("sawtooth", "-(2*$a)/pi*arctan(cot((pi*t)/$p))", self.default)
        self.sine = NumpyTemplate("sine", "$a*np.sin((2*np.pi)/np.abs($p)*t)", self.default)
        self.cosine = NumpyTemplate("cosine", "$a*np.cos((2*np.pi)/np.abs($p)*t)", self.default)

        self.sine1 = self.sine.copy(default={"p": "pi/6", "a": "0.5"))
        self.sine1.rename("sine1")

        if np_template:
            if isinstance(np_template, NumpyTemplate):
                self.np_template = np_template
            else:
                raise ValueError("invalid Numpy Template, use NumpyTemplate object constructor")
        elif function_name in self.__dict__:
            if isinstance(self.__dict__[function_name], NumpyTemplate):
                self.np_template = self.__dict__[function_name]
            if np_string:
                print(f"WARNING: function {function_name} already defined", file=sys.stderr)
        elif np_string:
            self.np_template = NumpyTemplate(name=function_name, template=np_string)
            self.__dict__[function_name] = self.np_template
        else:
            raise ValueError("function name or Numpy Template not provided")

        self.name = self.np_template.name
        self.np_template.update(kwargs)
        self.update(kwargs)

    def update(self, function_name: str=None, np_template: NumpyTemplate=None, **kwargs):
        if function_name:
            if function_name in self.__dict__:
                if isinstance(self.__dict__[function_name], NumpyTemplate):
                    self.np_template = self.__dict__[function_name]
        elif np_template:
            if isinstance(np_template, NumpyTemplate):
                self.np_template = np_template
            else:
                raise ValueError("invalid Numpy Template, use NumpyTemplate object constructor")
        self.np_template.update(kwargs)
        scope = {}
        import_np = f"from numpy import pi, cos, sin, tan, arccos, arcsin, arctan, e, exp, sqrt, abs\ndef csc(t): return 1/sin(t)\ndef sec(t): return 1/cos(t)\ndef cot(t): return 1/tan(t)"
        exec(f"{import_np}\n{self.np_template.lambda_str()}", scope)
        function = scope['f']
        self.f = function

