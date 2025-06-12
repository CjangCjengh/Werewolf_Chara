from observation.observation import Observation
from PIL import Image, ImageDraw, ImageFont
import observation.carcassonne_setting as carcassonne_setting


class Meeple:
    def __init__(self, color: str, owner: str):
        self.color = color
        self.owner = owner
        self.isplaced = False  # 标记 Meeple 是否已放置
        self.tile = None  # 记录 Meeple 所在的 Tile 对象
        self.position_key = None  # 记录 Meeple 所在 Tile 的哪个方向（N, E, S, W, 或 M）

    def place(self, tile, direction):
        self.isplaced = True
        self.tile = tile
        self.position_key = direction
        tile.edges[direction]['meeple'] = self  # 在 Tile 的对应方向上设置 Meeple

    def remove(self):
        if self.tile and self.position_key in self.tile.edges:
            self.tile.edges[self.position_key]['meeple'] = None  # 从瓦片上移除对 Meeple 的引用
        self.isplaced = False  # 标记为未放置
        self.tile = None  # 清除所在瓦片的引用
        self.position_key = None  # 清除位置信息


class Tile:
    def __init__(self, type, edges, isshield, ismonastery, position=(None, None)):
        self.type = type
        self.edges = edges
        self.rotation = 0
        self.isshield = isshield
        self.ismonastery = ismonastery
        self.position = position

    def rotate(self, angle):
        if angle % 90 != 0 or angle < 0 or angle >= 360:
            raise ValueError("Invalid rotation angle. Angle must be one of: 0, 90, 180, 270")

        num_rotations = angle // 90
        for _ in range(num_rotations):
            # 更新边缘信息及其内的Meeple位置和连接信息
            new_edges = {
                'N': self.edges['W'],
                'E': self.edges['N'],
                'S': self.edges['E'],
                'W': self.edges['S']
            }
            self.edges = new_edges
            # 更新Meeple位置和连接信息
            meeple_updates = {
                'N': 'E',
                'E': 'S',
                'S': 'W',
                'W': 'N'
            }
            for dir, edge in new_edges.items():
                if 'meeple_coordinates' in self.edges[dir]:
                    x, y = self.edges[dir]['meeple_coordinates']
                    x_c, y_c = x + 10, y + 10
                    x_c_r, y_c_r = 120 - y_c, x_c
                    edge['meeple_coordinates'] = (x_c_r - 10, y_c_r - 10)
                if 'connections' in self.edges[dir]:
                    # 将连接也进行相应的旋转
                    edge['connections'] = [meeple_updates[conn] if conn in meeple_updates else conn for conn in
                                           edge['connections']]

            # 应用新的边缘信息
            self.edges = new_edges

        self.rotation = (self.rotation + angle) % 360
        return self

    def make_image(self):
        image = Image.open(carcassonne_setting.tileTopath.get(self.type))
        rotated_image = image.rotate(-self.rotation, expand=True)

        # 粘贴每个已放置的Meeple
        for edge_key, edge in self.edges.items():
            if 'meeple' in edge and edge['meeple'] is not None:
                meeple = edge['meeple']
                if meeple.isplaced:
                    meeple_image_path = carcassonne_setting.meepleTopath.get(meeple.color)
                    meeple_image = Image.open(meeple_image_path)
                    meeple_x, meeple_y = edge['meeple_coordinates']
                    rotated_image.paste(meeple_image, (meeple_x, meeple_y), meeple_image)

        return rotated_image


