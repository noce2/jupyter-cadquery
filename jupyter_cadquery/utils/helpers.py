import math
import numpy as np


def explode(edge_list):
    return [[edge_list[i], edge_list[i + 1]] for i in range(len(edge_list) - 1)]


def flatten(nested_list):
    return [y for x in nested_list for y in x]


# CAD helpers


def distance(v1, v2):
    return np.linalg.norm([x - y for x, y in zip(v1, v2)])


def rad(deg):
    return deg / 180.0 * math.pi


def rotate_x(vector, angle):
    angle = rad(angle)
    mat = np.array([[1, 0, 0], [0, math.cos(angle), -math.sin(angle)], [0, math.sin(angle), math.cos(angle)],])
    return tuple(np.matmul(mat, vector))


def rotate_y(vector, angle):
    angle = rad(angle)
    mat = np.array([[math.cos(angle), 0, math.sin(angle)], [0, 1, 0], [-math.sin(angle), 0, math.cos(angle)],])
    return tuple(np.matmul(mat, vector))


def rotate_z(vector, angle):
    angle = rad(angle)
    mat = np.array([[math.cos(angle), -math.sin(angle), 0], [math.sin(angle), math.cos(angle), 0], [0, 0, 1],])
    return tuple(np.matmul(mat, vector))


def rotate(vector, angle_x=0, angle_y=0, angle_z=0):
    v = tuple(vector)
    if angle_z != 0:
        v = rotate_z(v, angle_z)
    if angle_y != 0:
        v = rotate_y(v, angle_y)
    if angle_x != 0:
        v = rotate_x(v, angle_x)
    return v


def pp_vec(v):
    return "(" + ", ".join([f"{o:10.5f}" for o in v]) + ")"


def pp_loc(loc, format=True):
    T = loc.wrapped.Transformation()
    t = T.Transforms()
    q = T.GetRotation()
    if format:
        return pp_vec(t) + ", " + pp_vec((q.X(), q.Y(), q.Z(), q.W()))
    else:
        return (t, (q.X(), q.Y(), q.Z(), q.W()))


#
# tree search
#


def tree_find_single_selector(tree, selector):
    if tree.name == selector:
        return tree

    for c in tree.children:
        result = tree_find_single_selector(c, selector)
        if result is not None:
            return result
    return None

