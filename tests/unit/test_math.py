import pytest

from pyglet.math import Mat4


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
        if matrix[4*c + c] == 0:
            for r in range(c + 1, 4):
                if matrix[4*r + c] != 0:
                    matrix = row_swap(matrix, c, r)
                    i = row_swap(i, c, r)

        # Make 0's in column for rows that aren't pivot row
        for r in range(4):
            if r != c:  # not the pivot row
                r_piv = matrix[4*r + c]
                if r_piv != 0:
                    piv = matrix[4*c + c]
                    scalar = r_piv / piv
                    matrix = row_mul(matrix, c, scalar)
                    matrix = row_sub(matrix, c, r)
                    i = row_mul(i, c, scalar)
                    i = row_sub(i, c, r)

        # Put matrix in reduced row-echelon form.
        piv = matrix[4*c + c]
        matrix = row_mul(matrix, c, 1/piv)
        i = row_mul(i, c, 1/piv)
    return i


def row_swap(matrix, r1, r2):
    lo = min(r1, r2)
    hi = max(r1, r2)
    values = (matrix[:lo*4]
              + matrix[hi*4:hi*4 + 4]
              + matrix[lo*4 + 4:hi*4]
              + matrix[lo*4:lo*4 + 4]
              + matrix[hi*4 + 4:])
    return Mat4(values)


def row_mul(matrix, r, x):
    values = (matrix[:r*4]
              + tuple(v * x for v in matrix[r*4:r*4 + 4])
              + matrix[r*4 + 4:])
    return Mat4(values)


# subtracts r1 from r2
def row_sub(matrix, r1, r2):
    row1 = matrix[4*r1:4*r1 + 4]
    row2 = matrix[4*r2:4*r2 + 4]
    values = (matrix[:r2*4]
              + tuple(v2 - v1 for (v1, v2) in zip(row1, row2))
              + matrix[r2*4 + 4:])
    return matrix.Mat4(values)


################
# test functions
################

def test_creation(mat4):
    assert len(mat4) == 16
    assert mat4 == (1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1)


def test_creation_from_list(mat4):
    mat4_from_list = Mat4([1, 0, 0, 0,
                           0, 1, 0, 0,
                           0, 0, 1, 0,
                           0, 0, 0, 1])
    assert mat4_from_list == mat4


def test_matrix_inversion(mat4):
    # Confirm `__invert__` method matches long hand utility method:
    inverse_1 = inverse(mat4)
    inverse_2 = ~mat4
    assert round(inverse_1, 9) == round(inverse_2, 9)
    # Confirm that Matrix @ it's inverse == identity Matrix:
    assert round(mat4 @ inverse_1, 9) == Mat4()
    assert round(mat4 @ inverse_2, 9) == Mat4()

