from copy import deepcopy


BUS_PREFIX = 'bus.'


def with_headroom(project):
    result = deepcopy(project)
    for target, value in result.parameters.items():
        if target.startswith(BUS_PREFIX):
            result.parameters[target] = value // 2
    for lane in result.automation:
        if lane.target.startswith(BUS_PREFIX):
            for point in lane.points:
                point.value //= 2
    return result.validate()
