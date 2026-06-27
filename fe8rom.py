import struct
from enum import IntEnum

# ROM constants
ROM_BASE = 0x08000000

# Confirmed addresses from FE8_clean.sym
CHARACTER_TABLE_ADDR = 0x08803D64  # gCharacterData
CLASS_TABLE_ADDR     = 0x08807164  # gClassData
CHAPTER_DATA_TABLE   = 0x088B0890  # gChapterDataTable
CHAPTER_ASSET_TABLE  = 0x088B363C  # gChapterDataAssetTable

PINFO_SIZE = 0x34  # 52 bytes per character entry
JINFO_SIZE = 0x54  # 84 bytes per class entry
CHAPTER_INFO_SIZE = 0x94  # 148 bytes per chapter entry
UNIT_DEF_SIZE = 0x14  # 20 bytes per unit definition

CHARACTER_COUNT = 0xFF  # 255 slots (PID 1-255)
CLASS_COUNT     = 0x80  # 128 slots (JID 1-127)

class PID(IntEnum):
    NONE = 0
    EIRIKA = 1
    SETH = 2
    GILLIAM = 3
    FRANZ = 4
    MOULDER = 5
    VANESSA = 6
    ROSS = 7
    NEIMI = 8
    COLM = 9
    GARCIA = 10
    INNES = 11
    LUTE = 12
    NATASHA = 13
    CORMAG = 14
    EPHRAIM = 15
    FORDE = 16
    KYLE = 17
    AMELIA = 18
    ARTUR = 19
    GERIK = 20
    TETHYS = 21
    MARISA = 22
    SALEH = 23
    EWAN = 24
    LARACHEL = 25
    DOZLA = 26
    RENNAC = 28
    DUESSEL = 29
    MYRRH = 30
    KNOLL = 31
    JOSHUA = 32
    SYRENE = 33
    TANA = 34

class JID(IntEnum):
    NONE = 0
    EPHRAIM_LORD = 1
    EIRIKA_LORD = 2
    EPHRAIM_MASTER_LORD = 3
    EIRIKA_MASTER_LORD = 4
    CAVALIER = 5
    CAVALIER_F = 6
    PALADIN = 7
    PALADIN_F = 8
    ARMOR_KNIGHT = 9
    ARMOR_KNIGHT_F = 10
    GENERAL = 11
    GENERAL_F = 12
    THIEF = 13
    MANAKETE = 14
    MERCENARY = 15
    MERCENARY_F = 16
    HERO = 17
    HERO_F = 18
    MYRMIDON = 19
    MYRMIDON_F = 20
    SWORDMASTER = 21
    SWORDMASTER_F = 22
    ASSASSIN = 23
    ASSASSIN_F = 24
    ARCHER = 25
    ARCHER_F = 26
    SNIPER = 27
    SNIPER_F = 28
    RANGER = 29
    RANGER_F = 30
    WYVERN_RIDER = 31
    WYVERN_RIDER_F = 32
    WYVERN_LORD = 33
    WYVERN_LORD_F = 34
    WYVERN_KNIGHT = 35
    WYVERN_KNIGHT_F = 36
    MAGE = 37
    MAGE_F = 38
    SAGE = 39
    SAGE_F = 40
    MAGE_KNIGHT = 41
    MAGE_KNIGHT_F = 42
    BISHOP = 43
    BISHOP_F = 44
    SHAMAN = 45
    SHAMAN_F = 46
    DRUID = 47
    DRUID_F = 48
    SUMMONER = 49
    SUMMONER_F = 50
    ROGUE = 51
    GORGONEGG2 = 52
    GREAT_KNIGHT = 53
    GREAT_KNIGHT_F = 54
    RECRUIT_T1 = 55
    JOURNEYMAN_T2 = 56
    PUPIL_T2 = 57
    RECRUIT_T2 = 58
    MANAKETE_2 = 59
    MANAKETE_MYRRH = 60
    JOURNEYMAN = 61
    PUPIL = 62
    FIGHTER = 63
    WARRIOR = 64
    BRIGAND = 65
    PIRATE = 66
    BERSERKER = 67
    MONK = 68
    PRIEST = 69
    BARD = 70
    RECRUIT = 71
    PEGASUS_KNIGHT = 72
    FALCON_KNIGHT = 73
    CLERIC = 74
    TROUBADOUR = 75
    VALKYRIE = 76
    DANCER = 77
    SOLDIER = 78
    NECROMANCER = 79
    FLEET = 80
    PHANTOM = 81
    REVENANT = 82
    ENTOUMBED = 83
    BONEWALKER = 84
    BONEWALKER_BOW = 85
    WIGHT = 86
    WIGHT_BOW = 87
    BAEL = 88
    ELDER_BAEL = 89
    CYCLOPS = 90
    MAUTHEDOOG = 91
    GWYLLGI = 92
    TARVOS = 93
    MAELDUIN = 94
    MOGALL = 95
    ARCH_MOGALL = 96
    GORGON = 97
    GORGONEGG = 98
    GARGOYLE = 99
    DEATHGOYLE = 100
    DRACO_ZOMBIE = 101
    DEMON_KING = 102
    CIVILIAN_M1 = 109
    CIVILIAN_F1 = 110
    CIVILIAN_M2 = 111
    CIVILIAN_F2 = 112
    CIVILIAN_M3 = 113
    CIVILIAN_F3 = 114