class Board:
    def __init__(self):
        self.tiles = {(0, 0): Tile('D', carcassonne_setting.tiles_info.get('D')[1], carcassonne_setting.tiles_info.get('D')[2],
                                   carcassonne_setting.tiles_info.get('D')[3], position=(0, 0))}
        self.min_row = 0
        self.max_row = 0
        self.min_col = 0
        self.max_col = 0
        self.monastery = []  # 存储修道院的坐标，方便后面计分检查

    def place_tile(self, new_tile: Tile, row, col):
        if (row, col) in self.tiles:
            return False  # Tile already placed

        # Directions to check [North, East, South, West]
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        dir_keys = ['N', 'E', 'S', 'W']
        around = []
        for d, key in zip(directions, dir_keys):
            adj_row, adj_col = row + d[0], col + d[1]
            adj_tile = self.tiles.get((adj_row, adj_col))
            around.append(adj_tile)
            if adj_tile:
                print(f"({row},{col})的{key}部是{new_tile.edges[key]['type']}，对比{adj_tile.position}的{dir_keys[(dir_keys.index(key) + 2) % 4]}是{adj_tile.edges[dir_keys[(dir_keys.index(key) + 2) % 4]]['type']}")
                if not new_tile.edges[key]['type'] == adj_tile.edges[dir_keys[(dir_keys.index(key) + 2) % 4]]['type']:
                    return False  # Edge types do not match
        if all(item is None for item in around):
            return False
        self.tiles[(row, col)] = new_tile
        new_tile.position = (row, col)
        if new_tile.ismonastery:
            self.monastery.append((row, col))

        self.min_row = min(self.min_row, row)
        self.max_row = max(self.max_row, row)
        self.min_col = min(self.min_col, col)
        self.max_col = max(self.max_col, col)
        return True

    def place_meeple(self, tile: Tile, position_key, meeple):
        if position_key not in tile.edges:
            return False, "指定位置不存在"

        edge = tile.edges[position_key]
        if 'ismeepleplaceable' not in edge.keys():
            return False, "此位置不允许放置Meeple"

        if edge['meeple'] is not None:
            return False, f"此位置已经有Meeple了"

        feature_type = edge['type']
        if feature_type in ['road', 'city'] and self.isFeatureOccupied(tile, position_key, feature_type):
            return False, f"这条{feature_type}上已有其他Meeple"

        meeple.place(tile, position_key)  # 使用 Meeple 的新方法设置位置
        return True, "Meeple放置成功"

    def isFeatureOccupied(self, start_tile, start_direction, feature_type):
        visited = set()
        print(f"===检查是否同一{feature_type}上是否有其它Meeple")
        return self._check_occupied(start_tile, start_direction, feature_type, visited)

    def _check_occupied(self, tile, direction, feature_type, visited):
        if (tile, direction) in visited:
            return False
        visited.add((tile, direction))
        print(f"======检查{tile.position},{direction}")
        current_edge = tile.edges[direction]
        if 'meeple' in current_edge and current_edge['meeple'] is not None:
            print(f"该{feature_type}被{current_edge['meeple'].tile.position}的meeple占据")
            return True  # 在当前边缘已经有Meeple
        # 检查所有连接的方向
        tocheck = current_edge['connections'].copy()
        tocheck.append(direction)
        # print(tocheck)
        for conn_dir in tocheck:
            if conn_dir == None:
                continue
            current_edge = tile.edges[conn_dir]
            if 'meeple' in current_edge and current_edge['meeple'] is not None:
                print(f"该{feature_type}被{current_edge['meeple'].tile.position}的{conn_dir}side的meeple占据")
                return True  # 在当前边缘已经有Meeple
            neighbor_position, t_dir = self._get_neighbor_position(tile.position, conn_dir)
            print(neighbor_position, t_dir)
            neighbor_tile = self.tiles.get(neighbor_position)
            if neighbor_tile is not None and self._check_occupied(neighbor_tile, t_dir, feature_type, visited):
                return True  # 递归检查邻接Tile

        return False

    def isFeatureCompleted(self, start_tile, start_direction):
        feature_type = start_tile.edges[start_direction]['type']
        print(f'===检查从{start_tile.position}的{start_direction}开始的{feature_type}是否闭合')
        to_check = [(start_tile, start_direction)]  # 初始检查队列
        visited = set()  # 已检查队列
        visited_tile = set()
        visited_tile.add(start_tile)
        involved_meeples = []  # 涉及到的Meeple列表及其位置
        is_closed = True  # 假设特征是闭合的，直到发现开放状态

        while to_check:
            current_tile, current_direction = to_check.pop(0)  # 从队列中获取一个待检查的项
            print(f"======{current_tile.position},{current_direction}")
            current_edge = current_tile.edges[current_direction]

            # 检查当前边缘是否已访问，避免重复处理
            if (current_tile, current_direction) in visited:
                continue
            visited.add((current_tile, current_direction))

            # 记录这个方向上的 Meeple 及其位置
            if current_edge.get('meeple') is not None:
                involved_meeples.append((current_edge['meeple'], current_tile, current_direction))

            # 检查连接信息
            connections = current_edge['connections'].copy()
            connections.append(current_direction)

            # 检查所有连接的方向
            for conn_dir in connections:
                if conn_dir == None:
                    continue
                # print(current_tile.position,conn_dir)
                neighbor_position, t_dir = self._get_neighbor_position(current_tile.position, conn_dir)
                neighbor_tile = self.tiles.get(neighbor_position)
                if neighbor_tile is None:
                    is_closed = False  # 邻接位置没有瓦片，开放状态
                    continue
                if ((neighbor_tile, t_dir) not in visited):
                    to_check.append((neighbor_tile, t_dir))  # 添加到检查队列
                visited_tile.add(neighbor_tile)
        print("闭合" if is_closed else "不闭合")

        return is_closed, involved_meeples, visited_tile

    def calculate_scores(self, tile):
        scores = {}

        # 首先检查修道院
        for monastery_position in self.monastery:
            monastery_tile = self.tiles.get(monastery_position)
            if monastery_tile and monastery_tile.ismonastery and 'M' in monastery_tile.edges:
                if monastery_tile.edges['M']['meeple']:
                    if self.is_monastery_complete(monastery_tile) == 8:
                        player = monastery_tile.edges['M']['meeple'].owner
                        scores[player] = scores.get(player, 0) + 9  # 修道院完成得9分
                        monastery_tile.edges['M']['meeple'].remove()

        checked_edge = set()  # 检查ege
        # 然后检查其他特征
        for direction, edge in tile.edges.items():
            if direction in checked_edge:
                continue
            if edge['type'] not in ['road', 'city']:
                continue
            print(f'检查{direction}')
            checked_edge.add(direction)
            checked_edge.update(t_direction for t_direction in edge['connections'])

            is_closed, involved_meeples, visited_tile = self.isFeatureCompleted(tile, direction)
            if is_closed:
                meeple_count = self.count_meeples(involved_meeples)
                max_meeple = max(meeple_count.values()) if meeple_count else 0
                if max_meeple > 0:  # 确保有 Meeple 存在
                    winners = [player for player, count in meeple_count.items() if count == max_meeple]
                    score = self.score_feature(edge['type'], visited_tile)
                    for player in winners:
                        scores[player] = scores.get(player, 0) + score
                # 移除所有 Meeple
                self.remove_meeples(involved_meeples)

        return scores

    def final_scoring(self):
        scores = {}
        for _, tile in self.tiles.items():
            for direction, edge in tile.edges.items():
                if edge['meeple'] and edge['meeple'].isplaced:
                    player = edge['meeple'].owner
                    if edge['type'] == 'monastery':  # 计算修道院
                        score = 9 if self.is_monastery_complete(tile) == 9 else 0
                        scores[player] = scores.get(player, 0) + score
                        edge['meeple'].remove()
                    elif edge['type'] in ['road', 'city']:
                        is_closed, involved_meeples, visited_tile = self.isFeatureCompleted(tile, direction)
                        meeple_count = self.count_meeples(involved_meeples)
                        max_meeple = max(meeple_count.values()) if meeple_count else 0
                        if max_meeple > 0:
                            winners = [player for player, count in meeple_count.items() if count == max_meeple]
                            score = self.score_feature(edge['type'], visited_tile, isfinal=True)
                            for player in winners:
                                scores[player.name] = scores.get(player.name, 0) + score
                        # 移除所有 Meeple
                        self.remove_meeples(involved_meeples)
        return scores

    def is_monastery_complete(self, monastery_tile):
        row, col = monastery_tile.position
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1), (0, 0)]
        complete_count = sum(1 for d in directions if (row + d[0], col + d[1]) in self.tiles)
        return complete_count

    def score_feature(self, feature_type, visited_tile, isfinal=False):
        score = 0
        val_shield = 2
        val_city = 2
        val_road = 1
        if isfinal:
            val_shield = 1
            val_city = 1
        for t in visited_tile:
            if t.isshield:
                score += val_shield
            score += (val_city if feature_type == 'city' else val_road)
        return score

    def remove_meeples(self, involved_meeples):
        for meeple, tile, direction in involved_meeples:
            if tile.edges[direction].get('meeple'):
                tile.edges[direction]['meeple'].remove()

    def count_meeples(self, involved_meeples):
        meeple_count = {}
        for meeple, tile, direction in involved_meeples:
            player = meeple.owner
            if player.name in meeple_count:
                meeple_count[player.name] += 1
            else:
                meeple_count[player.name] = 1
        return meeple_count

    def _get_neighbor_position(self, position, direction):
        # 根据方向计算邻接瓦片的位置
        row, col = position
        if direction == 'N':
            return (row - 1, col), 'S'
        elif direction == 'S':
            return (row + 1, col), 'N'
        elif direction == 'E':
            return (row, col + 1), 'W'
        elif direction == 'W':
            return (row, col - 1), 'E'

    def display(self):
        # Calculate dimensions
        rows = self.max_row - self.min_row + 3
        cols = self.max_col - self.min_col + 3

        # Create an empty board image with extra space for coordinates, title, and right margin
        board_width = cols * 120
        board_height = rows * 120
        extra_height = 100  # space for title and horizontal coordinates
        extra_width = 50  # space for vertical coordinates
        extra_right_width = 50  # Additional space on the right side

        board_image = Image.new('RGB', (board_width + extra_width + extra_right_width, board_height + extra_height),
                                'white')

        draw = ImageDraw.Draw(board_image)
        font = ImageFont.truetype("arial.ttf", 18)
        small_font = ImageFont.truetype("arial.ttf", 14)  # Smaller font for grid coordinates
        title_font = ImageFont.truetype("arial.ttf", 24)  # Larger font for the title

        # Draw tiles and potential placement grids
        for row in range(self.min_row - 1, self.max_row + 2):
            for col in range(self.min_col - 1, self.max_col + 2):
                x = (col - self.min_col + 1) * 120 + extra_width  # Adjust for extra space for vertical coordinates
                y = (row - self.min_row + 1) * 120 + extra_height - 50  # Adjust for extra space for title

                # Determine if the spot is a valid placement location
                if (row, col) not in self.tiles:
                    neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
                    if any((nr, nc) in self.tiles for nr, nc in neighbors):
                        draw.rectangle([x, y, x + 120, y + 120], fill='#CCCCCC', outline='black')
                        # Draw the coordinates in the center of the gray box
                        coord_text = f"({row}, {col})"
                        text_bbox = draw.textbbox((x + 60, y + 60), coord_text, font=small_font, anchor="mm")
                        draw.text((text_bbox[0], text_bbox[1]), coord_text, fill="black", font=small_font)
                else:
                    board_image.paste(self.tiles[(row, col)].make_image(), (x, y))

        # Draw horizontal coordinates at the top
        for col in range(self.min_col - 1, self.max_col + 2):
            x = (col - self.min_col + 1) * 120 + extra_width + 60
            text_bbox = draw.textbbox((x, 10), str(col), font=font, anchor="mm")
            draw.text((text_bbox[0], text_bbox[1]), str(col), fill="black", font=font)

        # Draw vertical coordinates on the left
        for row in range(self.min_row - 1, self.max_row + 2):
            y = (row - self.min_row + 1) * 120 + extra_height
            text_bbox = draw.textbbox((15, y), str(row), font=font, anchor="mm")
            draw.text((text_bbox[0], text_bbox[1]), str(row), fill="black", font=font)

        # Draw title below the board
        title = "Carcassonne Map"
        title_bbox = draw.textbbox(
            ((board_width + extra_width + extra_right_width) // 2, board_height + extra_height - 30), title,
            font=title_font, anchor="mm")
        draw.text((title_bbox[0], title_bbox[1]), title, fill="black", font=title_font)

        return board_image


class CarcassonneGameObservation(Observation):
    # info
    board = Board()
    deck = []
    current_player = None
    playersinfo = {}
    playerorder = []
    log=[]
    t_tile = board.tiles.get((0,0))

    def init(self):
        board = Board()
        deck = []
        current_player = None
        playersinfo = {}
        playerorder = []
        log = []
        t_tile = board.tiles.get((0,0))


    def create_image(self):
        pass


if __name__ == "__main__":
    pass
