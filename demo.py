from matrxs.agents.capabilities.capability import SenseCapability
from matrxs.agents.patrolling_agent import PatrollingAgentBrain
from matrxs.world_builder import WorldBuilder
import matrxs.objects.simple_objects as objects
import matrxs.objects.agent_body as agents_objs
import numpy as np


def create_builder():
    seed = 1
    np.random.seed(seed)

    builder = WorldBuilder(random_seed=seed, shape=[51, 31], tick_duration=0.1, verbose=True)

    builder.add_room(top_left_location=(21, 12), width=10, height=9, name="Compound",
                     door_locations=[(25, 12), (26, 12)], doors_open=True)

    ##################
    # Add forest areas
    ##################
    forest_areas = [[(0, 0), 7, 31], [(7, 0), 2, 15], [(9, 0), 10, 7], [(19, 0), 7, 5], [(26, 0), 8, 3],
                    [(47, 0), 4, 31]]
    tree_prob = 0.5

    # Add areas
    for idx, area in enumerate(forest_areas):
        builder.add_area(top_left_location=area[0], width=area[1], height=area[2], name=f"Forest_{idx}",
                         visualize_colour="#badb93")

    # Add trees
    i = 0
    for idx, area in enumerate(forest_areas):
        min_x = area[0][0]
        max_x = area[0][0] + area[1]
        min_y = area[0][1]
        max_y = area[0][1] + area[2]
        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                rnd_opacity = np.random.rand() * 0.5 + 0.5
                builder.add_object_prospect(location=(x, y), name=f"Tree_Forest_{idx}", callable_class=objects.Tree,
                                            probability=tree_prob, is_traversable=True, visualize_shape='img',
                                            img_name="tree.png", visualize_opacity=rnd_opacity)

    ############
    # Add Agents
    ############
    communicate_state_to_team = True

    # Add patrolling UGV's
    nr_patrol_ugvs = 3
    starts = [(22, 14), (29, 14), (25, 19)]
    patrol_points = [[(25, 9), (33, 9), (33, 23), (18, 23), (18, 9)],
                     [(17, 8), (17, 22), (32, 22), (32, 8), (24, 8)],
                     [(35, 4), (35, 28)]]
    for nr in range(nr_patrol_ugvs):
        patrol_agent = PatrollingAgentBrain(waypoints=patrol_points[nr], knowledge_decay=100,
                                            communicate_state_to_team=communicate_state_to_team)
        sense_capability = SenseCapability({objects.Wall: -1, objects.Door: -1, objects.Tree: 10,
                                            agents_objs.AgentBody: 10})
        builder.add_agent(location=starts[nr], agent_brain=patrol_agent, name=f"UGV_{nr}",
                          sense_capability=sense_capability, agent_speed_in_ticks=5, is_traversable=False,
                          visualize_shape='img', img_name="tank.png", team="patrol")

    # Add tracking UAV's

    return builder
