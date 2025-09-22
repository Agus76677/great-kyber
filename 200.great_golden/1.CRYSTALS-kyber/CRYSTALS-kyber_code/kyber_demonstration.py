"""
@Descripttion: CRYSTALS-kyber PKE的演示程序
@version: V1.0
@Author: HZW
@Date: 2025-03-10 12:00
"""

from kyber_k_PKE import *
import os
#os.urandom生成指定长度的随机字节串

def string_to_fixed_bytes(s, length=32, encoding='utf-8'):
    """
    将字符串转换为固定长度的字节序列。
    
    参数:
        s (str): 输入的字符串。
        length (int): 目标字节序列的长度，默认为32。
        encoding (str): 编码方式，默认为 'utf-8'。
        
    返回:
        bytes: 转换后的固定长度字节序列。
    """
    # 将字符串编码为字节序列
    bytes_seq = s.encode(encoding)
    
    # 如果字节序列长度小于目标长度，用零字节填充
    if len(bytes_seq) < length:
        bytes_seq = bytes_seq.ljust(length, b'\x00')
    # 如果字节序列长度大于目标长度，截取前length字节
    else:
        bytes_seq = bytes_seq[:length]
    
    return bytes_seq

def fixed_bytes_to_string(b, encoding='utf-8'):
    """
    将固定长度的字节序列解码为字符串。
    参数:
        b (bytes): 输入的字节序列,长度应为32字节。
        encoding (str): 编码方式，默认为 'utf-8'。 
    返回:
        str: 解码后的字符串。
        
    抛出:
        ValueError: 如果字节序列长度不是32字节。
    """
    # 检查字节序列长度
    if len(b) != 32:
        raise ValueError("字节序列长度必须为32字节") 
    # 解码字节序列为字符串
    try:
        text = b.decode(encoding)
    except UnicodeDecodeError:
        raise ValueError("字节序列包含无法解码的字节")
    # 移除可能的零字节填充
    text = text.rstrip('\x00')
    return text

def get_plaintext():
    """
    从终端提示用户输入一段明文消息。
    返回:
        str: 用户输入的明文消息。
    """
    plaintext = input("请输入一段明文消息: ")
    return plaintext

def main():
    msg=get_plaintext()
    m=string_to_fixed_bytes(msg) #将明文转换为固定长度的字节序列
    params=params512
    seed=os.urandom(32) 
    r=os.urandom(32)
    ek_pke, dk_pke = k_PKE_KeyGen(seed, params)
    c= k_PKE_Encrypt(ek_pke, m, r,params)
    print("密文:", c)
    decrypted_message = k_PKE_Decrypt(dk_pke, c, params)
    decrypted_msg=fixed_bytes_to_string(decrypted_message)
    print("解密后的明文:", decrypted_msg)
    
if __name__ == "__main__":
    main() ## input：Cryptographic center