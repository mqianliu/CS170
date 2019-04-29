# Put your solution here.
import networkx as nx
import random


def solve(client):
    client.end()
    client.start()
    all_students = list(range(1, client.students + 1))
    non_home = list(range(1, client.home)) + list(range(client.home + 1, client.v + 1))

    def find_position():
        all_students = list(range(1, client.students + 1))
        non_home = list(range(1, client.home)) + list(range(client.home + 1, client.v + 1))
        count = 0
        vote = [[0, i] for i in range(0, 101)]
        num_bots = [0 for _ in range(0, 101)]
        bots_position = []
        for v in non_home:
            scout_dict = client.scout(v, all_students)
            for key in scout_dict:
                if scout_dict[key] is True:
                    vote[v][0] += 1

        vote.sort(key=lambda x: x[0], reverse=True)
        # print(vote)
        # print(scout_dict)
        for node in vote:
            min_weight = 999999
            tempu = 0
            tempv = 0
            for i in range(1, client.v + 1):
                if node[1] != i and client.G[node[1]][i]['weight'] < min_weight:
                    tempu, tempv = node[1], i
                    min_weight = client.G[node[1]][i]['weight']
            num_check = client.remote(tempu, tempv)
            num_bots[tempv] += num_check
            num_bots[tempu] -= num_check
            count += num_check
            if count == client.bots:
                break
        for i in range(0, len(num_bots)):
            if num_bots[i] > 0:
                bots_position.append([i, num_bots[i]])
        print(bots_position)

    def MST():
        mst_edges = [[0 for col in range(client.v + 1)] for row in range(client.v + 1)]
        nodes = [0 for _ in range(client.v + 1)]
        edges = []
        for i in range(1, client.v + 1):
            if i != client.home:
                edges.append([client.home, i, client.G[client.home][i]['weight']])
        for num in range(client.v):
            edges.sort(key = lambda x : x[2])
            while True:
                new_edge = edges[0]
                if nodes[new_edge[1]] == 0:
                    break
                edges.pop(0)
            nodes[new_edge[1]] = 1
            mst_edges[new_edge[0]][new_edge[1]] = 1
            mst_edges[new_edge[1]][new_edge[0]] = 1
            for i in range(1, client.v + 1):
                if nodes[i] == 0:
                    edges.append([new_edge[1], i, client.G[new_edge[1]][i]['weight']])

        visited = [0 for _ in range(client.v + 1)]
        bots = [0 for _ in range(client.v + 1)]
        num = 0

        def dfs(node):
            nonlocal visited, bots, num
            visited[node] = 1
            for i in range(1, client.v + 1):
                if not visited[i] and mst_edges[node][i]:
                    dfs(i)
                    n = client.remote(i, node)
                    bots[node] += n
                    if n > bots[i]:
                        num += n - bots[i]
                    if num == 5:
                        return

        dfs(client.home)

    MST()
    client.end()
