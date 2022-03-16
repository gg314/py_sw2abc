""" Convert SongWright (SW) formatted files to .ABC format

To do: handle multi-line ties like in A-Lumbering We Go
"""
import sys
import logging
from pathlib import Path
import re
from collections import defaultdict
import click
import clipboard

NOTE_DICT = defaultdict(
    lambda: None,
    {
        "<": "C,",
        "=": "D,",
        ">": "E,",
        "?": "F,",
        "@": "G,",
        "A": "A,",
        "B": "B,",
        "C": "C",
        "D": "D",
        "E": "E",
        "F": "F",
        "G": "G",
        "a": "A",
        "b": "B",
        "c": "c",
        "d": "d",
        "e": "e",
        "f": "f",
        "g": "g",
        "h": "a",
        "i": "b",
        "j": "c'",
        "k": "d'",
        "l": "e'",
        "m": "f'",
        "n": "g'",
        "o": "a'",
        "p": "b'",
        "r": "z",
        "R": "z",
        "x": "y",
        "X": "y",
    },
)

ACC_DICT = defaultdict(
    lambda: None,
    {
        " ": "",  # normal
        "-": "",  # normal
        "#": "^",  # sharp
        "$": "^^",  # double sharp
        "&": "_",  # flat
        "*": "__",  # double flat
        "%": "=",  # natural
    },
)

DUR_DICT = defaultdict(
    lambda: None,
    {
        "1": "16",  # whole
        "2": "8",  # half
        "3": "12",  # dotted half
        "4": "4",  # quarter
        "5": "6",  # dotted quarter
        "6": "4",  # apparently triplet quarters (6th note). Mark triplets later.
        "7": "2",  # apparently triplet eighths (12th note). Mark triplets later.
        "8": "2",  # eighth
        "9": "3",  # dotted eighth
        "0": "1",  # sixteenth
    },
)

TIME_DICT = defaultdict(
    lambda: None,
    {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        # "?": 10, # Unknown, cannot infer
        # "?": 11, # Unknown, cannot infer
        "<": 12,
        "=": 13,
        ">": 14,
        "?": 15,
        "@": 16,
    },
)

CLEF_DICT = defaultdict(
    lambda: None,
    {
        "M": "treble",  # treble clef
        "m": "bass",  # bass clef
        "+": "treble",  # treble clef with bars joined to clef below
        "-": "bass",  # bass clef not joined below
    },
)


class LineState:
    """Maintain the state of the transcription"""

    def __init__(self):
        self.m_type = None
        self.m_flag = None
        self.h_line = None
        self.m_line = None
        self.l_line = None
        self.beats_per_meas = 40
        self.ref_num = 1
        self.title = None
        self.composers = []
        self.speed = None
        self.tempo_string = None
        self.key = None
        self.time = None
        self.notes = []
        self.output_lines = []


def parse_header(state):
    """Format the header lines once"""
    output_lines = []
    output_lines.append(f"X: {state.ref_num}")
    if state.title:
        output_lines.append(f"T: {state.title}")
    for c in state.composers:
        output_lines.append(f"C: {c}")
    if state.speed:
        if state.tempo_string:
            output_lines.append(f"Q: {state.tempo_string} 1/4={state.speed}")
        else:
            output_lines.append(f"Q: 1/4={state.speed}")
    if state.key:
        output_lines.append(f"K: {state.key}")
    if state.time:
        output_lines.append(f"M: {state.time}")
    output_lines.append("L: 1/16")
    for n in state.notes:
        output_lines.append(f"N: {n}")

    return output_lines


