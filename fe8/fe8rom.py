import struct
from enum import IntEnum
from typing import List, Optional, Tuple

# ROM constants
ROM_BASE = 0x08000000

# Portrait table base address — character portrait metadata entries
PORTRAIT_TABLE_ADDR = 0x088ACBC4
PORTRAIT_ENTRY_SIZE = 0x1C


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
    ARTUR = 13
    CORMAG = 14
    EPHRAIM = 15
    FORDE = 16
    KYLE = 17
    AMELIA = 18
    NATASHA = 19
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


# PID → portrait table entry slot index mapping.
# Slot n = entry at PORTRAIT_TABLE_ADDR + n * PORTRAIT_ENTRY_SIZE
# Values derived from FEBuilder portrait table dump (entry addr offsets).
PID_TO_PORTRAIT_SLOT = {
    PID.EIRIKA:   0x02,
    PID.SETH:     0x04,
    PID.GILLIAM:  0x05,
    PID.FRANZ:    0x06,
    PID.MOULDER:  0x07,
    PID.VANESSA:  0x08,
    PID.ROSS:     0x09,
    PID.NEIMI:    0x0A,
    PID.COLM:     0x0C,
    PID.GARCIA:   0x0E,
    PID.INNES:    0x0F,
    PID.LUTE:     0x10,
    PID.ARTUR:  0x11,
    PID.CORMAG:   0x13,
    PID.EPHRAIM:  0x14,
    PID.FORDE:    0x16,
    PID.KYLE:     0x18,
    PID.AMELIA:   0x19,
    PID.NATASHA:    0x1A,
    PID.GERIK:    0x1B,
    PID.TETHYS:   0x1C,
    PID.MARISA:   0x1E,
    PID.SALEH:    0x20,
    PID.EWAN:     0x21,
    PID.LARACHEL: 0x22,
    PID.DOZLA:    0x23,
    PID.RENNAC:   0x24,
    PID.DUESSEL:  0x25,
    PID.MYRRH:    0x26,
    PID.KNOLL:    0x29,
    PID.JOSHUA:   0x2A,
    PID.SYRENE:   0x2B,
    PID.TANA:     0x2C,
}


class JID(IntEnum):
    NONE = 0
    EIRIKA_LORD = 1
    EPHRAIM_LORD = 2
    EIRIKA_MASTER_LORD = 3
    EPHRAIM_MASTER_LORD = 4
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

# Pre-compiled struct parsers
_U16 = struct.Struct('<H')
_U32 = struct.Struct('<I')
_CHAR_HEADER = struct.Struct('<HH')      # name_msg, desc_msg
_CHAR_VALS = struct.Struct('9b')         # baseLevel + 8 base stats
_CHAR_ATTRS = struct.Struct('<I')        # attributes
_CHAR_TAIL = struct.Struct('<II')        # supportInfoPtr, _pU30
_CLASS_BASE_VALS = struct.Struct('8b')  # class base stats
_CLASS_MAX_VALS = struct.Struct('7b')   # class max stats
_CLASS_GROWTHS = struct.Struct('7B')    # class growths (unsigned — game stores 0-255)
_CLASS_ATTRS = struct.Struct('<I')      # class attributes
_CLASS_MOVE_PTRS = struct.Struct('<IIIII')  # move table ptrs
_CLASS_TAIL = struct.Struct('<III')     # terrain lookups + _pU50


def rom_offset(gba_addr: int) -> int:
    return gba_addr - ROM_BASE


class ROM:
    __slots__ = ('path', 'data')

    def __init__(self, path: str):
        self.path = path
        with open(path, 'rb') as f:
            self.data = bytearray(f.read())
        self.verify()

    def verify(self) -> None:
        assert len(self.data) > 0x100, "File too small"
        code = self.data[0xAC:0xB0].decode('ascii', errors='replace')
        assert code == 'BE8E', f"Not an FE8U ROM (got code {code})"

    def read(self, offset: int, size: int) -> bytes:
        return self.data[offset:offset+size]

    def write(self, offset: int, data: bytes) -> None:
        self.data[offset:offset+len(data)] = data

    def read_u8(self, offset: int) -> int:
        return self.data[offset]

    def read_u16(self, offset: int) -> int:
        return _U16.unpack_from(self.data, offset)[0]

    def read_u32(self, offset: int) -> int:
        return _U32.unpack_from(self.data, offset)[0]

    def write_u8(self, offset: int, val: int) -> None:
        self.data[offset] = val & 0xFF

    def write_u16(self, offset: int, val: int) -> None:
        _U16.pack_into(self.data, offset, val & 0xFFFF)

    def write_u32(self, offset: int, val: int) -> None:
        _U32.pack_into(self.data, offset, val & 0xFFFFFFFF)

    def fix_checksum(self) -> None:
        s = sum(self.data[0xA0:0xBD]) & 0xFF
        self.data[0xBD] = (0x100 - s) & 0xFF

    def save(self, path: str = None) -> None:
        self.fix_checksum()
        target = path or self.path
        with open(target, 'wb') as f:
            f.write(self.data)


