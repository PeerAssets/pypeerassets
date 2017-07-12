from hashlib import sha256
from random import SystemRandom, randrange


class PrivateKey:

    def __init__(self, privkey = None):

        self.p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
        self.n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
        Gx = 0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798
        Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
        self.g = (Gx, Gy)

        if privkey is None:
            self.privkey = SystemRandom().randrange(1,self.n)
            self.private_key = '{:0>64x}'.format(self.privkey).encode()

        else:
            if not isinstance(privkey,str):
                privkey = privkey.decode()
            self.privkey = int(privkey,16)
        
        self.public_key = self.pubkey()

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
        if isinstance(message, str):
            message = message.encode()

        z = self.hash_message(message)
    
        r = 0
        s = 0
    
        while not r or not s:
            
            privkey = randrange(1, self.n)
            x, y = scalar_mult(privkey, self.g, self.p, self.n)
    
            r = x % self.n
            s = ((z + r * self.privkey) * inverse_mod( privkey, self.n)) % self.n
    
        return (r, s)
    
    def verify_signature(self, message, signature, pubkey = None):
        ''' takes message input as string and signature input as tuple ( r, s ) '''
        
        z = self.hash_message(message.encode())
        
        if pubkey is None:
            pubkey = self.pubkey(compressed=False)
        
        r, s = signature
    
        w = inverse_mod(s, self.n)
        u1 = (z * w) % self.n
        u2 = (r * w) % self.n
    
        x, y = point_add(scalar_mult(u1, self.g,self.p, self.n),
                         scalar_mult(u2, pubkey, self.p, self.n), self.p)
    
        if (r % self.n) == (x % self.n):
            return True
        else:
            return False
    
    def pubkey(self, compressed=True):
        
        x, y = scalar_mult(self.privkey, self.g, self.p, self.n)
        
        if not compressed:
            return (x, y)

        x = '{:0>64x}'.format(x).encode()

        if not (y % 2):
            prefix = b'02'
        else:
            prefix = b'03'
            
        return prefix + x 

    def make_keypair(self):
        """Generates a random private-public key pair."""
        self.privkey = SystemRandom().randrange(1,self.n)

        self.public_key = self.pubkey()
        self.g = self.pubkey(compressed=False)
        self.private_key = '{:0>64x}'.format(self.privkey).encode()

        return {"private_key":self.private_key,"public_key": self.public_key}


def is_on_curve(point, p):

    if point is None:
        return True

    x, y = point

    return (y * y - x * x * x - 7) % p == 0

def point_neg(point, p):

    if point is None:
        return None

    x, y = point
    result = (x, -y % p)

    return result

def point_add(point1, point2, p):


    if point1 is None:
        return point2
    
    if point2 is None:
        return point1

    x1, y1 = point1
    x2, y2 = point2

    if x1 == x2 and y1 != y2:
        return None

    if x1 == x2:
        m = (3 * x1 * x1) * inverse_mod(2 * y1, p)
        
    else:
        m = (y1 - y2) * inverse_mod(x1 - x2, p)

    x3 = m * m - x1 - x2
    y3 = y1 + m * (x3 - x1)
    result = (x3 % p, -y3 % p)
    
    return result
    
def inverse_mod( privkey, p):

    if privkey == 0:
        raise ZeroDivisionError('division by zero')

    if privkey < 0:
        return p - inverse_mod(-privkey, p)

    s, old_s = 0, 1
    t, old_t = 1, 0
    r, old_r = p, privkey

    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    gcd, x, y = old_r, old_s, old_t

    assert gcd == 1
    assert (privkey * x) % p == 1

    return x % p

def scalar_mult(privkey, point, p, n):


    assert is_on_curve(point, p)

    if privkey % n == 0 or point is None:
        return None

    if privkey < 0:

        return scalar_mult(-privkey, point_neg(point, p), p, n)

    result = None
    addend = point

    while privkey:
        if privkey & 1:
            result = point_add(result, addend, p)

        addend = point_add(addend, addend, p)

        privkey >>= 1

    assert is_on_curve(result, p)

    return result
