from datetime import datetime
from blacksheep.messages import Request, Response
from blacksheep.server import Application
from blacksheep.server.bindings import FromJSON
from uuid import uuid4
import json
from blockchain import Blockchain
import bc_dataclass 

app = Application()
get = app.router.get
post = app.router.post


node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@get('/mine')
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = json({
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    })
    return response, 200
  

@post('/transactions/new')
def new_transaction(input: FromJSON[bc_dataclass.Transaction]):
    values = input.value

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values.keys() for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = json({'message': f'Transaction will be added to Block {index}'})
    return response, 201


@get('/chain')
def full_chain():
    response = json({
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    })
    return response, 200


@post('/nodes/register')
def register_nodes(request: FromJSON[bc_dataclass.nodes]):
    values = request.value

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = json({
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    })
    return response, 201


@get('/nodes/resolve')
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = json({
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        })
    else:
        response = json({
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        })

    return response, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