def parse_line(ltype, sep, data, state):
    """Parse a SW line into ABC line"""
    if ltype == "N":
        state.h_line = None
        state.m_line = None
        state.l_line = None
        state.title = data
        return state
    elif ltype == "C":
        if data:
            state.composers.append(data)
        return state  # composer
    elif ltype == "A":
        if data:
            state.composers.append(data)
        return state  # (transcription author)
    elif ltype == "T":
        if data:
            state.tempo_string = f'"{data}"'
        return state
    elif ltype == "S":
        if data:
            state.speed = data
        return state
    elif ltype == "K":
        if data:
            state.key = data
        return state  # May need to handle clef, one day.
    elif ltype == "B":
        try:
            if data:
                m = re.match(r"(.)/(.)", data)
                state.time = f"{TIME_DICT[m.group(1)]}/{TIME_DICT[m.group(2)]}"
                state.beats_per_meas = int(
                    TIME_DICT[m.group(1)] / TIME_DICT[m.group(2)] * 16
                )
        except Exception:  # pylint: disable=broad-except
            state.beats_per_meas = 16
            state.time = "4/4"
        return state
    elif ltype == "F":
        if data:
            state.notes.append(data)
        return state
    elif ltype == "H":
        state.h_line = data
        return state
    elif ltype in ("M", "m", "+", "-"):
        state.m_line = data
        state.m_type = ltype
        state.m_flag = sep
        return state
    elif ltype == "L":
        state.l_line = data

        m = re.match(r"^(\d+)(.*)", state.m_line)
        if m:
            clef = CLEF_DICT[state.m_type]  # clef.. never been anything but treble
            if clef != "treble":
                logging.warning("Not a treble clef!")
            # how many bars are on this line:
            bars = int(m.group(1))  # pylint: disable=unused-variable
            state.m_line = m.group(2)

        # print("SW:", state.m_line)
        build_str = ""
        beatcount = 0
        open_tie = 0
        open_triplet = 0
        phrasing = []  # used for aligning lyrics
        while True:
            if state.m_line == "":
                if beatcount >= state.beats_per_meas:
                    build_str += "|"
                break
            elif re.match("^S-1", state.m_line):  # first ending
                build_str += "|1"
                state.m_line = state.m_line[3:]
                beatcount = 0
            elif re.match("^S-2", state.m_line):  # second ending
                build_str += "|2"
                state.m_line = state.m_line[3:]
                beatcount = 0
            elif re.match("^S-5", state.m_line):  # repeat
                build_str += ":|"
                state.m_line = state.m_line[3:]
                beatcount = 0
            elif re.match("^S-6", state.m_line):  # bar
                build_str += "|"
                state.m_line = state.m_line[3:]
                beatcount = 0
            elif re.match("^S-9", state.m_line):  # fermata
                build_str += "H"
                state.m_line = state.m_line[3:]
            elif re.match("^W-[12345]", state.m_line):  # invisible delays? maybe?
                state.m_line = state.m_line[3:]
            elif re.match("^P-[024589]", state.m_line):  # accents? no idea!!
                state.m_line = state.m_line[3:]
            elif state.m_line[0] in [" ", "_"]:
                state.m_line = state.m_line[1:]
            elif beatcount >= state.beats_per_meas:
                build_str += "|"
                beatcount = 0
            elif m := re.match("^ST(.)(.)", state.m_line):  # update time-signature
                build_str += f" [M:{TIME_DICT[m.group(1)]}/{TIME_DICT[m.group(2)]}] "
                state.m_line = state.m_line[4:]
            elif re.match("^S-4", state.m_line):  # repeat-from
                build_str += "|:"
                state.m_line = state.m_line[3:]
            elif re.match(r"^(\S)([-#\$&\*%])(\S)", state.m_line):
                the_note = ""

                m = re.match(r"^(\S)([-#\$&\*%])([67])", state.m_line)  # start triplet
                if m:
                    if open_triplet == 0:
                        build_str += "(3 "
                    open_triplet += 1

                m = re.match(r"^(\S)([-#\$&\*%])(\S)", state.m_line)
                if NOTE_DICT[m.group(1)]:
                    if DUR_DICT[m.group(3)]:
                        the_note += (
                            ACC_DICT[m.group(2)]
                            + NOTE_DICT[m.group(1)]
                            + DUR_DICT[m.group(3)]
                        )
                        beatcount += float(DUR_DICT[m.group(3)])
                else:
                    logging.error("Found confusing group: %s", m.groups())

                if re.match(r"^(\S)([-#\$&\*%])(\S)_", state.m_line):
                    if not open_tie:
                        open_tie = 1
                        build_str += "(" + the_note
                    else:
                        open_tie += 1
                        build_str += the_note
                else:
                    if open_tie:
                        phrasing.append(open_tie)
                        open_tie = 0
                        build_str += the_note + ")"
                    else:
                        phrasing.append(open_tie)
                        build_str += the_note

                if open_triplet == 3:
                    build_str += " "
                    open_triplet = 0
                state.m_line = state.m_line[3:]
            else:
                state.m_line = state.m_line[1:]
                # warn here?

        lyrics_line = "w:"
        for note_count in phrasing:
            if m := re.match(r"\s*(\S+?)([\s-])(.*)", state.l_line):
                lyrics_line += (
                    " " + (m.group(1) + m.group(2)).strip() + (note_count * " _")
                )
                state.l_line = m.group(3)
            else:
                lyrics_line += " " + state.l_line
                break
        state.output_lines.append(build_str)
        state.output_lines.append(lyrics_line)
        return state  # time to process...
    else:
        logging.error("Unrecognized SW line type: %s", ltype)
        return state


@click.command()
@click.argument("filename", type=click.File("r"))
@click.option("--copy/--no-copy", default=False)
# @click.option("--file_out", help="output .abc filename")
def main(filename, copy):
    """Do the conversion"""
    try:
        contents = filename.readlines()
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Failed to open file %s: %s", filename.name, e)
        sys.exit()

    path_stem = Path(filename.name).stem
    print(f"Converting SW file: {path_stem}")
    # print("".join(contents))
    # print("=" * 150)

    state = LineState()
    line_pattern = re.compile(r"([A-Za-z])([-+])\s*(.*)")
    for line in contents:
        m = re.match(line_pattern, line.strip())
        if m:
            ltype = m.group(1)
            sep = m.group(2)
            data = m.group(3)
            state = parse_line(ltype.upper(), sep, data, state)

        else:
            logging.info("Line unrecognized: %s", line.strip())

    output = parse_header(state) + state.output_lines
    # print("\n".join(output))
    path_out = Path(f"./dt_abc/{path_stem}.abc")
    with open(path_out, encoding="UTF-8", mode="w") as f:
        f.write("\n".join(output))
    # print(f"Saving ABC to: {path_out}")
    if copy:
        clipboard.copy("\n".join(output))
