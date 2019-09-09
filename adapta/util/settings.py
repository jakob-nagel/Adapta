import json
import pkg_resources as pkg


default = pkg.resource_filename('adapta.resources', 'default_settings.json')
with open(default) as jsonfile:
    _settings = json.load(jsonfile)


def load(path):
    with open(path) as jsonfile:
        for name, value in json.load(jsonfile).items():
            _settings[name].update(value)


def _getter(name):
    def getter(self):
        value = _settings[self.__class__.__name__][name]
        if isinstance(value, str) and value[0] == '<' and value[-1] == '>':
            class_name, attribute_name = value[1:-1].split('.')
            value = _settings[class_name][attribute_name]
        return value
    return property(getter)


def use_settings(cls):
    for name in _settings[cls.__name__]:
        setattr(cls, name, _getter(name))
    return cls
