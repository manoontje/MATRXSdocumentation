import json
import os
from pathlib import Path

from shapely.geometry import Polygon, Point

import math

object_counter = 0


def next_obj_id():
    global object_counter
    res = object_counter
    object_counter += 1
    return res


def get_inheritence_path(callable_class):
    parents = callable_class.mro()
    parents = [str(p.__name__) for p in parents]
    return parents


def get_all_classes(class_, omit_super_class=False):
    # Include given class or not
    if omit_super_class:
        subclasses = set()
    else:
        subclasses = {class_}

    # Go through all child classes
    work = [class_]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    # Create a dict out of it
    act_dict = {}
    for action_class in subclasses:
        act_dict[action_class.__name__] = action_class

    return act_dict


def get_all_inherited_classes(super_type):
    all_classes = {super_type}
    work = [super_type]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in all_classes:
                all_classes.add(child)
                work.append(child)

    class_dict = {}
    for classes in all_classes:
        class_dict[classes.__name__] = classes

    return class_dict


def get_distance(coord1, coord2):
    """ Get distance between two x,y coordinates """
    dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
    dist = math.sqrt(sum(dist))
    return dist


def get_default_value(class_name, property_name):
    defaults = __load_defaults()

    if class_name in defaults:
        if property_name in defaults[class_name]:
            return defaults[class_name][property_name]
        else:
            raise Exception(f"The attribute {property_name} is not present in the defaults.json for class "
                            f"{class_name}.")
    else:
        raise Exception(f"The class name {class_name} is not present in the defaults.json.")


def __load_defaults():
    file_path = "matrxs/scenarios/defaults.json"
    return load_json(file_path)


def load_scenario(scenario_file):
    raise NotImplementedError


def load_json(file_path):
    with open(file_path, "r") as read_file:
        json_dict = json.load(read_file)
    return json_dict


def _get_line_coords(p1, p2):
    line_coords = []

    x1 = int(p1[0])
    x2 = int(p2[0])
    y1 = int(p1[1])
    y2 = int(p2[1])

    is_steep = abs(y2 - y1) > abs(x2 - x1)
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    rev = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        rev = True

    deltax = x2 - x1
    deltay = abs(y2 - y1)
    error = int(deltax / 2)
    y = y1

    if y1 < y2:
        ystep = 1
    else:
        ystep = -1
    for x in range(x1, x2 + 1):
        if is_steep:
            line_coords.append((y, x))
        else:
            line_coords.append((x, y))
        error -= deltay
        if error < 0:
            y += ystep
            error += deltax
    # Reverse the list if the coordinates were reversed
    if rev:
        line_coords.reverse()

    return line_coords


def _get_hull_and_volume_coords(corner_coords):
    # Check if there are any corners given
    if len(corner_coords) <= 1:
        raise Exception(f"Cannot create area; {len(corner_coords)} corner coordinates given, requires at least 2.")

    # Get the polygon represented by the corner coordinates
    # TODO remove the dependency to Shapely
    polygon = Polygon(corner_coords)

    (minx, miny, maxx, maxy) = polygon.bounds
    minx = int(minx)
    miny = int(miny)
    maxx = int(maxx)
    maxy = int(maxy)

    volume_coords = []
    for x in range(minx, maxx + 1):
        for y in range(miny, maxy + 1):
            p = Point(x, y)
            if polygon.contains(p):
                volume_coords.append((x, y))

    hull_coords = []
    corners = list(zip(polygon.exterior.xy[0], polygon.exterior.xy[1]))
    for idx in range(len(corners) - 1):
        p1 = corners[idx]
        p2 = corners[idx + 1]
        line_coords = _get_line_coords(p1, p2)
        hull_coords.extend(line_coords)

    # Add corners as well
    for corner in corner_coords:
        hull_coords.append(tuple(corner))

    return hull_coords, volume_coords