def rom_offset(gba_addr):
    return gba_addr - ROM_BASE

class ROM:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = bytearray(f.read())
        self.verify()

    def verify(self):
        assert len(self.data) > 0x100, "File too small"
        title = self.data[0xA0:0xAC].decode('ascii', errors='replace')
        code = self.data[0xAC:0xB0].decode('ascii', errors='replace')
        assert code == 'BE8E', f"Not an FE8U ROM (got code {code})"

    def read(self, offset, size):
        return self.data[offset:offset+size]

    def write(self, offset, data):
        self.data[offset:offset+len(data)] = data

    def read_u8(self, offset):
        return self.data[offset]

    def read_u16(self, offset):
        return struct.unpack_from('<H', self.data, offset)[0]

    def read_u32(self, offset):
        return struct.unpack_from('<I', self.data, offset)[0]

    def write_u8(self, offset, val):
        self.data[offset] = val & 0xFF

    def write_u16(self, offset, val):
        struct.pack_into('<H', self.data, offset, val & 0xFFFF)

    def write_u32(self, offset, val):
        struct.pack_into('<I', self.data, offset, val & 0xFFFFFFFF)

    def fix_checksum(self):
        """Fix GBA header checksum at offset 0xBD."""
        s = sum(self.data[0xA0:0xBD]) & 0xFF
        self.data[0xBD] = (0x100 - s) & 0xFF

    def save(self, path=None):
        self.fix_checksum()
        target = path or self.path
        with open(target, 'wb') as f:
            f.write(self.data)

    def gba_addr(self, offset):
        return ROM_BASE + offset

class CharacterData:
    def __init__(self, rom, pid):
        offset = rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE
        raw = rom.read(offset, PINFO_SIZE)
        self.pid = pid
        self.offset = offset

        self.name_msg, self.desc_msg = struct.unpack_from('<HH', raw, 0)
        self.id, self.jidDefault = struct.unpack_from('BB', raw, 4)
        self.fid, = struct.unpack_from('<H', raw, 6)
        self.fidMini, self.affinity, self._u0A = struct.unpack_from('BBB', raw, 8)
        vals = struct.unpack_from('9b', raw, 0x0B)
        self.baseLevel = vals[0]
        self.baseHP, self.basePow, self.baseSkl, self.baseSpd = vals[1:5]
        self.baseDef, self.baseRes, self.baseLck, self.baseCon = vals[5:9]
        self.baseWexp = list(raw[0x14:0x1C])
        self.growthHP, self.growthPow, self.growthSkl = raw[0x1C:0x1F]
        self.growthSpd, self.growthDef, self.growthRes = raw[0x1F:0x22]
        self.growthLck = raw[0x22]
        self._u23_27 = list(raw[0x23:0x28])
        self.attributes, = struct.unpack_from('<I', raw, 0x28)
        self.supportInfoPtr, = struct.unpack_from('<I', raw, 0x2C)
        self._pU30, = struct.unpack_from('<I', raw, 0x30)

    def pack(self):
        buf = bytearray(PINFO_SIZE)
        struct.pack_into('<HH', buf, 0, self.name_msg, self.desc_msg)
        buf[4:6] = bytes([self.id, self.jidDefault])
        struct.pack_into('<H', buf, 6, self.fid)
        buf[8:11] = bytes([self.fidMini, self.affinity, self._u0A])
        struct.pack_into('9b', buf, 0x0B,
            self.baseLevel,
            self.baseHP, self.basePow, self.baseSkl, self.baseSpd,
            self.baseDef, self.baseRes, self.baseLck, self.baseCon)
        buf[0x14:0x1C] = bytes(self.baseWexp)
        buf[0x1C:0x23] = bytes([
            self.growthHP, self.growthPow, self.growthSkl,
            self.growthSpd, self.growthDef, self.growthRes,
            self.growthLck])
        buf[0x23:0x28] = bytes(self._u23_27)
        struct.pack_into('<I', buf, 0x28, self.attributes)
        struct.pack_into('<II', buf, 0x2C, self.supportInfoPtr, self._pU30)
        return buf

    def write(self, rom):
        rom.write(self.offset, self.pack())

