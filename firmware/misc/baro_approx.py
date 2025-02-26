#!/usr/bin/python3

import math

# https://en.wikipedia.org/wiki/Barometric_formula 
# Based on the standard atmosphere model:
# P = Pb * (1 - (Lmb/Tmb)*(h - hb))^((g0*M0) / (R*Lmb))
# Our barometer range of ~10km puts us firmly in reference level 0, so we can
# set k = ((g0*M0) / (R*Lmb)) to be constant and hb to be 0:
# P = Pb * (1 - Lmb*h/Tmb)^k

# Solving for h yields:
# h = Tmb/Lmb * (1 - (P/Pb)^(1/k))
# Or equivalently:
# h = Tmb/Lmb * (1 - exp((1/k) * ln(P/Pb)))

# So now we have three clear steps:
# 1. Compute ln(P/Pb)
# 2. Divide by k and compute exp((1/k) * ln(P/Pb))
# 3. Subtract from 1 and multiply by Tmb/Lmb

# === 1. Compute ln(P/Pb) ===
# We can operate under the assumption here that 0 < P <= Pb. (Death Valley
# residents need not apply.) Just to be safe, when we implement this we should
# clamp P to Pb.
# Notably, since ln(0) is bad news, we can't use a regular old Maclaurin series.
# However, there's a commonly used Maclaurin series for ln(1+x), so we can aim
# for that:
# ln(P/Pb) = ln(1 + P/Pb-1)
# = -sum(i :: 1..inf) (-1)^i (P/Pb - 1)^i / i
# Let's throw together a quick function for this.
def true_ln_term(P, Pb):
    return math.log(P/Pb)
def approx_ln_term(P, Pb, n):
    return -sum((-1)**i * (P/Pb-1)**i / i for i in range(1, n+1))
print("Correct value: ", true_ln_term(30000, 101325))
print("Approx: ", [approx_ln_term(30000, 101325, n) for n in range(10)])
# We'll call the result of this `l`.

# === 2. Compute exp((1/k) * l) ===
# Likewise, we can approximate exp(l/k) with a Taylor series. In this case, we
# just have exp(x) = sum(1 :: 0..inf) x^n / n!.
def true_exp_term(l, k):
    return math.exp(l/k)
def approx_exp_term(l, k, n):
    return sum((l/k)**i / math.factorial(i) for i in range(n))
print("Correct value: ", true_exp_term(-1.217135790852217, 5.25588))
print("Approx: ", [approx_exp_term(-1.217135790852217, 5.25588, n) for n in range(10)])
# Luckily for us this converges much faster. We'll call this `q`.

# === 3. Subtract from 1 and multiply by Tmb/Lmb ===
# At this point, all of the really annoying stuff is done, and we just have
# some multiplying and adding to do. The most important thing here is to make
# sure our approximations earlier aren't introducing too much error. We can do
# this by computing the measured altitude at a few test locations and make sure
# all are in bounds.
def true_altitude(Tmb, Lmb, q):
    return Tmb/Lmb * (1 - q)
test_pres = [float(i) for i in range(30000, 100000, 1000)]
test_alt = [true_altitude(288.15, 0.0065,
        true_exp_term(true_ln_term(p, 101325), 5.25588)) for p in test_pres]
err_tol = 3
# We pick a reasonable tolerance value here (in meters)

# Asymptotic estimate for the number of multiplies required
def cost_func(ne, nl):
    return ne**2 + nl**2

# yes this could be done better in numpy, I'm tired
n_exp_max = 5
n_log_max = 50
best_ne = -1
best_nl = -1
while True:
    best_cost = None
    for n_exp in range(n_exp_max):
        for n_log in range(n_log_max):
            results = [true_altitude(288.15, 0.0065,
                    approx_exp_term(approx_ln_term(p, 101325, n_log), 5.25588, n_exp))
            for p in test_pres]
            max_err = max(abs(r - t) for r, t in zip(results, test_alt))
            if max_err < err_tol:
                # This combo meets tolerance!
                if best_cost is None:
                    # If we haven't seen anything yet, mark it down
                    best_cost = cost_func(n_exp, n_log)
                    best_ne = n_exp
                    best_nl = n_log
                else:
                    cost = cost_func(n_exp, n_log)
                    if cost < best_cost:
                        best_cost = cost
                        best_ne = n_exp
                        best_nl = n_log
    if best_cost is None:
        print("Failed to find sufficient accuracy, increasing range")
        n_exp_max *= 2
        n_log_max *= 2
    else:
        print("Best combo: ", best_ne, " exponential terms, ", best_nl, " log terms")
        break


