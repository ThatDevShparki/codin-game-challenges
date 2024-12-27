from __future__ import annotations

import sys
from collections import deque
from dataclasses import field
from enum import Enum
from typing import Any
from typing import NamedTuple


class Game:
    width: int
    height: int

    turn: int
    state: GameState | None
    history: list[GameState]
    outputs: list[GameOutput]

    """ Game methods """

    def update(
        self,
        player: ContestantState,
        opponent: ContestantState,
        entities: dict[Coord, Entity],
    ) -> None:
        print(player)
        print(opponent)
        print(entities)

        """Step 1: BFS graph from root"""
        graph: dict[Coord, Node] = {}
        unvisited_coords: deque[Coord] = deque()
        visited_coords: set[Coord] = set()

        # initialize with root
        root_node = Node(
            x=player.root.x,
            y=player.root.y,
            entity=player.root,
            neighbor_n=None,
            neighbor_e=None,
            neighbor_s=None,
            neighbor_w=None,
        )
        graph[player.root.coord] = root_node
        unvisited_coords.append(player.root.coord)

        # Iterate through all neighbors
        while unvisited_coords:
            coord = unvisited_coords.popleft()
            debug(f"Visiting {coord}")

            if coord in visited_coords:
                debug(" > Already visited")
                continue
            visited_coords.add(coord)

            node = graph.get(coord)
            if not node:
                continue

            for direction, (i, j) in DIRECTION_VECTORS.items():
                nx, ny = coord[0] + i, coord[1] + j
                entity = entities.get((nx, ny))
                if entity and entity.kind == EntityKind.WALL:
                    continue

                debug(" > Neighbour:", nx, ny)

                neighbor_dir = direction.reverse()
                neighbor_node = Node(
                    x=nx,
                    y=ny,
                    entity=entity,
                    neighbor_n=(node if neighbor_dir == Direction.NORTH else None),
                    neighbor_e=(node if neighbor_dir == Direction.EAST else None),
                    neighbor_s=(node if neighbor_dir == Direction.SOUTH else None),
                    neighbor_w=(node if neighbor_dir == Direction.WEST else None),
                )
                graph[(nx, ny)] = neighbor_node

                node = node.update_neighbor(direction, neighbor_node)
                debug(" > Updated node:", node)

                unvisited_coords.append((nx, ny))

        for coord, node in graph.items():
            debug(f"Node: {coord} - {node}")

        # Organize map as a graph
        # # Game state is updated before update every turn
        # assert self.state is not None

        # # Cache all entities and special entities such as organism and walls
        # entity_map: dict[tuple[int, int], Entity] = {}
        # organism: dict[tuple[int, int], Entity] = {}
        # walls: dict[tuple[int, int], Entity] = {}
        # proteins: dict[tuple[int, int], Entity] = {}
        # for entity in entities:
        #     coord = (entity.x, entity.y)
        #     entity_map[coord] = entity
        #     if (
        #         entity.kind in EntityKind.ORGANISMS
        #         and entity.owner == Contestant.PLAYER
        #     ):
        #         organism[coord] = entity
        #     if entity.kind == EntityKind.WALL:
        #         walls[coord] = entity
        #     if entity.kind in EntityKind.PROTEINS:
        #         proteins[coord] = entity

        # # Groom through proteins and find available points of entry for harvesters
        # protein_ports: list[
        #     tuple[tuple[int, int], Direction, Entity, int]
        # ] = []  # coord, direction, closest organ, and distance
        # # Only do maths if we can purchase port
        # if self.state.player.protein_c >= 1 and self.state.player.protein_d >= 1:
        #     for coord, entity in proteins.items():
        #         for neighbor, direction in neighborhood(
        #             *coord, width=self.width, height=self.height
        #         ):
        #             if neighbor not in entity_map:
        #                 # Let's calculate the distance and closest organ
        #                 closest_organ: Entity | None = None
        #                 closest_distance: int | None = None
        #                 for organ in organism.values():
        #                     o_distance = taxi_distance(
        #                         organ.x, organ.y, neighbor[0], neighbor[1]
        #                     )
        #                     if (
        #                         closest_distance is None
        #                         or o_distance < closest_distance
        #                     ):
        #                         closest_distance = o_distance
        #                         closest_organ = organ

        #                 # We know *something* is closest because we have atleast one organ
        #                 assert closest_organ is not None
        #                 assert closest_distance is not None

        #                 protein_ports.append(
        #                     (
        #                         neighbor,
        #                         direction.reverse(),  # Use the direction to point Harvster in
        #                         closest_organ,
        #                         closest_distance,
        #                     )
        #                 )

        #     protein_ports = sorted(protein_ports, key=lambda p: p[-1])
        #     coord, direction, entity, distance = protein_ports.pop(0)
        #     if distance == 1:
        #         return [
        #             Grow(EntityKind.HARVESTER, coord[0], coord[1], direction, entity)
        #         ]
        #     else:
        #         return [
        #             Grow(EntityKind.BASIC, coord[0], coord[1], Direction.NORTH, entity)
        #         ]

        # debug("No available resources for Harvesters- growing in best direction")
        # for organ in organism.values():
        #     for coord, _ in neighborhood(
        #         x=organ.x, y=organ.y, width=self.width, height=self.height
        #     ):
        #         if coord not in entity_map:
        #             return [
        #                 Grow(
        #                     EntityKind.BASIC, coord[0], coord[1], Direction.NORTH, organ
        #                 )
        #             ]

    def output(self, output: GameOutput) -> None:
        self.outputs.append(output)

    """ Game loop methods """

    def do_game_update(self) -> None:
        state = self.read_game_state()

        self.turn += 1
        self.outputs = []
        self.state = state
        self.history.append(state)

        self.update(
            player=state.player,
            opponent=state.opponent,
            entities=state.entities,
        )

        # This is to ensure that there are valid outputs
        while len(self.outputs) != state.actions:
            debug("Not enough actions, appending WAIT")
            self.output(Wait())

        self.process_game_outputs(self.outputs)

    """ Factory methods """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.turn = 0
        self.state = None
        self.history = []
        self.outputs = []

    @classmethod
    def from_input(cls) -> Game:
        width, height = [int(i) for i in read_input().split()]
        return Game(width=width, height=height)

    """ Helper methods """

    @staticmethod
    def read_game_state() -> GameState:
        # Read entities and cache by uid without refrence to root or parent
        tmp_entities: dict[
            int, tuple[Entity, int | None, int | None]
        ] = {}  # uid: (entity, parent_uid, root_uid)
        for idx in range(int(read_input())):
            (
                _x,
                _y,
                _kind,
                _owner,
                _uid,
                _dir,
                _parent_uid,
                _root_uid,
            ) = read_input().strip().split()

            _tmp_uid = int(_uid) if int(_uid) else (-idx)
            tmp_entities[_tmp_uid] = (
                Entity(
                    uid=_tmp_uid,
                    x=int(_x),
                    y=int(_y),
                    kind=EntityKind(_kind),
                    owner=None if _owner == "-1" else Contestant(_owner),
                    direction=Direction(_dir),
                    root=None,
                    parent=None,
                ),
                None if int(_parent_uid) == -1 else int(_parent_uid),
                None if int(_root_uid) == -1 else int(_root_uid),
            )

        # Process entities
        entities: dict[Coord, Entity] = {}
        roots: dict[Contestant, Entity] = {}

        for entity, parent_uid, root_uid in tmp_entities.values():
            if parent_uid:
                entity = entity.update_parent(tmp_entities[parent_uid][0])
            if root_uid:
                entity = entity.update_root(tmp_entities[root_uid][0])

            entities[entity.coord] = entity
            if entity.kind == EntityKind.ROOT and entity.owner:
                roots[entity.owner] = entity

        my_a, my_b, my_c, my_d = [int(i) for i in read_input().split()]
        player_state = ContestantState(
            root=roots[Contestant.PLAYER],
            protein_a=my_a,
            protein_b=my_b,
            protein_c=my_c,
            protein_d=my_d,
        )

        opp_a, opp_b, opp_c, opp_d = [int(i) for i in read_input().split()]
        opponent_state = ContestantState(
            root=roots[Contestant.OPPONENT],
            protein_a=opp_a,
            protein_b=opp_b,
            protein_c=opp_c,
            protein_d=opp_d,
        )

        required_actions_count = int(read_input())

        return GameState(
            player=player_state,
            opponent=opponent_state,
            entities=entities,
            actions=required_actions_count,
        )

    @staticmethod
    def process_game_outputs(outputs: list[GameOutput]) -> None:
        for output in outputs:
            output_str = " ".join(
                [output.command.value, *list(map(str, output.params))]
            )
            print(output_str)