class CharacterData:
    __slots__ = (
        'pid', 'offset',
        'name_msg', 'desc_msg',
        'id', 'jidDefault',
        'fid', 'fidMini', 'affinity', '_u0A',
        'baseLevel',
        'baseHP', 'basePow', 'baseSkl', 'baseSpd',
        'baseDef', 'baseRes', 'baseLck', 'baseCon',
        'baseWexp',
        'growthHP', 'growthPow', 'growthSkl',
        'growthSpd', 'growthDef', 'growthRes',
        'growthLck',
        '_u23_27',
        'attributes',
        'supportInfoPtr',
        '_pU30',
    )

    def __init__(self, rom: ROM, pid: int):
        offset = rom_offset(CHARACTER_TABLE_ADDR) + (pid - 1) * PINFO_SIZE
        raw = rom.read(offset, PINFO_SIZE)
        self.pid = pid
        self.offset = offset

        self.name_msg, self.desc_msg = _CHAR_HEADER.unpack_from(raw, 0)
        self.id, self.jidDefault = raw[4], raw[5]
        self.fid, = _U16.unpack_from(raw, 6)
        self.fidMini, self.affinity, self._u0A = raw[8], raw[9], raw[0x0A]
        vals = _CHAR_VALS.unpack_from(raw, 0x0B)
        self.baseLevel = vals[0]
        self.baseHP, self.basePow, self.baseSkl, self.baseSpd = vals[1:5]
        self.baseDef, self.baseRes, self.baseLck, self.baseCon = vals[5:9]
        self.baseWexp = list(raw[0x14:0x1C])
        self.growthHP, self.growthPow, self.growthSkl = raw[0x1C], raw[0x1D], raw[0x1E]
        self.growthSpd, self.growthDef, self.growthRes = raw[0x1F], raw[0x20], raw[0x21]
        self.growthLck = raw[0x22]
        self._u23_27 = list(raw[0x23:0x28])
        self.attributes, = _CHAR_ATTRS.unpack_from(raw, 0x28)
        self.supportInfoPtr, self._pU30 = _CHAR_TAIL.unpack_from(raw, 0x2C)

    def pack(self) -> bytearray:
        buf = bytearray(PINFO_SIZE)
        _CHAR_HEADER.pack_into(buf, 0, self.name_msg, self.desc_msg)
        buf[4:6] = bytes([self.id, self.jidDefault])
        _U16.pack_into(buf, 6, self.fid)
        buf[8:11] = bytes([self.fidMini, self.affinity, self._u0A])
        _CHAR_VALS.pack_into(buf, 0x0B,
            self.baseLevel,
            self.baseHP, self.basePow, self.baseSkl, self.baseSpd,
            self.baseDef, self.baseRes, self.baseLck, self.baseCon)
        buf[0x14:0x1C] = bytes(self.baseWexp)
        buf[0x1C:0x23] = bytes([
            self.growthHP, self.growthPow, self.growthSkl,
            self.growthSpd, self.growthDef, self.growthRes,
            self.growthLck])
        buf[0x23:0x28] = bytes(self._u23_27)
        _CHAR_ATTRS.pack_into(buf, 0x28, self.attributes)
        _CHAR_TAIL.pack_into(buf, 0x2C, self.supportInfoPtr, self._pU30)
        return buf

    def write(self, rom: ROM) -> None:
        rom.write(self.offset, self.pack())


