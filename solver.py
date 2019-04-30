# Put your solution here.
import networkx as nx
import random


def solve(client):
    client.end()
    client.start()

    def find_position():
        all_students = list(range(1, client.students + 1))
        non_home = list(range(1, client.home)) + list(range(client.home + 1, client.v + 1))
        count = 0
        vote = [[0, i] for i in range(0, 101)]
        num_bots = [0 for _ in range(0, 101)]
        remoted = [0 for _ in range(0, 101)]
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
            min_weight = float('inf')
            tempu = 0
            tempv = 0
            for i in range(1, client.v + 1):
                if node[1] != i and client.G[node[1]][i]['weight'] < min_weight:
                    tempu, tempv = node[1], i
                    min_weight = client.G[node[1]][i]['weight']
            num_check = client.remote(tempu, tempv)
            remoted[tempv] += num_check
            count += num_check - remoted[tempu]
            num_bots[tempv] += num_check
            if remoted[tempu] > 0:
                num_bots[tempu] -= num_check
            if count == client.bots:
                break
        for i in range(0, len(num_bots)):
            if num_bots[i] > 0:
                bots_position.append([i, num_bots[i]])
        #print(bots_position)
        return bots_position

    def floyd():
        distance = [[[float('inf'), [-1]] for _ in range(client.v + 1)] for _ in range(client.v + 1)]
        for i in range(1, client.v + 1):
            for j in range(1, client.v + 1):
                if i != j:
                    distance[i][j][0] = client.G[i][j]['weight']
                    distance[i][j][1] = [i, j]
                else:
                    distance[i][j][1] = [i]
        for k in range(1, client.v + 1):
            for i in range(1, client.v + 1):
                for j in range(1, client.v + 1):
                    if i != j and i != k and j != k and distance[i][j][0] > distance[i][k][0] + distance[k][j][0]:
                        distance[i][j][0] = distance[i][k][0] + distance[k][j][0]
                        distance[i][j][1] = distance[i][k][1][:] + distance[k][j][1][1:]
        return distance

    def mst2():
        bots = find_position()
        nodes = [client.home]
        edges = [[0 for col in range(client.v + 1)] for row in range(client.v + 1)]
        while len(bots):
            d = floyd()
            min_path = float('inf')
            start_node = -1
            end_node = -1
            for n in nodes:
                for b in bots:
                    if min_path > d[n][b[0]][0]:
                        min_path = d[n][b[0]][0]
                        start_node = n
                        end_node = b
            path = d[start_node][end_node[0]][1]
            for i in range(len(path) - 1):
                if path[i+1] in bots:
                    bots.remove(path[i+1])
                nodes.append(path[i+1])
                edges[path[i]][path[i+1]] = 1
                edges[path[i+1]][path[i]] = 1
            bots.remove(end_node)

        visited = [0 for _ in range(client.v + 1)]

        def dfs(n):
            nonlocal visited
            if visited[n]:
                return
            visited[n] = 1
            for i in nodes:
                if not visited[i] and edges[n][i]:
                    dfs(i)
                    client.remote(i, n)

        dfs(client.home)



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

    #MST()
    mst2()

    client.end()
