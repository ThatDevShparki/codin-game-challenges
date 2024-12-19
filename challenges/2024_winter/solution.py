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

        # Construct organism
        debug("organism")
        organism: list[Entity] = []
        for entity in entities:
            if entity.kind in EntityKind.ORGANISM and entity.owner == Contestant.PLAYER:
                organism.append(entity)
                debug(entity)

        # Locate all proteins and get the closest distance
        debug("proteins")
        proteins: list[
            tuple[Entity, Entity, int]
        ] = []  # protein, closest organ, distance
        for entity in entities:
            if entity.kind != EntityKind.PROTEIN_A or entity.owner:
                continue

            closest_organ: Entity | None = None
            closest_distance: int | None = None
            for organ in organism:
                o_distance = taxi_distance(organ.x, organ.y, entity.x, entity.y)
                if closest_distance is None or o_distance < closest_distance:
                    closest_distance = o_distance
                    closest_organ = organ

            debug(entity, closest_organ, closest_distance)

            # We know *something* is closest because we have atleast one organ
            assert closest_organ is not None
            assert closest_distance is not None

            proteins.append((entity, closest_organ, closest_distance))

        proteins = sorted(proteins, key=lambda p: p[-1])  # Sort by distance
        if not proteins:
            debug("NO PROTEIN AVAILABLE :(")
            return []

        next_protein, closest_organ, closest_distance = proteins.pop(0)
        if closest_distance > self.state.player.protein_a:
            debug("NO PROTEIN AVAILABLE :(")
            return []

        return [Grow(EntityKind.BASIC, next_protein.x, next_protein.y, closest_organ)]

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
    def ORGANISM(cls) -> list[EntityKind]:
        return [cls.ROOT, cls.BASIC]


class Contestant(Enum):
    PLAYER = "1"
    OPPONENT = "0"


class Direction(Enum):
    NONE = "X"
    NORTH = "N"
    SOUTH = "W"
    EAST = "E"
    WEST = "S"


""" Common utility methods """


def Grow(kind: EntityKind, x: int, y: int, parent: Entity) -> GameOutput:
    return GameOutput(
        command=GameCommand.GROW,
        params=[str(parent.uid), str(x), str(y), kind.value],
    )


def Wait() -> GameOutput:
    return GameOutput(command=GameCommand.WAIT, params=[])


def debug(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stderr, flush=True)


def taxi_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(y2 - y1) + abs(x2 - x1)


""" Game loop """

game = Game.initialize()
while True:
    game.do_game_update()