class ClassData:
    __slots__ = (
        'jid', 'offset',
        'name_msg', 'desc_msg',
        'id', 'jidPromotion', 'mapSprite', 'slowWalking',
        'fidDefault', '_u0A',
        'baseHP', 'basePow', 'baseSkl', 'baseSpd',
        'baseDef', 'baseRes', 'baseCon', 'baseMov',
        'maxHP', 'maxPow', 'maxSkl', 'maxSpd',
        'maxDef', 'maxRes', 'maxCon',
        'classRelativePower',
        'growthHP', 'growthPow', 'growthSkl',
        'growthSpd', 'growthDef', 'growthRes',
        'growthLck',
        'promotionHp', 'promotionPow', 'promotionSkl',
        'promotionSpd', 'promotionDef', 'promotionRes',
        'attributes',
        'baseWexp',
        'pBattleAnimDef', 'moveTable',
        'pTerrainAvoidLookup',
        'pTerrainDefenseLookup',
        'pTerrainResistanceLookup',
        '_pU50',
    )

    def __init__(self, rom: ROM, jid: int):
        offset = rom_offset(CLASS_TABLE_ADDR) + (jid - 1) * JINFO_SIZE
        raw = rom.read(offset, JINFO_SIZE)
        self.jid = jid
        self.offset = offset

        self.name_msg, self.desc_msg = _CHAR_HEADER.unpack_from(raw, 0)
        self.id, self.jidPromotion, self.mapSprite, self.slowWalking = raw[4], raw[5], raw[6], raw[7]
        self.fidDefault, = _U16.unpack_from(raw, 8)
        self._u0A = raw[0x0A]
        vals = _CLASS_BASE_VALS.unpack_from(raw, 0x0B)
        self.baseHP, self.basePow, self.baseSkl, self.baseSpd = vals[0:4]
        self.baseDef, self.baseRes, self.baseCon, self.baseMov = vals[4:8]
        max_vals = _CLASS_MAX_VALS.unpack_from(raw, 0x13)
        self.maxHP, self.maxPow, self.maxSkl, self.maxSpd = max_vals[0:4]
        self.maxDef, self.maxRes, self.maxCon = max_vals[4:7]
        self.classRelativePower = raw[0x1A]
        growths = _CLASS_GROWTHS.unpack_from(raw, 0x1B)
        self.growthHP, self.growthPow, self.growthSkl = growths[0:3]
        self.growthSpd, self.growthDef, self.growthRes = growths[3:6]
        self.growthLck = growths[6]
        promo = raw[0x22:0x28]
        self.promotionHp, self.promotionPow, self.promotionSkl = promo[0], promo[1], promo[2]
        self.promotionSpd, self.promotionDef, self.promotionRes = promo[3], promo[4], promo[5]
        self.attributes, = _CLASS_ATTRS.unpack_from(raw, 0x28)
        self.baseWexp = list(raw[0x2C:0x34])
        ptrs = _CLASS_MOVE_PTRS.unpack_from(raw, 0x34)
        self.pBattleAnimDef = ptrs[0]
        self.moveTable = list(ptrs[1:4])
        self.pTerrainAvoidLookup = ptrs[4]
        self.pTerrainDefenseLookup, self.pTerrainResistanceLookup, self._pU50 = _CLASS_TAIL.unpack_from(raw, 0x48)

    def pack(self) -> bytearray:
        buf = bytearray(JINFO_SIZE)
        _CHAR_HEADER.pack_into(buf, 0, self.name_msg, self.desc_msg)
        buf[4:8] = bytes([self.id, self.jidPromotion, self.mapSprite, self.slowWalking])
        _U16.pack_into(buf, 8, self.fidDefault)
        buf[0x0A] = self._u0A
        _CLASS_BASE_VALS.pack_into(buf, 0x0B,
            self.baseHP, self.basePow, self.baseSkl, self.baseSpd,
            self.baseDef, self.baseRes, self.baseCon, self.baseMov)
        _CLASS_MAX_VALS.pack_into(buf, 0x13,
            self.maxHP, self.maxPow, self.maxSkl, self.maxSpd,
            self.maxDef, self.maxRes, self.maxCon)
        buf[0x1A] = self.classRelativePower
        _CLASS_GROWTHS.pack_into(buf, 0x1B,
            self.growthHP, self.growthPow, self.growthSkl,
            self.growthSpd, self.growthDef, self.growthRes,
            self.growthLck)
        buf[0x22:0x28] = bytes([
            self.promotionHp, self.promotionPow, self.promotionSkl,
            self.promotionSpd, self.promotionDef, self.promotionRes])
        _CLASS_ATTRS.pack_into(buf, 0x28, self.attributes)
        buf[0x2C:0x34] = bytes(self.baseWexp)
        _CLASS_MOVE_PTRS.pack_into(buf, 0x34,
            self.pBattleAnimDef, self.moveTable[0],
            self.moveTable[1], self.moveTable[2],
            self.pTerrainAvoidLookup)
        _CLASS_TAIL.pack_into(buf, 0x48,
            self.pTerrainDefenseLookup,
            self.pTerrainResistanceLookup,
            self._pU50)
        return buf

    def write(self, rom: ROM) -> None:
        rom.write(self.offset, self.pack())


