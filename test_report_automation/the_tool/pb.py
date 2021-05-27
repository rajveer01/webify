from math import floor


exp = 'Exception: '


class IncrementNum:
    x = 0
    @property
    def f_num(self):
        self.x = floor(self.x) + 1
        return str(self.x) + ": "

    @property
    def s_num(self):
        if self.x % 1 > 0.7:
            self.x -= 0.7
        else:
            self.x += 0.1
        return str(round(self.x, 1)) + ': '


n = IncrementNum()
