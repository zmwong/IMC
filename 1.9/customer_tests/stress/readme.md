# Test Descriptions
The tests in this directory were generated based off concurrency test case specifications requiring high stress. Some of the tests were based off MemRunner's subtest0 default configuration.

The IMC XML test cases in this directory do not contain memory block configurations because they are meant to be used with Galaxy or with IMC's Execution Framework.

Please visit goto/imc.wiki to learn more about IMC's flows, algorithms, opcodes and other configurations used in these tests.

## Test case nomenclature
The naming of the test case files follows the following convention:

`FLOW(s)_ADDRESSING-ALGO_DATA-ALGO_OPCODE_GOAL.xml`
* `FLOW(s)` indicate the flows used
* `ADDRESSING-ALGO` represent what addressing algorithm was used
* `DATA-ALGO` is the data algorithm used for the writes/reads
* `OPCODE` is the specific ISA opcode used
* `GOAL` is the goal/objective of the test

Example: `burster_fast_random_byte_add_avx_vmovdqu_high_BW.xml` is the name of the test case that uses a Burser Flow, it uses a Fast Random addressing algorith, a Byte Add data algorithm and a AVX_VMOVDQU opcode for reads and writes.


### Addressing algorithms
Two main addressing mechanisms are used: Pseudo random addressing and Incremental addressing.

#### Pseudo Random Addressing
Generate pseudo random cacheline address sequences. In terms of stress, random memory access patterns prevent the CPU cache from effectively prefetching data, increasing cache misses and memory access latency.

#### Incremental Addressing

We are accessing the memory using an incremental addressing mechanism. When the test focuses on contiguos memory, we are writting back to back cachelines, covering the complete memory block. If the test is focused on stress, we are still using incremental addressing, but we are accessing memory with non-contiguous strides (e.g., every nth cacheline) to disrupt cache line utilization and increase memory traffic.

### Data algorithms

The main data algorithms used are Byte Add and LFSR. Byte Add is a very fast algorithm that helps increase BW due to the speed in which the patterns are generated. PseudoRandom algorithms, such as LFSR, simulate unpredictable workloads.


## Memory Considerations

Depending on cache size and the number of threads, consider using memory block sizes that will avoid caching. Additionally, there are test cases that use non-temporal hints that will help avoiding the cache.

# MemRunner translations

For the MemRunner translation, subtest0 was used a reference to generate similar IMC test cases. Any test case file with `GOAL` = `subtest0`, uses the algorithms



# Test files


| Test Number | Test Case                                                        | Opcode         | Description                                                                                              |
|-------------|------------------------------------------------------------------|----------------|----------------------------------------------------------------------------------------------------------|
| 1           | `burster_fast_random_byte_add_avx_vmovdqu_high_BW.xml             `| AVX_VMOVDQU    | Burster flow with fast random addressing and byte add data generation. High stress due its addressing mechanism and fast data generation. |
| 2           | `burster_increment_byte_add_avx_vmovdqu_high_BW.xml               `| AVX_VMOVDQU    |        |
| 3           | `burster_increment_lfsr_avx_vmovdqu_high_BW.xml                   `| AVX_VMOVDQU    | Incremental addressing with non-contiguous strides and an LFSR data generation algorithm.                              |
| 4           | `bursters_increment_byte_add_lfsr_avx_vmovdqu_variable_BW.xml     `| AVX_VMOVDQU    | Incremental addressing with non-contiguous strides. Uses two Burster flows with different data generation algorithms to generate variability in stress.   |
| 5           | `bursters_increment_various_avx_vmovdqu_subtest0_high_BW.xml      `| AVX_VMOVDQU    | Incremental addressing with non-contiguous strides. This test uses similar algorithms as in MemRunner, but modified with non-contiguous addresses to increase stress. |
| 6           | `burster_increment_byte_add_avx_vmovntdq_contiguous_mem.xml       `| AVX_VMOVNTDQ   | Burster flow with incremental contiguous addressing and data generated with byte add. Uses Non-Temporal hints to avoid caching. |
| 7           | `burster_increment_lfsr_avx_vmovntdq_contiguous_mem.xml           `| AVX_VMOVNTDQ   | Incremental addressing and an LFSR data generation algorithm with AVX VMOVNTDQ opcode. Uses Non-Temporal hints to avoid caching. |
| 8           | `bursters_increment_byte_add_lfsr_avx_vmovntdq_var_BW_cont_mem.xml`| AVX_VMOVNTDQ   | Uses two Burster flows with different data generation algorithms to generate a variable stress. Both burster flows will use a contiguous addressing mechanism.|
| 9           | `bursters_increment_various_avx_vmovntdq_subtest0.xml             `| AVX_VMOVNTDQ   | Translation of memRunner's subtest0. This test uses 7 burster flows with contiguous incremental addressing and 7 different data generation algorithms. Please see "Subtest0 Description".|
| 10          | `burster_fast_random_byte_add_avx512_vmovdqu_high_BW.xml          `| AVX512_VMOVDQU | Burster flow with fast random addressing and byte add data generation.                     |
| 11          | `burster_increment_byte_add_avx512_vmovdqu_high_BW.xml            `| AVX512_VMOVDQU | This test uses a non-contiguous incremental addressing mechanism with an avx512 opcode. Focused on high stress. |
| 12          | `burster_increment_lfsr_avx512_vmovdqu_high_BW.xml                `| AVX512_VMOVDQU | Burster flow with non-contiguous incremental addressing and an LFSR data generation algorithm. |
| 13          | `bursters_increment_byte_add_lfsr_avx512_vmovdqu_variable_BW.xml  `| AVX512_VMOVDQU | Uses two Burster flows with different data generation algorithms to generate a variable stress.   |
| 14          | `burster_increment_byte_add_avx512_vmovntdq_contiguous_mem.xml    `| AVX512_VMOVNTDQ| One burster flow using a contiguous incremental addressing mechanism and an AVX512 VMOVNTDQ opcode. |
| 15          | `burster_increment_lfsr_avx512_vmovntdq_contiguous_mem.xml        `| AVX512_VMOVNTDQ| Contiguous incremental addressing and an LFSR data generation algorithm with AVX512 VMOVNTDQ opcode.  |
| 16          | `bursters_increment_various_avx512_vmovntdq_subtest0.xml          `| AVX512_VMOVNTDQ| Translation of memRunner's subtest0. This test uses 7 burster flows with contiguous incremental addressing and 7 different data generation algorithms. Please see "Subtest0 Description".|


