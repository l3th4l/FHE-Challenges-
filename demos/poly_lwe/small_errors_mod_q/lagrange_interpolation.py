from sage.all import * 

def lagrange_polynomial(xs, xk, modulo = None):
    assert modulo

    F = GF(modulo)
    R = PolynomialRing(F, 'x')
    x = R.gen()


    l = 1 
    for xi in xs:
        if xi != xk:
            num = R(x - xi) 
            den = F(xk - xi)
            inv_den = den.inverse_of_unit()
            l *= num * inv_den
            
    return l 

def recostruct_polynomial(xs, ys, degree, modulo = None):
    assert modulo 
    assert len(xs) == len(ys) 
    assert len(xs) >= degree 

    return sum([yi * lagrange_polynomial(xs, xi, modulo = modulo) for xi, yi in zip(xs, ys)])





