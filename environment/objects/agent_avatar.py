from environment.objects.env_object import EnvObject

from scenario_manager.helper_functions import get_default_value


class AgentAvatar(EnvObject):

    def __init__(self, location, possible_actions, sense_capability, class_callable,
                 callback_agent_get_action, callback_agent_set_action_result, callback_agent_observe,
                 name="Agent", is_human_agent=False,
                 customizable_properties=None,
                 is_traversable=None, carried_by=None, team=None, agent_speed_in_ticks=None,
                 visualize_size=None, visualize_shape=None, visualize_colour=None,
                 **custom_properties):
        """
        This class is a representation of an agent in the GridWorld.
        It is used as a measure to keep the real Agent code and Environment code separate. This AgentAvatar is used by
        the environment to update the GUI, perform actions, and update properties. It is kept in sync with the real
        Agent object every iteration.

        It inherits from EnvObject which allows you set any custom properties you want. In addition it also has all the
        mandatory properties of an EnvObject plus a few extra. Which is the team name the agent is part of (if any) and
        what the avatar is carrying.

        In addition the avatar keeps a set of callbacks to methods inside the Agent. This forms the connection between
        the GridWorld (that calls them) and the Agent (that defined them).

        :param location: List or tuple of length two. Mandatory. The location of the AgentAvatar in the grid world.
        :param possible_actions: The list of Action class names this agent may be able to perform. This allows you to
        create agents that can only perform a couple of the available actions.
        :param sense_capability: The SenseCapability object.
        :param class_callable: The Agent class; in other words, the class of the agent's brain. This is stored here so
        that the Visualizer (which visualises an agent based on this avatar object) and agents knows what kind of agent
        it is. Allows you to visualize certain agent types in a certain way.

        :param callback_agent_get_action: The callback function as defined by the Agent instance of which this is an
        AgentAvatar of. It is called each tick by the GridWorld. As such the GridWorld determines when the Agent can
        perform an action by calling this function which is stored in the Agent's AgentAvatar.
        :param callback_agent_set_action_result: Same as the callback_get_action but is used by GridWorld to set the
        ActionResult object in the Agent after performing the action. This allows the Agent to know how its planned
        action went.
        :param callback_agent_observe: Similar to callback_agent_get_action, is used by GridWorld to obtain the
        processed state dictionary of the Agent. As the GridWorld does not know exactly what the Agent is allowed to
        see or not, the 'observe' preprocesses the given state further. But to accurately visualise what the agent sees
        we have to obtain that pre-processed state, which is done through this callback.

        :param name: String Defaults to "Agent". The name of the agent, does not need to be unique.
        :param is_human_agent: Boolean. Defaults to False. Boolean to signal that the agent represented by this avatar
        is a human controlled agent.
        :param customizable_properties: List. Optional, default obtained from defaults.json. The list of attribute names
        that can be customized by other objects (including AgentAvatars and as an extension any Agent).
        :param is_traversable: Boolean. Optional, default obtained from defaults.json. Signals whether other objects can
        be placed on top of this object.
        :param carried_by: List. Optional, default obtained from defaults.json. A list of who is carrying this object.
        :param team: The team name the agent is part of. Defaults to the team name similar to the AgentAvatars unique
        ID, as such denoting that by default each AgentAvatar belongs to its own team and as an extension so does its
        "brain" the Agent.
        :param agent_speed_in_ticks: Integer. Optional, default obtained from defaults.json. Denotes the speed with
        which the agent can perform actions. For example, a speed of 5 would mean that it can perform an action every 5
        steps of the simulation.

        :param visualize_size: Float. Optional, default obtained from defaults.json. A visualisation property used by
        the Visualizer. Denotes the size of the object, its unit is a single grid square in the visualisation (e.g. a
        value of 0.5 is half of a square, object is in the center, a value of 2 is twice the square's size centered on
        its location.)
        :param visualize_shape: Int. Optional, default obtained from defaults.json. A visualisation property used by the
        Visualizer. Denotes the shape of the object in the visualisation.
        :param visualize_colour: Hexcode string. Optional, default obtained from defaults.json. A visualisation property
        used by the Visualizer. Denotes the
        :param **custom_properties: Optional. Any other keyword arguments. All these are treated as custom attributes.
        For example the property 'heat'=2.4 of an EnvObject representing a fire.
        """

        # A list of EnvObjects or any class that inherits from it. Denotes all objects the AgentAvatar is currently
        # carrying. Note that these objects do not exist on the WorldGrid anymore, so removing them in this list deletes
        # them permanently.
        self.is_carrying = []  # list of EnvObjects that this object carries

        # The property that signals whether the agent this avatar represents is a human agent
        self.is_human_agent = is_human_agent

        # Save the other attributes the GridWorld expects an AgentAvatar to have.
        self.sense_capability = sense_capability
        self.action_set = possible_actions
        self.agent_speed_in_ticks = agent_speed_in_ticks
        self.get_action_func = callback_agent_get_action
        self.set_action_result_func = callback_agent_set_action_result
        self.ooda_observe = callback_agent_observe

        # Obtain any defaults from the defaults.json file if not set already
        self.is_traversable = is_traversable
        if self.is_traversable is None:
            self.is_traversable = get_default_value(class_name="AgentAvatar", property_name="is_traversable")
        self.visualize_size = visualize_size
        if self.visualize_size is None:
            self.visualize_size = get_default_value(class_name="AgentAvatar", property_name="visualize_size")
        self.visualize_shape = visualize_shape
        if self.visualize_shape is None:
            self.visualize_shape = get_default_value(class_name="AgentAvatar", property_name="visualize_shape")
        self.visualize_colour = visualize_colour
        if self.visualize_colour is None:
            self.visualize_colour = get_default_value(class_name="AgentAvatar", property_name="visualize_colour")
        self.agent_speed_in_ticks = visualize_colour
        if self.agent_speed_in_ticks is None:
            self.agent_speed_in_ticks = get_default_value(class_name="AgentAvatar",
                                                          property_name="agent_speed_in_ticks")

        # Defines an agent is blocked by an action which takes multiple time steps. Is updated based on the speed with
        # which an agent can perform actions.
        self.blocked = False

        # Denotes the last action performed by the agent, at what tick and how long it must take
        self.last_action = {"duration_in_ticks": 0, "tick": 0}

        # Call the super constructor (we do this here because then we have access to all of EnvObject, including a
        # unique id
        super().__init__(location, name, customizable_properties=customizable_properties, is_traversable=is_traversable,
                         class_callable=class_callable,
                         carried_by=carried_by, visualize_size=visualize_size, visualize_shape=visualize_shape,
                         visualize_colour=visualize_colour, possible_actions=possible_actions, team=team,
                         objects_carrying={}, agent_speed_in_ticks=agent_speed_in_ticks,
                         **custom_properties)

        # If there was no team name given, the AgentAvatar (and as an extension its Agent) is part of its own team which
        # is simply its object id. Since we already set the 'team' property we have to override it. We cannot do it
        # before the super constructor because there the id is assigned.
        if team is None:
            self.team = self.obj_id
        self.change_property("team", self.team)

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
        self.blocked = not ((curr_tick >= self.last_action["tick"] + self.last_action["duration_in_ticks"]) and \
                            (curr_tick >= self.last_action["tick"] + self.properties["agent_speed_in_ticks"]))
        return self.blocked

    def set_agent_changed_properties(self, props: dict):
        """
        The Agent has possibly changed some of its properties during its OODA loop. Here the agent properties are also
        updated in the Agent Avatar, if it is allowed to change them as defined in 'customizable_properties' list.
        """
        # get all agent properties of this Agent Avatar in one dictionary
        avatar_props = self.properties

        # check for each property if it has been changed by the agent, and if we need
        # to update our local copy (here in Agent Avatar) of the agent properties to match that
        for prop in props.keys():
            if prop not in avatar_props.keys():
                raise Exception(f"Agent {self.obj_id} tried to remove the property {prop}, which is not allowed.")

            # check if the property has changed, and skip if not the case
            if props[prop] == avatar_props[prop]:
                continue

            # if the agent has changed the property, check if the agent has permission to do so
            if prop not in self.customizable_properties:
                raise Exception(f"Agent {self.obj_id} tried to change a non-writable property: {prop}.")

            # The agent changed the property and the agent had permission to do so
            # update special properties
            self.change_property(prop, props[prop])

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

    @property
    def properties(self):
        """
        Returns the custom properties of this object, but also any mandatory properties such as location, name,
        is_traversable and all visualisation properties (those are in their own dictionary under 'visualisation').

        In the case we return the properties of a class that inherits from EnvObject, we check if that class has

        :return: All mandatory and custom properties in a dictionary.
        """

        # Copy the custom properties
        properties = self.custom_properties.copy()

        # Add all mandatory properties. Make sure that these are updated if one are added to the constructor!
        properties['name'] = self.obj_name
        properties['location'] = self.location
        properties['is_traversable'] = self.is_traversable
        properties['class_inheritance'] = self.class_inheritance
        properties['is_carrying'] = [obj.properties for obj in self.is_carrying]
        properties['visualisation'] = {
            "size": self.visualize_size,
            "shape": self.visualize_shape,
            "colour": self.visualize_colour,
            "depth": self.visualize_depth
        }

        return properties

    @properties.setter
    def properties(self, property_dictionary: dict):
        """
        Here to protect the 'properties' variable. It does not do anything and should not do anything!
        """
        pass

