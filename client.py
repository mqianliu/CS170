###############################################################################
# Berkeley CS170 SP19 Project skeleton                                        #
# DO NOT edit this file unless you know what you're doing!                    #
# However, feel free to peruse to understand its functions.                   #
###############################################################################

import sys
# Python 3 verification
if sys.version_info < (3, 0):
    print('Please use Python 3.')
    sys.exit()

import argparse
from datetime import datetime
import json
import networkx as nx
import os
from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests import Session
import time

LOCAL_URL = 'http://127.0.0.1:5000/api/'
REMOTE_URL = 'http://guavabot-api.cs170.org/'

### Implements a stateful client that interacts with the server.
class Client:
    def __init__(self, submit):
        # Whether or not this is a submission run.
        self.submit = submit
        if submit:
            self.base_url = REMOTE_URL
        else:
            self.base_url = LOCAL_URL

        self.session = Session()
        self.session.mount('http://', HTTPAdapter(max_retries=Retry(total=30,
            status_forcelist=[429, 500, 503], backoff_factor=1,
            method_whitelist=frozenset(['GET', 'POST']))))

        self.last_request = time.perf_counter()

        log_filename = datetime.now().strftime('logs/log_%y%m%d.txt')
        if not os.path.exists('logs'):
            os.makedirs('logs')
        self.log = open(log_filename, 'a+')

        if self.submit:
            with open('group_token', 'r') as f:
                self.group_token = f.readline().strip()
        self.__print__('Client initialized! '
            + ('Using group token {}.'.format(self.group_token) if self.submit \
                else ''))

    ### Starts a rescue; a session between client and server. To be terminated
    ### with an end() call.
    ### Returns False if an error occurred, True otherwise.
    # Locally stores graph : a weighted graph representing the city
    #                        (format found below),
    #                home  : the home vertex,
    #                k     : the number of students,
    #                l     : the number of bots in the city,
    #                s     : the time it takes a student to scout a vertex,
    # In addition, some data about the graph is stored for your convenience.
    #                n     : the number of vertices of the graph,
    #                m     : the number of edges of the graph.
    # Lastly, some bookkeeping is done, also for your convenience.
    #                time          : the elapsed time since the beginning.
    #                                This is initialized to 0.
    #                cant_scout    : a list of sets, each set representing the
    #                                vertices that student i may not scout.
    #                bot_count     : a list storing the number of bots at vertex
    #                                i.
    #                bot_locations : a list of vertex indices, one for each
    #                                known bot. Generated from bot_count.
    # Please note any unexpected changes you make to these variables may affect
    # the correctness of this skeleton.
    #
    # We have provided you graph files in the form of *.edgelist. You're welcome
    # to modify these as you wish, but do note that ultimately you will be
    # tested on the exact graphs provided.
    # Graphs are stored in the following format (networkx weighted edgelist).
    # This is K_{3, 3} with random edge weights:
    # 1 4 10
    # 1 5 30
    # 1 6 40
    # 2 4 50
    # 2 5 20
    # 2 6 25
    # 3 4 15
    # 3 5 18
    # 3 6 40
    def start(self):
        status_code, response = self.__request__('start', {})
        if status_code in [400, 401, 403]:
            self.__print__('/start API ' + str(status_code) + ' Error: '
                + response['error'] + '. See ' + response['documentation_url']
                + ' for more details.')
            return False
        elif status_code != 200:
            self.__print__('/start API ' + str(status_code) + ' Error.')
            return False

        if self.submit:
            graph_name = 'eval_graphs/' + response['city'] + '.json'
        else:
            graph_name = 'test_graphs/' + response['city'] + '.json'
        self.G = self.graph = self.city = self.__read_graph__(graph_name)
        self.h = self.home = response['home']
        self.k = self.students = response['k']
        self.l = self.bots = response['l']
        self.s = self.scout_time = response['s']

        self.n = self.v = len(self.graph)
        self.m = self.e = self.graph.size()

        self.time = 0
        self.cant_scout = [set() for _ in range(self.k + 1)]
        self.bot_count = [0] * (self.n + 1)

        self.__print__('/start API Call succeeded (home = ' + str(self.home)
            + ', students = ' + str(self.students) + ', bots = '
            + str(self.bots) + ', scout_time = ' + str(self.scout_time) + ')!')
        return True

    ### Scouts a vertex with a set of students. Updates the time elapsed.
    ### Returns the students' reports (dictionary of student ids to booleans
    ### of whether they saw bots).
    ### Note that the report may be incorrect (students are unreliable).
    ### On error, returns None.
    def scout(self, vertex, students):
        if not isinstance(vertex, int):
            self.__print__('/scout API Error: vertex is not an integer. '
                + 'Skipping call.')
            return
        if not isinstance(students, list) or len(students) == 0:
            self.__print__('/scout API Error: students is not a list or is an '
                + 'empty list. Skipping call.')
            return
        if vertex <= 0 or vertex > self.n:
            self.__print__('/scout API Error: vertex ' + str(vertex)
                + ' out of bounds [1, ' + str(self.n) + ']. Skipping call.')
            return
        if vertex == self.home:
            self.__print__('/scout API Error: vertex cannot be home. '
                + 'Skipping call.')
            return
        for student in students:
            if student <= 0 or student > self.k:
                self.__print__('/scout API Error: student ' + str(student)
                    + ' out of bounds [1, ' + str(self.k) + ']. Skipping call.')
                return
            if vertex in self.cant_scout[student]:
                self.__print__('/scout API Error: student ' + str(student)
                    + ' may not scout vertex ' + str(vertex) + '. Skipping call.')
                return

        status_code, response = self.__request__('scout',
            {'vertex': vertex, 'students': students})
        if status_code in [400, 401, 403]:
            self.__print__('/scout API ' + str(status_code) + ' Error: '
                + response['error'] + '. See ' + response['documentation_url']
                + ' for more details.')
            return
        elif status_code != 200:
            self.__print__('/scout API ' + str(status_code) + ' Error.')
            return

        response['reports'] = {int(student): found for student, found in \
            response['reports'].items()}

        self.time = response['time']

        self.__print__('/scout API Call succeeded (v = ' + str(vertex)
            + ', s = ' + str(students) + ')! '
            + 'Bots found by students ' + ', '.join([str(student) \
                for student, found in response['reports'].items() if found]))
        return response['reports']

    ### Remotes all bots along edge frum->to. In other words, all bots (if any)
    ### on `frum` are moved to `to`.
    ### Returns the number of bots remoted.
    ### On error, returns None.
    def remote(self, frum, to):
        if not isinstance(frum, int):
            self.__print__('/remote API Error: frum is not an integer. '
                + 'Skipping call.')
            return
        if not isinstance(to, int):
            self.__print__('/remote API Error: to is not an integer. '
                + 'Skipping call.')
            return
        if frum <= 0 or frum > self.n:
            self.__print__('/remote API Error: vertex \'from\' ' + str(frum)
                + ' out of bounds [1, ' + str(self.n) + ']. Skipping call.')
            return
        if to <= 0 or to > self.n:
            self.__print__('/remote API Error: vertex \'to\' ' + str(to)
                + ' out of bounds [1, ' + str(self.n) + ']. Skipping call.')
            return
        if frum == to:
            self.__print__('/remote API Error: vertices \'from\' and \'to\' '
                + 'are the same. Skipping call.')
            return
        if not self.graph.has_edge(frum, to):
            self.__print__('/remote API Error: edge (' + str(frum) + ', '
                + str(to) + ') does not exist. Skipping call.')
            return

        status_code, response = self.__request__('remote',
            {'from_vertex': frum, 'to_vertex': to})
        if status_code in [400, 401, 403]:
            self.__print__('/remote API ' + str(status_code) + ' Error: '
                + response['error'] + '. See ' + response['documentation_url']
                + ' for more details.')
            return
        elif status_code != 200:
            self.__print__('/remote API ' + str(status_code) + ' Error.')
            return

        self.time = response['time']
        # Scouting is no longer permitted at frum.
        for student in range(self.k + 1):
            self.cant_scout[student].add(frum)
        # Scouting is no longer permitted at to only if bots were remoted.
        if response['bots_remoted'] != 0:
            for student in range(self.k + 1):
                self.cant_scout[student].add(to)

        # Update the number of known bots at both ends of the edge.
        self.bot_count[frum] = 0
        self.bot_count[to] += response['bots_remoted']

        self.__print__('/remote API Call succeeded (edge = '
            + str(frum) + '->' + str(to) + ')! ' + str(response['bots_remoted'])
            + ' bot(s) remoted.')
        return response['bots_remoted']

    ### Terminates the active rescue, regardless of if all bots have returned
    ### to home. Prints out rescue results and saves the submit token if
    ### submitting.
    ### Returns False on error, True otherwise.
    def end(self):
        status_code, response = self.__request__('end', {})
        if status_code in [400, 401, 403]:
            self.__print__('/end API ' + str(status_code) + ' Error: '
                + response['error'] + '. See ' + response['documentation_url']
                + ' for more details.')
            return False
        elif status_code != 200:
            self.__print__('/end API ' + status_code + ' Error.')
            return False

        self.__print__('/end API Call succeeded!')
        self.__print__('Score: ' + str(response['score']))

        return True

    ### Retrieves your submit token, as well as informing about the
    ### number of evaluation rescues completed and remaining.
    ### Saves the submit token if save is True.
    ### Returns a dictionary containing submit_token, completed, and remaining
    ### rescues.
    ### On error, returns None
    def submission(self, save=True):
        status_code, response = self.__request__('submission', {}, REMOTE_URL)
        if status_code in [400, 401, 403]:
            self.__print__('/submission API ' + str(status_code) + ' Error: '
                + response['error'] + '. See ' + response['documentation_url']
                + ' for more details.')
            return
        elif status_code != 200:
            self.__print__('/submission API ' + status_code + ' Error.')
            return

        self.__print__('Rescues Remaining: ' + str(response['completed']) + '/'
            + str(response['completed'] + response['remaining']))

        if save:
            filename = datetime.now().strftime(
                'submit_tokens/submit_token_%y%m%d_%H%M%S.txt')
            if not os.path.exists('submit_tokens'):
                os.makedirs('submit_tokens')
            with open(filename, 'w+') as f:
                f.write(response['submit_token'])
            self.__print__('Saved submit_token at ' + filename + '. Submit this on '
                + 'Gradescope.')

        return {k: v for k, v in response.items() \
            if k in ['submit_token', 'completed', 'remaining']}

    @property
    def bot_locations(self):
        locations = []
        for index in range(self.n + 1):
            locations.extend([index] * self.bot_count[index])
        return locations

    ### Opens file_name and reads the contents as a weighted edgelist.
    ### Retuns a networkx graph object.
    def __read_graph__(self, file_name):
        with open(file_name, 'r') as f:
            data = json.load(f)
        G = nx.Graph()
        G.add_weighted_edges_from(data['edgelist'])
        return G

    ### Performs a POST request to the proxy server with JSON data.
    ### Returns status code, JSON response.
    def __request__(self, endpoint, data, base_url=None):
        if self.submit:
            data['group_token'] = self.group_token

        # Rate limit to 40 rps.
        delta = time.perf_counter() - self.last_request
        if delta < 1.0 / 40.0:
            time.sleep(1.0 / 40.0 - delta)

        if base_url is None:
            base_url = self.base_url
        url = base_url + endpoint
        response = self.session.post(url, data=data)

        self.last_request = time.perf_counter()
        return response.status_code, response.json()

    ### Prints the message with a prepended timestamp. Logs as well
    ### if this is a submission.
    ### Returns None.
    def __print__(self, msg):
        time = datetime.now().strftime('%H:%M:%S')
        if self.submit:
            self.log.write('[' + time + '] ' + msg + '\n')
        print('[' + time + '] ' + msg)

