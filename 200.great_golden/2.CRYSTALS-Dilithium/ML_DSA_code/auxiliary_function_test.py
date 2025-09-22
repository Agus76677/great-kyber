"""
@Descripttion: ML_DSA 辅助函数
@version: V1.0
@Author: HZW
@Date: 2025-03-12 20:00
"""
import pytest
import numpy as np
import random
import os
from auxiliary_function import *

def test_InterToBits_BitsToInter():
    for i in range(256):
        t=InterToBits(i,8)
        c=BitsToInter(t,8)
        assert c==i
            
        
def test_BytesToBits_BitsToBytes():
    B=[ i for i in range(256)]
    t=BytesToBits(B,8)
    c=BitsToBytes(t,8)
    assert c==B
    
    
    
def test_SimpleBitPack_SimpleBitUnPack():
    for i in range(100):
        array = np.random.randint(0, q, size=256)
        Poly1 = Poly(array)
        y=SimpleBitPack(Poly1,q)
        assert len(y)==32*q.bit_length()
        t=SimpleBitUnPack(y,q)
        assert t==Poly1
        
        
def test_BitPack_BitUnPack():
    a,b=50,7000
    for i in range(100):
        array = np.random.randint(-a, b, size=256)
        Poly1 = Poly(array)
        y=BitPack(Poly1,a,b)
        assert len(y)==32*(a+b).bit_length()
        t=BitUnPack(y,a,b)
        assert t==Poly1

def test_HintBitpack_HintBitUnPack():
    for params2 in {ML_DSA_44,ML_DSA_65,ML_DSA_87}:

        h = Vec([Poly([1,0,0,0,1,1]+[0]*250)]*params2.k)
        print(h)
        y=HintBitpack(h,params2.omega,params2.k)
        print(y)
        assert len(y)==params2.omega+params2.k
        t=HintBitUnPack(y,params2.omega,params2.k)
        assert t==h
        

def test_mod_pm():
    # Test for odd n
    assert mod_pm(5, 7) == -2
    assert mod_pm(10, 7) == 3 
    
    # Test for even n
    assert mod_pm(7, 6) == 1  
    assert mod_pm(9, 6) == 3 

