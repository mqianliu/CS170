# Put your solution here.
import networkx as nx
import random


def solve(client):
    client.end()
    client.start()
    all_students = list(range(1, client.students + 1))
    non_home = list(range(1, client.home)) + list(range(client.home + 1, client.v + 1))



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

    def dfs(node):
        nonlocal visited
        visited[node] = 1
        for i in range(1, client.v + 1):
            if not visited[i] and mst_edges[node][i]:
                dfs(i)
                client.remote(i, node)


    dfs(client.home)
    #print(visited)

    client.end()
