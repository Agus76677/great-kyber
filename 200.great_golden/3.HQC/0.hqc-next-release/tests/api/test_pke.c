/**
 * @file test_pke.c
 * @brief Unit test for the HQC PKE API (keygen → encrypt → decrypt → verify).
 *
 */

#include <munit.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>
#include "hqc.h"
#include "munit_utils.h"
#include "parameters.h"
#include "symmetric.h"

/**
 * @brief End-to-end test: HQC PKE keygen → encrypt → decrypt.
 *
 * @param params     (unused) Framework parameters.
 * @param user_data  (unused) Opaque pointer passed by the framework.
 * @return MUNIT_OK on success; the test asserts on failure.
 *
 * @test
 * - Asserts that `hqc_pke_decrypt` returns 0 (success).
 * - Asserts that the decrypted message `m2` equals the original `m1`.
 */
static MunitResult test_pke_api(const MunitParameter params[], void* user_data) {
    (void)params;
    (void)user_data;

    unsigned char seed[SEED_BYTES] = {0};
    unsigned char theta[SEED_BYTES] = {0};
    unsigned char m1[VEC_K_SIZE_BYTES] = {0};
    unsigned char m2[VEC_K_SIZE_BYTES] = {0};
    ciphertext_pke_t c_pke = {0};

    /* Fill buffers with pseudo-random values from Munit */
    munit_rand_memory(SEED_BYTES, seed);
    munit_rand_memory(SEED_BYTES, theta);
    munit_rand_memory(VEC_K_SIZE_BYTES, m1);

    unsigned char ek_pke[PUBLIC_KEY_BYTES] = {0};
    unsigned char dk_pke[SECRET_KEY_BYTES] = {0};

    /* Keygen, encrypt, decrypt */
    hqc_pke_keygen(ek_pke, dk_pke, seed);
    hqc_pke_encrypt(&c_pke, ek_pke, (uint64_t*)m1, theta);
    int result = hqc_pke_decrypt((uint64_t*)m2, dk_pke, &c_pke);

    /* Check decrypt return code – if nonzero, treat as failure */
    munit_assert_int(result, ==, 0);

    /* Compare plaintext vectors m1 vs m2 */
    munit_assert_memory_equal(VEC_K_SIZE_BYTES, m1, m2);

    return MUNIT_OK;
}

/**
 * @brief Test registry for the PKE API suite.
 */
MunitTest pke_tests[] = {MUNIT_TEST_ENTRY("pke_api", test_pke_api), MUNIT_TEST_END};
