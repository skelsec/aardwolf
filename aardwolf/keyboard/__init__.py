
import enum
import json
import base64

class VK_MODIFIERS(enum.IntFlag):
    VK_SHIFT = 1
    VK_CONTROL = 2
    VK_MENU = 4
    VK_CAPITAL = 8
    VK_OEM_8 = 16
    VK_KANA = 32
    VK_NUMLOCK = 64
    VK_WIN = 128

class KeyboardLayout:
    def __init__(self):
        self.klid = None
        self.name = None
        self.RightAltIsAltGr = None 
        self.ShiftCancelsCapsLock = None 
        self.ChangesDirectionality = None
        self.char_to_sc_nomod = {} #char -> sc
        self.char_to_sc = {} #char -> (sc,modifiers)
        self.sc_to_char = {} #scancode -> modifiers -> char
        self.vk_to_sc = {}
        self.sc_to_vk = {}

    def char_to_scancode(self, char):
        if char in self.char_to_sc_nomod:
            return self.char_to_sc_nomod[char], VK_MODIFIERS(0)
        
        return self.char_to_sc[char]

    def scancode_to_char(self, sc, modifiers:VK_MODIFIERS = VK_MODIFIERS(0)):
        """0 is no modifiers present"""
        if sc not in self.sc_to_char:
            return None
        avilable_modifiers = self.sc_to_char[sc]
        if len(avilable_modifiers) == 0:
            return None
        if modifiers in avilable_modifiers:
            return avilable_modifiers[modifiers]
        #print('available modifiers: %s' % avilable_modifiers)
        if modifiers not in avilable_modifiers and VK_MODIFIERS(0) in avilable_modifiers:
            return avilable_modifiers[VK_MODIFIERS(0)]
        return None

    def scancode_to_vk(self, sc):
        if sc not in self.sc_to_vk:
            return None
        return self.sc_to_vk[sc]
    
    def vk_to_scancode(self, vk):
        return self.vk_to_sc[vk]

    def to_dict(self):
        return {
            'klid' : self.klid,
            'name' : self.name,
            'RightAltIsAltGr' : self.RightAltIsAltGr,
            'ShiftCancelsCapsLock' : self.ShiftCancelsCapsLock,
            'ChangesDirectionality' : self.ChangesDirectionality,
            'char_to_sc' : self.char_to_sc,
            'sc_to_char' : self.sc_to_char,
            'vk_to_sc' : self.vk_to_sc,
            'sc_to_vk' : self.sc_to_vk,
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())

    @staticmethod
    def from_dict(d):
        kl = KeyboardLayout()
        kl.klid = d['klid']
        kl.name = d['name']
        kl.RightAltIsAltGr = d['RightAltIsAltGr']
        kl.ShiftCancelsCapsLock = d['ShiftCancelsCapsLock']
        kl.ChangesDirectionality = d['ChangesDirectionality']
        kl.sc_to_char = {}
        kl.char_to_sc_nomod = {}
        for k in d['sc_to_char']:
            sc = int(k)
            kl.sc_to_char[sc] = {}
            for modifier in d['sc_to_char'][k]:
                if modifier == '0':
                    kl.char_to_sc_nomod[d['sc_to_char'][k][modifier]] = sc
                mo = VK_MODIFIERS(int(modifier))
                kl.sc_to_char[sc][mo] = d['sc_to_char'][k][modifier]
        
        kl.char_to_sc = {}
        for k in d['char_to_sc']:
            if k in kl.char_to_sc and kl.char_to_sc[k][1] == '':
                continue

            kl.char_to_sc[k] = d['char_to_sc'][k]
            if kl.char_to_sc[k][1] != '':
                mo = VK_MODIFIERS(int(kl.char_to_sc[k][1]))
                kl.char_to_sc[k] = (kl.char_to_sc[k][0], mo)
            else:
                kl.char_to_sc[k] = (kl.char_to_sc[k][0], mo)

        kl.sc_to_vk = {}
        for k in d['sc_to_vk']:
            kl.sc_to_vk[int(k)] = d['sc_to_vk'][k]

        kl.vk_to_sc = {}
        for k in d['sc_to_vk']:
            if d['sc_to_vk'][k] in kl.vk_to_sc and kl.vk_to_sc[d['sc_to_vk'][k]] < int(k):
                continue
            kl.vk_to_sc[d['sc_to_vk'][k]] = int(k)

        #kl.vk_to_sc = {v: k for k, v in d['sc_to_vk'].items()}

        return kl
    
    @staticmethod
    def from_json(s):
        return KeyboardLayout.from_dict(json.loads(s))
    
    @staticmethod
    def from_layoutdata(layoutdata):
        lj = base64.b64decode(layoutdata).decode()
        return KeyboardLayout.from_json(lj)