class ChapterData:
    __slots__ = (
        'chapter_id', 'offset',
        'internalNamePtr',
        'mapObj1Id', 'mapObj2Id', 'mapPaletteId', 'mapTileConfigId',
        'mapMainLayerId', 'mapTileAnim1Id', 'mapTileAnim2Id',
        'mapChangeLayerId', 'initialFogLevel', '_unk0D',
        'initialWeather', 'battleTileSet',
        'easyModeLevelMalus', 'normalModeLevelMalus', 'difficultModeLevelBonus',
        'mapSongIndices',
        'mapEventDataId', 'gmapEventId',
    )

    def __init__(self, rom: ROM, chapter_id: int):
        offset = rom_offset(CHAPTER_DATA_TABLE) + chapter_id * CHAPTER_INFO_SIZE
        raw = rom.read(offset, CHAPTER_INFO_SIZE)
        self.chapter_id = chapter_id
        self.offset = offset
        self.internalNamePtr, = _U32.unpack_from(raw, 0)
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
        bits, = _U16.unpack_from(raw, 0x14)
        self.easyModeLevelMalus = bits & 0xF
        self.normalModeLevelMalus = (bits >> 4) & 0xF
        self.difficultModeLevelBonus = (bits >> 8) & 0xF
        self.mapSongIndices = list(struct.unpack_from('<8H', raw, 0x16))
        self.mapEventDataId = raw[0x74]
        self.gmapEventId = raw[0x75]

    def write(self, rom: ROM) -> None:
        rom.write(self.offset, self.internalNamePtr.to_bytes(4, 'little'))


# Item data
ITEM_TABLE_ADDR = 0x08809B10  # gItemData
ITEM_DATA_SIZE = 0x24  # 36 bytes per ItemData entry

WEAPON_TYPE_NAMES = ['Sword', 'Lance', 'Axe', 'Bow', 'Staff', 'Anima', 'Light', 'Dark']

DRAGONSTONE_ITEM_ID = 0xAA

VULNERARY_ITEM_ID = 0x6C

MASTER_SEAL_ITEM_ID = 0x88

PROMOTION_ITEM_IDS = frozenset({0x64, 0x65, 0x66, 0x67, 0x68, 0x88, 0x8A, 0x97, 0x98, 0x99})

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

STORY_EXCLUSIVE_ITEM_IDS = frozenset({
    0x09,  # Rapier (Eirika's prf sword)
    0x78,  # Reginleif (Ephraim's prf lance)
    0x85,  # Sieglinde (Eirika's prf sword, Ch16)
    0x92,  # Siegmund (Ephraim's prf lance, Ch16)
})

MONSTER_BLOCKED_ITEM_IDS = frozenset({
    0x0A, 0x3D, 0x44, 0x90, 0xA6, 0xA8, 0xA9,
    0xAB, 0xAC, 0xAD, 0xAE, 0xAF, 0xB0, 0xB1,
    0xB2, 0xB3, 0xB4, 0xB5, 0xBE, 0xBF,
})

BALLISTA_ITEM_IDS = frozenset({0x35, 0x36, 0x37})

STAFF_ITEM_IDS = frozenset({
    0x4B, 0x4C, 0x4D, 0x4E, 0x4F, 0x50, 0x51,
    0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 
    0x59, 0x8C})

# Palette mapping tables
PALETTE_CLASS_TABLE_PTR_OFF = 0x575B4  # ROM offset of pointer to palette class table
PALETTE_INDEX_TABLE_PTR_OFF = 0x57394  # ROM offset of pointer to palette index table
PALETTE_ENTRY_SIZE = 7
PALETTE_TABLE_ADDR = 0x08EF8004  # 16-byte entries: [GBA ptr, 3-char name, 9 pad]
PALETTE_INTERLEAVE_COUNT = 5  # PLAYER, ENEMY, NPC, OTHER, LINK
PALETTE_COLORS = 16
PALETTE_SUB_SIZE = PALETTE_COLORS * 2  # 32 bytes per sub-palette
PALETTE_SET_SIZE = PALETTE_INTERLEAVE_COUNT * PALETTE_SUB_SIZE  # 160 bytes total