""" Types"""

Coord = tuple[int, int]


class GameOutput(NamedTuple):
    command: GameCommand
    params: list[str]


class GameCommand(Enum):
    GROW = "GROW"
    WAIT = "WAIT"


class GameState(NamedTuple):
    player: ContestantState
    opponent: ContestantState
    entities: dict[Coord, Entity]
    actions: int


class ContestantState(NamedTuple):
    root: Entity
    protein_a: int
    protein_b: int
    protein_c: int
    protein_d: int


class Entity(NamedTuple):
    uid: int
    x: int
    y: int
    kind: EntityKind
    owner: Contestant | None
    direction: Direction
    parent: Entity | None
    root: Entity | None

    @property
    def coord(self) -> Coord:
        return (self.x, self.y)

    """ factory methods """

    def update_parent(self, parent: Entity) -> Entity:
        return Entity(
            uid=self.uid,
            x=self.x,
            y=self.y,
            kind=self.kind,
            owner=self.owner,
            direction=self.direction,
            parent=parent,
            root=self.root,
        )

    def update_root(self, root: Entity) -> Entity:
        return Entity(
            uid=self.uid,
            x=self.x,
            y=self.y,
            kind=self.kind,
            owner=self.owner,
            direction=self.direction,
            parent=self.parent,
            root=root,
        )


