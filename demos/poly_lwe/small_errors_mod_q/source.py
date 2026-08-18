from itertools import product as cart
from time import time
from sage.all import * 
from generate_f_q import generate_prime, irreducible_poly_mod_q

from rlwe import DiscreteGaussianDistributionPolynomialSampler, RingLWE

from math import ceil


N = 4 
d = 4
sigma = 2

q =  generate_prime(n = 7, max_k = 200)
R_q = PolynomialRing(Zmod(q), 'x')

print("q = ", q) #find a polynomial 

f = irreducible_poly_mod_q(q, max_order = d, n = N)
D = DiscreteGaussianDistributionPolynomialSampler(ZZ['x'], n=euler_phi(N), sigma=sigma)

cipher = RingLWE(N, q, D, poly = f)


print(f"f(x) = {R_q(f)} (mod {q})")

print(f"[factorized] f(x) = {R_q(f).factor()} (mod {q})")

print("roots of f(x) : ", R_q(f).roots())

#Generate samples 
samples = [cipher() for _ in range(30)]

alpha = R_q(f).roots()[3][0]
alpha_order = Zmod(q)(alpha).multiplicative_order()

def generate_error_sums(n, sigma, truncate_limit, moduli, order):
    max_val = int(math.ceil(truncate_limit * sigma))
    possible_values = range(-max_val, max_val + 1)

    #generate sum  1
    sums1 = []
    for vec in cart(possible_values, repeat=ceil(n/order)):
        sums1.append(sum(vector(Zmod(moduli), vec)))

    sums2 = []
    if not n % order == 0:
        for vec in cart(possible_values, repeat=ceil(n/order)-1):
            sums2.append(sum(vector(Zmod(moduli), vec)))

    return list(set(sums1)), list(set(sums2))

def generate_error_set(alpha, q, n, sigma, order):
    alpha_is = vector(Zmod(q), [pow(alpha, i, q) for i in range(min(n, order))])

    k1 = order - n % order 
    k2 = max(0, order - k1)


    s1, s2 = generate_error_sums(n, sigma, 4, q, order)
    possible_coefficients = [s1] * k1 + [s2] * k2

    
    #find all possible sums
    return set([alpha_is  * vector(coeffs) for coeffs in cart(*possible_coefficients)])


#TODO : look for a more effecient way to check membership in S

if __name__=="__main__":

    S = generate_error_set(alpha, q, N, sigma, alpha_order)

    print(f"\n\nThe homomorphic image of the secret under alpha = {alpha} should be : {cipher.secret_poly.lift()(alpha)}")

    print(" ---- Searching for the secret ---- ")

    start = time()
    for g in range(0, q):
        valid = True
        for a, b in samples[:5]:
            e1_alpha = R_q(list(b - g*a))(alpha)
            if not(e1_alpha in S):
                valid = False
                break 
        if valid:
            print(f"\nWe've found {g} to be a valid guess for the secret during search")
            print(f"\ntime taken = {time() - start:.2f} seconds")
            break
       
