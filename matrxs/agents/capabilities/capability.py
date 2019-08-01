import numpy as np


class Capability:
    def __init__(self):
        pass


class SenseCapability(Capability):

    def __init__(self, detectable_objects):
        """Blabla

        Parameters
        ----------
        detectable_objects
        """
        super().__init__()
        self.__detectable_objects = {}
        for obj_type, sense_range in detectable_objects.items():
            if obj_type is None:
                # If the obj_type is none, we can detect all object types
                self.__detectable_objects = {"*": sense_range}  # hence all other object types in there have no effect
                break  # as such we break this loop
            else:
                if sense_range > 0:
                    self.__detectable_objects[obj_type] = sense_range
                else:
                    self.__detectable_objects[obj_type] = np.inf

    def get_capabilities(self):
        return self.__detectable_objects
