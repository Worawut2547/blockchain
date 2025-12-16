import hashlib
import json
import datetime
import os
from urllib.parse import urlparse

import requests

class Block:
    def __init__(self, index, timestamp, body, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.body = body
        self.previous_hash = previous_hash
        self.nonce = nonce
        # คำนวณ hash ทันทีที่สร้าง block
        self.current_hash = self.hash()
    
    # เข้ารหัส block
    def hash(self):
        # สร้าง Dictionary เพื่อเก็บข้อมูลของ block
        block_data = {
            'index': self.index,
            'timestamp': str(self.timestamp),
            'body': self.body,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce    
        }
        # เเปลง python object -> json object
        encode_block = json.dumps(block_data, sort_keys=True).encode()

        # เข้ารหัสด้วย sha256
        return hashlib.sha256(encode_block).hexdigest()
    
    # แปลง Block เป็น dictionary
    def to_dict(self):
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'body': self.body,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'current_hash': self.current_hash
        }
    
class Blockchain:
    def __init__(self):
        # เก็บกลุ่มของ Blockchain
        # list ที่เก็บ Blockchain
        self.chain = []
        self.pending_data = []

        # เก็บการ hack ที่รอ mining
        self.pending_hack = None

        # สร้าง node อื่น ๆ ในเครือข่ายลงใน set
        self.nodes = set()

        self.network = NodeManager()

        # สร้าง genesis block
        self.create_genesis_block()

    def execute_pending_hack(self):
        if not self.pending_hack:
            return None
        target_index = self.pending_hack['target_index']
        fake_data = self.pending_hack['fake_data']

        # เข้าถึง block เป้าหมาย
        target_block = self.chain[target_index]
        previous_block = self.chain[target_index - 1]

        # แก้ไขข้อมูลในบล็อก
        original_body = target_block.body
        print(f"Original body: {original_body}")
        target_block.body = fake_data # ใส่ข้อมูลปลอม
        print(f"Fake body: {target_block.body}")

        # Re-mine (ชุดใหม่เพื่อให้ hash ถูกต้อง)
        print(f"Re-mining Block {target_index}...")
        new_nonce = Mining.proof_of_work(previous_block.nonce)

        # อัพเดท nonce และ hash ใหม่
        target_block.nonce = new_nonce
        target_block.current_hash = target_block.hash()

        # ล้าง pending_hack หลังจากทำเสร็จ
        self.pending_hack = None

        return {
            "index": target_index,
            "original_body": original_body,
            "new_body": target_block.body,
            "new_nonce": new_nonce,
            "new_hash": target_block.current_hash
        }

    def resolve_conflicts(self, current_node=None):
        print("-----------------------------------------------------")
        print("Resolving conflicts...")
        print(f"Current node: {current_node}")
        # อ่านไฟล์ล่าสุดก่อน
        self.network.load_nodes_from_file()
        # ดึงรายชื่อ node ทั้งหมดในเครือข่าย
        neighbours = self.network.nodes
        print(f"Neighbours: {neighbours}")
        new_chain = None

        # ความยาวของ chain ที่เรามีอยู่
        max_length = len(self.chain)

        # เช็คความถูกต้องของ node ตัวเอง
        am_i_corrupted = not self.is_chain_valid()
        print(f"Am I corrupted? {am_i_corrupted}")

        # วนลูปตรวจสอบ chain ของ node อื่น ๆ
        for node in neighbours:
            # ข้าม node ตัวเอง
            if current_node is not None and node in current_node:
                print(f"Skipping current node: {node}")
                continue
            try:
                # ยิง request ไปยัง node อื่นเพื่อดึง chain ของเขามาเปรียบเทียบ
                response = requests.get(f"{node}/raw_chain")

                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']

                    is_longer = length > max_length
                    is_healing = am_i_corrupted and length == len(self.chain)

                    if (is_longer or is_healing) and self.is_chain_valid_json_chain(chain):
                        max_length = length
                        new_chain = chain

            except:
                print(f"Could not connect to node {node}")
                continue

            if new_chain:
                self.chain = self.convert_json_to_chain(new_chain)
                self.pending_data = []
                print("Blockchain was replaced by the longest valid chain from the network.")
                return True
        return False

    def convert_json_to_chain(self, chain):
        object_chain = []
        for block_data in chain:
            block = Block(
                block_data['index'],
                block_data['timestamp'],
                block_data['body'],
                block_data['previous_hash'],
                block_data['nonce']
            )
            block.current_hash = block_data['current_hash']
            object_chain.append(block)
        return object_chain

    def is_chain_valid_json_chain(self, chain):
        # เช็คความถูกต้องของ chain ที่รับมา
        # แปลง json chain เป็น object ของ Block
        temp_chain = self.convert_json_to_chain(chain)
        return self.check_chain_validity(temp_chain)
    
    def check_chain_validity(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]

            # ตรวจสอบ hash ของ block ปัจจุบันว่าตรงกับ hash ที่ควรเป็นไหม
            if block.current_hash != block.hash():
                return False
            
            # ตรวจสอบ previous_hash ว่าตรงกับ hash ของบล็อกก่อนหน้าหรือไม่
            if block.previous_hash != previous_block.current_hash:
                return False

            # ตรวจสอบ proof of work (เเก้สมการถูกไหม)
            previous_nonce = previous_block.nonce
            nonce = block.nonce

            equation_nonce = str((nonce**2) - (previous_nonce**2))
            hash_operation = hashlib.sha256(equation_nonce.encode()).hexdigest()

            if hash_operation[:4] != '0000':
                return False
            
            # ขยับไปคู่ถัดไป
            previous_block = block
            block_index += 1
        return True

    def create_genesis_block(self):
        # สร้าง genesis block โดยกำหนดค่า index = 0, previous_hash = '0'
        genesis_block = Block(0, str(datetime.datetime.now()), 'Genesis Block', '0')
        # เพิ่ม genesis block ลงใน chain
        self.chain.append(genesis_block)
    
    @property
    # ดึง block ล่าสุด
    def get_previous_block(self):
        return self.chain[-1]

    def create_block(self, body):
        # ดึง block ล่าสุดขึ้นมาเอาค่า hash , index
        previous_block = self.get_previous_block
        previous_nonce = previous_block.nonce

        # เริ่มกระบวนการขุด (Mining) เพื่อหา nonce ใหม่
        print("Mining new block...")
        print("-----------------------------------------------------")
        nonce = Mining.proof_of_work(previous_nonce)
        print(f"New nonce found: {nonce}")

        # เตรียมค่า index, timestamp ให้ block ใหม่
        new_index = previous_block.index + 1
        new_timestamp = str(datetime.datetime.now())
        # ดึงค่า hash ของ block ล่าสุด
        previous_hash = previous_block.current_hash

        # สร้าง object จาก class Block
        new_block = Block(new_index, new_timestamp, body, previous_hash, nonce)

        # เพิ่ม block ใหม่ลงใน chain
        self.chain.append(new_block)
        print(f"Block {new_index} has been added to the blockchain.")
        return new_block
    
    def is_chain_valid(self):
        print("-----------------------------------------------------")
        print("Validating blockchain...")
        previous_block = self.chain[0]
        block_index = 1

        while block_index < len(self.chain):
            block = self.chain[block_index]

            # ตรวจสอบ hash ของ block ปัจจุบันว่าตรงกับ hash ที่ควรเป็นไหม
            if block.current_hash != block.hash():
                print(f"Block {block_index} has invalid hash.")
                print(f"Calculated hash: {block.hash()}")
                print(f"Stored hash: {block.current_hash}")
                return False
            
            # ตรวจสอบ previous_hash ว่าตรงกับ hash ของบล็อกก่อนหน้าหรือไม่
            if block.previous_hash != previous_block.current_hash:
                print(f"Block {block_index} has invalid previous hash.")
                print(f"Value previous hash in block: {block.previous_hash}")
                print(f"Value current hash in previous block: {previous_block.current_hash}")
                print(f"Origin body: {block.body} edited to\n {previous_block.body}")
                return False

            # ตรวจสอบ proof of work (เเก้สมการถูกไหม)
            previous_nonce = previous_block.nonce
            nonce = block.nonce

            equation_nonce = str((nonce**2) - (previous_nonce**2))
            hash_operation = hashlib.sha256(equation_nonce.encode()).hexdigest()

            if hash_operation[:4] != '0000':
                print(f"Block {block_index} has invalid proof of work.")
                return False
            
            # ขยับไปคู่ถัดไป
            previous_block = block
            block_index += 1
        return True
    
    def add_data(self, data):
        self.pending_data.append(data)

        # คืนค่า index ของ block ถัดไปที่จะถูกบันทึก
        return self.get_previous_block.index + 1

