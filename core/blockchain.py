import hashlib
import json
import datetime

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

        # สร้าง genesis block
        self.create_genesis_block()
    
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

            # ตรวจสอบความถูกต้องของ hash
            # โดย previous hash ของ block ปัจจุบัน ต้องเท่ากับ current hash ของ block ก่อนหน้า
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