class ClassData:
    def __init__(self, rom, jid):
        offset = rom_offset(CLASS_TABLE_ADDR) + (jid - 1) * JINFO_SIZE
        raw = rom.read(offset, JINFO_SIZE)
        self.jid = jid
        self.offset = offset

        self.name_msg, self.desc_msg = struct.unpack_from('<HH', raw, 0)
        self.id, self.jidPromotion, self.mapSprite, self.slowWalking = raw[4:8]
        self.fidDefault, = struct.unpack_from('<H', raw, 8)
        self._u0A = raw[0x0A]
        vals = struct.unpack_from('8b', raw, 0x0B)
        self.baseHP, self.basePow, self.baseSkl, self.baseSpd = vals[0:4]
        self.baseDef, self.baseRes, self.baseCon, self.baseMov = vals[4:8]
        max_vals = struct.unpack_from('7b', raw, 0x13)
        self.maxHP, self.maxPow, self.maxSkl, self.maxSpd = max_vals[0:4]
        self.maxDef, self.maxRes, self.maxCon = max_vals[4:7]
        self.classRelativePower = raw[0x1A]
        growths = struct.unpack_from('7b', raw, 0x1B)
        self.growthHP, self.growthPow, self.growthSkl = growths[0:3]
        self.growthSpd, self.growthDef, self.growthRes = growths[3:6]
        self.growthLck = growths[6]
        promo = raw[0x22:0x28]
        self.promotionHp, self.promotionPow, self.promotionSkl = promo[0:3]
        self.promotionSpd, self.promotionDef, self.promotionRes = promo[3:6]
        self.attributes, = struct.unpack_from('<I', raw, 0x28)
        self.baseWexp = list(raw[0x2C:0x34])
        ptrs = struct.unpack_from('<IIIIIII', raw, 0x34)
        self.pBattleAnimDef = ptrs[0]
        self.moveTable = list(ptrs[1:4])
        self.pTerrainAvoidLookup = ptrs[4]
        self.pTerrainDefenseLookup = ptrs[5]
        self.pTerrainResistanceLookup = ptrs[6]
        self._pU50, = struct.unpack_from('<I', raw, 0x50)

    def pack(self):
        buf = bytearray(JINFO_SIZE)
        struct.pack_into('<HH', buf, 0, self.name_msg, self.desc_msg)
        buf[4:8] = bytes([
            self.id, self.jidPromotion, self.mapSprite, self.slowWalking])
        struct.pack_into('<H', buf, 8, self.fidDefault)
        buf[0x0A] = self._u0A
        struct.pack_into('8b', buf, 0x0B,
            self.baseHP, self.basePow, self.baseSkl, self.baseSpd,
            self.baseDef, self.baseRes, self.baseCon, self.baseMov)
        struct.pack_into('7b', buf, 0x13,
            self.maxHP, self.maxPow, self.maxSkl, self.maxSpd,
            self.maxDef, self.maxRes, self.maxCon)
        buf[0x1A] = self.classRelativePower
        struct.pack_into('7b', buf, 0x1B,
            self.growthHP, self.growthPow, self.growthSkl,
            self.growthSpd, self.growthDef, self.growthRes,
            self.growthLck)
        buf[0x22:0x28] = bytes([
            self.promotionHp, self.promotionPow, self.promotionSkl,
            self.promotionSpd, self.promotionDef, self.promotionRes])
        struct.pack_into('<I', buf, 0x28, self.attributes)
        buf[0x2C:0x34] = bytes(self.baseWexp)
        struct.pack_into('<IIIII', buf, 0x34,
            self.pBattleAnimDef, self.moveTable[0],
            self.moveTable[1], self.moveTable[2],
            self.pTerrainAvoidLookup)
        struct.pack_into('<III', buf, 0x48,
            self.pTerrainDefenseLookup,
            self.pTerrainResistanceLookup,
            self._pU50)
        return buf

    def write(self, rom):
        rom.write(self.offset, self.pack())

