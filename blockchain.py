import hashlib
import json
from time import time
import asyncio
from urllib.parse import urlparse
import aiohttp
import requests
import socket
import logging
from collections import OrderedDict as odict

Logger = logging.getLogger(__name__)

class Blockchain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        self.nodes = set()
        self.tasks_validchain_nodes = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)


    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = odict([
            ('index', len(self.chain) + 1),
            ('timestamp', time()),
            ('transactions', self.current_transactions),
            ('proof', proof),
            ('previous_hash', previous_hash or self.hash(self.chain[-1]))
        ])

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block


    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        tx = odict([
                ('sender', sender),
                ('recipient', recipient),
                ('amount', amount)
            ])
        self.current_transactions.append(tx)

        return self.last_block['index'] + 1


    @property
    def last_block(self):
        return self.chain[-1]


    @staticmethod
    def get_host():
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception as ex:
            Logger.error({'action':'get_host', 'error': ex})
            return '127.0.0.1'


    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
         - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
         - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return: <int>
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof


    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    async def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        last_block = chain[0]
        idx = 1
        while idx < len(chain):
            block = chain[idx]
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            idx += 1

        return True



    async def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.
        :return: <bool> True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        print(neighbours)
        new_chain = None
        response = None

        # We're only looking for chains longer than ours
        length_mychain = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            url = 'http://{}/chain'.format(node)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if not resp.status == 200:
                        return False
                    response = await resp.json()
                    print(response)
                    length = response[0]['length']
                    chain = response[0]['chain']
                    # Check if the length is longer and the chain is valid
                    if length > length_mychain and await self.valid_chain(chain):
                        length_mychain = length
                        new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False