

class Mat4:
    def __init__(self, array=None, identity=1.0):
        self.array = array or (identity, 0.0, 0.0, 0.0,
                               0.0, identity, 0.0, 0.0,
                               0.0, 0.0, identity, 0.0,
                               0.0, 0.0, 0.0, identity)

    def __mul__(self, other):
        assert type(other) is Mat4
        return Mat4(array=tuple(s * o for s, o in zip(self.array, other.array)))

    def __matmul__(self, other):
        assert type(other) is Mat4
        pass

    def __iter__(self):
        return iter(self.array)

    def __repr__(self):
        arr = self.array
        return f"{self.__class__.__name__}{arr[0:4]}\n    {arr[4:8]}\n    {arr[8:12]}\n    {arr[12:16]}"