def lz77_decompress(data: bytearray, offset: int) -> Optional[bytearray]:
    if offset + 4 > len(data) or data[offset] != 0x10:
        return None
    decomp_size = data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16)
    result = bytearray()
    pos = offset + 4
    while len(result) < decomp_size:
        if pos >= len(data):
            break
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(result) >= decomp_size:
                break
            if pos >= len(data):
                break
            if flags & (0x80 >> bit):
                result.append(data[pos])
                pos += 1
            else:
                if pos + 2 > len(data):
                    break
                block = data[pos] | (data[pos+1] << 8)
                pos += 2
                disp = block & 0x0FFF
                n = ((block >> 12) & 0xF) + 3
                for _ in range(n):
                    if len(result) >= decomp_size:
                        break
                    copy_pos = len(result) - disp - 1
                    if copy_pos < 0:
                        break
                    result.append(result[copy_pos])
    return result[:decomp_size]


def lz77_compressed_size(data: bytearray, offset: int) -> int:
    """Return the number of compressed bytes consumed starting at *offset*.
    Returns 0 if the data doesn't start with a valid LZ77 header."""
    if offset + 4 > len(data) or data[offset] != 0x10:
        return 0
    decomp_size = data[offset+1] | (data[offset+2] << 8) | (data[offset+3] << 16)
    result_len = 0
    pos = offset + 4
    while result_len < decomp_size:
        if pos >= len(data):
            return pos - offset
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if result_len >= decomp_size:
                return pos - offset
            if pos >= len(data):
                return pos - offset
            if flags & (0x80 >> bit):
                result_len += 1
                pos += 1
            else:
                if pos + 2 > len(data):
                    return pos - offset
                pos += 2
                block = data[pos - 2] | (data[pos - 1] << 8)
                disp = block & 0x0FFF
                n = ((block >> 12) & 0xF) + 3
                result_len += n
    return pos - offset


def lz77_compress(data: bytearray) -> bytearray:
    n = len(data)
    header = bytearray([0x10, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF])
    result = bytearray()
    pos = 0
    while pos < n:
        flags_byte_pos = len(result)
        result.append(0)
        for bit in range(8):
            if pos >= n:
                result[flags_byte_pos] |= (0x80 >> bit)
                continue
            best_disp = 0
            best_len = 0
            max_len = min(n - pos, 18)
            search_start = max(0, pos - 4096)
            for search_pos in range(search_start, pos):
                match_len = 0
                while match_len < max_len and data[search_pos + match_len] == data[pos + match_len]:
                    match_len += 1
                if match_len > best_len:
                    best_len = match_len
                    best_disp = pos - search_pos - 1
                    if best_len == max_len:
                        break
            if best_len >= 3:
                block = ((best_len - 3) << 12) | best_disp
                result.extend([block & 0xFF, (block >> 8) & 0xFF])
                pos += best_len
            else:
                result[flags_byte_pos] |= (0x80 >> bit)
                result.append(data[pos])
                pos += 1
    return header + result


def pal15_to_rgb(c: int) -> tuple:
    return ((c & 0x1F) * 8, ((c >> 5) & 0x1F) * 8, ((c >> 10) & 0x1F) * 8)