class Mining:
    @staticmethod
    def proof_of_work(previous_nonce):
        # ต้องการหา nonce ที่ทำให้ hash มีค่าเริ่มต้นด้วย '0000'
        new_nonce = 1 # ค่า nonce เริ่มต้น
        check_proof = False

        # เเก้โจทย์หาค่า nonce 
        while check_proof is False:
            equation_nonce = str((new_nonce**2) - (previous_nonce**2))

            hash_operation = hashlib.sha256(equation_nonce.encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_nonce += 1
        return new_nonce

class NodeManager:
    def __init__(self):
        self.nodes = set()
        self.load_nodes_from_file()

    def register_node(self, address):
        # โหลดข้อมูลก่อนเพิ่ม node ใหม่
        self.load_nodes_from_file()

        # เพิ่ม node ใหม่ลงใน set
        self.nodes.add(address)

        # บันทึกข้อมูล node ลงไฟล์
        self.save_nodes_to_file()

    def save_nodes_to_file(self):
        try:
            with open('nodes.json', 'w') as file:
                json.dump(list(self.nodes), file)
        except Exception as e:
            print(f"Error saving nodes to file: {e}")
    
    def load_nodes_from_file(self):
        if os.path.exists('nodes.json'):
            try:
                with open('nodes.json', 'r') as file:
                    nodes_list = json.load(file)
                    self.nodes = set(nodes_list)
            except Exception as e:
                print(f"Error loading nodes from file: {e}")