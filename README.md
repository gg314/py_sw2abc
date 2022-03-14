# py_sw2abc

The SongWright file format is an orphaned format with no apparent standard.
The [ABC format](https://abcnotation.com/wiki/) is well-defined, powerful, and compatible with [other libraries](https://github.com/paulrosen/abcjs) and services.

This project is an attempt to improve on previous scripts which translate SongWright files to ABC files. There are other (Perl and gawk) scripts around but they are incomplete & unmaintained. This Python approach has allowed for pretty reasonable results so far but there are improvements to be made.

### Usage:

To do. The output will be copied to the clipboard conditional on the `--copy` flag.

```python
py_sw2abc <file_in> [--copy/no-copy]
```

### Example

**SongWright input:**

```N-A-Beggin' I Will Go
C-
A-
T-
S-100
K-C
B-4/4
F-
H-
M-1c-8 S-6 c-8 G-8 G-8 F-8 E-4 D-8 E-8 C-8 D-8 E-8 F-8 G-5 G-8 G-8 c-8 c-8 c-8 c-4 c-8 c-8 d-8 e-8 f-8 d-8 e-4 S-6 S-6
L-      Of all the trades in  Eng-  land the beg- gin' is the best,      For when a beg- gar's tired, he  can sit him down and rest,
H-chorus:
M-5d-8 c-8 S-6 e-4 d-8_c-8 b-4 a-8_b-8 c-8_b-8 a-8_G-8 a-8_G-8 F-8 E-8 F-4 a-4 G-4 b-4 W-2 c-3 R-8 S-6 S-6
L-       And a   beg-     gin'   I        will    go,      will     go,   And  a- beg-    gin'    I       will     go.
```

**py_sw2abc output:**

```X: 1
T: A-Beggin' I Will Go
Q: 1/4=100
K: C
M: 4/4
L: 1/16
c2|c2G2G2F2E4D2E2|C2D2E2F2G6G2|G2c2c2c2c4c2c2|d2e2f2d2e4||
w: Of all the trades in Eng- land the beg- gin' is the best, For when a beg- gar's tired, he can sit him down and rest,
d2c2|e4(d2c2)B4(A2B2)|(c2B2)(A2G2)(A2G2)F2E2|F4A4G4B4|c12z2||
w: And a beg- gin'_ I will_ go,_ will_ go,_ And a- beg- gin' I will go.
```

![py_sw2abc output](/examples/py_sw2abc_output.png)

(image rendered with ABCjs)

**Compare to previous scripts:**

```T:A-Beggin' I Will Go
M:4/4
L:1/8
K:C
 c| cG GF E2 DE| CD EF G3 G| Gc cc c2 cc| de fd e2|| dc| e2d-c B2A-B|\
c-BA-GA-G FE| F2 A2 G2 B2| c6 z||
```

![py_sw2abc output](/examples/gawk_output.png)

(image rendered with ABCjs)
