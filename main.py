#!/usr/bin/env python3

# Software License Agreement (BSD License)
#
# Copyright (c) 2020, Ben Schattinger
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#      * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#      * Neither the name of the Southwest Research Institute, nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Strings embedded in this file may not be under this license.


import re
import sys
from itertools import islice
from typing import Callable

from bs4 import BeautifulSoup

SIM_LEFT_PAREN = '❨'
SIM_COMMA = 'ꓹ'
STARTS_WITH_COMMENT = re.compile(r'^\w+:', re.MULTILINE)
ALL_STRUCTS = re.compile(r'struct\s+(\w+)\s*{[^}]+}\s*;')
ALL_TYPEDEF_STRUCTS = re.compile(r'typedef\s+(?:struct|enum|union)\s*{[^}]+}\s*(\w+)\s*;')
SIMPLE_TYPEDEF = re.compile(r'typedef\s+(?!struct|enum|union)([^;])+;')
FRONT_TYPES = ['MP_GRP_POS_INFO', 'MP_P_VAR_BUFF', 'MP_ALARM_DATA', 'MP_MOV_CTRL_DATA', 'MP_JOB_POS_DATA',
               'MP_INTP_TYPE', 'MP_POS', 'MP_POS_TAG', 'MP_TRQLMT_RANGE', 'dirent', 'DIR']
FRONT_TYPES_RE = re.compile(
    r'typedef\s+(?:struct|enum|union)\s*{[^}]+}\s*(?:' + '|'.join(FRONT_TYPES) + r')\s*;')
DIRENT = re.compile(r'struct\s+dirent\s*{[^}]+}\s*;')
REMOVE_NOTES = re.compile(r'\[[^[]+]')
FIX_DEFINES = re.compile(r'#define *([^\s(]+)\s*([^;\n]*);?')
FIX_DEFINE_PAREN = re.compile(r'#define (\w+) \((\d+)\)')
FIX_MISSING_COMMA = re.compile(r'((?:const\s+)?\w+\s*\*\s*\w+)\s+((?:const\s+)?\w+\s*\*)')
FIX_RESERVED = re.compile(r'reserved (\d)')
FIX_MISSING_BRACE = re.compile(r'typedef\s+struct\s+([^{\s])')
FIX_STRUCT_COMMA = re.compile(r'typedef\s+struct\s*{\s*int\s+id,')
FIX_TRAILING_COMMA = re.compile(r'[;,]\s+\)')
FIX_APPINFO = re.compile(r'(CHAR\s+reserved\[36];\s*)};')
RENAME_MP_RS_SEND = re.compile(r'int\s+mpRsClose(\([^)]+buf_len\s+\);)')
RENAME_CART_POS_EX = re.compile(r'LONG\s+mpGetCartPos\s+(\(\s+MP_CARTPOS_EX[^)]+\);)')
REMOVE_MP_COORD = re.compile(r'typedef\s+struct\s*{[^}]+}\s*MP_COORD\s*;')
REMOVE_MP_CLOSE = re.compile(r'LONG\s+mpClose\([^)]+\)\s*;')


def nth(iterable, n, default=None):
    """Returns the 0-indexed nth item or a default value"""
    return next(islice(iterable, n, None), default)


def remove_prefix(text, prefix, default=''):
    if text.startswith(prefix):
        return text[len(prefix):]
    return default


def find_syntax_headers(document: BeautifulSoup):
    return filter(lambda item: item.text == 'Syntax', document.find_all('b'))


def has_child_of_type(root, tag: str) -> bool:
    if root.name == tag:
        return True
    if hasattr(root, 'children'):
        return next(filter(lambda child: has_child_of_type(child, tag), root.children), None) is not None
    return False


def index(l: [str], f: Callable[[str], bool]) -> int:
    return next((i for i, v in enumerate(iter(l)) if f(v)), -1)


