# -*- coding: UTF-8 -*-

class CodecsKeys(object):
    UTF8 = 'UTF8'
    GBK = 'GBK'


class CodecsIterator(object):
    def __init__(self, sentence, encoding=CodecsKeys.UTF8):
        self._sentence = sentence
        self._encoding = encoding
        self._healthy = True
        self._rep = self._find_second_by_first((0, 0))

    def _find_second_by_first(self, rep):
        if len(self._sentence) == rep[0]:  # end of sentence
            return rep[0], rep[0] + 1

        if self._encoding == CodecsKeys.UTF8:
            if self._sentence[rep[0]] & 0x80 == 0:
                return rep[0], rep[0] + 1
            elif self._sentence[rep[0]] & 0xE0 == 0xC0:
                return rep[0], rep[0] + 2
            elif self._sentence[rep[0]] & 0xF0 == 0xE0:
                return rep[0], rep[0] + 3
            elif self._sentence[rep[0]] & 0xF8 == 0xF0:
                return rep[0], rep[0] + 4
            else:
                self._healthy = False
                return rep
        elif self._encoding == CodecsKeys.GBK:
            if self._sentence[rep[0]] & 0x80 == 0:
                return rep[0], rep[0] + 1
            else:
                return rep[0], rep[0] + 2
        else:
            raise ValueError("encoding error!")

    @property
    def rep(self):
        return self._rep

    def is_end(self):
        return len(self._sentence) < self._rep[1]

    def is_good(self):
        return self._healthy

    def auto_increment(self):
        """
        for foreach
        :return:
        """
        self._rep = (self._rep[1], self._rep[1])
        if self._rep[0] <= len(self._sentence):
            self._rep = self._find_second_by_first(self._rep)
        return self

    def has_next(self):
        return ord(self._sentence[self._rep[1]]) != 0

    def next(self):
        rep = (self._rep[1], 0)
        rep = self._find_second_by_first(rep)
        return rep


class Hasher(object):
    @staticmethod
    def hash(sentence):
        hash_value = 0
        for ch in sentence:
            hash_value = hash_value * 101 + ch
        return hash_value

    @staticmethod
    def default_string_hash(sentence):
        return Hasher.hash(sentence)


class SenSplitTab(object):
    __three_periods_utf8_size__ = 4
    __three_periods_utf8_buff__ = [
        b"\xef\xbc\x9f\xef\xbc\x81\xe2\x80\x9d",
        b"\xe3\x80\x82\xe2\x80\x99\xe2\x80\x9d",
        b"\xef\xbc\x81\xe2\x80\x99\xe2\x80\x9d",
        b"\xe2\x80\xa6\xe2\x80\xa6\xe2\x80\x9d"]
    __three_periods_utf8_key__ = [
        Hasher.hash(__three_periods_utf8_buff__[0]),
        Hasher.hash(__three_periods_utf8_buff__[1]),
        Hasher.hash(__three_periods_utf8_buff__[2]),
        Hasher.hash(__three_periods_utf8_buff__[3]),
    ]

    __two_periods_utf8_size__ = 6
    __two_periods_utf8_buff__ = [
        b"\xe3\x80\x82\xe2\x80\x9d",
        b"\xef\xbc\x81\xe2\x80\x9d",
        b"\xef\xbc\x9f\xe2\x80\x9d",
        b"\xef\xbc\x9b\xe2\x80\x9d",
        b"\xef\xbc\x9f\xef\xbc\x81",
        b"\xe2\x80\xa6\xe2\x80\xa6"
    ]
    __two_periods_utf8_key__ = [
        Hasher.hash(__two_periods_utf8_buff__[0]),
        Hasher.hash(__two_periods_utf8_buff__[1]),
        Hasher.hash(__two_periods_utf8_buff__[2]),
        Hasher.hash(__two_periods_utf8_buff__[3]),
        Hasher.hash(__two_periods_utf8_buff__[4]),
        Hasher.hash(__two_periods_utf8_buff__[5])
    ]

    __one_periods_utf8_size__ = 4
    __one_periods_utf8_buff__ = [
        b"\xe3\x80\x82",
        b"\xef\xbc\x81",
        b"\xef\xbc\x9f",
        b"\xef\xbc\x9b"
    ]
    __one_periods_utf8_key__ = [
        Hasher.hash(__one_periods_utf8_buff__[0]),
        Hasher.hash(__one_periods_utf8_buff__[1]),
        Hasher.hash(__one_periods_utf8_buff__[2]),
        Hasher.hash(__one_periods_utf8_buff__[3])
    ]

    @staticmethod
    def key_equal(hash_value, key_list):
        for key in key_list:
            if hash_value == key:
                return True
        return False


