from typing import NamedTuple

FieldCoordinates = NamedTuple('FieldCoordinates', [('row', int), ('column', int)])


class Field(dict[FieldCoordinates]):
    pass
    # def __init__(self, coordinates: dict[FieldCoordinates]):
    #     self._coordinates = coordinates
    #
    # def __getitem__(self, item: FieldCoordinates):
    #     return self._coordinates[item]
