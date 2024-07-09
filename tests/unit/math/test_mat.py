import pytest

from pyglet.math import Mat3, Mat4, Vec3


@pytest.fixture()
def mat3():
    return Mat3()


@pytest.fixture()
def mat4():
    return Mat4()


##################
# helper functions
##################

def inverse(matrix):
    """The inverse of a Matrix.

    Using Gauss-Jordan elimination, the matrix supplied is transformed into
    the identity matrix using a sequence of elementary row operations (below).
    The same sequence of operations is applied to the identity matrix,
    transforming it into the supplied matrix's inverse.
    Elementary row operations:
        - multiply row by a scalar
        - swap two rows
        - add two rows together"""

    i = Mat4()  # identity matrix

    # The pivot in each column is the element at Matrix[c, c] (diagonal elements).
    # The pivot row is the row containing the pivot element. Pivot elements must
    # be non-zero.
    # Any time matrix is changed, so is i.
    for c in range(4):
        # Find and swap pivot row into place
        if matrix[4 * c + c] == 0:
            for r in range(c + 1, 4):
                if matrix[4 * r + c] != 0:
                    matrix = _row_swap(matrix, c, r)
                    i = _row_swap(i, c, r)

        # Make 0's in column for rows that aren't pivot row
        for r in range(4):
            if r != c:  # not the pivot row
                r_piv = matrix[4 * r + c]
                if r_piv != 0:
                    piv = matrix[4 * c + c]
                    scalar = r_piv / piv
                    matrix = _row_mul(matrix, c, scalar)
                    matrix = _row_sub(matrix, c, r)
                    i = _row_mul(i, c, scalar)
                    i = _row_sub(i, c, r)

        # Put matrix in reduced row-echelon form.
        piv = matrix[4 * c + c]
        matrix = _row_mul(matrix, c, 1 / piv)
        i = _row_mul(i, c, 1 / piv)
    return i


def _row_swap(matrix, r1, r2):
    lo = min(r1, r2)
    hi = max(r1, r2)
    values = (matrix[:lo * 4]
              + matrix[hi * 4:hi * 4 + 4]
              + matrix[lo * 4 + 4:hi * 4]
              + matrix[lo * 4:lo * 4 + 4]
              + matrix[hi * 4 + 4:])
    return Mat4(*values)


def _row_mul(matrix, r, x):
    values = (matrix[:r * 4]
              + tuple(v * x for v in matrix[r * 4:r * 4 + 4])
              + matrix[r * 4 + 4:])
    return Mat4(*values)


# subtracts r1 from r2
def _row_sub(matrix, r1, r2):
    row1 = matrix[4 * r1:4 * r1 + 4]
    row2 = matrix[4 * r2:4 * r2 + 4]
    values = (matrix[:r2 * 4]
              + tuple(v2 - v1 for (v1, v2) in zip(row1, row2))
              + matrix[r2 * 4 + 4:])
    return Mat4(*values)


############
# test cases
############
def test_mat3_creation(mat3):
    assert len(mat3) == 9
    assert mat3 == (1, 0, 0,
                    0, 1, 0,
                    0, 0, 1)


def test_mat4_creation(mat4):
    assert len(mat4) == 16
    assert mat4 == (1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1)


def test_mat4_inversion(mat4):
    # Confirm `__invert__` method matches long hand utility method:
    inverse_1 = inverse(mat4)
    inverse_2 = ~mat4
    assert round(inverse_1, 9) == round(inverse_2, 9)
    # Confirm that Matrix @ its inverse == identity Matrix:
    assert round(mat4 @ inverse_1, 9) == Mat4()
    assert round(mat4 @ inverse_2, 9) == Mat4()


def test_mat3_inversion(mat3):
    # TODO: add long hand inversion for mat3
    inverse_2 = ~mat3
    # Confirm that Matrix @ its inverse == identity Matrix:
    assert round(mat3 @ inverse_2, 9) == Mat3()


def test_mat3_associative_mul():
    swap_xy = Mat3(0, 1, 0, 1, 0, 0, 0, 0, 1)
    scale_x = Mat3(2, 0, 0, 0, 1, 0, 0, 0, 1)
    v1 = (swap_xy @ scale_x) @ Vec3(0, 1, 0)
    v2 = swap_xy @ (scale_x @ Vec3(0, 1, 0))
    assert v1 == v2 and abs(v1) != 0
