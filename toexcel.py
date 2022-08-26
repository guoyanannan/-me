import base64
import json
from Crypto.Cipher import AES


# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    return str.encode(value)  # 返回byte


def decrypt_oralce():
    # 秘钥
    key = 'Nercar701'
    # 密文
    with open('bankdata.bin', 'r', encoding='utf-8') as banks:
        text = banks.read()
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 优先逆向解密base64成bytes
    base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
    print(base64_decrypted,type(base64_decrypted))
    # bytes解密
    decrypted_text = str(aes.decrypt(base64_decrypted),encoding='utf-8') # 执行解密密并转码返回str
    decrypted_text = base64.b64decode(decrypted_text.encode('utf-8')).decode('utf-8')

    print(decrypted_text)
    # print(json.loads(decrypted_text))
    # print(type(json.loads(decrypted_text)))
    print('----------冷轧----------- \n',json.loads(decrypted_text)['冷轧']['英文'],':\n',len(json.loads(decrypted_text)['冷轧']['英文']))
    print(json.loads(decrypted_text)['冷轧']['中文'],':\n',len(json.loads(decrypted_text)['冷轧']['中文']))
    print('----------热轧----------- \n',json.loads(decrypted_text)['热轧']['英文'],':\n',len(json.loads(decrypted_text)['热轧']['英文']))
    print(json.loads(decrypted_text)['热轧']['中文'],':\n',len(json.loads(decrypted_text)['热轧']['中文']))
    print('----------板材----------- \n',json.loads(decrypted_text)['板材']['英文'],':\n',len(json.loads(decrypted_text)['板材']['英文']))
    print(json.loads(decrypted_text)['板材']['中文'],':\n',len(json.loads(decrypted_text)['板材']['中文']))
    print('----------棒材----------- \n',json.loads(decrypted_text)['棒材']['英文'],':\n',len(json.loads(decrypted_text)['棒材']['英文']))
    print(json.loads(decrypted_text)['棒材']['中文'],':\n',len(json.loads(decrypted_text)['棒材']['中文']))
    print('----------铸坯----------- \n',json.loads(decrypted_text)['铸坯']['英文'],':\n',len(json.loads(decrypted_text)['铸坯']['英文']))
    print(json.loads(decrypted_text)['铸坯']['中文'],':\n',len(json.loads(decrypted_text)['铸坯']['中文']))
    print('----------字符----------- \n',json.loads(decrypted_text)['字符']['英文'],':\n',len(json.loads(decrypted_text)['字符']['英文']))
    print(json.loads(decrypted_text)['字符']['中文'],':\n',len(json.loads(decrypted_text)['字符']['中文']))
    return json.loads(decrypted_text)


if __name__ == '__main__':
    _ = decrypt_oralce()