from datetime import datetime
from blacksheep.server import Application
from blacksheep.server.bindings import FromJSON, FromForm
from blacksheep.server.templating import use_templates
from jinja2 import PackageLoader
from uuid import uuid4
from blockchain import Blockchain
import bc_dataclass 


app = Application(show_error_details=True, debug=True)
get = app.router.get
post = app.router.post


node_identifier = str(uuid4()).replace('-', '')

view = use_templates(app, loader=PackageLoader("app", "templates"), enable_async=False)


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
    nblock = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': nblock['index'],
        'transactions': [ {
            'sender':tx['sender'],
            'recipient':tx['recipient'],
            'amount':tx['amount']
            } for tx in nblock['transactions']],
        'proof': nblock['proof'],
        'previous_hash': nblock['previous_hash'],
    }
    #return response, 200
    return view("mine", response)


@get('/transaction')
def get_transaction():
    response_message = 'No transactions added.'

    response = {
        'message': response_message,
        'transactions': blockchain.current_transactions,
        'length': len(blockchain.current_transactions),
    }
    #return response, 201
    return view("transaction", response)


@post('/transaction')
def new_transaction(input: FromForm[bc_dataclass.Transaction]):
    values = input.value
    response_message = ''

    # Check that the required fields are in the POST'ed data and Create a new Transaction
    #required = ['sender', 'recipient', 'amount']
    required = ['recipient', 'amount']
    if all(k in dir(values) for k in required):
        index = blockchain.new_transaction(
            #values.sender, 
            node_identifier,
            values.recipient, 
            values.amount)
        response_message = 'Transaction will be added to Block {}.'.format(index)
    else:
        response_message = 'No transactions added.'

    response = {
        'message': response_message,
        'transactions': blockchain.current_transactions,
        'length': len(blockchain.current_transactions),
    }
    #return response, 201
    return view("transaction", response)


@get('/chain')
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return response, 200


@get('/nodes/register')
def register_nodes():
    response = {
        'message': 'Please supply a valid list of nodes',
        'total_nodes': list(blockchain.nodes),
    }
    #return response, 201
    return view("register", response)


@post('/nodes/register')
def register_nodes(input: FromForm[bc_dataclass.node]):
    """
    add new endorsers
    """
    print(input.value.node)
    values = input.value
    if values is None:
        return "Error: Please supply a valid list of nodes", 400

    # for node in nodes:
    #     blockchain.register_node(node)
    blockchain.register_node(values.node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    #return response, 201
    return view("register", response)


@get('/nodes/resolve')
async def consensus():
    replaced = await blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    #return response, 200
    return  view("resolve", {'message':response['message'], 'chains':blockchain.chain})


@get("/")
def home():
    return view("mine","")

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)