def test_Power2Round():
    # Test multiple values
    for x in [1, 1000, q-1, q//2]:
        r1, r0 = Power2Round(x)
        # Verify bounds
        assert abs(r0) <= (1 << d)
        # Verify reconstruction
        assert (r1 << d) + r0 == x % q

def test_Decompose():
    a = 95232  # Example gamma_2 * 2 value for ML_DSA_44
    # Test multiple values
    for x in [1, 1000, q-1, q//2]:
        r1, r0 = Decompose(x, a)
        # Verify bounds
        assert abs(r0) <= a
        # Verify reconstruction (except for q-1 case)
        if x != q-1:
            assert r1 * a + r0 == x % q

def test_HighBits_LowBits():
    a = 95232  # Example gamma_2 * 2 value
    
    # Test that HighBits and LowBits match Decompose
    for x in [1, 1000, q//2, q-2]:
        r1, r0 = Decompose(x, a)
        assert HighBits(x, a) == r1
        assert LowBits(x, a) == r0
        
        # Test reconstruction
        high = HighBits(x, a)
        low = LowBits(x, a)
        if x != q-1:
            assert (high * a + low) % q == x % q

def test_MakeHint_UseHint():
    a = 95232  # Example gamma_2 * 2 value
    
    # Test hint creation and usage
    for r in [1000, q//2, q-2]:
        for z in [1, -1, a//2, -a//2]:
            h = MakeHint(z, r, a)
            assert h in [0, 1]  # Hint should be binary
            
            # Test hint usage
            v1 = HighBits(r + z, a)
            v2 = UseHint(h, r, a)
            if h == 1:
                assert v1 == v2  # UseHint should recover high bits when hint is 1

def test_make_hint_optimised():
    a = 95232  # Example gamma_2 * 2 value
    gamma2 = a >> 1
    
    # Test boundary conditions
    assert make_hint_optimised(gamma2, 0, a) == 0
    assert make_hint_optimised(gamma2 + 1, 0, a) == 1
    assert make_hint_optimised(q - gamma2, 0, a) == 0
    
    # Test regular cases
    assert make_hint_optimised(gamma2 - 1, 0, a) == 0
    assert make_hint_optimised(gamma2 + 100, 0, a) == 1
            

def test_ntt_intt():
    for i in range(100):
        array3 = np.random.randint(0, q, size=256)
        Poly1 = Poly(array3)
        Poly2 = Poly1
        result = Poly1.NTT().INTT()
        
        assert Poly2 == result
        
    Poly1=Poly([1,384,0]+[0]*253) #384x^1+1
    Poly2=Poly([1,2,0]+[0]*253) #2x^1+1
    Poly3=Poly([1,386,768]+[0]*253) #768x^2+386x^1+1
    Poly2=Poly2.NTT()
    assert Poly1.NTT().MultiplyNTT(Poly2).INTT()==Poly3


def test_pkEncode_pkDecode():
    temp=(q-1).bit_length()-d
    temp1=2**temp
    for params2 in {ML_DSA_44,ML_DSA_65,ML_DSA_87}:
        for _ in range(100):
            rho = os.urandom(32)
            t_1 = Vec([Poly(np.random.randint(0,temp1, size=256)) for _ in range(params2.k)])  # 假设 k = 4

            pk = pkEncode(rho, t_1, params2.k)
            assert len(pk)==(32+32*params2.k*temp)
            rho_d,t_1d=pkDecode(pk,params2.k)
            assert rho_d==rho
            assert t_1d==t_1


def test_skEncode_skDecode():
    for params2 in {ML_DSA_44,ML_DSA_65,ML_DSA_87}:
        for _ in range(100):
            rho = os.urandom(32)
            K = os.urandom(32)
            tr=os.urandom(64)

            s1 = Vec([Poly(np.random.randint(-params2.eta,params2.eta, size=256)) for _ in range(params2.l)])  # 假设 k = 4
            s2 = Vec([Poly(np.random.randint(-params2.eta,params2.eta, size=256)) for _ in range(params2.k)]) 
            t0 = Vec([Poly(np.random.randint(-2**(d-1)+1,2**(d-1), size=256)) for _ in range(params2.k)]) 

            sk =skEncode(rho,K,tr,s1,s2,t0,params2.k,params2.l,params2.eta)
            assert len(sk)==(32+32+64+32*((params2.k+params2.l)*(2*params2.eta).bit_length()+d*params2.k))
            
            rho_1d,K_1d,tr_1d,s1_1d,s2_1d,t0_1d=skDecode(sk,params2.k,params2.l,params2.eta)

            assert rho_1d==rho
            assert K_1d  ==K
            assert tr_1d ==tr
            assert s1_1d==s1
            assert s2_1d==s2
            assert t0_1d==t0

def test_sigEncode_sigDecode():
    for params2 in {ML_DSA_44,ML_DSA_65,ML_DSA_87}:
        # for _ in range(100):
        c_tie = os.urandom(params2.lambda_1//4)

        z = Vec([Poly(np.random.randint(-params2.gamma_1+1,params2.gamma_1, size=256)) for _ in range(params2.l)]) 
        print("z:",z.Norm())
        h = Vec([Poly([1,0,0,0,1,1]+[0]*250)]*params2.k) 

        sigma =sigEncode(c_tie,z.mod_pm(),h,params2.k,params2.l,params2.gamma_1,params2.omega)
        assert len(sigma)==(params2.lambda_1//4+params2.l*32*(1+(params2.gamma_1-1).bit_length())+params2.omega+params2.k)

        c_tie_1d,z_1d,h_1d=sigDecode(sigma,params2.lambda_1,params2.gamma_1,params2.l,params2.omega,params2.k)
        print("z1d:",z_1d.Norm())
        print(c_tie_1d==c_tie) 
        print(z_1d==z) 
        print(h_1d==h) 

test_sigEncode_sigDecode()
           
def test_w1Encode():
    for params2 in {ML_DSA_44,ML_DSA_65,ML_DSA_87}:
        for _ in range(100):
            temp = ((q-1)//(2*params2.gamma_2)-1)
            
            w1 = Vec([Poly(np.random.randint(0, temp+1, size=256)) for _ in range(params2.k)])
            
            try:
                w1_tie = w1Encode(w1, params2.k, params2.gamma_2)
                
                # Check the output length 
                expected_length = 32 * params2.k * temp.bit_length()
                assert len(w1_tie) == expected_length
                
            except Exception as e:
                pytest.fail(f"w1Encode failed with error: {str(e)}")
                
                
def test_SampleInBall():
    # Test for different parameter sets
    for params2 in {ML_DSA_44, ML_DSA_65, ML_DSA_87}:
        for _ in range(10):
            rho = os.urandom(params2.lambda_1//4)
            c = SampleInBall(rho, params2.tau)
            
            # Check polynomial length
            assert len(c.cs) == 256
            
            # Count non-zero coefficients (should equal tau)
            non_zero = sum(1 for coeff in c.cs if coeff != 0)
            assert non_zero == params2.tau
            
            # Check coefficients are in {-1, 0, 1}
            for coeff in c.cs:
                assert coeff in {-1, 0, 1}

def test_RejNTTPoly():
    for _ in range(10):
        # Generate random seed
        rho = os.urandom(34)  # 32 bytes for seed + 2 bytes for position
        
        poly = RejNTTPoly(rho)
        
        # Check polynomial length
        assert len(poly.cs) == 256
        
        # Check coefficients are in [0, q-1]
        for coeff in poly.cs:
            assert 0 <= coeff < q

def test_RejBoundedPoly():
    for params2 in {ML_DSA_44, ML_DSA_65, ML_DSA_87}:
        for _ in range(10):
            rho = os.urandom(66)
            poly = RejBoundedPoly(rho, params2.eta)
            
            # Check polynomial length
            assert len(poly.cs) == 256
            
            # Check coefficient bounds
            for coeff in poly.cs:
                assert -params2.eta <= coeff <= params2.eta

def test_ExpandA():
    for params2 in {ML_DSA_44, ML_DSA_65, ML_DSA_87}:
        # Generate random seed
        rho = os.urandom(32)
        
        # Generate matrix
        A = ExpandA(rho, params2.k, params2.l)
        
        # Check matrix dimensions
        assert len(A.cs) == params2.k
        assert len(A.cs[0]) == params2.l
        
        # Check each polynomial in matrix
        for row in A.cs:
            for poly in row:
                assert len(poly.cs) == 256
                # Check coefficients are in [0, q-1]
                for coeff in poly.cs:
                    assert 0 <= coeff < q

def test_ExpandS():
    for params2 in {ML_DSA_44, ML_DSA_65, ML_DSA_87}:
        # Generate random seed
        rho = os.urandom(64)
        
        # Generate vectors
        s1, s2 = ExpandS(rho, params2.k, params2.l, params2.eta)
        
        # Check vector dimensions
        assert len(s1.ps) == params2.l
        assert len(s2.ps) == params2.k
        
        # Check s1 coefficients
        for poly in s1.ps:
            assert len(poly.cs) == 256
            for coeff in poly.cs:
                assert -params2.eta <= coeff <= params2.eta
                
        # Check s2 coefficients
        for poly in s2.ps:
            assert len(poly.cs) == 256
            for coeff in poly.cs:
                assert -params2.eta <= coeff <= params2.eta

def test_ExpandMask():
    for params2 in {ML_DSA_44, ML_DSA_65, ML_DSA_87}:
        # Generate random seed
        rho = os.urandom(64)
        mu = random.randint(0, 1000)
        
        # Generate vector
        y = ExpandMask(rho, mu, params2.l, params2.gamma_1)
        
        # Check vector dimension
        assert len(y.ps) == params2.l
        
        # Check coefficients bounds
        for poly in y.ps:
            assert len(poly.cs) == 256
            for coeff in poly.cs:
                assert -params2.gamma_1 + 1 <= coeff <= params2.gamma_1