class ChapterData:
    def __init__(self, rom, chapter_id):
        offset = rom_offset(CHAPTER_DATA_TABLE) + chapter_id * CHAPTER_INFO_SIZE
        raw = rom.read(offset, CHAPTER_INFO_SIZE)
        self.chapter_id = chapter_id
        self.offset = offset
        self.internalNamePtr, = struct.unpack_from('<I', raw, 0)
        self.mapObj1Id = raw[4]
        self.mapObj2Id = raw[5]
        self.mapPaletteId = raw[6]
        self.mapTileConfigId = raw[7]
        self.mapMainLayerId = raw[8]
        self.mapTileAnim1Id = raw[9]
        self.mapTileAnim2Id = raw[0x0A]
        self.mapChangeLayerId = raw[0x0B]
        self.initialFogLevel = raw[0x0C]
        self._unk0D = raw[0x0D]
        self.initialWeather = raw[0x12]
        self.battleTileSet = raw[0x13]
        bits, = struct.unpack_from('<H', raw, 0x14)
        self.easyModeLevelMalus = bits & 0xF
        self.normalModeLevelMalus = (bits >> 4) & 0xF
        self.difficultModeLevelBonus = (bits >> 8) & 0xF
        self.mapSongIndices = list(struct.unpack_from('<8H', raw, 0x16))
        self.mapEventDataId = raw[0x74]
        self.gmapEventId = raw[0x75]

# Item data
ITEM_TABLE_ADDR = 0x08809B10  # gItemData
ITEM_DATA_SIZE = 0x24  # 36 bytes per ItemData entry

WEAPON_TYPE_NAMES = ['Sword', 'Lance', 'Axe', 'Bow', 'Staff', 'Anima', 'Light', 'Dark']

DRAGONSTONE_ITEM_ID = 0xAA

VULNERARY_ITEM_ID = 0x6C

MASTER_SEAL_ITEM_ID = 0x88

PROMOTION_ITEM_IDS = {0x64, 0x65, 0x66, 0x67, 0x68, 0x88, 0x8A, 0x97, 0x98, 0x99}

PROMO_FUNCTION_TABLE_ADDR = 0x08057DD0

PROMO_ITEM_TABLES = {
    0x62: 0x0880C848,
    0x63: 0x0880C889,
    0x64: 0x0880C8CA,
    0x65: 0x0880C90B,
    0x66: 0x0880C94C,
    0x67: 0x0880C98D,
    0x68: 0x0880C9CE,
    0x69: 0x0880CA0F,
    0x88: 0x0880CA0F,
}

PROMO_CLASS_TABLE_BASE = 0x0880CD1B

PROMO_CLASS_FUNCTION_TABLE = 0x08057EF0

STORY_EXCLUSIVE_ITEM_IDS = {
    0x09,  # Rapier (Eirika's prf sword)
    0x78,  # Reginleif (Ephraim's prf lance)
    0x85,  # Sieglinde (Eirika's prf sword, Ch16)
    0x92,  # Siegmund (Ephraim's prf lance, Ch16)
}

MONSTER_BLOCKED_ITEM_IDS = {
    0x0A,  # Dummy / Mani Katti (unused, locked to Eirika)
    0x90,  # Wretched Air
    0xA6,  # Nightmare
    0xA8,  # Demon Light
    0xA9,  # Ravager
    0xAB,  # Demon Surge
    0xAC,  # Shadowshot
    0xAD,  # Rotten Claw
    0xAE,  # Fetid Claw
    0xAF,  # Poison Claw
    0xB0,  # Lethal Talon
    0xB1,  # Fiery Fang
    0xB2,  # Hellfang
    0xB3,  # Evil Eye
    0xB4,  # Crimson Eye
    0xB5,  # Stone / Monster Stone
}

# Palette mapping tables
# FE8 uses two character-indexed tables (7 bytes each, indexed by PID-1)
# to associate characters with their custom color palettes per class tier.
PALETTE_CLASS_TABLE_PTR_OFF = 0x575B4  # ROM offset of pointer to palette class table
PALETTE_INDEX_TABLE_PTR_OFF = 0x57394  # ROM offset of pointer to palette index table
PALETTE_ENTRY_SIZE = 7