def split_sentence(text, encoding=CodecsKeys.UTF8):
    """
    :param text: str, the text which will be split
    :param encoding: see CodesKeys. default is UTF8
    :return: tupe(num, sentence_list)
    """
    text = text.encode("utf-8")
    text_len = len(text)
    sentence_list = []
    sentence = b""
    itx = CodecsIterator(text, encoding)
    while itx.is_good() and itx.is_end() is False:
        if itx.rep[1] == itx.rep[0] + 1:
            sentence += text[itx.rep[0]:itx.rep[0]+1]
            ch = text[itx.rep[0]:itx.rep[0]+1].decode("utf-8")
            if ch == '\r' or ch == '\n' or ch == '!' or ch == '?' or ch == ';':
                sentence_list.append(sentence.decode("utf-8"))
                sentence = b""
        elif itx.rep[1] == itx.rep[0] + 3:
            found_periods = False
            if itx.rep[1] + 6 <= text_len:
                chunk = text[itx.rep[0]:itx.rep[0]+9]
                hash_value = Hasher.default_string_hash(chunk)
                if SenSplitTab.key_equal(hash_value, SenSplitTab.__three_periods_utf8_key__):
                    sentence += chunk
                    sentence_list.append(sentence.decode("utf-8"))
                    sentence = b""
                    found_periods = True
                    itx.auto_increment()
                    itx.auto_increment()
            if found_periods is False and itx.rep[1] + 3 <= text_len:
                chunk = text[itx.rep[0]:itx.rep[0]+6]
                hash_value = Hasher.default_string_hash(chunk)
                if SenSplitTab.key_equal(hash_value, SenSplitTab.__two_periods_utf8_key__):
                    sentence += chunk
                    sentence_list.append(sentence.decode("utf-8"))
                    sentence = b""
                    found_periods = True
                    itx.auto_increment()

            if found_periods is False:
                chunk = text[itx.rep[0]:itx.rep[0]+3]
                hash_value = Hasher.default_string_hash(chunk)
                if SenSplitTab.key_equal(hash_value, SenSplitTab.__one_periods_utf8_key__):
                    sentence += chunk
                    sentence_list.append(sentence.decode("utf-8"))
                    sentence = b""
                    found_periods = True

            if found_periods is False:
                sentence += text[itx.rep[0]:itx.rep[0]+3]
        else:
            sentence += text[itx.rep[0]:itx.rep[1]]

        itx = itx.auto_increment()

    if len(sentence) > 0:
        sentence_list.append(sentence.decode("utf-8"))

    return len(sentence_list), sentence_list


