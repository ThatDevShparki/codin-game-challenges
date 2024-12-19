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
        debug(self.state)

        return []

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
                    # direction=Direction(_organ_dir),
                    direction=_organ_dir,
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
    # direction: Direction
    direction: str
    parent_uid: int | None
    parent: Entity | None
    root_uid: int | None
    root: Entity | None


class EntityKind(Enum):
    ROOT = "ROOT"
    WALL = "WALL"
    BASIC = "BASIC"
    PROTEIN_A = "A"
    PROTEIN_B = "B"
    PROTEIN_C = "C"
    PROTEIN_D = "D"


class Contestant(Enum):
    PLAYER = "1"
    OPPONENT = "0"


class Direction(Enum):
    NORTH = "N"
    SOUTH = "W"
    EAST = "E"
    WEST = "S"


""" Common utility methods """


def Grow(uid: int, x: int, y: int, kind: EntityKind) -> GameOutput:
    return GameOutput(command=GameCommand.GROW, params=[str(x), str(y), kind.value])


def Wait() -> GameOutput:
    return GameOutput(command=GameCommand.WAIT, params=[])


def debug(*args: Any, **kwargs: Any) -> None:
    print(*args, **kwargs, file=sys.stderr, flush=True)


""" Game loop """

game = Game.initialize()
while True:
    game.do_game_update()
