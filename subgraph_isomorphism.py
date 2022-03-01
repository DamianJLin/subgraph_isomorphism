# -*- coding:utf-8 -*-
# AUTHOR:   yaolili
# FILE:     vf.py
# ROLE:     vf2 algorithm
# CREATED:  2015-11-28 20:55:11
# MODIFIED: 2015-12-05 11:58:12
# ADAPTED: 2019-06-25 for Quantum Circuit Transformation by Sanjiang Li (SL)
# all comments by SL started with '#sl'
import networkx as nx
from maps import Map
import time


class Vf:

    # Here pairs are taken from sub_not_in_map_neighbour and g_not_in_map_neighbour, not from sub_in_map_neighbour and
    # g_in_map_neighbour
    @staticmethod
    def candidate(sub_nim_neighbour, g_nim_neighbour):

        if not (sub_nim_neighbour and g_nim_neighbour):
            raise Exception("Class Vf candidate() arguments value error! sub_not_in_map_neighbour or gNMNeighbor is"
                            "empty!")

        if not (isinstance(sub_nim_neighbour, list) and isinstance(g_nim_neighbour, list)):
            raise Exception("Class Vf candidate() arguments type error! type list expected!")

        if not all(isinstance(x, int) for x in sub_nim_neighbour):
            raise Exception("Class Vf candidate() arguments type error! int in sub_not_in_map_neighbour list expected!")

        if not all(isinstance(x, int) for x in g_nim_neighbour):
            raise Exception("Class Vf candidate() arguments type error! int in gNMNeighbor list expected!")

        pairs = []

        # These candidates should be ranked. TODO: rank by distance function?
        for x in sub_nim_neighbour:
            for y in g_nim_neighbour:
                pairs.append([x, y])

        return pairs

    # method = 0, pre; method = 1, succ
    # Divide the graph neighborhood of a vertex into two disjoint parts:
    # pre (in map) and succ (not in map)
    @staticmethod
    def pre_succ(vertex_neighbour, mapping, method):
        # vertexNeighbor and map can be empty
        if not (isinstance(vertex_neighbour, list) and isinstance(mapping, list)):
            raise TypeError("Class Vf preSucc() arguments type error! vertexNeighbor and map expected list!")
        if not (method == 0 or method == 1):
            raise ValueError("Class Vf preSucc() arguments value error! method expected 0 or 1!")

        result = []
        # succ
        if method:
            for vertex in vertex_neighbour:
                if vertex not in mapping:
                    result.append(vertex)
        # pre
        else:
            for vertex in vertex_neighbour:
                if vertex in mapping:
                    result.append(vertex)
        return result

    def candidate_meets_rules(self, v1, v2, subgraph, graph, result, sub_map, g_map, sub_m_neighbour, g_m_neighbour):

        if not result:
            return True

        v1_neighbor = list(nx.all_neighbors(subgraph, v1))
        v2_neighbor = list(nx.all_neighbors(graph, v2))

        v1_pre = self.pre_succ(v1_neighbor, sub_map, 0)
        v1_succ = self.pre_succ(v1_neighbor, sub_map, 1)
        v2_pre = self.pre_succ(v2_neighbor, g_map, 0)
        v2_succ = self.pre_succ(v2_neighbor, g_map, 1)

        if len(v1_pre) > len(v2_pre) or len(v1_succ) > len(v2_succ):
            return False

        for pre in v1_pre:
            if result[pre] not in v2_pre:
                return False

        # A vertex is a neighbor of subMap if it is not in and a neighbor of some vertex in the map
        # Number of all x which is a neighbourhood of v1 and the map
        len1 = len(set(v1_neighbor) & set(sub_m_neighbour))
        len2 = len(set(v2_neighbor) & set(g_m_neighbour))

        if len1 > len2:
            return False
        return True

    def dfs_match(self, subgraph, graph, result, stop):
        """

        :param subgraph:
        :param graph:
        :param result:
        :param stop: The time limit.
        :return:
        """
        time_start = time.time()
        if not isinstance(result, dict):
            raise TypeError("Class Vf dfs_match() arguments type error! result expected dict!")

        cur_map = Map(result)  # Create a Map object!

        if len(result) == len(nx.nodes(subgraph)):
            return result

        # Construct the current neighborhoods of the mapping
        sub_m_neighbor = cur_map.neighbor(subgraph, 0)
        g_m_neighbor = cur_map.neighbor(graph, 1)

        if sub_m_neighbor and len(sub_m_neighbor) > len(g_m_neighbor):
            return {}

        sub_x = sub_m_neighbor[:]
        if not sub_m_neighbor:
            sub_x = list(set(nx.nodes(subgraph)) - set(cur_map.subMap()))

        # gNMNeighbor is only used for selecting the candidate pairs
        # Rank the unmapped neighbors by their degrees and select the highest one
        sub_u_deg = list([nx.degree(subgraph, v), v] for v in sub_x)
        sub_u_deg.sort(key=lambda t: t[0], reverse=True)
        selected_vertex = sub_u_deg[0][1]

        # Our AGs are always connected. gMNeighbor is empty iff result is empty!
        g_nim_neighbour = g_m_neighbor[:]
        if not sub_m_neighbor:
            g_nim_neighbour = list(set(nx.nodes(graph)) - set(cur_map.gMap()))

        # ------------------------------------------------------------
        sub_y_deg = list(item[0] for item in sub_u_deg)
        g_u_deg = list([nx.degree(graph, v), v] for v in g_nim_neighbour)
        g_u_deg.sort(key=lambda t: t[0], reverse=True)
        g_y_deg = list(item[0] for item in g_u_deg)

        if len(sub_y_deg) > len(g_y_deg) or sum(sub_y_deg) > sum(g_y_deg):
            return {}
        for i in range(len(sub_y_deg)):
            if sub_y_deg[i] > g_y_deg[i]:
                return {}
        # ------------------------------------------------------------

        # Remove those graph neighbours which cannot match the subgraph candidate node
        g_nim_neighbour = [t for t in g_nim_neighbour if nx.degree(subgraph, selected_vertex) <= nx.degree(graph, t)]

        if not g_nim_neighbour:
            return {}

        pairs = self.candidate([selected_vertex], g_nim_neighbour)
        if not pairs:
            return {}

        for pair in pairs:

            v1, v2 = pair
            # Note we should use subMNeighbor & gMNeighbor, not *NMNeighbor!
            if (self.candidate_meets_rules(v1, v2, subgraph, graph, result,
                                           cur_map.subMap(), cur_map.gMap(),
                                           sub_m_neighbor, g_m_neighbor)):

                result[v1] = v2  # Extend the mapping!

                if time.time() - time_start > stop:
                    print(f'dfs_match time exceeded {stop}')
                    return {}

                self.dfs_match(subgraph, graph, result, stop)

                if len(result) == len(nx.nodes(subgraph)):
                    return result

                # The pair is not helpful, and we pop it out and restore the mapping.
                result.pop(v1)

        return {}
