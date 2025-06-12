tileTopath = {'A': 'resources/carcassonne/tile/A.png', 'B': 'resources/carcassonne/tile/B.png', 'C': 'resources/carcassonne/tile/C.png',
              'D': 'resources/carcassonne/tile/D.png', 'E': 'resources/carcassonne/tile/E.png', 'F': 'resources/carcassonne/tile/F.png',
              'G': 'resources/carcassonne/tile/G.png', 'H': 'resources/carcassonne/tile/H.png', 'I': 'resources/carcassonne/tile/I.png',
              'J': 'resources/carcassonne/tile/J.png', 'K': 'resources/carcassonne/tile/K.png', 'L': 'resources/carcassonne/tile/L.png',
              'M': 'resources/carcassonne/tile/M.png', 'N': 'resources/carcassonne/tile/N.png', 'O': 'resources/carcassonne/tile/O.png',
              'P': 'resources/carcassonne/tile/P.png', 'Q': 'resources/carcassonne/tile/Q.png', 'R': 'resources/carcassonne/tile/R.png',
              'S': 'resources/carcassonne/tile/S.png', 'T': 'resources/carcassonne/tile/T.png', 'U': 'resources/carcassonne/tile/U.png',
              'V': 'resources/carcassonne/tile/V.png', 'W': 'resources/carcassonne/tile/W.png', 'X': 'resources/carcassonne/tile/X.png'}

meepleTopath = {'blue': 'resources/carcassonne/meeple/blue_meeple.png', 'black': 'resources/carcassonne/meeple/black_meeple.png',
                'green': 'resources/carcassonne/meeple/green_meeple.png', 'pink': 'resources/carcassonne/meeple/pink_meeple.png',
                'yellow': 'resources/carcassonne/meeple/yellow_meeple.png', }

edge_A = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (80, 90),
          'meeple': None},
    'W': {'type': 'field', 'connections': ['E', 'N'], 'ismeepleplaceable': False},
    'M': {'type': 'monastery', 'ismeepleplaceable': True, 'meeple_coordinates': (42, 42),
          'meeple': None}
}

edge_B = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'field', 'connections': []},
    'M': {'type': 'monastery', 'ismeepleplaceable': True, 'meeple_coordinates': (50, 55),
          'meeple': None}
}

edge_C = {
    'N': {'type': 'city', 'connections': ['E', 'W', 'S'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 50),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N', 'W', 'S'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 50),
          'meeple': None},
    'S': {'type': 'city', 'connections': ['E', 'W', 'N'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 50),
          'meeple': None},
    'W': {'type': 'city', 'connections': ['E', 'N', 'S'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 50),
          'meeple': None}
}

edge_D = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (46, 5),
          'meeple': None},
    'E': {'type': 'road', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (87, 50),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'road', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (17, 56),
          'meeple': None}
}

edge_E = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (54, 8),
          'meeple': None},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'field', 'connections': []}
}

edge_F = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'city', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 60),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'city', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 60),
          'meeple': None}
}

edge_G = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'city', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 60),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'city', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 60),
          'meeple': None}
}

edge_H = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (94, 58),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (3, 44),
          'meeple': None}
}

edge_I = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (47, 6),
          'meeple': None},
    'E': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (99, 53),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'field', 'connections': []}
}

edge_J = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (46, 7),
          'meeple': None},
    'E': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (87, 47),
          'meeple': None},
    'S': {'type': 'road', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (40, 88),
          'meeple': None},
    'W': {'type': 'field', 'connections': []}
}

edge_K = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (60, 10),
          'meeple': None},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'road', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (46, 85),
          'meeple': None},
    'W': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (15, 38),
          'meeple': None}
}

edge_L = {
    'N': {'type': 'city', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 5),
          'meeple': None},
    'E': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (98, 39),
          'meeple': None},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (40, 90),
          'meeple': None},
    'W': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (10, 45),
          'meeple': None}
}

edge_M = {
    'N': {'type': 'city', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 5),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N'], 'ismeepleplaceable': True, 'meeple_coordinates': (90, 42),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'field', 'connections': []}
}