class ItemData:
    def __init__(self, rom, item_id):
        offset = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        raw = rom.read(offset, ITEM_DATA_SIZE)
        self.item_id = item_id
        self.offset = offset
        self.name_text_id = struct.unpack_from('<H', raw, 0)[0]
        self.desc_text_id = struct.unpack_from('<H', raw, 2)[0]
        self.use_desc_text_id = struct.unpack_from('<H', raw, 4)[0]
        self.number = raw[6]  # item index/id
        self.weapon_type = raw[7]  # 0=Sword,1=Lance,2=Axe,3=Bow,4=Staff,5=Anima,6=Light,7=Dark,9=Item
        self.attributes = struct.unpack_from('<I', raw, 8)[0]
        self.p_stat_bonuses = struct.unpack_from('<I', raw, 0x0C)[0]
        self.p_effectiveness = struct.unpack_from('<I', raw, 0x10)[0]
        self.max_uses = raw[0x14]
        self.might = raw[0x15]
        self.hit = raw[0x16]
        self.weight = raw[0x17]
        self.crit = raw[0x18]
        self.encoded_range = raw[0x19]
        self.min_range = self.encoded_range & 0xF
        self.max_range = (self.encoded_range >> 4) & 0xF
        self.cost_per_use = struct.unpack_from('<H', raw, 0x1A)[0]
        self.weapon_rank = raw[0x1C]
        self.icon_id = raw[0x1D]
        self.use_effect_id = raw[0x1E]
        self.weapon_effect_id = raw[0x1F]
        self.weapon_exp = raw[0x20]

    def is_weapon(self):
        if self.weapon_type == 4:
            return self.max_uses > 0
        return self.weapon_type <= 7 and self.max_uses > 0 and self.might > 0

