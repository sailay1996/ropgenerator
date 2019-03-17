# -*- coding:utf-8 -*- 
# Scanner module: Scan binaries to get useful infos for exploits 

import subprocess
import mmap
import re

import lief

g_binary_lief = None
g_binary_name = None
g_offset = 0

def init_scanner(filename):
    global g_binary_lief
    global g_binary_name
    
    g_binary_lief = None
    g_binary_name = None
    g_offset = 0
    g_binary_lief = lief.parse(filename)
    if( not g_binary_lief is None ):
        g_binary_name = filename

def set_offset(off):
    global g_offset
    g_offset = off

# Return a dict
# (func_name: func_address)
def get_pltgot_functions():
    global g_offset
    global g_binary_lief
    res = {}
    for rel in g_binary_lief.pltgot_relocations:
        if( rel.has_symbol ):
            res[rel.symbol.name] = rel.address+g_offset
    return res

# Return a dict
# (func_name: func_address)
def get_symtab_functions():
    global g_offset
    global g_binary_lief
    res = {}
    for s in g_binary_lief.symbols:
        if( s.is_function and s.value != 0):
            res[s.name] = s.value+g_offset
    return res

# Returns the address of a section
def get_section_address(section):
    global g_offset
    global g_binary_lief
    if( not g_binary_lief.has_section(section) ):
        return None
    return g_binary_lief.get_section(section).virtual_address
    
# Returns the address of a function as a pair
# (func_name, address)
def get_function_address(func_name){
    pltgot_funcs = get_pltgot_functions
    symtab_funcs = get_symtab_functions()
    if( func_name in pltgot_funcs ):
        return (func_name, pltgot_funcs[func_name])
    if( func_name in symtab_funcs ):
        return (func_name, symtab_funcs[func_name])
    return (None, None)
}

def verify_bad_bytes(addr, bad_bytes):
    addrBytes = re.findall('..',('{:'+'{:02d}'\
        .format(Arch.currentArch.octets)+'x}').format(addr))
    for byte in bad_bytes:
        if( byte in addrBytes):
            return False
    return True
    
# Find a string chnk by chunk in the binary
def find_bytes(byte_string, bad_bytes = [], add_null=False ):
    """
    Parameters
    ----------
    badbytes : bad bytes for substrings addresses
    add_null : if True then add terminaison null bytes in the end of the substrings 
    
    Example: 
        byte_string = 'abc' then result is the address of a string 'abc\x00'
        or a list of addresses s.t elements form 'abc' like 'ab\x00' 'c\x00' 
    """
    global g_offset
    global g_binary_lief
    
    def _find_substr(m,string):
        if( not string ):
            return [-1,0]
        # Initialize
        offset = -1
        index = len(string)
        substring = string
        # Search biggest substring 
        while( offset == -1 ):
            if( len(substring) <= 0 ):
                return [-1,0]
            offset = m.find(substring)
            if( offset != -1 ):
                return [offset, index]
            else:
                substring = substring[:-1]
            index = index -1
    
    def _find_substr_add_null(m, string):
        if( not string ):
            return [-1,0]
        # Initialize
        offset = -1
        index = len(string)
        last_is_null = (string[-1] == '\x00')
        if( not last_is_null ):
            substring = string + '\x00'
        else:
            substring = string
        # Search biggest substring 
        while( offset == -1 ):
            if( len(substring) <= 0 ):
                return [-1,0]
            offset = m.find(substring)
            if( offset != -1 ):
                return [offset, index]
            else:
                substring = substring[:-2]
                if( not substring ):
                    return [-1,0]
                last_is_null = (substring[-1] == '\x00')    
                if( not last_is_null ):
                    substring = substring + '\x00'
            index = index -1
                
    # Getting all readable segments
    segments = []
    for segment in g_binary_lief.segments:
        # Check flags (depends on binary format)
        if( curr_bin_type() == BinType.ELF32 or
            curr_bin_type() == BinType.ELF64):
            if( not ((segment.flags & lief.ELF.SEGMENT_FLAGS.R != 0 ) &&
                    (segment.flags & lief.ELF.SEGMENT_FLAGS.W == 0 ))):
                continue
        data = segment.content
        addr = segment.virtual_address + offset
        segments.append((data, addr))
    if( not segments ):
            return []
            
    # Getting bytes as substrings  
    res = []
    substring = str(byte_string)
    while( substring ):
        found = False
        segment_num = 0
        (m, segment_addr) = segments[segment_num]
        start = 0
        end = len(m)-1
        ## 
        m_tmp = str(m)
        segment_changed = False
        while( not found ):
            if( not m_tmp ):
                segment_changed = True
                segment_num += 1
                
            if( segment_num >= len(segments)):
                # Coudln't find substring in any segments 
                return []
                
            if( segment_changed ):
                (m, segment_addr) = segments[segment_num]
                start = 0
                end = len(m)-1
                m_tmp = str(m)
                
            # Get substring address 
            if( add_null ):
                (offset, index ) = _find_substr_add_null(m_tmp, substring)
            else:
                (offset, index ) = _find_substr(m_tmp, substring)
            # We didn't find any match, try next segment 
            if( index == 0 ):
                segment_num += 1
                segment_changed = True
            else:
                segment_changed = False
            # Check for bad bytes in the address 
            if( not segment_changed ):
                if( verify_bad_bytes(start+offset, bad_bytes)):
                    found = True
                else:
                    m_tmp = m_tmp[offset:]
                
        # We add the best substring we found
        if( add_null and substring[:index] != '\x00'):
            res.append([offset+segment_addr+_offset,substring[:index]+"\x00"])
        else:
            res.append([offset+segment_addr+_offset,substring[:index]])
        
        # And continue...
        substring = substring[index:]
        segment_num = 0
    
    return res