def dedup_lines(lines: [str]) -> [str]:
    new_list = []
    seen = set()
    for item in lines:
        if item not in seen:
            new_list.append(item)
            seen.add(item)
    return new_list


def remove_duplicate_matches(text: str, regex) -> str:
    structs = {}
    for match in regex.finditer(text):
        name = match.group(1)
        structs[name] = structs.get(name, 0) + 1
    for name, occurrences in structs.items():
        if occurrences > 1:
            spans = []
            for match in regex.finditer(text):
                if match.group(1) == name:
                    spans.append((match.start(), match.end()))
            for i in range(len(spans) - 1, 0, -1):
                text = text[:spans[i][0]] + text[spans[i][1]:]
    return text


def dedup_structs(text: str):
    text = remove_duplicate_matches(text, ALL_STRUCTS)
    text = remove_duplicate_matches(text, ALL_TYPEDEF_STRUCTS)
    return text


def move_to_top(lines: [str], matches: Callable[[str], bool]):
    for i in range(len(lines) - 1, -1, -1):
        if matches(lines[i]):
            lines.insert(0, lines.pop(i))


def move_typedefs(text: str) -> str:
    for match in FRONT_TYPES_RE.finditer(text):
        text = match.group(0) + text[:match.start()] + text[match.end():]
    for match in DIRENT.finditer(text):
        text = match.group(0) + text[:match.start()] + text[match.end():]
    for match in SIMPLE_TYPEDEF.finditer(text):
        text = match.group(0) + text[:match.start()] + text[match.end():]
    return text


def fix_defines(text: str) -> str:
    text = FIX_DEFINES.sub(r'\n#define \1 \2', text)
    text = FIX_DEFINE_PAREN.sub(r'#define \1 \2', text)
    lines = text.splitlines()
    move_to_top(lines, lambda line: line.startswith('#define'))

    # remove duplicates
    last_define = len(lines) - index(lines[::-1], lambda x: x.startswith('#define'))

    deduplicated = dedup_lines(lines[:last_define])
    lines[:len(deduplicated)] = deduplicated
    del lines[len(deduplicated):last_define]

    return '\n'.join(lines)


def fix_weirdness(text: str) -> str:
    text = move_typedefs(text)
    text = fix_defines(text)
    text = text.replace('MAX_JOB_MOV_POS _NUM', 'MAX_JOB_MOV_POS_NUM')
    text = text.replace('_ ', '_')
    text = text.replace('structLONG', 'struct { LONG')
    text = text.replace('sTool/No', 'sToolNo')
    text = text.replace('*.', '*')
    text = text.replace('MS_COORD', 'MP_COORD')
    text = text.replace('ox, py, pz', 'px, py, pz')
    text = FIX_MISSING_COMMA.sub(r'\1, \2', text)
    text = FIX_RESERVED.sub(r'reserved\1', text)
    text = FIX_MISSING_BRACE.sub(r'typedef struct { \1', text)
    text = FIX_STRUCT_COMMA.sub(r'typedef struct { int id;', text)
    text = FIX_TRAILING_COMMA.sub(r')', text)
    text = FIX_APPINFO.sub(r'\1} MP_APPINFO_SEND_DATA;', text)
    text = RENAME_MP_RS_SEND.sub(r'int mpRsSend\1', text)
    text = RENAME_CART_POS_EX.sub(r'LONG mpGetCartPosEx\1', text)
    text = REMOVE_MP_COORD.sub(r'', text)
    text = REMOVE_MP_CLOSE.sub(r'', text)
    text = dedup_structs(text)

    return text