ITEM_NAMES = {
    0x00: '(None)',
     0x01: 'Iron Sword', 0x02: 'Slim Sword', 0x03: 'Steel Sword', 0x04: 'Silver Sword',
     0x05: 'Iron Blade', 0x06: 'Steel Blade', 0x07: 'Silver Blade', 0x08: 'Poison Sword',
     0x09: 'Rapier', 0x0A: 'Mani Katti',     0x0B: 'Brave Sword', 0x0C: 'Shamshir',
     0x0D: 'Killing Edge', 0x0E: 'Armorslayer', 0x0F: 'Wyrmslayer',
     0x10: 'Light Brand', 0x11: 'Runesword', 0x12: 'Lancereaver', 0x13: 'Zanbato',
     0x14: 'Iron Lance', 0x15: 'Slim Lance', 0x16: 'Steel Lance', 0x17: 'Silver Lance',
     0x18: 'Toxin Lance', 0x19: 'Brave Lance', 0x1A: 'Killer Lance', 0x1B: 'Horseslayer',
     0x1C: 'Javelin', 0x1D: 'Spear', 0x1E: 'Axereaver',
     0x1F: 'Iron Axe', 0x20: 'Steel Axe', 0x21: 'Silver Axe', 0x22: 'Poison Axe',
     0x23: 'Brave Axe', 0x24: 'Killer Axe', 0x25: 'Halberd', 0x26: 'Hammer',
     0x27: 'Devil Axe', 0x28: 'Hand Axe', 0x29: 'Tomahawk',
     0x2A: 'Swordreaver', 0x2B: 'Swordslayer',
     0x2C: 'Hatchet',
     0x2D: 'Iron Bow', 0x2E: 'Steel Bow', 0x2F: 'Silver Bow',
     0x30: 'Poison Bow', 0x31: 'Killer Bow', 0x32: 'Brave Bow',
     0x33: 'Short Bow', 0x34: 'Longbow',
    0x35: 'Ballista', 0x36: 'Iron Ballista', 0x37: 'Killer Ballista',
    0x38: 'Fire', 0x39: 'Thunder', 0x3A: 'Elfire',
    0x3B: 'Bolting', 0x3C: 'Fimbulvetr', 0x3D: 'Dummy',
    0x3E: 'Excalibur',
    0x3F: 'Lightning', 0x40: 'Shine', 0x41: 'Divine',
    0x42: 'Purge', 0x43: 'Aura', 0x44: 'Dummy',
    0x45: 'Flux', 0x46: 'Luna', 0x47: 'Nosferatu',
    0x48: 'Eclipse', 0x49: 'Fenrir', 0x4A: 'Gleipnir',
    0x4B: 'Heal', 0x4C: 'Mend', 0x4D: 'Recover',
    0x4E: 'Physic', 0x4F: 'Fortify', 0x50: 'Restore',
    0x51: 'Silence', 0x52: 'Sleep', 0x53: 'Berserk',
    0x54: 'Warp', 0x55: 'Rescue', 0x56: 'Torch',
    0x57: 'Hammerne', 0x58: 'Unlock', 0x59: 'Barrier',
    0x5A: 'Dragon Axe',
    0x5B: 'Angelic Robe', 0x5C: 'Energy Ring', 0x5D: 'Secret Book',
    0x5E: 'Speedwing', 0x5F: 'Goddess Icon', 0x60: 'Dragonshield',
    0x61: 'Talisman',
    0x62: 'Swiftsole', 0x63: 'Body Ring', 0x64: 'Hero Crest',
    0x65: 'Knight Crest', 0x66: 'Orion\'s Bolt', 0x67: 'Elysian Whip',
    0x68: 'Guiding Ring', 0x69: 'Chest Key',
    0x6A: 'Door Key', 0x6B: 'Lockpick', 0x6C: 'Vulnerary',
    0x6D: 'Elixir', 0x6E: 'Pure Water', 0x6F: 'Antitoxin',
    0x70: 'Torch (Item)', 0x71: 'Fili Shield',
    0x72: 'Member Card', 0x73: 'Silver Card',
    0x74: 'White Gem', 0x75: 'Blue Gem',
    0x76: 'Red Gem', 0x77: 'Gold',
    0x78: 'Reginleif', 0x79: 'Chest Key (5 uses)',
    0x7A: 'Mine', 0x7B: 'Light Rune',
    0x7C: 'Hoplon Guard', 0x7D: 'Fila\'s Might',
    0x7E: 'Ninis\'s Grace', 0x7F: 'Thor\'s Ire',
    0x80: 'Set\'s Litany',     0x81: 'Shadowkiller', 0x82: 'Bright Lance',
    0x83: 'Fiendcleaver',     0x84: 'Beacon Bow',
    0x85: 'Sieglinde', 0x86: 'Battle Axe',
    0x87: 'Ivaldi', 0x88: 'Master Seal',
    0x89: 'Metis\'s Tome', 0x8A: 'Dummy',
    0x8B: 'Sharp Claw', 0x8C: 'Latona',
    0x8D: 'Dragonspear', 0x8E: 'Vidofnir',
    0x8F: 'Naglfar',
    0x90: 'Wretched Air', 0x91: 'Audhulma',
    0x92: 'Siegmund', 0x93: 'Garm',
    0x94: 'Nidhogg',
    0x95: 'Heavy Spear',
    0x96: 'Short Spear', 0x97: 'Ocean Seal',
    0x98: 'Lunar Brace', 0x99: 'Solar Brace',
    0x9A: '1 Gold', 0x9B: '5 Gold',
    0x9C: '10 Gold', 0x9D: '50 Gold',
    0x9E: '100 Gold', 0x9F: '3,000 Gold',
    0xA0: '5,000 Gold', 0xA1: 'Wind Sword',
    0xA2: 'Vuln (2)', 0xA3: 'Vuln (3)?',
    0xA4: 'Vuln (4)?',
    0xA5: 'Dance Sword', 0xA6: 'Nightmare (Staff)',
    0xA7: 'Stone Shard', 0xA8: 'Demon Light',
    0xA9: 'Ravager', 0xAA: 'Dragonstone',
    0xAB: 'Demon Surge', 0xAC: 'Shadowshot',
    0xAD: 'Rotten Claw', 0xAE: 'Fetid Claw',
    0xAF: 'Poison Claw', 0xB0: 'Lethal Talon',
    0xB1: 'Fiery Fang', 0xB2: 'Hellfang',
    0xB3: 'Evil Eye', 0xB4: 'Crimson Eye',
    0xB5: 'Stone', 0xB6: 'Alacalibur', 0xB7: 'Juna Fruit',
    0xB8: '150 Gold', 0xB9: '200 Gold', 0xBA: 'Black Gem',
    0xBB: 'Gold Gem',
}

def build_weapon_pools(rom):
    pools = {t: [] for t in range(8)}
    for item_id in range(256):
        off = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > len(rom.data):
            break
        raw = rom.data[off:off+ITEM_DATA_SIZE]
        stored_id = raw[6]
        wep_type = raw[7]
        wep_rank = raw[0x1C]
        if stored_id != item_id or stored_id in MONSTER_BLOCKED_ITEM_IDS or stored_id in STORY_EXCLUSIVE_ITEM_IDS:
            continue
        if wep_type <= 7 and raw[0x14] > 0 and raw[0x19] > 0:
            if wep_type != 4 and raw[0x15] == 0:
                continue
            pools[wep_type].append((stored_id, wep_rank))
    return pools
