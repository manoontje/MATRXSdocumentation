from matrxs.agents.human_agent_brain import HumanAgentBrain
from matrxs.agents.patrolling_agent import PatrollingAgentBrain
from matrxs.world_builder import WorldBuilder
from matrxs.actions.move_actions import *


def create_factory():
    factory = WorldBuilder(random_seed=1, shape=[8, 8], tick_duration=0.5, verbose=True,
                           run_visualization_server=True)
    human_agent = HumanAgentBrain()

    usrinp_action_map = {
        'w': MoveNorth.__name__,
        'd': MoveEast.__name__,
        's': MoveSouth.__name__,
        'a': MoveWest.__name__
    }

    factory.add_human_agent([1,1], human_agent, name="Sam",
                            usrinp_action_map=usrinp_action_map, visualize_shape='img',
                            img_name="fireman.png")
    factory.add_human_agent([2, 2], human_agent, name="Bob",
                            usrinp_action_map=usrinp_action_map, visualize_shape='img',
                            img_name="constructionworker.png")
    factory.add_human_agent([3, 1], human_agent, name="Jasper",
                            usrinp_action_map=usrinp_action_map, visualize_shape='img',
                            img_name="civilian.png")
    factory.add_room([3,3],3,3,name="room1",door_locations=[(3,4)])

    factory.add_agent([0,0], PatrollingAgentBrain(waypoints=[(0, 0), (0, 7)]), name="3xpl0re8ot", visualize_shape='img', has_menu=True, img_name="explorervehicle.png")

    factory.add_agent([3, 0], PatrollingAgentBrain(waypoints=[(3, 0), (3, 7)]), name="p3pp3r",
                      visualize_shape='img', has_menu=True, img_name="pepper.png")

    factory.add_agent([7, 0], PatrollingAgentBrain(waypoints=[(7, 0), (7, 7)]), name="U4V",
                      visualize_shape='img', has_menu=True, img_name="uav.png")

    return factory
