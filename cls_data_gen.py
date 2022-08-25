import base64
import json
from Crypto.Cipher import AES


# str不是16的倍数那就补足为16的倍数
def add_to_16(value):
    while len(value) % 16 != 0:
        value += '\0'
    print(value)
    return str.encode(value)  # 返回byte


# 加密
def encrypt_oracle(v: str = '1.0.0.0'):
    key= 'Nercar701'
    cls_info = {
                'version': v,
                '字符':{
                      '英文': ['BeiJing','0','1','2','3','4','5','6','7','8','9',
                              'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                              'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                              '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                              'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                              'u','v','w','x','y','z'],
                      '中文': ['背景','0','1','2','3','4','5','6','7','8','9',
                             'A','B','C','D','E','F','G','H','I','G','K','L','M','N',
                             'O','P','Q','R','S','T','U','V','W','X','Y','Z','!','@',
                             '#','$','%','^','&','*','(',')','_','+','a','b','c','d','e',
                             'f','g','h','i','g','k','l','m','n','o','p','q','r','s','t',
                             'u','v','w','x','y','z']
                       },
                '冷轧':{
                      '英文':[
                            'AnXian', 'BaiXianTiao', 'CaShangXingDian', 'ChongZiYin', 'CuoBianYin', 'HeiDian', 'HengXiangYaGunYin', 'LuZhaYin', 'SeCha', 'ShuiYin', 'ShuiYinBaiDian', 'TuoPiXian',
                            'YaShangDian', 'XiHuaShang', 'XiaoSuiLang','ZhuangShangYin','ZongXiangZheHenYin','GunShangYin','HengXiangGunYin','BeiJing',
                            'SuiBian', 'ZheBian', 'QieKouBuLiang', 'KuanDuYiChang', 'JiaShang', 'JuBuWeiQieBian', 'CanJian', 'HouDuYiChang', 'BianSun', 'GuaBian', 'GongQi', 'QiaoQu',
                            'ZhongLang', 'BianLang', 'QiGu', 'LianDaoWan', 'ZhengMianLangZhuang', 'JiaoChaLang','HuXing', 'YingJuan', 'JiaZha', 'KongDong', 'BiaoMianFenCeng', 'BianSiYaRu',
                            'ReZhuaShang', 'JiaCeng', 'DianJiShang', 'YangHuaPiHen', 'GunYin', 'ZangWu', 'BiaoMianLieWen', 'YiWuYaRu', 'HuaShang', 'ZaoShang', 'CaShang', '2BXiaoBaiDian',
                            'YangCan', 'TuoPi', 'ReLieGunWen', 'ZheDie', 'BiaoMianCuCao', 'XiuBan', 'QiKongTuoPi', 'ShiKongDianShi', 'BanDian', 'SuanYin', 'TuiHuoGuoDu', 'TuiHuoBuZu',
                            'QianSuan', 'GuoSuan', 'ZhenHen', 'JiaHen', 'ZheHen', 'TingJiHen','XiuPiYaRu', 'NianJiao', 'YouJiao', 'ShuiXiBuLiang', 'ShuiYin', 'ShuaGunYin',
                            'JiaoZhiJiCanLiu', 'BaHen', 'FuZuoWuYinHen', 'XiuPiBaHen', 'BanMianHei', 'YaHen', 'BaiBan', 'TingJiJuan', 'LianZhuBaoPian', 'YouBan', 'SeZeAn','HeiXian',
                            'ErCiTuiHuoJuan', 'JianSuJuan', 'SuanNi', 'AoKeng', 'TingCheBan', 'QiPi', 'XianFeng', 'GuaShang', 'GuaHen', 'TiaoZhuangTuoPi', 'PenHaoCanLiu', 'LieWenGunHen',
                            'FuShiDian', 'SuanXiBuZu', 'BiaoMian2D', 'YanMoHen', 'SeZeBuJun','ZhiYinHen', 'JuanQuHen', 'YaYin', 'SuanXiBuJun', 'GuangZeTiaoWen', 'PaiGuWen', 'ZhaRuXiuPi2B',
                            'TaXing', 'BaGuaJuan', 'CeYuanBoLangJuan', 'SongSanGangJuan', 'NeiQuanTaXian', 'TuoYuanGangJuan', 'DanZhongBuZu', 'SanLeiTuoPi', 'HanFeng','YiLeiTuoPi', 'ErLeiTuoPi',
                            'SiLeiTuoPi', 'HanKong', 'HanFengBuDing', 'ZhaJiHen', 'XiuDian', 'BianBuYaXiu', 'BaoGuangSeCha', 'ReYaGuaShang', 'HeiDai', 'ReGunYin', 'ZaoShangFenSan',
                            'JianDuanReYaGuaShang', 'XianXingJiaZa', 'CengJianCaShang','ErLeiReYaGuaShang', 'YanZhongYangHuaPiTuoLuoHen'],
                      '中文':[
                            '暗线', '白线条', '擦伤星点', '虫子印', '挫边印', '黑点', '横向压辊印', '炉渣印', '色差', '水印', '水印白点', '脱皮线','压伤点', '细划伤', '小碎浪','撞伤印','纵向折痕印',
                            '辊伤印','横向辊印','背景',
                            '碎边', '折边', '切口不良', '宽度异常', '夹伤', '局部未切边', '残剪', '厚度异常', '边损', '刮边', '拱起', '翘曲', '中浪', '边浪', '起鼓', '镰刀弯', '整面浪状', '交叉浪',
                            '弧形', '硬卷', '夹渣', '孔洞', '表面分层', '边丝压入', '热抓伤', '夹层', '电击伤', '氧化皮痕', '辊印', '脏污', '表面裂纹', '异物压入', '划伤', '凿伤', '擦伤', '2B小白点',
                            '氧残', '脱皮', '热裂辊纹', '折叠', '表面粗糙', '锈斑', '气孔脱皮', '蚀孔点蚀', '斑点', '酸印', '退火过度', '退火不足', '欠酸', '过酸', '振痕', '夹痕', '折痕', '停机痕',
                            '锈皮压入', '黏胶', '油胶', '水洗不良', '水印', '刷辊印', '胶脂剂残留', '疤痕', '附作物印痕', '锈皮疤痕', '板面黑', '压痕', '白斑', '停机卷', '连铸剥片', '油班', '色泽暗',
                            '黑线', '二次退火卷', '减速卷', '酸泥', '凹坑', '停车斑', '起皮', '线缝', '刮伤', '刮痕', '条状脱皮', '喷号残留', '裂纹辊痕', '腐蚀点', '酸洗不足', '表面2D', '研磨痕', '色泽不均',
                            '纸印痕', '卷曲痕', '压印', '酸洗不均', '光泽条纹', '排骨纹', '扎入锈皮2B', '塔形', '八卦卷', '侧缘波浪卷', '松散钢卷', '内圈塌陷', '椭圆钢卷', '单重不足', '三类脱皮', '焊缝',
                            '一类脱皮', '二类脱皮', '四类脱皮', '焊孔', '焊缝补丁', '轧机痕', '锈点', '边部轧锈', '曝光色差', '热轧刮伤', '黑带', '热辊印', '凿伤分散', '间断热轧刮伤', '线性夹杂', '层间擦伤',
                            '二类热轧刮伤', '严重氧化皮脱落痕']

                       },
                '热轧':{
                       '英文':['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'YaLan', 'KongDong', 'ZhaRuWaiWu','BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen','LiangHuaShang', 'XianFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                             'ZhenHen','PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin','BaoGuangYinHen', 'TingJiWenLi', 'BaiTieLin', 'ReZhaBianBuZheDie', 'ReZhaJuChiBian', 'LianGangHuaShang','LianGangJiaZa', 'LianGangXiWeiJiaZa', 'LianGangFenCeng', 'LianGangHeiDai', 'LianGangXianXingJiaZaWu',
                             'MXingLieWen','ReZhaBanBianHuaHen','ZhiGangXianXingJiaZa', 'ZhiGangYanMoHen', 'ReYaMoCaHen', 'LianGangBa', 'GongZuoGunMaDian','YiWuYaRu', 'TuBao', 'LaSiYaRu', 'AoKeng', 'CaShang', 'HuaShang', 'TiaoZhuangChongPi','LianGangBianBuKaiLie','ReZhaRCLHen',
                             'ReZhaGunYin','ReZhaJiaSongGunYin','ReZhaYangHuaPiBoLi','ReZhaZhanGang',],

                       '中文':['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物','剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕','亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                             '振痕','片状铁鳞', '波形', '水滴', '水雾', '水印','曝光印痕', '停机纹理', '白铁鳞', '热轧边部折叠', '热轧锯齿边', '炼钢划伤','炼钢夹杂', '炼钢细微夹杂', '炼钢分层', '炼钢黑带', '炼钢线性夹杂物', 
                             'M型裂纹','热轧板边划痕','制钢线性夹杂', '制钢研磨痕', '热轧摩擦痕', '炼钢疤', '工作辊麻点','异物压入', '凸包', '拉丝压入', '凹坑', '擦伤', '划伤', '条状重皮','炼钢边部开裂','热轧RCL痕',
                             '热轧辊印','热轧夹送辊印','热轧氧化皮剥离','热轧粘钢',]
                       },
                '板材':{
                       '英文':['DaiFenLei', 'ZongXiangLieWen', 'HengXiangLieWen', 'BianLie', 'ShuiYin', 'GunYin',
                           'YaKeng', 'QiaoPi', 'XianXingQueXian', 'HuaShang', 'YaHen', 'ShuiDi',
                           'PingBiBianBu', 'PingBiTouWei', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan', 'BeiJingSi',
                           'BeiJingWu', 'BeiJingLiu', 'BeiJingQi', 'BeiJingBa', 'MaDian', 'YiWuYaRu',
                           'ShuiWen', 'JieBa', 'YangHuaTiePi', 'XianXingQueXianYi', 'YiSiYiWuYaRu'],
                       '中文':['待分类', '纵向裂纹', '横向裂纹', '边裂', '水印', '辊印',
                           '压坑', '翘皮', '线性缺陷', '划伤', '压痕', '水滴',
                           '屏蔽边部', '屏蔽头尾', '背景一', '背景二', '背景三', '背景四',
                           '背景五', '背景六', '背景七', '背景八', '麻点', '异物压入',
                           '水纹', '结疤', '氧化铁皮', '线性缺陷一', '疑似异物压入']
                       },
                '棒材': {
                       '英文': ['DaiFenLei', 'JingZhaGunYin', 'DaiTouGunYin', 'ZhaLan', 'KongDong', 'ZhaRuWaiWu',
                           'BaoPian', 'JieBa', 'XianZhuangJiaZa', 'ZhuPiHuaShang', 'ZongXiangLieWen', 'GuaHen',
                           'LiangHuaShang', 'XiaFeng', 'YiCiXiuPi', 'ErCiXiuPi', 'TieLinYaRu', 'YangHuaTiePi',
                           'ZhenHen', 'PianZhuangTieLin', 'BoXing', 'ShuiDi', 'ShuiWu', 'ShuiYin',
                           'BaoGuangYinHen', 'TingZhiShuXian', 'BaiTieLin', 'BeiJingYi', 'BeiJingEr', 'BeiJingSan',
                           'BeiJingSi', 'QiPi', 'TouWeiBian', 'BianYuanPoLie', 'BeiJingWu', 'BeiJingLiu',
                           'BeiJingQi', 'BianYuanMaoCi', 'GuoBaoGuang', 'BeiJingBa', 'BeiJingJiu', 'BeiJingShi',
                           'BeiJingShiYi', 'XiuPiTuoLuo', 'AoKeng', 'ErDuo', 'HuaShang', 'BeiJing'],
                       '中文': ['待分类', '精轧辊印', '带头辊印', '轧烂', '孔洞', '轧入外物',
                           '剥片', '结疤', '线状夹杂', '铸坯划伤', '纵向裂纹', '刮痕',
                           '亮划伤', '狭缝', '一次锈皮', '二次锈皮', '铁鳞压入', '氧化铁皮',
                           '振痕', '片状铁鳞', '波形', '水滴', '水雾', '水印',
                           '曝光印痕', '停止竖线', '白铁鳞', '背景一', '背景二', '背景三',
                           '背景四', '起皮', '头尾边', '边缘破裂', '背景五', '背景六',
                           '背景七', '边缘毛刺', '过曝光', '背景八', '背景九', '背景十',
                           '背景十一', '锈皮脱落', '凹坑', '耳朵', '划伤', '背景']
                        },
                '铸坯':{
                       '英文':['BeiJing', 'ZongXiangLieWen', 'HengXiangLieWen', 'HuaShang', 'ShuiZhaYin', 'GunYin',
                           'ZhaPi', 'QieGeKaiKou', 'TingZhiXian', 'CaHuaShang', 'DuanMianHanZha', 'JieHen'],
                       '中文':['背景', '纵向裂纹', '横向裂纹', '划伤', '水渣印', '辊印',
                           '渣皮', '切割开口', '停止线', '擦划伤', '端面焊渣', '接痕']
                       },
                }
    mystr = json.dumps(cls_info)
    print(mystr)
    text = base64.b64encode(mystr.encode('utf-8')).decode('ascii')
    print('base64：',text)
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 先进行aes加密
    encrypt_aes = aes.encrypt(add_to_16(text))
    print('aes加密:',encrypt_aes)
    # 用base64转成字符串形式
    encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')  # 执行加密并转码返回bytes
    print('加密后转为字节：',encrypted_text) #测试打印加密数据
    # 写入加密数据到文件
    with open("classname.bin","w") as bankdata:
        bankdata.write(encrypted_text)


# 解密方法
def decrypt_oralce():
    # 秘钥
    key = 'Nercar701'
    # 密文
    with open('classname.bin', 'r', encoding='utf-8') as banks:
        text = banks.read()
    # 初始化加密器
    aes = AES.new(add_to_16(key), AES.MODE_ECB)
    # 优先逆向解密base64成bytes
    base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
    # bytes解密
    decrypted_text = str(aes.decrypt(base64_decrypted),encoding='utf-8') # 执行解密密并转码返回str
    decrypted_text = base64.b64decode(decrypted_text.encode('utf-8')).decode('utf-8')

    # print(decrypted_text)
    #print(json.loads(decrypted_text))
    # print(type(json.loads(decrypted_text)))
    print('----------版本----------- \n', json.loads(decrypted_text)['version'], '\n',len(json.loads(decrypted_text)['version']))
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
    encrypt_oracle()
    class_defect_infos = decrypt_oralce()
