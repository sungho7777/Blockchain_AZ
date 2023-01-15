# Module 2 - Create a Cryptocurrency

# To be installed:
#   Flask == 0.12.2: pip3 install Flask==0.12.2
#   Postman HTTP client: https://www.getpostman.com/
#   requests == 2.18.4: pip3 install requests==2.18.4

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# -------------------------------------------------------
#
# Part 1 - Building a Blockchain (블록체인 구축)
#
# -------------------------------------------------------

class Blockchain:
    '''
    
        init
            chain, transaction, block, nodes 초기화한다.
            시스템 재부팅 시 모든 데이터는 초기화 된다.
            
            
    '''
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
    
    '''
    
        create block
            index: chain 순서(index)
            timestamp: block 생성 시간
            proof: 조건에 맞는 hash 값을 찾았을때까지의 반복한 횟수
            previous_hash: 이전 block 의 hash 값
            transactions: 업무, block에 넣고 싶은 값 등.
        
        block
            block 을 만든 후 transactions 을 초기화 한다.
            생성된 block을 chain에 연결 한다.(append)
            
    '''
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block
    
    '''
    
        get previous block
            이전의 block chain 의 정보를 return 해준다.
            mind block 또는 add transaction 시 사용한다.
    
    '''
    def get_previous_block(self):
        return self.chain[-1]

    '''
    
        proof of work
            sha256 이용하여 조건에 맞는 hash 값이 맞을때까지 시도하며, 시도한 횟수(proof)을 return 해준다.
            
        hash operation
            찾는 값의 자리수를 늘리거나, 조건을 어렵게 할 수도록 오래 걸린다.
            proof 의 return 값을 높은 수가 나온다.
        
        previous proof
            새로운 proof 값은 이전 chain 의 proof 값 이후부터 찾는다.
    
    '''
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    '''
    
        hash
            해당 chain의 hash 값을 단순 return 해준다.
            chain validation chack 시에 사용한다.
    
    '''
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    '''
        
        is chain valid
            해당 chain 의 정보가 true 인지 체크한다.
            방법은 proof 값 생성시 조건과 동일하게 한다.
        
    '''
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    '''
    
        add transaction
            block 에 넣고(저장) 싶은 데이터를 새로운 block에 add 한다.
            
    
    '''
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    '''
    
        add node
            현 시스템에 접속 된 node의 정보를 nodes 에 add 한다.
            본 경우 5001, 5002, 5003 을 예를 들어 테스트 진행한다.
    
    '''
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    '''
    
        replace chain
            모든 node 들이 가지고 있는 chain 의 정보를 찾아 그중 제일 긴 chain 수를 찾는다.
            동시에 그 chain 이 옳바른 chain 이면 그 chain 으로 갈아탄다.
            성공시 true
            실패시 false
    
    '''
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# -------------------------------------------------------
#
# Part 2 - Mining our Blockchain (블록체인 채굴)
# : Flask
#   https://flask.palletsprojects.com/en/2.2.x/quickstart/
# -------------------------------------------------------

# Creating a Web App
app = Flask(__name__)
#app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Creating an address for the node on Port 5000
node_address = str(uuid4()).replace('-', '')

# Creating a Blockchain
blockchain =  Blockchain()

# Mining a new block
'''

    mine block
        previous block: 해당 block chain 의 이전 block 정보를 가져온다.
        previoud proof: 이전 chain 의 proof 값을 가져온다.
        proof: 생성될 block 의 proof 값을 가져온다.(이전 proof 값 보다 크다.)
        previous hash: 이전 chain 의 hash 값을 가져온다.
        add transaction: block 에 넣을 정보를 add 한다.
        block: 새로운 block 을 만든다. (proof, 이전 hash 값)
        
'''
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'AAAAA', amount = 1)
    block = blockchain.create_block(proof, previous_hash)

    response = {'message':'Congratulation, you just mined a block',
                'messageKr': '축하합니다. 방금 블록을 채굴했습니다.',
               'index': block['index'],
               'timestamp': block['timestamp'],
               'proof': block['proof'],
               'previous_hash': block['previous_hash'],
               'transactions': block['transactions']
               }
    
    return jsonify(response), 200

# Getting the full Blockchain
'''
    
    get chain
        현재 정상적인 chain 정보를 가져온다.
    
'''
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
'''

    is valid
        현재 chain이 정상적인지 체크한다.
        
'''
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.',
                    'messageKr': '문제없습니다. 이 블록은 유효합니다.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.',
                    'messageKr': '문제가 생겼습니다. 이 블록에는 문제가 있습니다.'}
    return jsonify(response), 200

# Adding a new transaction to Blockchain
'''

    add transaction
        json
        {
            "sender": "",
            "receiver": "",
            "amount": 1000
        }
        위 형태의 json 파일을 불러온다.

    index
        현재 blockchain 에 transaction 값을 add 한다. (반복 가능.)
    
'''
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all (key in json for key in transaction_keys):
        return '트랜잭션의 일부 요소가 누락되었습니다.', 400
        #return 'Some elements of the transaction are missing', 400
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction will added to Block {index}',
                'messageKr': f'이 트랜잭션은 Block에 추가됩니다. {index}'}
    return jsonify(response), 201

# -------------------------------------------------------
#
# Part 3 - Decentralizing our Blockchain (블록체인 탈중앙화)
#
# -------------------------------------------------------

# Connection new nodes
'''
    connect node
        json
        {
            "nodes": ["http://127.0.0.1:5001",
                      "http://127.0.0.1:5002",
                      "http://127.0.0.1:5003"]
        }
        5001, 5002, 5003 노드들을 연결한다.
    
'''
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {
        'message': 'All the nodes are now connected. The MacCoin Blockchain now contains the following nodes:',
        'messageKr': '이제 모든 노드가 연결되었습니다. MacCoin 블록체인에는 이제 다음 노드가 포함됩니다.',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
'''
    replace chain
        is_chain_replaced
            모든 node 들이 가지고 있는 chain 의 정보를 찾아 그중 제일 긴 chain 수를 찾는다.
            동시에 그 chain 이 옳바른 chain 이면 그 chain 으로 갈아탄다.
            성공시 true
            실패시 false
        
'''
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'messageKr': '노드에는 서로 다른 체인이 있으므로 체인이 가장 긴 체인으로 교체되었습니다.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'messageKr': '문제 없습니다. 지금 체인이 가장 깁니다.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5000)































# end