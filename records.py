from collections import namedtuple


StreamRecord = namedtuple('StreamRecord', ['stream_id', 
                                           'client_ip', 
                                           'client_port', 
                                           'server_ip', 
                                           'server_port', 
                                           'protocol', 
                                           'timestamp'])

TrafficRecord = namedtuple('TrafficRecord', ['stream_id', 
                                             'timestamp', 
                                             'direction',
                                             'payload'])