def parse_string(new_text: str, text: str, remove_notes=True) -> str:
    new_text = new_text.replace('Typedef', 'typedef')
    new_text_stripped = new_text.strip()
    if new_text_stripped.startswith('#'):
        new_text += '\n'
        text += new_text
    elif new_text_stripped.startswith('/*'):
        text_without_trailing = text.rstrip()[:-1]
        nl = text_without_trailing.rfind(',') + 1
        if nl == 0:
            nl = text_without_trailing.rfind('(') + 1
        if nl == 0:
            closing_comment = text_without_trailing.rfind('*/')
            if closing_comment >= 0:
                nl = closing_comment + 2
        new_text = new_text.replace('/*', '/**').replace('(', SIM_LEFT_PAREN).replace(',', SIM_COMMA)
        text = text[:nl] + new_text + text[nl:]
    else:
        new_text = new_text.replace('(', '(\n')
        text += REMOVE_NOTES.sub('', new_text) if remove_notes else new_text
    return text


def main():
    if len(sys.argv) != 2:
        print('You must specify a file', file=sys.stderr)
        exit(1)

    document = BeautifulSoup(open(sys.argv[1]), 'html.parser')
    print(r"""#pragma once

#include <endian.h>
#include <stddef.h>
#include <stdint.h>
#include <ctype.h>
#include <locale.h>
#include <math.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#define CONST const
#define UNIT UINT
#define ERROR -1
#define OK 0
#define NG 1
#define TRUE 1
#define FALSE 0
#define ON 1
#define OFF 0
#define AF_INET 2
#define SOCK_STREAM 1
#define INADDR_ANY 0
#define SOMAXCONN 5
#define TCP_NODELAY 1
#define TRQ_NEWTON_METER 1
#define MP_INC_PULSE_DTYPE 0x80
#define MP_INTERPOLATION_CLK 1
#define FOREVER while(1)
#define MP_GRP_NUM 32
#define MP_GRP_AXES_NUM 8
#define MAX_TOOL_NAME 8
#define S_VAR_SIZE 32
#define TRANS_FILE_LEN (32 + 1 + 3)
#define MP_LIST_DATA_SIZE 1000 // Size of work area used for reading
#define OFFLINE_SYSTEM_VERSION_SIZE 22
#define TID_SELF 0
#define MP_STACK_SIZE 0
#define mpExitUsrRoot _mpExitUsrRoot()
#define mpDeleteSelf mpDeleteTask(TID_SELF)
typedef char CHAR;
typedef unsigned char UCHAR;
typedef short SHORT;
typedef unsigned short USHORT;
typedef int INT;
typedef int BOOL;
typedef unsigned int UINT;
typedef long LONG;
typedef unsigned long ULONG;
typedef int8_t INT8;
typedef int16_t INT16;
typedef int32_t INT32;
typedef int64_t INT64;
typedef uint8_t UINT8;
typedef uint16_t UINT16;
typedef uint32_t UINT32;
typedef uint64_t UINT64;
typedef UINT socklen_t;
typedef INT MP_WDG_HANDLE;
typedef INT MP_SVS_HANDLE;
typedef INT STATUS;
typedef ULONG CTRLG_T;
typedef ULONG EXEJT_T;
typedef ULONG TIME;
typedef LONG fd_mask;
typedef void *SEM_ID;
typedef void *MSG_Q_ID;
typedef enum {
    SEM_Q_FIFO,
    SEM_Q_PRIORITY
} SEM_B_OPTIONS;
typedef enum {
    SEM_EMPTY,
    SEM_FULL
} SEM_B_STATE;
typedef enum {
    MP_PRI_IO_CLK_TAKE,
    MP_PRI_IP_CLK_TAKE,
    MP_PRI_TIME_CRITICAL,
    MP_PRI_TIME_NORMAL
} MP_PRIORITY;
typedef enum {
    /** Pulse Not used */
    MP_PULSE_TYPE,
    /** Angle Not used */
    MP_ANGLE_TYPE,
    /** Base coordinate system Not used */
    MP_BASE_TYPE,
    /** Robot System Not used */
    MP_ROBOT_TYPE,
    /** User coordinate system */
    MP_USER_TYPE
} MP_COORD_TYPE;
typedef enum {
    MP_R1_GID,
    MP_R2_GID,
    MP_R3_GID,
    MP_R4_GID,
    MP_R5_GID,
    MP_R6_GID,
    MP_R7_GID,
    MP_R8_GID,
    MP_B1_GID,
    MP_B2_GID,
    MP_B3_GID,
    MP_B4_GID,
    MP_B5_GID,
    MP_B6_GID,
    MP_B7_GID,
    MP_B8_GID,
    MP_S1_GID,
    MP_S2_GID,
    MP_S3_GID,
    MP_S4_GID,
    MP_S5_GID,
    MP_S6_GID,
    MP_S7_GID,
    MP_S8_GID,
    MP_S9_GID,
    MP_S10_GID,
    MP_S11_GID,
    MP_S12_GID,
    MP_S13_GID,
    MP_S14_GID,
    MP_S15_GID,
    MP_S16_GID,
    MP_S17_GID,
    MP_S18_GID,
    MP_S19_GID,
    MP_S20_GID,
    MP_S21_GID,
    MP_S22_GID,
    MP_S23_GID,
    MP_S24_GID
} MP_GRP_ID_TYPE;
typedef enum {
    mpRsDataBit_7,
    mpRsDataBit_8
} MP_RS_DATA_BIT;
typedef enum {
    mpRsStopBit_one,
    mpRsStopBit_1point5,
    mpRsStopBit_two
} MP_RS_STOP_BIT;
typedef enum {
    mpRsParity_none,
    mpRsParity_odd,
    mpRsParity_even
} MP_RS_PARITY;
typedef enum {
    mpRsBaudrate_150,
    mpRsBaudrate_300,
    mpRsBaudrate_600,
    mpRsBaudrate_1200,
    mpRsBaudrate_2400,
    mpRsBaudrate_4800,
    mpRsBaudrate_9600,
    mpRsBaudrate_19200
} MP_RS_BAUDRATE;
#define FD_SETSIZE 2048
#define NFDBITS 32
#define howmany(x, y) ((unsigned int)(((x) + ((y)-1))) / (unsigned int)(y))
typedef struct fd_set {
    fd_mask fds_bits[howmany(FD_SETSIZE, NFDBITS)];
} fd_set;
#define FD_ZERO(p) memset((char *)(p), '\0', sizeof(*(p)))
#define FD_SET(n, p) ((p)->fds_bits[(n) / NFDBITS] |= (1 << ((n) % NFDBITS)))
#define FD_ISSET(n, p) ((p)->fds_bits[(n) / NFDBITS] & (1 << ((n) % NFDBITS)))
typedef struct {
    /** S_VAR_SIZE (32 characters)+null character\0 */
    UCHAR ucValue[S_VAR_SIZE+1];
    UCHAR reserved[3];
} MP_SVAR_RECV_INFO;
typedef struct {
    /** Variable type (Only MP_RESTYPE_VAR_S is valid) */
    USHORT usType;
    /** Variable index */
    USHORT usIndex;
    /** S_VAR_SIZE (32 characters)+null character\0 */
    UCHAR ucValue[S_VAR_SIZE + 1];
    CHAR reserved[3];
} MP_SVAR_SEND_INFO;
typedef struct {
    /** The array storing the character string of the written file */
    UCHAR cFileName[TRANS_FILE_LEN + 1];
    CHAR reserved[3];
} MP_FILE_NAME_SEND_DATA;
typedef struct {
    /** main command */
    int main_comm;
    /** sub command */
    int sub_comm;
    /** task number of job in execution (0-15) */
    int exe_tsk;
    /** application number of execution control group */
    int exe_apl;
    /** text command data sent by SKILLSND */
    char cmd[256];
    /** for future addition (reserved) */
    int usr_opt;
} SYS2MP_SENS_MSG;
typedef struct {
    /** control group */
    CTRLG_T ctrl_grp;
    /** shift data */
    LONG val[MP_GRP_AXES_NUM];
} MP_SHIFT_VALUE_DATA;
typedef struct {
    MP_RS_DATA_BIT dataBit;
    MP_RS_STOP_BIT stopBit;
    MP_RS_PARITY parity;
    MP_RS_BAUDRATE baudRate;
} MP_RS_CONFIG;
typedef struct {
    /** Error number */
    USHORT err_no;
    /** Always 1 with the normal end */
    USHORT uIsEndFlag;
    /** The number of read job names */
    USHORT uListDataNum;
    /** Work area used for reading */
    UCHAR cListData[MP_LIST_DATA_SIZE];
    CHAR reserved[2];
} MP_GET_JOBLIST_RSP_DATA;
typedef struct {
    long vj;
    long v;
    long vr;
} MP_SPEED;
typedef struct {
    /** XYZ position (microns) */
    long x, y, z;
    /** Wrist angle (unit: 0.0001 deg) */
    long rx, ry, rz;
    /** Elbow angle (unit: 0.0001 deg) */
    long ex1, ex2;
} MP_COORD;
struct timeval {
    /** second */
    long tv_sec;
    /** micro second */
    long tv_usec;
};
struct in_addr {
    ULONG s_addr;
};
struct sockaddr {
    UCHAR sa_len;
    UCHAR sa_family;
    CHAR sa_data[14];
};
struct sockaddr_in {
    UCHAR sin_len;
    UCHAR sin_family;
    USHORT sin_port;
    struct in_addr sin_addr;
    CHAR sin_zero[8];
};
struct stat {
    /** device ID number */
    unsigned long st_dev;
    /** file serial number */
    unsigned long st_ino;
    /** file mode (see below) */
    int st_mode;
    /** number of links to file */
    unsigned long st_nlink;
    /** user ID of file's owner */
    unsigned short st_uid;
    /** group ID of file's group */
    unsigned short st_gid;
    /** device ID, only if special file */
    unsigned long st_rdev;
    /** size of file, in bytes */
    long long st_size;
    /** time of last access */
    TIME st_atime;
    /** time of last modification */
    TIME st_mtime;
    /** time of last change of file status */
    TIME st_ctime;
    long st_blksize;
    long st_blocks;
    /** file attribute byte (dosFs only) */
    unsigned char st_attrib;
    /** reserved for future use */
    int reserved1;
    /** reserved for future use */
    int reserved2;
    /** reserved for future use */
    int reserved3;
    /** reserved for future use */
    int reserved4;
    /** reserved for future use */
    int reserved5;
    /** reserved for future use */
    int reserved6;
};

/* File mode (st_mode) bit masks */
#define S_IFMT   0xf000 // file type field
#define S_IFIFO  0x1000 // fifo
#define S_IFCHR  0x2000 // character special
#define S_IFDIR  0x4000 // directory
#define S_IFBLK  0x6000 // block special
#define S_IFREG  0x8000 // regular
#define S_IFLNK  0xa000 // symbolic link
#define S_IFSOCK 0xc000 // socket
typedef void (*FUNCPTR)(int, int, int, int, int, int, int, int, int, int);
#define max(a,b) \
    ({ __typeof__ (a) _a = (a); \
    __typeof__ (b) _b = (b); \
    _a > _b ? _a : _b; })
#define min(a,b) \
    ({ __typeof__ (a) _a = (a); \
    __typeof__ (b) _b = (b); \
    _a < _b ? _a : _b; })
void _mpExitUsrRoot();
int abs(int x);
void mpFree(void *ptr);""")
    robot_name = str(document.body.find(string=lambda x: len(x.strip()))).split()[0]
    if robot_name == 'YRC1000' or robot_name == 'YRC1000micro':
        print("""#if !defined(YRC1000) && !defined(YRC1000u)
#error You must specify the robot type. This file only works with YRC1000 and YRC1000u controllers.
#endif""")
    else:
        print(f"""#ifndef {robot_name}
#error You must specify the robot type. This file only works with {robot_name} controllers.
#endif""")
    final_text = []
    for fn in document.find_all(string=re.compile(r'\s*(Syntax:|multiple control groups\)\.).*')):
        text = ''
        left_over = remove_prefix((fn.text if hasattr(fn, 'text') else str(fn)).strip(), 'Syntax:')

        ele = fn.next_sibling
        while ':' not in str(ele) and '\uf06e' not in str(ele) and not has_child_of_type(ele, 'b'):
            if ele.name == 'hr':
                ele = nth(ele.next_siblings, 7)
            new_text = left_over + (ele.text if hasattr(ele, 'text') else str(ele))
            if '<' in new_text:
                break
            left_over = ''
            comment_idx = new_text.find('/*')
            if comment_idx >= 0:
                text = parse_string(new_text[:comment_idx], text, remove_notes=False)
                if new_text.find('*/') < 0:
                    left_over = new_text[comment_idx:]
                else:
                    text = parse_string(new_text[comment_idx:], text, remove_notes=False)
            else:
                text = parse_string(new_text, text, remove_notes=False)
            ele = ele.next_sibling
            if nth(ele.next_siblings, 5).name == 'hr':
                ele = nth(ele.next_siblings, 5)
        if not text.strip().endswith(';'):
            text += ';'
        text = text.replace(SIM_LEFT_PAREN, '(').replace(SIM_COMMA, ',').replace('\u00a0', ' ')
        text = text.replace('attribute(expansion)', 'attribute (expansion)')
        if text not in final_text:
            final_text.append(text)
    final_text.append("""
typedef struct {
    /** Target control group which executes the increment value move */
    CTRLG_T ctrl_grp;
    /** Master side control group for coordinated (synchronized) operation */
    CTRLG_T m_ctrl_grp;
    /** Slave side control group for coordinated (synchronized) operation */
    CTRLG_T s_ctrl_grp;
    MP_GRP_POS_INFO grp_pos_info[MP_GRP_NUM];
} MP_EXPOS_DATA;""")
    final_text = '\n'.join(final_text)
    for fn in find_syntax_headers(document):
        text = ''

        ele = fn.next_sibling
        left_over = ''
        while '\uf06e' not in str(ele):
            new_text = left_over + (ele.text if hasattr(ele, 'text') else str(ele))
            if STARTS_WITH_COMMENT.search(new_text):
                break
            left_over = ''
            comment_idx = new_text.find('/*')
            if comment_idx >= 0:
                text = parse_string(new_text[:comment_idx], text)
                closing_comment = new_text.find('*/')
                if closing_comment < 0:
                    left_over = new_text[comment_idx:]
                else:
                    text = parse_string(new_text[comment_idx:closing_comment + 2], text)
                    text = parse_string(new_text[closing_comment + 2:], text)
            else:
                text = parse_string(new_text, text)
            ele = ele.next_sibling
        if not text.strip().endswith(';'):
            text += ';'
        text = text.replace(SIM_LEFT_PAREN, '(').replace(SIM_COMMA, ',').replace('\u00a0', ' ')
        final_text += text + '\n'
    print(fix_weirdness(final_text))
    print(r"""
#if BYTE_ORDER == BIG_ENDIAN
#ifndef FS100
#error Somehow we think that this controller is Big Endian?
#endif
#define mpHtonl(n) (n)
#define mpHtons(n) (n)
#define mpNtohl(n) (n)
#define mpNtohs(n) (n)
#else
#ifdef FS100
#error Somehow we think that this controller is Little Endian?
#endif
#define mpHtonl __builtin_bswap32
#define mpHtons __builtin_bswap16
#define mpNtohl __builtin_bswap32
#define mpNtohs __builtin_bswap16
#endif""")


if __name__ == '__main__':
    main()
