from environment.objects.basic_objects import EnvObject
from copy import copy


class AgentAvatar(EnvObject):
    """
    This class is a representation of an agent in the GridWorld.
    It is used as a measure to keep the real Agent code and Environment code
    seperate. This AgentAvatar is used by the environment to update the GUI, perform actions,
    and update properties. It is kept in sync with the real Agent object every iteration.
    """

    def __init__(self, agent_id, sense_capability, action_set, get_action_func,
                 set_action_result_func, ooda_observe, ooda_orient, agent_properties,
                 properties_agent_writable, class_name_agent):

        # define which properties are required for the agent
        self.required_props = ["location", "size", "is_traversable", "colour", "shape", "name", "agent_speed_in_ticks"]

        # check validity of the passed properties
        self.__check_properties_validity(agent_id, agent_properties)

        # create an Env obj from this agent
        super().__init__(obj_id=agent_id,
                         obj_name=agent_properties["name"],
                         location=agent_properties["location"],
                         properties=agent_properties,
                         is_traversable=agent_properties["is_traversable"])

        # Set the variables that the grid world expect each agent avatar to have
        self.is_carrying = []  # list of EnvObjects that this object carries

        # save the other
        self.sense_capability = sense_capability
        self.action_set = action_set
        self.get_action_func = get_action_func
        self.set_action_result_func = set_action_result_func
        self.ooda_observe = ooda_observe
        self.ooda_orient = ooda_orient
        self.class_name_agent = class_name_agent
        self.properties_agent_writable = properties_agent_writable

        # defines an agent is blocked by an action which takes multiple timesteps
        self.blocked = False
        # is the last action performed by the agent, at what tick and how long it takes
        self.last_action = {"duration_in_ticks": 0, "tick": 0}


    def __check_properties_validity(self, id, props):
        """
        Check if all required properties are present
        :param id {int}:        (human)agent_id
        :param props {dict}:    dictionary with agent properties
        """
        # check if all required properties have been defined
        for prop in self.required_props:
            if prop not in props:
                raise Exception(f"The (human) agent with {id} is missing the property {prop}. \
                        All of the following required properties need to be defined: {self.required_props}.")


    def set_agent_busy(self, curr_tick, action_duration):
        """
        specify the duration of the action in ticks currently being executed by the
        agent, and its starting tick
        """
        self.last_action = {"duration_in_ticks": action_duration, "tick": curr_tick}


    def check_agent_busy(self, curr_tick):
        """
        check if the agent is done with executing the action
        """
        self.blocked =  not( (curr_tick >= self.last_action["tick"] + self.last_action["duration_in_ticks"]) and \
                             (curr_tick >= self.last_action["tick"] + self.properties["agent_speed_in_ticks"]) )
        return self.blocked


    def set_agent_changed_properties(self, props):
        """
        The Agent has possibly changed some of its properties during its OODA loop.
        Here the agent properties are also updated in the Agent Avatar, if it
        was not a agent_read_only property.
        """
        # get all agent properties of this Agent Avatar in one dictionary
        AA_props = self.get_properties()

        # check for each property if it has been changed by the agent, and if we need
        # to update our local copy (here in Agent Avatar) of the agent properties to match that
        for prop in props:
            if prop not in AA_props:
                raise Exception(f"Agent {self.obj_id} tried to remove the property {prop}, which is not allowed.")

            # check if the property has changed, and skip if not the case
            if props[prop] == AA_props[prop]:
                continue

            # if the agent has changed the property, check if the agent has permission to do so
            if prop not in self.properties_agent_writable:
                raise Exception(f"Agent {self.obj_id} tried to change a non-writable property: {prop}.")

            ## the agent changed the property and the agent had permission to do so
            # update special properties
            if prop == 'location':
                self.location = props[prop]
            elif prop == "is_traversable":
                self.is_traversable = props[prop]
            elif prop == "name":
                self.name = props[prop]
            # update normal properties
            else:
                self.properties = props[prop]

    def get_properties(self):
        """
        Overrides the get_properties of EnvObject with the purpose to translate all objects this agent avatar is
        carrying to a dictionary and append it to its properties.
        :return: A dictionary of properties describing this agent and its avatar.
        """
        props = super().get_properties()

        # Go through all objects we are carrying, append their properties to a list and assign it to our properties
        carrying_props_list = []
        for obj in self.is_carrying:
            carrying_props_list.append(obj.get_properties())
        props['carrying'] = carrying_props_list

        return props

    @property
    def location(self):
        """
        We override the location pythonic property here so we can override its setter.
        :return: The location tuple of the form; (x, y).
        """
        return tuple(self.__location)

    @location.setter
    def location(self, loc):
        """
        Overrides the setter of the location (pythonic) property so we can transfer also all carried objects with us
        on any location change made anywhere.
        :param loc:
        :return:
        """
        # Set the location to our private location xy list
        self.__location = loc

        # Carrying action is done here
        # First we check if we even have a 'carrying' property, as the future might hold an AgentAvatar who specifically
        # removes this property. In that case we return.
        if 'carrying' not in self.properties.keys():
            return
        # Next we retrieve whatever it is the agent avatar is carrying (if we have a 'carrying' property at all)
        carried_objs = self.properties['carrying']
        # If we carry nothing, we are done
        if len(carried_objs) == 0:
            return
        # Otherwise we loop over all objects and adjust their location accordingly (since these are also EnvObjects,
        # their setter for location gets called, in the case we are carrying an AgentAvatar this setter is called
        for obj in carried_objs:
            obj.location = loc  # this requires all objects in self.properties['carrying'] to be EnvObject
