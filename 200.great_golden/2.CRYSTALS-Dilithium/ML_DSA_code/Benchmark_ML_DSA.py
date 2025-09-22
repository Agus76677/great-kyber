"""
@Descripttion: ML_DSA benchmark
@version: V1.0
@Author: HZW
@Date: 2025-03-14 16:00
"""
from ML_DSA import *
from time import time
from statistics import mean

def Benchmark_ML_DSA(params, name, count):
    print("-" * 30)
    print(f"  {name} | ({count} calls)")
    print("-" * 30)

    fail= 0
    KeyGen_times = []
    Sign_times = []
    Verify_times = []
    # 32 byte message
    m = b"Your sign message "

    for _ in range(count):
        ML_DSA1=ML_DSA(params)
        M=os.urandom(32)
        ctx=os.urandom(54)

        t0 = time()
        pk,sk= ML_DSA1.KeyGen()
        KeyGen_times.append(time() - t0)

        t1 = time()
        sigma=ML_DSA1.Sign(sk, M, ctx)
        Sign_times.append(time() - t1)

        t2 = time()
        Verify = ML_DSA1.Verify(pk, M, sigma,ctx)
        Verify_times.append(time() - t2)
        if not Verify:
            fail += 1

    print(f"KeyGen  average: {round(mean(KeyGen_times), 3)}")
    print(f"Sign    average: {round(mean(Sign_times),3)}")
    print(f"Verify  average: {round(mean(Verify_times),3)}")
    print(f"Fail number: {fail}")


if __name__ == "__main__":
    count = 1000
    Benchmark_ML_DSA(ML_DSA_44, "Dilithium2", count)
    Benchmark_ML_DSA(ML_DSA_65, "Dilithium3", count)
    Benchmark_ML_DSA(ML_DSA_87, "Dilithium5", count)