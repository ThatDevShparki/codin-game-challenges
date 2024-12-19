from __future__ import annotations

import sys
from enum import Enum
from typing import Any, NamedTuple


class Game:
    width: int
    height: int
    state: GameState | None
    outputs: list[GameOutput]

    def update(self, entities: list[Entity]) -> list[GameOutput]:
        # Game state is updated before update every turn
        assert self.state is not None

        debug(self.state)

        # Cache all entities and special entities such as organism and walls
        entity_map: dict[tuple[int, int], Entity] = {}
        organism: dict[tuple[int, int], Entity] = {}
        walls: dict[tuple[int, int], Entity] = {}
        proteins: dict[tuple[int, int], Entity] = {}
        for entity in entities:
            coord = (entity.x, entity.y)
            entity_map[coord] = entity
            if (
                entity.kind in EntityKind.ORGANISMS
                and entity.owner == Contestant.PLAYER
            ):
                organism[coord] = entity
            if entity.kind == EntityKind.WALL:
                walls[coord] = entity
            if entity.kind in EntityKind.PROTEINS:
                proteins[coord] = entity

        # Groom through proteins and find available points of entry for harvesters
        debug("Protein ports:")
        protein_ports: list[
            tuple[tuple[int, int], Direction, Entity, int]
        ] = []  # coord, direction, closest organ, and distance
        # Only do maths if we can purchase port
        if self.state.player.protein_c >= 1 and self.state.player.protein_d >= 1:
            for coord, entity in proteins.items():
                for neighbor, direction in neighborhood(
                    *coord, width=self.width, height=self.height
                ):
                    if neighbor not in entity_map:
                        # Let's calculate the distance and closest organ
                        closest_organ: Entity | None = None
                        closest_distance: int | None = None
                        for organ in organism.values():
                            o_distance = taxi_distance(
                                organ.x, organ.y, neighbor[0], neighbor[1]
                            )
                            if (
                                closest_distance is None
                                or o_distance < closest_distance
                            ):
                                closest_distance = o_distance
                                closest_organ = organ

                        # We know *something* is closest because we have atleast one organ
                        assert closest_organ is not None
                        assert closest_distance is not None

                        protein_ports.append(
                            (
                                neighbor,
                                direction.reverse(),  # Use the direction to point Harvster in
                                closest_organ,
                                closest_distance,
                            )
                        )

            protein_ports = sorted(protein_ports, key=lambda p: p[-1])
            coord, direction, entity, distance = protein_ports.pop(0)
            if distance == 1:
                return [
                    Grow(EntityKind.HARVESTER, coord[0], coord[1], direction, entity)
                ]
            else:
                return [
                    Grow(EntityKind.BASIC, coord[0], coord[1], Direction.NORTH, entity)
                ]

        debug("No available resources for Harvesters- growing in best direction")
        for organ in organism.values():
            for coord, _ in neighborhood(
                x=organ.x, y=organ.y, width=self.width, height=self.height
            ):
                if coord not in entity_map:
                    return [
                        Grow(
                            EntityKind.BASIC, coord[0], coord[1], Direction.NORTH, organ
                        )
                    ]

    """ Game loop methods """

    def do_game_update(self) -> None:
        input_turn = self.read_game_inputs()
        self.state = input_turn.state

        outputs = self.update(entities=input_turn.entities)

        # This is for debugging
        while len(outputs) != input_turn.actions:
            debug("Not enough actions, appending WAIT")
            outputs.append(Wait())

        self.print_game_outputs(outputs)

    """ Factory methods """

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.state = None
        self.outputs = []

    @classmethod
    def initialize(cls) -> Game:
        game_input_init = cls.read_game_init()
        return Game(
            width=game_input_init.width,
            height=game_input_init.height,
        )

    """ Helper methods """

    @staticmethod
    def read_game_init() -> GameInputInit:
        width, height = [int(i) for i in input().split()]
        return GameInputInit(width=width, height=height)

    @staticmethod
    def read_game_inputs() -> GameInputTurn:
        entities: list[Entity] = []
        for _ in range(int(input())):
            (
                _x,
                _y,
                _kind,
                _owner,
                _organ_id,
                _organ_dir,
                _organ_parent_id,
                _organ_root_id,
            ) = input().strip().split()
            entities.append(
                Entity(
                    uid=int(_organ_id),
                    x=int(_x),
                    y=int(_y),
                    kind=EntityKind(_kind),
                    owner=None if _owner == "-1" else Contestant(_owner),
                    direction=Direction(_organ_dir),
                    root_uid=(None if _organ_root_id == "-1" else int(_organ_root_id)),
                    parent_uid=(
                        None if _organ_parent_id == "-1" else int(_organ_parent_id)
                    ),
                    root=None,
                    parent=None,
                )
            )

        my_a, my_b, my_c, my_d = [int(i) for i in input().split()]
        player_state = ContestantState(
            protein_a=my_a, protein_b=my_b, protein_c=my_c, protein_d=my_d
        )

        opp_a, opp_b, opp_c, opp_d = [int(i) for i in input().split()]
        opponent_state = ContestantState(
            protein_a=opp_a, protein_b=opp_b, protein_c=opp_c, protein_d=opp_d
        )

        required_actions_count = int(input())

        return GameInputTurn(
            entities=entities,
            state=GameState(player=player_state, opponent=opponent_state),
            actions=required_actions_count,
        )

    @staticmethod
    def print_game_outputs(outputs: list[GameOutput]) -> None:
        for output in outputs:
            output_str = " ".join(
                [output.command.value, *list(map(str, output.params))]
            )
            print(output_str)


""" Types"""


class GameOutput(NamedTuple):
    command: GameCommand
    params: list[str]


class GameCommand(Enum):
    GROW = "GROW"
    WAIT = "WAIT"


class GameInputInit(NamedTuple):
    width: int
    height: int


class GameInputTurn(NamedTuple):
    entities: list[Entity]
    state: GameState
    actions: int


class GameState(NamedTuple):
    player: ContestantState
    opponent: ContestantState


class ContestantState(NamedTuple):
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
    parent_uid: int | None
    parent: Entity | None
    root_uid: int | None
    root: Entity | None


class EntityKind(Enum):
    ROOT = "ROOT"
    WALL = "WALL"
    BASIC = "BASIC"
    HARVESTER = "HARVESTER"
    PROTEIN_A = "A"
    PROTEIN_B = "B"
    PROTEIN_C = "C"
    PROTEIN_D = "D"

    @classmethod
    @property
    def ORGANISMS(cls) -> list[EntityKind]:  # type: ignore
        return [cls.ROOT, cls.BASIC, cls.HARVESTER]

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


def debug(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stderr, flush=True)


def taxi_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(y2 - y1) + abs(x2 - x1)


def neighborhood(
    x: int, y: int, width: int, height: int
) -> list[tuple[tuple[int, int], Direction]]:
    neighbors: list[tuple[tuple[int, int], Direction]] = [
        ((x, y - 1), Direction.NORTH),
        ((x, y + 1), Direction.SOUTH),
        ((x + 1, y), Direction.EAST),
        ((x - 1, y), Direction.WEST),
    ]
    return list(
        filter(lambda n: 0 <= n[0][0] < width and 0 <= n[0][1] < height, neighbors)
    )


""" Game loop """

game = Game.initialize()
while True:
    game.do_game_update()
