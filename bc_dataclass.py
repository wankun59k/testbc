from dataclasses import dataclass, field
from typing import List

@dataclass
class Transaction:
    sender: int
    recipient: str
    amount: int
    def __init__(self, sender:int, recipient:str, amount:int) -> None:
        self.sender = sender
        self.recipient = recipient
        self.amount = amount


@dataclass
class node:
    node: str
    def __init__(self, node:str) -> None:
        self.node = node


@dataclass
class nodes:
    nodes: List[node] = field(default_factory=list)
  