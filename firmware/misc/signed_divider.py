import math

def make_divider(d, bits):
    p = math.ceil(math.log2(abs(d)))
    m = math.ceil((1 << (bits + p)) / d) & ((1 << bits) - 1)
    def corr(n):
        return n + (1 if n < 0 else 0)
    def divider(n):
        q = m*n >> bits
        t = corr(((n-q) >> 1) + q) >> (p-1)
        return t
    return divider

for d in range(2, 32768):
    divider = make_divider(d, 16)
    for n in range(-32768, 32768):
        if int(n/d) != divider(n):
            print(f"{n}/{d}: expected {int(n/d)}, got {divider(n)}")
            exit(-1)