import attr
import collections


def increment(value):
    return str(int(value) + 1)


def reset(value):
    return "0"


class Part:
    def __init__(self, name, value, position):
        self.name = name
        self.value = value
        self.position = position

    def __repr__(self):
        return self.name + ":" + (self.value or "<none>")

    def __str__(self):
        return repr(self)


def parse_version(regex, version):
    match = regex.match(version)
    matchdict = match.groupdict()
    res = list()
    for name, value in matchdict.items():
        position = match.start(name)
        if position != -1:
            part = Part(name, value, position)
            res.append(part)
    res.sort(key=lambda x: x.position)
    return res


def get_parts(regex, version):
    match = regex.match(version)
    matchdict = match.groupdict()
    return matchdict.group()


class Bumper:
    def __init__(self, *, parse, serialize):
        self.parse = parse
        self.serialize = serialize

    def bump(self, version, part_name):
        known_parts = get_parts(version)
        parts = parse_version(self.parse, version)
        found = False
        for part in parts:
            if part.name == part_name:
                part.value = increment(part.value)
                found = True
            else:
                if found:
                    part.value = reset(part.value)
        for known_parts in known_part:
            pass

        template = self.serialize[0]
        for part in parts:
            template = template.replace("{%s}" % part.name, part.value)
        return template
