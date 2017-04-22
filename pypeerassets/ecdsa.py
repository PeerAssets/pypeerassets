from hashlib import sha256
from random import randrange
from binascii import hexlify, unhexlify

class ECDSA:
    def __init__(self,k):
        
        self.p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
        self.n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
        self.Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
        self.Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
        self.k = k
        self.g = (self.Gx,self.Gy)
        
    def point_neg(self,point):
    
        if point is None:
            return None
    
        x, y = point
        result = (x, -y % self.p)
    
        return result
    
    def point_add(self,point1, point2):
    
    
        if point1 is None:
            return point2
        
        if point2 is None:
            return point1
    
        x1, y1 = point1
        x2, y2 = point2
    
        if x1 == x2 and y1 != y2:
            return None
    
        if x1 == x2:
            m = (3 * x1 * x1) * self.modinv(2 * y1, self.p)
            
        else:
            m = (y1 - y2) * self.modinv(x1 - x2, self.p)
    
        x3 = m * m - x1 - x2
        y3 = y1 + m * (x3 - x1)
        result = (x3 % self.p, -y3 % self.p)
        
        return result
        
    def modinv(self, k, p):

        assert k != 0
        
        if k < 0:
            return p - self.modinv(-k, self.p)
        
        euclid = {"x":0,"_x":1,"y":1,"_y":0,"z":p,"_z":k}
    
        while euclid["z"] != 0:
            val = euclid["_z"] // euclid["z"]
            euclid["_z"], euclid["z"] = euclid["z"], euclid["_z"] - val * euclid["z"]
            euclid["_x"], euclid["x"] = euclid["x"], euclid["_x"] - val * euclid["x"]
            euclid["_y"], euclid["y"] = euclid["y"], euclid["_y"] - val * euclid["y"]
    
        assert euclid["_z"] == 1
        
        return euclid["_x"] % p
    
    def scalar_mult(self,k, point):

        if k % self.n == 0 or point is None:
            return None
    
        if k < 0:
            return self.scalar_mult(-k, point_neg(point))
    
        result = None
        dub = point
    
        while k:
            if k & 1:
                # Add.
                result = self.point_add(result, dub)
    
            # Double.
            dub = self.point_add(dub, dub)
    
            k >>= 1
            
        return result

    def hash_message(self, message):

        message_hash = sha256(sha256(message).digest()).digest()
        e = int.from_bytes(message_hash, 'big')
        if e.bit_length() > self.n.bit_length():
            z = e >> (e.bit_length() - self.n.bit_length())
        else:
            z = e << (self.n.bit_length() - e.bit_length())
            
        assert z.bit_length() <= self.n.bit_length()
    
        return z
    
    def sign_message(self, message):
        ''' takes message input as string '''
        z = self.hash_message(message.encode())
    
        r = 0
        s = 0
    
        while not r or not s:
            
            K = randrange(1, self.n)
            x, y = self.scalar_mult(K, self.g)
    
            r = x % self.n
            s = ((z + r * self.k) * self.modinv( K, self.n)) % self.n
    
        return (r, s)
    
    def verify_signature(self, message, signature, pubkey = None):
        ''' takes message input as string and signature input as tuple ( r, s ) '''
        
        z = self.hash_message(message.encode())
        
        if pubkey is None:
            pubkey = self.pubkey(compressed=False)
        
        r, s = signature
    
        w = self.modinv(s, self.n)
        u1 = (z * w) % self.n
        u2 = (r * w) % self.n
    
        x, y = self.point_add(self.scalar_mult(u1, self.g),
                         self.scalar_mult(u2, pubkey))
    
        if (r % self.n) == (x % self.n):
            return True
        else:
            return False
    
    def pubkey(self, compressed=True):
        
        x, y = self.scalar_mult(self.k, self.g)
        
        if not compressed:
            return (x, y)
        
        if y % 2 == 0:
            prefix = b'02'
        else:
            prefix = b'03'
            
        return prefix + hex( x )[2:].encode()