def rgb_to_pal15(r: int, g: int, b: int) -> int:
    return (min(r // 8, 31)) | (min(g // 8, 31) << 5) | (min(b // 8, 31) << 10)


def color_distance(c1: int, c2: int) -> float:
    r1, g1, b1 = pal15_to_rgb(c1)
    r2, g2, b2 = pal15_to_rgb(c2)
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    return (2 * dr * dr + 4 * dg * dg + 3 * db * db) ** 0.5


def read_palette_set(rom: ROM, palette_id: int) -> Optional[bytearray]:
    """Read a 5-palette set (160 bytes) by palette ID. Returns None if invalid."""
    table_off = rom_offset(PALETTE_TABLE_ADDR) + palette_id * 16
    if table_off + 16 > len(rom.data):
        return None
    ptr = _U32.unpack_from(rom.data, table_off)[0]
    if not (0x08000000 <= ptr <= 0x09000000):
        return None
    data_off = ptr - ROM_BASE
    decomp = lz77_decompress(rom.data, data_off)
    if decomp is None or len(decomp) != PALETTE_SET_SIZE:
        return None
    return decomp


def deinterleave_palette(data: bytearray, slot: int) -> bytearray:
    """Extract one sub-palette (32 bytes, 16 colors) from the interleaved set.
    slot: 0=PLAYER, 1=ENEMY, 2=NPC, 3=OTHER, 4=LINK."""
    result = bytearray(PALETTE_SUB_SIZE)
    for i in range(PALETTE_COLORS):
        src_off = i * PALETTE_INTERLEAVE_COUNT * 2 + slot * 2
        result[i * 2] = data[src_off]
        result[i * 2 + 1] = data[src_off + 1]
    return result


def interleave_palettes(subs: list) -> bytearray:
    """Interleave 5 sub-palettes back into one 160-byte set."""
    result = bytearray(PALETTE_SET_SIZE)
    for slot, sub in enumerate(subs):
        for i in range(PALETTE_COLORS):
            dst_off = i * PALETTE_INTERLEAVE_COUNT * 2 + slot * 2
            result[dst_off] = sub[i * 2]
            result[dst_off + 1] = sub[i * 2 + 1]
    return result


_MAX_ROM_SIZE = 32 * 1024 * 1024  # 32 MB — maximum GBA ROM size


def _cleanup_stale_palette_entries(rom: ROM) -> None:
    """Zero out palette entries with non-4-byte-aligned data pointers."""
    table_off = rom_offset(PALETTE_TABLE_ADDR)
    for pid in range(1, 256):
        off = table_off + pid * 16
        if off + 16 > len(rom.data):
            break
        ptr = _U32.unpack_from(rom.data, off)[0]
        if ptr != 0 and ptr % 4 != 0:
            for i in range(16):
                rom.data[off + i] = 0


def _find_next_palette_id(rom: ROM) -> int:
    """Find the next unused palette ID (starting from 1)."""
    _cleanup_stale_palette_entries(rom)
    table_off = rom_offset(PALETTE_TABLE_ADDR)
    for pid in range(1, 256):
        off = table_off + pid * 16
        if off + 4 > len(rom.data):
            break
        ptr = _U32.unpack_from(rom.data, off)[0]
        if ptr == 0:
            return pid
    return -1


_GBA_ROM_16MB = 16 * 1024 * 1024   # 16 MB — GBA ROM address space boundary

# Running write pointer for palette data written into free space within the
# original 16 MB ROM.  Initialized lazily on first use.
_palette_write_ptr = None


def reset_palette_write_ptr():
    """Reset the palette write pointer.  Call at the start of each run."""
    global _palette_write_ptr
    _palette_write_ptr = None


class _PaletteAllocator:
    """Bump allocator that carves palette data from free ROM blocks."""

    def __init__(self, rom: ROM):
        PAL_REGION_START = 0x00EF8000
        PAL_REGION_END   = 0x00F00000
        MIN_BLOCK = 64
        blocks = []
        block_start = None
        for i in range(min(len(rom.data), _GBA_ROM_16MB)):
            b = rom.data[i]
            if b == 0x00:
                if block_start is None:
                    block_start = i
            else:
                if block_start is not None:
                    size = i - block_start
                    if size >= MIN_BLOCK and not (PAL_REGION_START <= block_start < PAL_REGION_END):
                        blocks.append((block_start, size))
                    block_start = None
        if block_start is not None:
            size = len(rom.data) - block_start
            if size >= MIN_BLOCK and not (PAL_REGION_START <= block_start < PAL_REGION_END):
                blocks.append((block_start, size))
        # Sort largest-first so we use the biggest block first
        blocks.sort(key=lambda x: -x[1])
        self._blocks = blocks
        self._idx = 0    # current block index
        self._pos = 0    # offset within current block

    def alloc(self, nbytes: int) -> int:
        """Return a GBA address for *nbytes* bytes, or -1 if no space."""
        while self._idx < len(self._blocks):
            base, size = self._blocks[self._idx]
            aligned = (nbytes + 3) & ~3
            if self._pos + aligned <= size:
                addr = base + self._pos
                self._pos += aligned
                return ROM_BASE + addr
            self._idx += 1
            self._pos = 0
        return -1


_palette_allocator = None


def get_palette_allocator(rom: ROM):
    """Return (or create) the palette allocator for this ROM."""
    global _palette_allocator
    if _palette_allocator is None:
        _palette_allocator = _PaletteAllocator(rom)
    return _palette_allocator


def reset_palette_allocator():
    """Reset the palette allocator.  Call at the start of each run."""
    global _palette_allocator
    _palette_allocator = None


def write_palette_set(rom: ROM, palette_data: bytearray, name: str = '') -> int:
    """Write a new 5-palette set into free space within the 16 MB ROM
    boundary.  Returns palette ID or -1."""
    global _palette_write_ptr
    if len(palette_data) != PALETTE_SET_SIZE:
        return -1

    compressed = lz77_compress(palette_data)
    needed = len(compressed)
    aligned = (needed + 3) & ~3  # 4-byte alignment

    pid = _find_next_palette_id(rom)
    if pid < 0:
        return -1

    # Initialize the write pointer on first use
    if _palette_write_ptr is None:
        _palette_write_ptr = _find_palette_free_space(rom)
        if _palette_write_ptr < 0:
            return -1  # no free space available

    write_start = _palette_write_ptr
    end = write_start + aligned
    if end > _GBA_ROM_16MB:
        return -1  # out of space within 16 MB

    # Ensure ROM data is large enough (pad with zeros if needed)
    if end > len(rom.data):
        rom.data.extend(b'\x00' * (end - len(rom.data)))

    rom.data[write_start:write_start + aligned] = (
        compressed + b'\x00' * (aligned - needed))
    _palette_write_ptr = end

    data_gba = ROM_BASE + write_start

    # Write palette table entry
    table_off = rom_offset(PALETTE_TABLE_ADDR) + pid * 16
    _U32.pack_into(rom.data, table_off, data_gba)
    name_bytes = name.encode('ascii', errors='replace')[:3].ljust(3, b'\x00')
    rom.data[table_off + 4:table_off + 7] = name_bytes
    for i in range(7, 16):
        rom.data[table_off + i] = 0

    return pid


def swap_portrait_entries(rom: ROM, pid_a: int, pid_b: int) -> bool:
    """Swap portrait table data between two PIDs. Returns True on success."""
    slot_a = PID_TO_PORTRAIT_SLOT.get(pid_a)
    slot_b = PID_TO_PORTRAIT_SLOT.get(pid_b)
    if slot_a is None or slot_b is None:
        return False
    base_off = rom_offset(PORTRAIT_TABLE_ADDR)
    off_a = base_off + slot_a * PORTRAIT_ENTRY_SIZE
    off_b = base_off + slot_b * PORTRAIT_ENTRY_SIZE
    if off_a + PORTRAIT_ENTRY_SIZE > len(rom.data) or off_b + PORTRAIT_ENTRY_SIZE > len(rom.data):
        return False
    tmp = bytearray(rom.data[off_a:off_a + PORTRAIT_ENTRY_SIZE])
    rom.data[off_a:off_a + PORTRAIT_ENTRY_SIZE] = rom.data[off_b:off_b + PORTRAIT_ENTRY_SIZE]
    rom.data[off_b:off_b + PORTRAIT_ENTRY_SIZE] = tmp
    return True


_EVENT_CMDS_WITH_UD = (0x40, 0x41, 0x42, 0x43, 0x54, 0x8C, 0xA8, 0xAA, 0xC4)


class ItemData:
    __slots__ = (
        'item_id', 'offset',
        'name_text_id', 'desc_text_id', 'use_desc_text_id',
        'number', 'weapon_type', 'attributes',
        'p_stat_bonuses', 'p_effectiveness',
        'max_uses', 'might', 'hit', 'weight', 'crit',
        'encoded_range', 'min_range', 'max_range',
        'cost_per_use', 'weapon_rank', 'icon_id',
        'use_effect_id', 'weapon_effect_id', 'weapon_exp',
    )

    def __init__(self, rom: ROM, item_id: int):
        offset = rom_offset(ITEM_TABLE_ADDR) + item_id * ITEM_DATA_SIZE
        raw = rom.read(offset, ITEM_DATA_SIZE)
        self.item_id = item_id
        self.offset = offset
        self.name_text_id, self.desc_text_id = struct.unpack_from('<HH', raw, 0)
        self.use_desc_text_id, = _U16.unpack_from(raw, 4)
        self.number = raw[6]
        self.weapon_type = raw[7]
        self.attributes, = _U32.unpack_from(raw, 8)
        self.p_stat_bonuses, = _U32.unpack_from(raw, 0x0C)
        self.p_effectiveness, = _U32.unpack_from(raw, 0x10)
        self.max_uses = raw[0x14]
        self.might = raw[0x15]
        self.hit = raw[0x16]
        self.weight = raw[0x17]
        self.crit = raw[0x18]
        self.encoded_range = raw[0x19]
        self.min_range = self.encoded_range & 0xF
        self.max_range = (self.encoded_range >> 4) & 0xF
        self.cost_per_use, = _U16.unpack_from(raw, 0x1A)
        self.weapon_rank = raw[0x1C]
        self.icon_id = raw[0x1D]
        self.use_effect_id = raw[0x1E]
        self.weapon_effect_id = raw[0x1F]
        self.weapon_exp = raw[0x20]

    def is_weapon(self) -> bool:
        if self.weapon_type == 4:
            return self.max_uses > 0
        return self.weapon_type <= 7 and self.max_uses > 0 and self.might > 0

    def write(self, rom: ROM) -> None:
        """Minimal write — only patches the offset for ItemData changes."""
        buf = bytearray(ITEM_DATA_SIZE)
        _U16.pack_into(buf, 0, self.name_text_id)
        _U16.pack_into(buf, 2, self.desc_text_id)
        _U16.pack_into(buf, 4, self.use_desc_text_id)
        buf[6] = self.number
        buf[7] = self.weapon_type
        _U32.pack_into(buf, 8, self.attributes)
        _U32.pack_into(buf, 0x0C, self.p_stat_bonuses)
        _U32.pack_into(buf, 0x10, self.p_effectiveness)
        buf[0x14] = self.max_uses
        buf[0x15] = self.might
        buf[0x16] = self.hit
        buf[0x17] = self.weight
        buf[0x18] = self.crit
        buf[0x19] = self.encoded_range
        _U16.pack_into(buf, 0x1A, self.cost_per_use)
        buf[0x1C] = self.weapon_rank
        buf[0x1D] = self.icon_id
        buf[0x1E] = self.use_effect_id
        buf[0x1F] = self.weapon_effect_id
        buf[0x20] = self.weapon_exp
        rom.write(self.offset, buf)


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
    0x65: 'Knight Crest', 0x66: "Orion's Bolt", 0x67: 'Elysian Whip',
    0x68: 'Guiding Ring', 0x69: 'Chest Key',
    0x6A: 'Door Key', 0x6B: 'Lockpick', 0x6C: 'Vulnerary',
    0x6D: 'Elixir', 0x6E: 'Pure Water', 0x6F: 'Antitoxin',
    0x70: 'Torch (Item)', 0x71: 'Fili Shield',
    0x72: 'Member Card', 0x73: 'Silver Card',
    0x74: 'White Gem', 0x75: 'Blue Gem',
    0x76: 'Red Gem', 0x77: 'Gold',
    0x78: 'Reginleif', 0x79: 'Chest Key (5 uses)',
    0x7A: 'Mine', 0x7B: 'Light Rune',
    0x7C: 'Hoplon Guard', 0x7D: "Fila's Might",
    0x7E: "Ninis's Grace", 0x7F: "Thor's Ire",
    0x80: "Set's Litany",     0x81: 'Shadowkiller', 0x82: 'Bright Lance',
    0x83: 'Fiendcleaver',     0x84: 'Beacon Bow',
    0x85: 'Sieglinde', 0x86: 'Battle Axe',
    0x87: 'Ivaldi', 0x88: 'Master Seal',
    0x89: "Metis's Tome", 0x8A: 'Dummy',
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


def build_weapon_pools(rom: ROM, include_ballista: bool = False) -> dict:
    excluded = MONSTER_BLOCKED_ITEM_IDS | STORY_EXCLUSIVE_ITEM_IDS
    if not include_ballista:
        excluded |= BALLISTA_ITEM_IDS
    pools = {t: [] for t in range(8)}
    item_table_off = rom_offset(ITEM_TABLE_ADDR)
    data_len = len(rom.data)
    for item_id in range(256):
        off = item_table_off + item_id * ITEM_DATA_SIZE
        if off + ITEM_DATA_SIZE > data_len:
            break
        raw = rom.data[off:off+ITEM_DATA_SIZE]
        stored_id = raw[6]
        if stored_id != item_id or stored_id in excluded:
            continue
        wep_type = raw[7]
        if wep_type <= 7 and raw[0x14] > 0 and raw[0x19] > 0:
            if wep_type != 4 and raw[0x15] == 0:
                continue
            pools[wep_type].append((stored_id, raw[0x1C]))
    return pools
