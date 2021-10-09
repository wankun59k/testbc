from dataclasses import dataclass
from typing import List

@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: int

@dataclass
class node:
    node: str


@dataclass
class nodes:
    nodes: List[node]