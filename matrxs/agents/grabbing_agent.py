from matrxs.agents.agent_brain import AgentBrain
from matrxs.utils.agent_utils.navigator import Navigator
from matrxs.utils.agent_utils.state_tracker import StateTracker


class GrabbingAgentBrain(AgentBrain):
    """This is the PatrollingAgentBrain class.
    """

    def __init__(self, waypoints):
        super().__init__()
        self.state_tracker = None
        self.navigator = None
        self.waypoints = waypoints

    def initialize(self):
        """
        Initialization of the agent's state tracker.
        :return:
        """
        # Initialize this agent's state tracker
        self.state_tracker = StateTracker(agent_id=self.agent_id)

        self.navigator = Navigator(agent_id=self.agent_id, action_set=self.action_set,
                                   algorithm=Navigator.A_STAR_ALGORITHM)

        self.navigator.add_waypoints(self.waypoints, is_circular=True)

    def filter_observations(self, state):
        """
        Filtering the agent's observations.
        :param state:
        :return:
        """
        self.state_tracker.update(state)
        return state

    def decide_on_action(self, state):
        """
        Decision of which action to perform.
        :param state:
        :return:
        """

        move_action = self.navigator.get_move_action(self.state_tracker)

        return move_action, {}