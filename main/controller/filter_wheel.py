import itertools

class FilterWheel():

    def __init__(self, position_1, position_2, position_3, position_4, position_5, position_6, position_7, position_8):
        self.position_1 = position_1
        self.position_2 = position_2
        self.position_3 = position_3
        self.position_4 = position_4
        self.position_5 = position_5
        self.position_6 = position_6
        self.position_7 = position_7
        self.position_8 = position_8

    def filter_position_dict(self):
        i = itertools.count(0)
        return {filter:next(i) for filter in self.__dict__.values()}
