from flask import Flask, request, jsonify
import argparse
import datetime
from core import Blockchain

# สร้าง Web App
app = Flask(__name__)

blockchain = Blockchain()
nodes =  blockchain.network

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
    # check & Self-healing
    replaced = blockchain.resolve_conflicts(current_node=request.host_url.rstrip('/'))

    if not blockchain.is_chain_valid():
        return jsonify({"message": "Blockchain is invalid. Cannot mine new block."}), 400
    
    # ตรวจสอบว่ามีการ hack รออยู่หรือไม่
    if blockchain.pending_hack:
        hack_result = blockchain.execute_pending_hack()

        return jsonify({
            "message": "Block hacked and mined successfully.",
            "detail": hack_result
        }), 200
    else:
         # เอาข้อมูลทั้งหมดที่รออยู่ (pending_data) มาเป็น body ของบล็อกใหม่
        body_data = list(blockchain.pending_data)
    
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
    # บอก blockchain ว่า คือ node ปัจจุบัน อย่าโทรมา
    current_node = request.host_url.rstrip('/')
    print(f"Current node: {current_node}")

    # สั่ง Sync ข้อมูล กับ node อื่น ๆ ในเครือข่าย
    replaced = blockchain.resolve_conflicts(current_node=current_node)

    # เตรียมข้อมูล
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
    if replaced:
        message = "The Blockchain was replaced by the longest valid chain from the network."
    else:
        message = "The Blockchain is up to date."
    response = {
        "message": message,
        "was_replaced": replaced,
        "chain": chain_data,
        "length": len(chain_data)
    }
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid()
    print(f"Blockchain valid: {is_valid}")
    if is_valid:
        response = {"message": "The Blockchain is valid."}
    else:
        # ถ้า valid = False (โดนโจมตี) 
        response = {"message": "The Blockchain got attacked!"}
        # เริ่มกระบวนการ consensus
        replaced = blockchain.resolve_conflicts()

        if replaced:
            # กู้คืนสำเร็จ
            print(f"Blockchain was edited. Replaced with the valid chain from network...")
            response = {
                "message": "The Blockchain has been restored through consensus.",
                "status": "replaced"
            }
        else:
            # กู้คืนไม่สำเร็จ
            print(f"Blockchain could not be restored. No valid chain found in network.")
            response = {
                "message": "The Blockchain could not be restored. No valid chain found in network.",
                "status": "Corrupted"
            }
            
    return jsonify(response), 200


@app.route('/hack_block/<index>', methods=['POST'])
def hack_block(index):
    json_data = request.get_json()
    if json_data is None:
        return "Missing JSON data", 400

    # รับข้อมูลว่าจะทำการแก้ไข block ไหน
    target_index = int(index)
    fake_data = json_data.get('body')

    # ตรวจสอบว่ามี block ดังกล่าวหรือไม่
    if target_index is None or target_index >= len(blockchain.chain):
        return "Invalid block index", 400
    # เก็บใน pending_hack ก่อน
    blockchain.pending_hack = {
        "target_index": target_index,
        "fake_data": fake_data
    }
    '''
    # เริ่มการ hack
    # เข้าถึง block เป้าหมาย
    target_block = blockchain.chain[target_index]

    # แก้ไขข้อมูลในบล็อก
    original_body = target_block.body
    print(f"Original body: {original_body}")
    
    target_block.body = fake_data # ใส่ข้อมูลปลอม
    print(f"Fake body: {target_block.body}")


    # คำนวณ hash ใหม่หลังจากแก้ไขข้อมูล
    target_block.current_hash = target_block.hash()
    '''
    response = {
        "message": f"HACKED edit Block {target_index} complete.",
        "next_step": "Please call /mine_block to execute the attack."
        #"original_body": original_body,
        #"new_data": target_block.body,
        #"new_hash": target_block.current_hash
    }
    return jsonify(response), 200


@app.route('/node/register', methods=['POST'])
def register_node():
    origin = request.host_url.rstrip('/')
    print(f"Origin: {origin}")

    nodes.register_node(origin)

    response = {
        "message": "New nodes have been added",
        "origin": origin,
        "total_nodes": list(nodes.nodes)
    }
    return jsonify(response), 201


# endpoint สำหรับให้ node อื่น ดึงข้อมูลไปตรวจสอบ
@app.route('/raw_chain', methods=['GET'])
def raw_chain():
    # ส่งข้อมูลกลับไป ไม่ต้อง sync
    chain_data = [block.to_dict() for block in blockchain.chain]

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
    parser = argparse.ArgumentParser()
    # ดึงค่าจาก command line argument --port หรือ -p :<port>
    parser.add_argument('-p', '--port', type=int, default=5000, help='Port to run the server on')
    args = parser.parse_args()
    port = args.port

    app.run(host='0.0.0.0', port=port)
