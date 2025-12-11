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
    
class Blockchain:
    def __init__(self):
        # เก็บกลุ่มของ Blockchain
        # list ที่เก็บ Blockchain
        self.chain = []
        self.pending_data = []

        # สร้าง node อื่น ๆ ในเครือข่ายลงใน set
        self.nodes = set()

        self.network = NodeManager()

        # สร้าง genesis block
        self.create_genesis_block()

    def resolve_conflicts(self):
        # ดึงรายชื่อ node ทั้งหมดในเครือข่าย
        neighbours = self.network.nodes
        print(f"Neighbours: {neighbours}")
        new_chain = None

        # ความยาวของ chain ที่เรามีอยู่
        max_length = len(self.chain)

        # วนลูปตรวจสอบ chain ของ node อื่น ๆ
        for node in neighbours:
            try:
                # ยิง request ไปยัง node อื่นเพื่อดึง chain ของเขามาเปรียบเทียบ
                response = requests.get(f"{node}/get_chain")
            except:
                print(f"Could not connect to node {node}")
                continue


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
        return new_block
    
    def is_chain_valid(self):
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
        self.nodes.add(address)
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