if __name__ == '__main__':
    print("start")
    # result = split_sentence('元芳你怎么看？我就趴窗口上看呗！')
    # result = split_sentence('服务创新!招商银行青岛分行多措并举助力“暖冬行动”')
    # result = split_sentence(' 　　挖贝网1月18日消息，欧浦智网(002711，股吧)（002711）公司控股股东佛山市中基投资有限公司所持有的公司股份新增轮候冻结。　　截至2019年1月16日收盘，中基投资持有公司500，855，934股股份，占公司股份总数的47.4264%。中基投资所持有的公司股份累计被质押的数量为500，850，242股，占其持有公司股份总数的99.9989%，占公司股份总数的47.4258%；其所持有的公司股份累计被司法冻结的数量为500，855，934股，占其持有公司股份总数的100%，占公司股份总数的47.4264%； 中基投资所持有的公司股份累计被轮候冻结的数量为3，463，872，180股，超过其实际持有的上市公司股份数量。作者：王光军（责任编辑: 和讯网站）')
    result = split_sentence(' 　　冬日天寒，为了让来往银行办理业务的市民们能有更舒适的体验，招商银行青岛分行以一系列的服务创新举措，用温馨的服务环境和温暖的服务行为，为这个冬天增温保暖。　　举措一：红彤彤的暖手门套　　冬季天寒，银行营业厅大门的门把手因为冰冷的温度而受到大家的冷遇，今年来往，招商银行青岛分行营业网点的客户可再也不用发愁了，分行为全辖所有营业网点的门把手统一配上了红彤彤的绒布暖手套，绒布保温性能好，手感温和，手握上去不会有冰冷刺骨的感觉，精心改造的“小细节”让这个冬天既有温度也有风度。　　举措二：爱心餐点爱意浓　　百度百科说：冬季，人们感到最舒适的温度是19-24℃，夏季，则是17-22℃。当然，每个人受年龄、性别、环境等因素影响舒适度也会不一样。所以，最适合的和最需要的自然也应该是舒适的。招商银行一直提倡“以客户为中心”的服务理念，“因您而变”始终是招银人的服务座右铭。根据网点工作人员的观察，很多客户在中午时间段，如11：30-13：00左右，在银行办理业务的时候不免有焦灼情绪，而一天中这个时间段正好是人们午餐的最佳时间。为了缓解客户在此时间办理业务或等待的焦虑，提升消费者的服务体验和满意度，招商银行青岛分行在多次征询一线干部员工的意见基础上，反复比较行内合格供应商供货的商品质量，最终选定了青岛本地著名食品商标“青食”品牌的饼干产品，从巧克力饼干到梳打饼干，再到无糖饼干，满足不同消费者的口味和身体需要。同时，分行还统一了网点饮品基础种类，，让暖冬行动真正走进银行网点，走近市民者身边。　　举措三：提升网点服务环境优　　根据中国银保监会及招商银行总行的要求，分行所有网点的理财销售专区都统一配备了员工销售资质证书和员工信息牌，既规范了银行员工的销售行为和职责，也为金融消费者权益保护提供了有力支持。本次暖冬行动中，招商银行青岛分行专心致力于厅堂服务环境的提升，为金融消费者提供更美观舒适的窗口服务，为此，分行为全辖营业网点500余位一线员工，统一拍摄职业形象照片，并为全辖28家营业网点和一家私人银行中心拍摄职业形象全家福，全力提升银行网点窗口形象，为“暖冬行动”助力加油!　　举措四：以实际行动践行社会责任　　为解决冬日积雪带来的出行安全问题，招商银行青岛辽阳西路支行自发组织员工一早来到网点，清扫台阶上、地面上的冰层和积雪，并在醒目的位置上摆放了“小心地滑”标识，还安排专人及时察看台阶、路面的情况，并提醒过往的人们注意脚下湿滑，人们纷纷为这些在冷风中提供温暖的小伙伴们点赞!为营造圣诞气氛，给客户送去温暖，招商银行青岛南京路支行按照圣诞主题特色，用精美的圣诞树、象征平安的圣诞礼盒、刺绣的圣诞树毛巾，以及各式各样的圣诞许愿卡，为往来支行的客户们送上惊喜和祝福。大家纷纷表示，在招行的营业厅里，不仅能够体验到银行专业便捷的金融服务，还能收到独具节日特色的“窝心”礼物，真是寒冬里的一道暖阳。许多客户还特意领取了圣诞许愿卡，将自己浓浓的心意写在卡片上，悬挂于圣诞树的枝头，为自己及家人祈福。 在这个冬日，每天清晨，招商银行青岛市南支行的员工都会在厅堂煮上一壶暖暖的养生茶，有大枣、枸杞、菊花、桂圆……让每一位来到厅堂的客户都能品尝到一杯热热的养生茶，驱除身上的寒气。这份暖心的关怀让来往的客户深受感动：“哎呀，好冷啊，我是从单位走到你们银行来的，没想到能在你们这儿喝上一杯养生茶，瞬间觉得自己暖和过来了。真是雪中送炭啊!”……　　招商银行青岛分行始终坚持“以客户为中心”的服务准则，以客户需求为先，不断创新服务举措，提升服务水平，致力于为岛城人民提供温馨服务，向着打造“最佳客户体验银行”的目标不断奋进。')
    print(result)