# Subtest0 Description

For the subtest0, there are 7 different tests (or flows in IMC's terms) that MemRunner executes. For OS_COPY tests, the memory block is written in an incremental and sequential manner, meaning that it does not use random addressing or modify the steps size. The tests are summarized below.

1. **Test 1: "Int--"**
   - **Write/Read Iterations**: 1 each
   - **Delay**: No delay for both write and read
   - **Buffer**: Step size of 1, offset of 0, linear step enabled
   - **Test Type**: OSCOPY_DATA
   - **Data Size**: INT_DATA
   - **Data Calculation**: DEC_DATA
   - **Limits**: Write and read limits set to 500 GB
   - **Internal Variables**: All set to 0

2. **Test 2: "Char++"**
   - Similar to Test 1, but with:
     - **Data Size**: CHAR_DATA
     - **Data Calculation**: INC_DATA

3. **Test 3: "Int_Rand"**
   - Similar to Test 1, but with:
     - **Data Calculation**: RND_DATA

4. **Test 4: "Int_Inv"**
   - Similar to Test 1, but with:
     - **Data Calculation**: INV_DATA

5. **Test 5: "Int_Walk"**
   - Similar to Test 1, but with:
     - **Data Calculation**: WSB_DATA

6. **Test 6: "ULL_Inv"**
   - Similar to Test 1, but with:
     - **Data Size**: ULL_DATA
     - **Data Calculation**: INV_DATA

7. **Test 7: "ULL_Walk"**
   - Similar to Test 1, but with:
     - **Data Size**: ULL_DATA
     - **Data Calculation**: WSB_DATA


### IMC's subtest0 translation

To translate this test, we must have 7 burster flows, all of them with an incremental addressing mechanism with a step size equal to the total number of bursts used. The 7 flows were setup with different data generation algorithms, based on MemRunner's subtest0 tests:

1. **Burster Flow**
   - Decrement algorithm starting at `0xFFFFFFFFFFFFFFFF` and ending at `0` with a decrementor of 1.

2. **Burster Flow**
   - Increment algorithm starting at `0` and ending at `0xFFFFFFFFFFFFFFFF` with a incrementor of 1.

3. **Burster Flow**
   - Fast random algorithm for data generation, random seed.

4. **Burster Flow**
   - Negator algorithm for data generation with `0x0` seed.

5. **Burster Flow**
   - Walking one algorithm for data generation.

6. **Burster Flow**
   - Negator algorithm for data generation with `0x0` seed.

7. **Burster Flow**
   - Walking zero algorithm for data generation.