### Argument parsing and running solver.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Guavabot client: move all bots home!')
    parser.add_argument('--solver', dest='solver_file', default='solver',
        help='The Python solver to use. Please use the module name; that is, '
            + 'omit ".py".')
    parser.add_argument('--submit', action='store_true',
        help='Run the autograder; test your solver against the staff inputs.')

    args = parser.parse_args()
    if args.solver_file.endswith('.py'):
        print('The solver should just be the module name; don\'t include .py.')
        sys.exit()

    client = Client(args.submit)

    if args.submit:
        submission = client.submission()
        # Invalid group token check
        if not submission:
            print('Invalid group token.')
            sys.exit()
        if submission['remaining'] <= 0:
            print('0 rescues remaining. Terminating.')
            sys.exit()
        statement = 'I understand I only have ' + str(submission['remaining']) \
            + ' rescues remaining.'
        accept = input(
'''
=============================================================================
| SUBMISSION                                                                |
|---------------------------------------------------------------------------|
| This is the final message before you start running the autograder!        |
| Note that you have a finite number of rescues. Once used up, you will not |
|   be allowed to run the autograder, and the score you receive is final.   |
| Your score is based on ALL rescues made, so make them count!              |
|                                                                           |
| Warning: This may take a long time! Ensure a stable connection.           |
=============================================================================
> Your group has used {completed}/{total} rescues.
> ENTER THE FOLLOWING TO CONTINUE: '{statement}'
> '''.format(statement=statement, completed=submission['completed'],
            total=submission['completed'] + submission['remaining']))
        if accept.lower() != statement.lower():
            print('Submission cancelled.')
            sys.exit()

    solver = __import__(args.solver_file)
    if args.submit:
        for i in range(48):
            if client.submission(save=False)['remaining'] <= 0:
                print('0 rescues remaining. Terminating.')
                sys.exit()
            client.__print__('Starting submission {}.'.format(i + 1))
            solver.solve(client)
            client.__print__('Finished submission {}.'.format(i + 1))
        client.submission()
    else:
        solver.solve(client)