edge_N = {
    'N': {'type': 'city', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 5),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N'], 'ismeepleplaceable': True, 'meeple_coordinates': (90, 42),
          'meeple': None},
    'S': {'type': 'field', 'connections': []},
    'W': {'type': 'field', 'connections': []}
}

edge_O = {
    'N': {'type': 'city', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 10),
          'meeple': None},
    'E': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (90, 55),
          'meeple': None},
    'S': {'type': 'road', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (55, 85),
          'meeple': None},
    'W': {'type': 'city', 'connections': ['N'], 'ismeepleplaceable': True, 'meeple_coordinates': (8, 42),
          'meeple': None}
}

edge_P = {
    'N': {'type': 'city', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 10),
          'meeple': None},
    'E': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (90, 55),
          'meeple': None},
    'S': {'type': 'road', 'connections': ['E'], 'ismeepleplaceable': True, 'meeple_coordinates': (55, 85),
          'meeple': None},
    'W': {'type': 'city', 'connections': ['N'], 'ismeepleplaceable': True, 'meeple_coordinates': (8, 42),
          'meeple': None}
}

edge_Q = {
    'N': {'type': 'city', 'connections': ['E', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'S': {'type': 'field', 'connections': [None]},
    'W': {'type': 'city', 'connections': ['E', 'N'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None}
}

edge_R = {
    'N': {'type': 'city', 'connections': ['E', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'S': {'type': 'field', 'connections': [None]},
    'W': {'type': 'city', 'connections': ['E', 'N'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None}
}

edge_S = {
    'N': {'type': 'city', 'connections': ['E', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 96),
          'meeple': None},
    'W': {'type': 'city', 'connections': ['E', 'N'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None}
}

edge_T = {
    'N': {'type': 'city', 'connections': ['E', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'E': {'type': 'city', 'connections': ['N', 'W'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 96),
          'meeple': None},
    'W': {'type': 'city', 'connections': ['E', 'N'], 'ismeepleplaceable': True, 'meeple_coordinates': (45, 35),
          'meeple': None}
}

edge_U = {
    'N': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (34, 10),
          'meeple': None},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'road', 'connections': ['N'], 'ismeepleplaceable': True, 'meeple_coordinates': (60, 80),
          'meeple': None},
    'W': {'type': 'field', 'connections': []}
}

edge_V = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'field', 'connections': []},
    'S': {'type': 'road', 'connections': ['W'], 'ismeepleplaceable': True, 'meeple_coordinates': (61, 87),
          'meeple': None},
    'W': {'type': 'road', 'connections': ['S'], 'ismeepleplaceable': True, 'meeple_coordinates': (13, 31),
          'meeple': None}
}

edge_W = {
    'N': {'type': 'field', 'connections': []},
    'E': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (95, 56),
          'meeple': None},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (55, 93),
          'meeple': None},
    'W': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (7, 48),
          'meeple': None}
}

edge_X = {
    'N': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (46, 12),
          'meeple': None},
    'E': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (100, 55),
          'meeple': None},
    'S': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (50, 97),
          'meeple': None},
    'W': {'type': 'road', 'connections': [None], 'ismeepleplaceable': True, 'meeple_coordinates': (8, 56),
          'meeple': None}
}

# 定义每种类型的牌的数量
tiles_info = {'A': (2, edge_A, False, True), 'B': (4, edge_B, False, True), 'C': (1, edge_C, True, False),
              'D': (3, edge_D, False, False), 'E': (5, edge_E, False, False), 'F': (2, edge_F, True, False),
              'G': (1, edge_G, False, False), 'H': (3, edge_H, False, False), 'I': (2, edge_I, False, False),
              'J': (3, edge_J, False, False), 'K': (3, edge_K, False, False), 'L': (3, edge_L, False, False),
              'M': (2, edge_M, True, False), 'N': (3, edge_N, False, False), 'O': (1, edge_O, True, False),
              'P': (3, edge_P, False, False), 'Q': (1, edge_Q, True, False), 'R': (3, edge_R, False, False),
              'S': (2, edge_S, True, False), 'T': (1, edge_T, False, False), 'U': (8, edge_U, False, False),
              'V': (9, edge_V, False, False), 'W': (4, edge_W, False, False), 'X': (1, edge_X, False, False)}