# We still don't have particularly fast floating-point math on our little 16-bit
# CPU, so our next step is to make all of this integer operations. Furthermore,
# we want it to be all fixed-size integer operations, since heap allocations are
# not a good idea in our puny 256 *bytes* of memory.
from ctypes import *
# If we unroll our previous functions for clarity, our baseline algorithm looks
# like this (we get rid of some of the Pythonic comprehensions stuff because
# eventually this needs to become C):
class ATM:
    K = 5.25588
    Tmb = 288.15
    Lmb = 0.0065

def true_alt(P, Pb):
    return true_altitude(ATM.Tmb, ATM.Lmb,
        true_exp_term(true_ln_term(P, Pb), ATM.K))
def taylor_baseline(P, Pb):
    l = 0
    for i in range(best_nl):
        # Note that we can pull out a factor of (-1)^i here to avoid alternating
        # signs
        term = (1 - P/Pb)**(i+1) / (i+1)
        l -= term
    
    q = 0
    for i in range(best_ne):
        q += (l / ATM.K)**i / math.factorial(i)
    
    return ATM.Tmb/ATM.Lmb * (1 - q)

print("Exact value: ", ["{0:0.2f}".format(true_alt(p, 101325)) for p in test_pres])
print("Taylor float: ", ["{0:0.2f}".format(taylor_baseline(p, 101325)) for p in test_pres])

# We now want to get rid of as much floating-point math as we can. Our first
# stop is `term` in the ln(x) loop. Note that we assume P/Pb is positive and no
# more than 1, so 0 <= 1-P/Pb < 1. We can nicely represent this as a 16-bit int
# representing a value in 65536ths. Conveniently, the 1 wraps around, so
# 1-P/Pb ~ -P/Pb.

