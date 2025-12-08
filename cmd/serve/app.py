from flask import Flask, request, jsonify
import datetime
from core.blockchain import Block, Blockchain, Mining

# สร้าง Web App
app = Flask(__name__)

blockchain = Blockchain()

@app.route('/add_data', methods=['POST'])
def add_data():
    # รับข้อมูล JSON จาก request
    json_data = request.get_json()
    if json_data is None:
        return "Missing JSON data", 400
    
    index = blockchain.add_data(json_data)

    response = {"message": f"This data will be added to Block {index}"}
    return jsonify(response), 201


@app.route('/mine_block', methods=['GET'])
def mine_block():
    # เอาข้อมูลทั้งหมดที่รออยู่ (pending_data) มาเป็น body ของบล็อกใหม่
    body_data = list(blockchain.pending_data)

    # สร้าง block
    new_block = blockchain.create_block(body_data)
    # ล้างข้อมูล pending_data หลังจากบันทึกลงบล็อกแล้ว
    blockchain.pending_data = []

    response = {
        "message": "New Block Mined",
        "index": new_block.index,
        "body": new_block.body,
        "timestamp": new_block.timestamp,
    }
    
    return jsonify(response), 200
    

@app.route('/get_chain', methods=['GET'])
def get_chain():
    chain_data = []
    # วนลูปเเปลง object เป็น dictionary เพื่อส่งกลับเป็น JSON
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "body": block.body,
            "previous_hash": block.previous_hash,
            "current_hash": block.current_hash,
            "nonce": block.nonce
        })
    
    response = {
        "chain": chain_data,
        "length": len(chain_data)
    }
    return jsonify(response), 200


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, Blockchain!"

# Run Server
if __name__ == '__main__':
    app.run()
