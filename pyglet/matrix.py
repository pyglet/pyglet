

class Mat4:
    """A 4x4 Matrix

    `Mat4` is a simple 4x4 Matrix, with a few operators.
    Two types of multiplication are possible. The "*" operator
    will perform elementwise multiplication, wheras the "@"
    operator will perform Matrix multiplication.
    """
    __slots__ = 'array'

    def __init__(self, array=None, main=1.0):
        """Create a Matrix

        A Matrix can be created with tuple containing 16 floats
        or ints. Alternatively, you can create provide an int
        for the main diagonal. If nothing is provided, an identity
        Matrix will be created (1.0 on the main diagonal).

        :Parameters:
            `array` : tuple of float or int
                A one dimentional array containing the elements.
            `main` : float or int
                The data to fill the main diagonal with. Ignored
                if `array` is provided.
        """
        self.array = array or (main, 0.0, 0.0, 0.0,
                               0.0, main, 0.0, 0.0,
                               0.0, 0.0, main, 0.0,
                               0.0, 0.0, 0.0, main)

    def __add__(self, other):
        assert type(other) is Mat4, "Only addition with Mat4 types is supported"
        return Mat4(array=tuple(s + o for s, o in zip(self.array, other.array)))

    def __sub__(self, other):
        assert type(other) is Mat4, "Only subtraction from Mat4 types is supported"
        return Mat4(array=tuple(s - o for s, o in zip(self.array, other.array)))

    def __mul__(self, other):
        assert type(other) is Mat4, "Only multiplication with Mat4 types is supported"
        return Mat4(array=tuple(s * o for s, o in zip(self.array, other.array)))

    def __matmul__(self, other):
        assert type(other) is Mat4
        sarray = self.array
        oarray = other.array
        # Rows:
        r0 = sarray[0:4]
        r1 = sarray[4:8]
        r2 = sarray[8:12]
        r3 = sarray[12:16]
        # Columns:
        c0 = oarray[0::4]
        c1 = oarray[1::4]
        c2 = oarray[2::4]
        c3 = oarray[3::4]

        a = sum(s * o for s, o in zip(r0, c0))
        b = sum(s * o for s, o in zip(r0, c1))
        c = sum(s * o for s, o in zip(r0, c2))
        d = sum(s * o for s, o in zip(r0, c3))

        e = sum(s * o for s, o in zip(r1, c0))
        f = sum(s * o for s, o in zip(r1, c1))
        g = sum(s * o for s, o in zip(r1, c2))
        h = sum(s * o for s, o in zip(r1, c3))

        i = sum(s * o for s, o in zip(r2, c0))
        j = sum(s * o for s, o in zip(r2, c1))
        k = sum(s * o for s, o in zip(r2, c2))
        l = sum(s * o for s, o in zip(r2, c3))

        m = sum(s * o for s, o in zip(r3, c0))
        n = sum(s * o for s, o in zip(r3, c1))
        o = sum(s * o for s, o in zip(r3, c2))
        p = sum(s * o for s, o in zip(r3, c3))

        Mat4((a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p))

    def __getitem__(self, index):
        if type(index) is tuple:
            row, column = index
            assert 0 <= row <= 3 and 0 <= column <= 3, "row and column must range from 0-3"
            return self.array[row * 3 + column]
        else:
            return self.array[index]

    def __iter__(self):
        return iter(self.array)

    def __repr__(self):
        arr = self.array
        return f"{self.__class__.__name__}{arr[0:4]}\n    {arr[4:8]}\n    {arr[8:12]}\n    {arr[12:16]}"
