class Obj(dict):
    def __init__(self, d):
        super().__init__()
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [Obj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Obj(b) if isinstance(b, dict) else b)


def dict_2_obj(d: dict):
    return Obj(d)


def formated_content_picker(source, separator):
    temp_str = source[source.index(separator) + len(separator):]
    return temp_str[:temp_str.index(separator)]