class EntityKind(Enum):
    ROOT = "ROOT"
    WALL = "WALL"
    BASIC = "BASIC"
    HARVESTER = "HARVESTER"
    TENTACLE = "TENTACLE"
    PROTEIN_A = "A"
    PROTEIN_B = "B"
    PROTEIN_C = "C"
    PROTEIN_D = "D"

    @classmethod
    @property
    def ORGANISMS(cls) -> list[EntityKind]:  # type: ignore
        return [cls.ROOT, cls.BASIC, cls.HARVESTER, cls.TENTACLE]

    @classmethod
    @property
    def PROTEINS(cls) -> list[EntityKind]:  # type: ignore
        return [cls.PROTEIN_A, cls.PROTEIN_B, cls.PROTEIN_C, cls.PROTEIN_D]


class Contestant(Enum):
    PLAYER = "1"
    OPPONENT = "0"


class Direction(Enum):
    NONE = "X"
    NORTH = "N"
    SOUTH = "W"
    EAST = "E"
    WEST = "S"

    def reverse(self) -> Direction:
        if self == Direction.NORTH:
            return Direction.SOUTH
        if self == Direction.SOUTH:
            return Direction.NORTH

        if self == Direction.EAST:
            return Direction.WEST
        if self == Direction.WEST:
            return Direction.EAST

        return Direction.NONE


DIRECTION_VECTORS: dict[Direction, Coord] = {
    Direction.NORTH: (0, -1),
    Direction.SOUTH: (0, 1),
    Direction.EAST: (1, 0),
    Direction.WEST: (-1, 0),
}


class Node:
    x: int
    y: int
    entity: Entity | None

    parent: Node | None = None
    children: set[Node] = field(default_factory=set)
    features: dict[Direction, Node | None] = field(default_factory=dict)

    @property
    def coord(self) -> Coord:
        return (self.x, self.y)

    def __init__(
        self,
        x: int,
        y: int,
        entity: Entity | None,
        parent: Node | None = None,
        children: set[Node] | None = None,
        features: dict[Direction, Node | None] | None = None,
    ):
        self.x = x
        self.y = y
        self.entity = entity
        self.parent = parent
        self.children = children or set()
        self.features = features or {}

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.entity))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Node):
            return False
        return all([self.x == other.x, self.y == other.y, self.entity == other.entity])


class Strategy:
    source: Node
    target: Node
    kind: EntityKind
    direction: Direction
    cost: Cost
    fitness: Fitness

    def __init__(
        self,
        source: Node,
        target: Node,
        kind: EntityKind,
        cost: Cost,
        fitness: Fitness,
        direction: Direction = Direction.NONE,
    ) -> None:
        self.source = source
        self.target = target
        self.kind = kind
        self.direction = direction
        self.cost = cost
        self.fitness = fitness

    def __hash__(self) -> int:
        return hash((self.source, self.target, self.kind, self.cost, self.fitness))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Strategy):
            return False

        return all(
            [
                self.source == other.source,
                self.target == other.target,
                self.kind == other.kind,
                self.cost == other.cost,
                self.fitness == other.fitness,
            ]
        )

    @classmethod
    def for_entity_kind(
        cls,
        source: Node,
        target: Node,
        kind: EntityKind,
        direction: Direction = Direction.NONE,
    ) -> Strategy:
        return Strategy(
            source=source,
            target=target,
            kind=kind,
            cost=Cost.for_entity_kind(kind),
            fitness=Fitness.for_entity_kind(kind),
            direction=direction,
        )


class Cost(NamedTuple):
    a: int
    b: int
    c: int
    d: int

    @classmethod
    def for_entity_kind(cls, kind: EntityKind) -> Cost:
        if kind == EntityKind.BASIC:
            return cls(a=1, b=0, c=0, d=0)
        if kind == EntityKind.HARVESTER:
            return cls(a=0, b=0, c=1, d=1)
        if kind == EntityKind.TENTACLE:
            return cls(a=0, b=1, c=1, d=0)
        return cls(a=0, b=0, c=0, d=0)


class Fitness(NamedTuple):
    score: int

    @classmethod
    def for_entity_kind(cls, kind: EntityKind) -> Fitness:
        if kind in EntityKind.ORGANISMS:
            return cls(score=1)
        return cls(score=0)


""" Common utility methods """


def Grow(
    kind: EntityKind, x: int, y: int, direction: Direction, parent: Entity
) -> GameOutput:
    return GameOutput(
        command=GameCommand.GROW,
        params=[str(parent.uid), str(x), str(y), kind.value, direction.value],
    )


def Wait() -> GameOutput:
    return GameOutput(command=GameCommand.WAIT, params=[])


def read_input() -> str:
    _input = input()
    # debug(_input)
    return _input


def debug(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stderr, flush=True)


def taxi_distance(p1: Coord, p2: Coord) -> int:
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])


""" Game loop """

if __name__ == "__main__":
    game = Game.from_input()
    while True:
        game.do_game_update()
