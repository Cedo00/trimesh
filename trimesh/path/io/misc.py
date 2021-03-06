import numpy as np

from ..entities import Line, Arc

from ... import util

from ...geometry import faces_to_edges
from ...grouping import group_rows

from collections import deque

from shapely import ops


def dict_to_path(drawing_obj):
    '''

    '''
    loaders = {'Arc': Arc, 'Line': Line}
    vertices = np.array(drawing_obj['vertices'])
    entities = [None] * len(drawing_obj['entities'])
    for entity_index, entity in enumerate(drawing_obj['entities']):
        entities[entity_index] = loaders[entity['type']](
            points=entity['points'], closed=entity['closed'])
    return {'entities': entities,
            'vertices': vertices}


def lines_to_path(lines):
    '''
    Turn line segments into a Path2D or Path3D object.

    Parameters
    ------------
    line: (n, 2, 2) float, Path2D object from line segments
          (n, 2, 3) float, Path3D object from line segments
          (n, 2) float: Path2D object, assumes vertices are connected
          (n, 3) float: Path3D object, assumes vertices are connected

    Returns
    -----------
    kwargs: dict, kwarg for Path constructor
    '''
    lines = np.asanyarray(lines, dtype=np.float64)

    if util.is_shape(lines, (-1, (2, 3))):
        # the case where we have a list of points
        # we are going to assume they are connected
        result = {'entities': np.array([Line(np.arange(len(lines)))]),
                  'vertices': lines}
        return result

    elif util.is_shape(lines, (-1, 2, 2)):
        # case where we have 2D lines
        # linemerge will quickly clean up the lines
        linestrings = ops.linemerge(lines)
        return linestrings_to_path(linestrings)

    elif util.is_shape(lines, (-1, 2, 3)):
        entities = [Line([i, i + 1])
                    for i in range(0, (lines.shape[0] * 2) - 1, 2)]
        vertices = lines.reshape((-1, lines.shape[2]))
        result = {'entities': entities,
                  'vertices': vertices}
    else:
        raise ValueError('Lines must be (n,(2|3)) or (n,2,(2|3))')
    return result


def polygon_to_path(polygon):
    '''
    Load shapely Polygon objects into a trimesh.path.Path2D object

    Parameters
    -------------
    polygon: shapely.geometry.Polygon object

    Returns
    -------------
    kwargs: dict, keyword arguments for Path2D constructor
    '''
    entities = deque([Line(points=np.arange(len(polygon.exterior.coords)))])
    vertices = deque(np.array(polygon.exterior.coords))

    # append interiors as single Line objects
    for boundary in polygon.interiors:
        entities.append(Line(np.arange(len(boundary.coords)) +
                             len(vertices)))
        vertices.extend(boundary.coords)

    return {'entities': np.array(entities),
            'vertices': np.array(vertices)}


def linestrings_to_path(multi):
    '''
    Load shapely LineString objects into a trimesh.path.Path2D object

    Parameters
    -------------
    multi: LineString or MultiLineString

    Returns
    -------------
    kwargs: dict, keyword arguments for Path2D constructor
    '''
    entities = deque()
    vertices = deque()

    if not util.is_sequence(multi):
        multi = [multi]

    for line in multi:
        if hasattr(line, 'coords'):
            coords = np.array(line.coords)
            entities.append(Line(np.arange(len(coords)) +
                                 len(vertices)))
            vertices.extend(coords)

    return {'entities': np.array(entities),
            'vertices': np.array(vertices)}


def faces_to_path(mesh, face_ids=None):
    '''
    Given a mesh and face indices find the outline edges and
    turn them into a Path3D.

    Parameters
    ---------
    mesh:  Trimesh object
    facet: (n) list of indices of mesh.faces

    Returns
    ---------
    kwargs: dict, kwargs for Path3D constructor
    '''
    if face_ids is None:
        faces = mesh.faces
    else:
        faces = mesh.faces[face_ids]

    edges = np.sort(faces_to_edges(faces), axis=1)
    unique_edges = group_rows(edges, require_count=1)
    segments = mesh.vertices[edges[unique_edges]]
    return lines_to_path(segments)
