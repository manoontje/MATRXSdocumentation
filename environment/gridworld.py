import datetime
import math
import time
from collections import OrderedDict

from agents.Agent import Agent
from agents.HumanAgent import HumanAgent
from environment.actions.object_actions import *
from environment.helper_functions import get_all_classes
from environment.objects.env_object import *
from visualization.visualizer import Visualizer


TIME_FOCUS_TICK_DURATION = 'aim_for_constant_tick_duration'
TIME_FOCUS_SIMULATION_DURATION = 'aim_for_accurate_global_tick_duration'


class GridWorld:

    def __init__(self, shape, tick_duration, simulation_goal=None, run_sail_api=True, run_visualization_server=True,
                 time_focus=TIME_FOCUS_TICK_DURATION, rnd_seed=1):
        self.tick_duration = tick_duration
        self.registered_agents = OrderedDict()
        self.environment_objects = OrderedDict()
        self.current_nr_ticks = 0
        self.simulation_goal = simulation_goal
        self.all_actions = get_all_classes(Action, omit_super_class=True)
        self.current_available_id = 0
        self.shape = shape
        self.run_sail_api = run_sail_api
        self.run_visualization_server = run_visualization_server
        self.time_focus = time_focus
        self.grid = np.array([[None for x in range(shape[0])] for y in range(shape[1])])
        self.is_done = False
        self.rnd_seed = rnd_seed
        self.rnd_gen = np.random.RandomState(seed=self.rnd_seed)
        self.curr_tick_duration = 0.
        self.carry_dict = {}
        self.tick_start_time = datetime.datetime.now()
        self.sleep_duration = tick_duration
        self.visualizer = None

    def initialize(self):
        # We update the grid, which fills everything with added objects and agents
        self.__update_grid()

        # Initialize the visualizer
        self.visualizer = Visualizer(self.shape)

    def run(self):
        self.initialize()
        is_done = False
        while not is_done:
            is_done, tick_duration = self.step()


    def register_agent(self, agent, agent_avatar: AgentAvatar):
        """ Register human agents and agents to the gridworld environment """

        # Random seed for agent between 1 and 10000000, might need to be adjusted still
        agent_seed = self.rnd_gen.randint(1, 10000000)

        # check if the agent can be succesfully placed at that location
        self.validate_obj_placement(agent_avatar)

        # Add agent to registered agents
        self.registered_agents[agent_avatar.obj_id] = agent_avatar

        print("Created agent with id", agent_avatar.obj_id)

        # Get all properties from the agent avatar
        avatar_props = agent_avatar.properties

        agent.factory_initialise(agent_name=agent_avatar.obj_name,
                                 action_set=agent_avatar.action_set,
                                 sense_capability=agent_avatar.sense_capability,
                                 agent_properties=avatar_props,
                                 customizable_properties=agent_avatar.customizable_properties,
                                 rnd_seed=agent_seed)

        return agent_avatar.obj_id



    def register_env_object(self, env_object: EnvObject):
        """ this function adds the objects """

        # check if the object can be succesfully placed at that location
        self.validate_obj_placement(env_object)

        # Assign id to environment sparse dictionary grid
        self.environment_objects[env_object.obj_id] = env_object

        return env_object.obj_id

    def validate_obj_placement(self, env_object):
        """
        Checks whether an object can be successfully placed on the grid
        """
        obj_loc = env_object.location

        # get the objects at the target object location
        objs_at_loc = self.get_objects_in_range(obj_loc, "*", 0)

        # check how many of these objects are intraversable
        intraversable_objs = []
        for obj in objs_at_loc:
            if not objs_at_loc[obj].is_traversable:
                intraversable_objs.append(objs_at_loc[obj].obj_id)

        # two intraversable objects can't be at the same location
        if not env_object.is_traversable and len(intraversable_objs) > 0:
            raise Exception(f"Invalid placement. Could not place object {env_object.obj_id} in grid, location already "
                            f"occupied by intraversable object {intraversable_objs} at location {obj_loc}")

    def step(self):

        # Check if we are done based on our global goal assessment function
        self.is_done = self.check_simulation_goal()

        # If this grid_world is done, we return immediately
        if self.is_done:
            return self.is_done, 0.

        # Set tick start of current tick
        tick_start_time_current_tick = datetime.datetime.now()

        # Go over all agents, detect what each can detect, figure out what actions are possible and send these to
        # that agent. Then receive the action back and store the action in a buffer.
        # Also, update the local copy of the agent properties, and save the agent's state for the GUI.
        # Then go to the next agent.
        # This blocks until a response from the agent is received (hence a tick can take longer than self.tick_duration!!)
        action_buffer = OrderedDict()
        for agent_id, agent_obj in self.registered_agents.items():

            state = self.__get_agent_state(agent_obj)

            # go to the next agent, if this agent is still busy performing an action
            if agent_obj.check_agent_busy(curr_tick=self.current_nr_ticks):
                # only do the observe and orient of the OODA loop to update the GUI
                filtered_agent_state = agent_obj.ooda_observe(state)
                self.visualizer.save_state(inheritance_chain=agent_obj.class_inheritance, id=agent_id,
                                           state=filtered_agent_state)
                continue

            possible_actions = self.__get_possible_actions(agent_id=agent_id, action_set=agent_obj.action_set)

            # For a HumanAgent any user inputs from the GUI for this HumanAgent are send along
            if agent_obj.is_human_agent:
                usrinp = self.visualizer.userinputs[agent_id.lower()] if \
                                agent_id.lower() in self.visualizer.userinputs else None
                filtered_agent_state, agent_properties, action_class_name, action_kwargs = agent_obj.get_action_func(
                    state=state,
                    agent_properties=agent_obj.properties, possible_actions=possible_actions, agent_id=agent_id,
                    userinput=usrinp)
            else:
                # perform the OODA loop and get an action back
                filtered_agent_state, agent_properties, action_class_name, action_kwargs = agent_obj.get_action_func(
                    state=state,
                    agent_properties=agent_obj.properties, possible_actions=possible_actions,
                    agent_id=agent_id)

            # store the action in the buffer
            action_buffer[agent_id] = (action_class_name, action_kwargs)

            # the Agent (in the OODA loop) might have updated its properties,
            # process these changes in the Avatar Agent
            agent_obj.set_agent_changed_properties(agent_properties)

            # save what the agent observed to the visualizer
            self.visualizer.save_state(inheritance_chain=agent_obj.class_inheritance, id=agent_id,
                                       state=filtered_agent_state)

        # save the state of the god view in the visualizer
        self.visualizer.save_state(inheritance_chain="god", id="god", state=self.__get_complete_state())

        # update the visualizations of all (human)agents and god
        self.visualizer.update_guis(tick=self.current_nr_ticks)

        # Perform the actions in the order of the action_buffer (which is filled in order of registered agents
        for agent_id, action in action_buffer.items():
            # Get the action class name
            action_class_name = action[0]
            # Get optional kwargs
            action_kwargs = action[1]

            if action_kwargs is None:  # If kwargs is none, make an empty dict out of it
                action_kwargs = {}

            # Actually perform the action (if possible), also sets the result in the agent's brain
            self.__perform_action(agent_id, action_class_name, action_kwargs)

            # Update the grid
            self.__update_grid()

        # Perform the update method of all objects
        for env_obj in self.environment_objects.values():
            env_obj.update_properties(self)

        # Increment the number of tick we performed
        self.current_nr_ticks += 1

        # Check how much time the tick lasted already
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time_current_tick
        self.curr_tick_duration = tick_duration.total_seconds()
        total_time = (tick_end_time - self.tick_start_time)
        self.sleep_duration = self.tick_duration * self.current_nr_ticks - total_time.total_seconds()

        # Sleep for the remaining time of self.tick_duration
        self.__sleep()

        # Compute the total time of our tick (including potential sleep)
        tick_end_time = datetime.datetime.now()
        tick_duration = tick_end_time - tick_start_time_current_tick
        self.curr_tick_duration = tick_duration.total_seconds()
        print(f"Tick {self.current_nr_ticks} took {self.curr_tick_duration} seconds")

        return self.is_done, self.curr_tick_duration

    def get_env_object(self, requested_id, obj_type=None):
        obj = None

        if requested_id in self.registered_agents.keys():
            if obj_type is not None:
                if isinstance(self.registered_agents[requested_id], obj_type):
                    obj = self.registered_agents[requested_id]
            else:
                obj = self.registered_agents[requested_id]

        if requested_id in self.environment_objects.keys():
            if obj_type is not None:
                if isinstance(self.environment_objects[requested_id], obj_type):
                    obj = self.environment_objects[requested_id]
            else:
                obj = self.environment_objects[requested_id]

        return obj

    def get_objects_in_range(self, agent_loc, object_type, sense_range):
        """
        Get all objects of a obj type (normal objects or agent) within a
        certain range around the agent's location
        """

        env_objs = OrderedDict()
        # loop through all environment objects
        for obj_id, env_obj in self.environment_objects.items():
            # get the distance from the agent location to the object
            coordinates = env_obj.location
            distance = self.__get_distance(coordinates, agent_loc)

            # check if the env object is of the specified type, and within range
            if (object_type is None or object_type == "*" or isinstance(env_obj, object_type)) and \
                    distance <= sense_range:
                env_objs[obj_id] = env_obj

        # agents are also environment objects, but stored seperatly. Also check them.
        for agent_id, agent_obj in self.registered_agents.items():
            coordinates = agent_obj.location
            distance = self.__get_distance(coordinates, agent_loc)

            # check if the env object is of the specified type, adn within range
            if (object_type is None or object_type == "*" or isinstance(agent_obj, object_type)) and \
                    distance <= sense_range:
                env_objs[agent_id] = agent_obj
        return env_objs

    def check_simulation_goal(self):

        if self.simulation_goal is not None:
            if isinstance(self.simulation_goal, list):
                for sim_goal in self.simulation_goal:
                    is_done = sim_goal.goal_reached(self)
                    if is_done is False:
                        return False
            else:
                return self.simulation_goal.goal_reached(self)

        return False

    def remove_from_grid(self, object_id, remove_from_carrier=True):
        """
        Remove an object from the grid
        :param object_id: ID of the object to remove
        :param remove_from_carrier: whether to also remove from agents which carry the
        object or not.
        """
        # Remove object first from grid
        grid_obj = self.get_env_object(object_id)  # get the object
        loc = grid_obj.location  # its location

        self.grid[loc[1], loc[0]].remove(grid_obj.obj_id)  # remove the object id from the list at that location
        if len(self.grid[loc[1], loc[0]]) == 0:  # if the list is empty, just add None there
            self.grid[loc[1], loc[0]] = None

        # Remove object from the list of registered agents or environmental objects
        # Check if it is an agent
        if object_id in self.registered_agents.keys():
            # Check if the agent was carrying something, if so remove property from carried item
            for obj_id in self.registered_agents[object_id].is_carrying:
                self.environment_objects[obj_id].carried_by.remove(object_id)

            # Remove agent
            success = self.registered_agents.pop(object_id,
                                                 default=False)  # if it exists, we get it otherwise False

        # Else, check if it is an object
        elif object_id in self.environment_objects.keys():
            # remove from any agents carrying this object if asked for
            if remove_from_carrier:
                # If the object was carried, remove this from the agent properties as well
                for agent_id in self.environment_objects[object_id].carried_by:
                    obj = self.environment_objects[object_id]
                    self.registered_agents[agent_id].is_carrying.remove(obj)

            # Remove object
            success = self.environment_objects.pop(object_id,
                                                   default=False)  # if it exists, we get it otherwise False
        else:
            success = False  # Object type not specified

        if success is not False:  # if succes is not false, we successfully removed the object from the grid
            success = True

        return success

    def add_to_grid(self, grid_obj):
        if isinstance(grid_obj, EnvObject):
            loc = grid_obj.location
            if self.grid[loc[1], loc[0]] is not None:
                self.grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.grid[loc[1], loc[0]] = [grid_obj.obj_id]
        else:
            loc = grid_obj.location
            if self.grid[loc[1], loc[0]] is not None:
                self.grid[loc[1], loc[0]].append(grid_obj.obj_id)
            else:
                self.grid[loc[1], loc[0]] = [grid_obj.obj_id]

    def __sleep(self):
        """
        Sleeps the current python thread for the amount of time that is left after self.curr_tick_duration up to
        in self.tick_duration
        :return:
        """
        if self.sleep_duration > 0:
            time.sleep(self.sleep_duration)
        else:
            self.__warn(
                f"The average tick took longer than the set tick duration of {self.tick_duration}. "
                f"Programm is to heavy to run real time")

    def __update_grid(self):
        self.grid = np.array([[None for x in range(self.shape[0])] for y in range(self.shape[1])])
        for obj_id, obj in self.environment_objects.items():
            self.add_to_grid(obj)
        for agent_id, agent in self.registered_agents.items():
            self.add_to_grid(agent)

    # get all objects and agents on the grid
    def __get_complete_state(self):
        """
        Compile all objects and agents on the grid in one state dictionary
        :return: state with all objects and agents on the grid
        """

        # create a state with all objects and agents
        state = {}
        for obj_id, obj in self.environment_objects.items():
            state[obj.obj_id] = obj.properties
        for agent_id, agent in self.registered_agents.items():
            state[agent.obj_id] = agent.properties

        return state

    def __get_agent_state(self, agent_obj):
        agent_loc = agent_obj.location
        sense_capabilities = agent_obj.sense_capability.get_capabilities()
        objs_in_range = OrderedDict()

        # Check which objects can be sensed with the agents' capabilities, from
        # its current position.
        for obj_type, sense_range in sense_capabilities.items():
            env_objs = self.get_objects_in_range(agent_loc, obj_type, sense_range)
            objs_in_range.update(env_objs)

        state = {}
        # Save all properties of the sensed objects in a state dictionary
        for env_obj in objs_in_range:
            state[env_obj] = objs_in_range[env_obj].properties

        return state

    def __get_distance(self, coord1, coord2):
        dist = [(a - b) ** 2 for a, b in zip(coord1, coord2)]
        dist = math.sqrt(sum(dist))
        return dist

    def __get_possible_actions(self, action_set, agent_id):
        # List where we store our possible actions in for a specific agent

        possible_actions = []
        # Go through the action set
        for action_type in action_set:
            # If the action from the set is a known action we continue
            if action_type in self.all_actions:
                # We get the action constructor
                action_class = self.all_actions[action_type]
                # And we call that constructor to create an action object
                action = action_class()
                # Then we check if the action is possible, which returns a boolean, and a string that we ignore
                # (contains the reason why the action is not possible)
                is_possible, reason = action.is_possible(grid_world=self, agent_id=agent_id, kwargs={})

                # If the action is possible, we append it to possible actions list
                if is_possible:
                    possible_actions.append(action_type)
        # If no actions, we warn that this is the case
        if len(possible_actions) == 0:
            warn_str = f"No possible actions for agent {agent_id}."
            warnings.warn(self.__warn(warn_str))

        return possible_actions

    def __perform_action(self, agent_id, action_name, action_kwargs):

        # Check if the agent still exists (you would only get here if the agent is removed during this tick.
        if agent_id not in self.registered_agents.keys():
            result = ActionResult(ActionResult.AGENT_WAS_REMOVED.replace("{AGENT_ID}", agent_id), succeeded=False)
            return result

        if action_name is None:  # If action is None, we send an action result that no action was given (and succeeded)
            result = ActionResult(ActionResult.NO_ACTION_GIVEN, succeeded=True)

        # action known, but agent not capable of performing it
        elif action_name in self.all_actions.keys() and not action_name in self.registered_agents[agent_id].action_set:
            result = ActionResult(ActionResult.AGENT_NOT_CAPABLE, succeeded=False)

        elif action_name in self.all_actions.keys():  # Check if action is known
            # Get action class
            action_class = self.all_actions[action_name]
            # Make instance of action
            action = action_class()
            # Check if action is possible, if so we can perform the action otherwise we send an ActionResult that it was
            # not possible.
            is_possible = action.is_possible(self, agent_id, **action_kwargs)

            if is_possible[0]:  # First return value is the boolean (seceond is reason why, optional)
                # Apply world mutation
                result = action.mutate(self, agent_id, **action_kwargs)

                # The agent is now busy performing this action
                self.registered_agents[agent_id].set_agent_busy(curr_tick=self.current_nr_ticks,
                                                                action_duration=action.duration_in_ticks)
            else:
                # If the action is not possible, send a failed ActionResult with the is_possible message if given,
                # otherwise use the default one.
                custom_not_possible_message = is_possible[1]  # is_possible[1]
                if custom_not_possible_message is not None:
                    result = ActionResult(custom_not_possible_message, succeeded=False)
                else:
                    result = ActionResult(ActionResult.ACTION_NOT_POSSIBLE, succeeded=False)
        else:  # If the action is not known
            result = ActionResult(ActionResult.UNKNOWN_ACTION, succeeded=False)

        # Get agent's send_result function
        set_action_result = self.registered_agents[agent_id].set_action_result_func
        # Send result of mutation to agent
        set_action_result(result)

        # Update world if needed
        if action_name is not None:
            self.__update_agent_location(agent_id)

        return result

    def __update_agent_location(self, agent_id):
        # Get current location of the agent
        loc = self.registered_agents[agent_id].location
        # Check if that spot in our list that represents the grid, is None or a list of other objects
        if self.grid[loc[1], loc[0]] is not None:  # If not None, we append the agent id to it
            self.grid[loc[1], loc[0]].append(agent_id)
        else:  # if none, we make a new list with the agent id in it.
            self.grid[loc[1], loc[0]] = [agent_id]

        # Update the Agent Avatar's location as well
        self.registered_agents[agent_id].location = loc

    def __update_obj_location(self, obj_id):
        loc = self.environment_objects[obj_id].location
        if self.grid[loc[1], loc[0]] is not None:
            self.grid[loc[1], loc[0]].append(obj_id)
        else:
            self.grid[loc[1], loc[0]] = [obj_id]

    def __warn(self, warn_str):
        return f"[@{self.current_nr_ticks}] {warn_str}"