def as_uxp16_ratio(n, d):
    # Since inputs are int32s, we have to do the initial conversion in bigint
    # (uint64 in the C implementation) but can convert down to int16 fairly
    # quickly once we have a ratio
    return c_uint16((int(n)<<16) // d)


def as_uxp32_ratio(n, d):
    return c_uint16((int(n)<<32) // d)

def mul_uxp16(a: c_uint16, b: c_uint16):
    return c_uint16((a.value * b.value) >> 16)

def uxp16_pow(n: c_uint16, p: int):
    if p == 0:
        return 0 # 1 wraps around
    result = n
    for _ in range(p-1):
        result = mul_uxp16(result, n)
    return result

def taylor_fixed_log(P, Pb):
    l_uxp = c_uint32(0)
    
    one_minus_ppb = c_uint16((1<<16) - as_uxp16_ratio(P, Pb).value)
    # We can make a small optimization and accumulate the exponentiated result
    exp_val_l = one_minus_ppb
    for i in range(best_nl):
        term = c_uint16(exp_val_l.value // (i+1))
        l_uxp = c_uint32(l_uxp.value + term.value)
        exp_val_l = mul_uxp16(exp_val_l, one_minus_ppb)
    
    l = -l_uxp.value / 65536

    q = 0
    for i in range(best_ne):
        q += (l / ATM.K)**i / math.factorial(i)
    
    return ATM.Tmb/ATM.Lmb * (1 - q)

print("Taylor integer-log: ", ["{0:0.2f}".format(taylor_fixed_log(p, 101325)) for p in test_pres])

# The next step is to compute the exponential portion in fixed-point. Of note
# is that we can do all of our exponentiation and summing in 16-bit. Consider:
# * Tmb/Lmb is a positive constant.
# * Therefore, the sign of altitude is the same as the sign of 1-q.
# * Because q is the result of e^x, it must be positive.
# * Because we assumed P < Pb, altitude must be positive, so 1-q must also.
# * Therefore, 0 < q < 1.
# Because q is produced by an alternating series, individual terms may be more
# than 1. However, since addition, multiplication, and constant exponentiation
# all work under modulo, we can consider everything to be "mod 1" (or mod 65536
# in our fixed-point universe) and our results should be fine. Notably, however,
# fixed-point multiplication doesn't behave the same with positive and negative
# numbers, and l is always negative; therefore, we pull out (-1)^i by just
# alternately adding and subtracting.

def taylor_fixed_exp(P, Pb):
    l_uxp = c_uint32(0)
    
    one_minus_ppb = c_uint16((1<<16) - as_uxp16_ratio(P, Pb).value)
    # We can make a small optimization and accumulate the exponentiated result
    exp_val_l = one_minus_ppb
    for i in range(best_nl):
        term = c_uint16(exp_val_l.value // (i+1))
        l_uxp = c_uint32(l_uxp.value + term.value)
        exp_val_l = mul_uxp16(exp_val_l, one_minus_ppb)
    
    q_uxp = c_uint16(0)
    # The 0th term is 1 / 0! = 1 = 0 mod 1, so we can ignore it
    l_over_k = c_uint16(int(l_uxp.value / ATM.K))
    exp_val_e = l_over_k
    fact_val = 1
    for i in range(1, best_ne):
        # Likewise, optimize the exponentiation and factorial by accumulating
        # (I know that we won't overflow with factorial with this number of
        # iterations, so just using python bigint for brevity)
        fact_val *= i

        term = exp_val_e.value // fact_val
        exp_val_e = mul_uxp16(exp_val_e, l_over_k)
        if i & 1 == 0:
            q_uxp = c_uint16(q_uxp.value + term)
        else:
            q_uxp = c_uint16(q_uxp.value - term)

    q = q_uxp.value / 65536
    
    return ATM.Tmb/ATM.Lmb * (1 - q)

print("Taylor integer-exp: ", ["{0:0.2f}".format(taylor_fixed_exp(p, 101325)) for p in test_pres])

# Now all of our expensive Taylor series terms are in fixed-point, but we still
# have a few floating-point multiplications and divisions that it would be nice
# to be rid of. Specifically, we would like to get rid of the divide-by-k in
# the exponential part and multiplication by Tmb/Lmb in the post-processing part.
# 
# We use the method here:
# https://ridiculousfish.com/blog/posts/labor-of-division-episode-i.html

def make_divider(d, bits):
    p = math.ceil(math.log2(d))
    m = math.ceil((1 << (bits + p)) / d) & ((1 << bits) - 1)
    def divider(n):
        q = m*n >> bits
        t = (((n - q) >> 1) + q) >> (p-1)
        return t
    return divider

div_k = make_divider(ATM.K, 32)
div_tl = make_divider(ATM.Lmb/ATM.Tmb * 65536, 16)
def taylor_fixed(P, Pb):
    l_uxp = c_uint32(0)
    
    one_minus_ppb = c_uint16((1<<16) - as_uxp16_ratio(P, Pb).value)
    # We can make a small optimization and accumulate the exponentiated result
    exp_val_l = one_minus_ppb
    for i in range(best_nl):
        term = c_uint16(exp_val_l.value // (i+1))
        l_uxp = c_uint32(l_uxp.value + term.value)
        exp_val_l = mul_uxp16(exp_val_l, one_minus_ppb)
    
    q_uxp = c_uint16(0)
    # The 0th term is 1 / 0! = 1 = 0 mod 1, so we can ignore it
    l_over_k = c_uint16(div_k(l_uxp.value))
    exp_val_e = l_over_k
    fact_val = 1
    for i in range(1, best_ne):
        # Likewise, optimize the exponentiation and factorial by accumulating
        # (I know that we won't overflow with factorial with this number of
        # iterations, so just using python bigint for brevity)
        fact_val *= i

        term = exp_val_e.value // fact_val
        exp_val_e = mul_uxp16(exp_val_e, l_over_k)
        if i & 1 == 0:
            q_uxp = c_uint16(q_uxp.value + term)
        else:
            q_uxp = c_uint16(q_uxp.value - term)

    one_minus_q_uxp = c_uint16(-q_uxp.value) # Use the 1-q ~ -q trick again
    return div_tl(one_minus_q_uxp.value)

print("Taylor integer: ", ["{0:0.2f}".format(taylor_fixed(p, 101325)) for p in test_pres])

print("Final error: ", max(abs(taylor_fixed(p, 101325) - t)
        for p, t in zip(test_pres, test_alt)), " meters")

# To actually implement this in our C program, it would be handy to generate
# the divider functions without doing any of the expensive float math on our
# MCU. We'll make a quick command-line tool to implement the functionality of 
# the make_divider function in make_divider.py.

# We can implement the GZP6816 barometer's conversion via the same division-by-
# multiplication algorithm as well:

class GZP:
    pmin = 30000
    pmax = 110000
    dmin = 1677722
    dmax = 15099494

test_adc = range(GZP.dmin, GZP.dmax, 1000)
test_pa = [((GZP.pmax-GZP.pmin)/(GZP.dmax-GZP.dmin)*(d - GZP.dmin) + GZP.pmin)
           for d in test_adc]
div_gzp = make_divider((GZP.dmax-GZP.dmin)/(GZP.pmax-GZP.pmin), 32)
approx_pa = [div_gzp(d - GZP.dmin) + GZP.pmin for d in test_adc]

print("Maximum error of ADC conversion: ", max([abs(a - t) for a, t in zip(approx_pa, test_pa)]), "Pa")