# sfzen

#### Intro

The SFZen package provides several scripts for SFZ inspection and maintenance,
and a simple object-oriented SFZ parsing and manipulation library which you can
use in your own scripts.

#### Credits

This project borrows a good deal from sfzlint by [J. Isaac
Stone](https://github.com/jisaacstone). I made everything as object-oriented
and pythonic as I could, and added a few methods which sfzlint didn't cover.
Many thanks to "jisaacstone" for doing the ground work. Anyone who contributes
to the Linux music community deserves recognition!

## Command-line tools

There are several command-line scripts provided, including:

### sfz-copy
Copies an SFZ to another location with multiple ways of handling samples.

Basic invocation:

    sfz-copy sfzs/Foo-Piano.sfz projects/Bar/

This will copy the SFZ file "Foo-Piano.sfz" into the "projects/Bar/" folder.
All the samples referenced in the original SFZ will be copied to a folder named
"Foo-Piano-samples". The structure of the copied files will be:

    ┣━ projects/Bar
    ┗━━┳━ Foo-Piano.sfz
       ┣━ Foo-Piano-samples/
       ┗━┳━ sample-1.wav
         ┣━ sample-2.wav
         ┗━ ...

If you would like to make save space, as when you might be editing the target
SFZ, but have no need to modify the original samples, there are several options
which allow you to do that:

    --symlink,  -s  Create symlinks in the target samples folder.
    --hardlink, -l  Hardlink samples in the target samples folder.
    --abspath,  -a  Point to the original samples - absolute path.
    --relative, -r  Point to the original samples - relative path.

### sfz-validate
Checks whether SFZ files are formatted correctly, and opcode values are of the
correct type and have valid values.

To validate a single SFZ:

    sfz-validate sfzs/Foo-Piano.sfz

This will print detailed errors, one per line:

    sfzs/Foo-Piano.sfz:37 "lovel=0": Value [0] is below the minimum [1] for "lovel"
    sfzs/Foo-Piano.sfz:39 "volume=10": Value [10.0] is above the maximum [6.0] for "volume"

If you would like a simple summary, use the "--summary" option:

    $ sfz-validate --summary sfzs/Foo-Piano.sfz
        1 MinError
        1 MaxError

You may pass several filenames on the command line. To validate all the SFZs
found inside a folder and all of its subfolders, use the "--recurse" option:

    $ sfz-validate --summary --recurse sfzs/
       34 MaxError
        8 MinError

To see what common errors occurred, use the "--summary" option twice:

    $ sfz-validate -s -s --recurse sfzs/
       34 MaxError
           2 fillfo_depth=1506
           2 fillfo_depth=2528
           [ .. ]
        8 MinError
           2 fillfo_depth=-1302
           1 fillfo_depth=-7200
           [ .. ]

### sfz-opcode-usage
Lists all of the opcodes used in one or many .sfz files.

Basic invocation (recursing to subfolders):

    $ sfz-opcode-usage -r sfzs/
    lokey
    hikey
    [ .. ]
    amp_velcurve_1
    amp_velcurve_127


### sfz-samples
Prints paths to samples used in a given SFZ.

Basic invocation:

    $ sfz-samples sfzs/VSCO/Harp.sfz
    KSHarp_G3_mf.wav
    KSHarp_D6_mf.wav
    [ .. ]

Print absolute paths:

    $ sfz-samples --abspath sfzs/VSCO/Harp.sfz
    /mnt/data-drive/sfzs/VSCO/Harp/KSHarp_A4_mf.wav
    /mnt/data-drive/sfzs/VSCO/Harp/KSHarp_F6_mf.wav
    [ .. ]

### sfz-opcode-info
Displays data type, allowable values, aliases and descriptions of opcodes.

    $ sfz-opcode-info loopmode
    loopmode
    --------
    Opcode name: loop_mode
    Category:    Sample Playback
    Version:     v1
    Type:        str
    Choices:
            no_loop         no looping will be performed. Sample will play straight from start to
                            end, or until note off, whatever reaches first.
            one_shot        sample will play from start to end, ignoring note off. This is
                            commonly used for drums. This mode is engaged automatically if the
                            count opcode is defined.
            loop_continuous once the player reaches sample loop point, the loop will play until
                            note expiration.
            loop_sustain    the player will play the loop while the note is held, by keeping it
                            depressed or by using the sustain pedal (CC64). The rest of the sample
                            will play after note release.
    Default:     no_loop
    Description:
       Allows playing samples with loops defined in the unlooped mode.

### sfz-liquid-safe
Strips an SFZ of opcodes which liquidsfz does not support.


# API

## Basic Usage

    from sfzen import SFZ

    sfz = SFZ(filename)
    ... do stuff ...
    sfz.write(sys.stdout)

## SFZ structure and navigation.

The structure of an instance of SFZ follows the SFZ format. It may contain headers
of various types, and headers can contain opcodes.

For programming covenience, the SFZ class extends the Header class, inheriting
its attributes and methods.

The SFZ class exposes a "subheaders()" method which returns a list of headers
which are immediate children of the SFZ. Subsequently, calling "subheaders()"
on each subheader returns a list of headers contained in *it*. You could use
this structure to iterate through the headers and opcodes in an SFZ.

Another way to iterate through is to call the "walk()" method. This is a
generator function which recurses through the tree structure of the SFZ,
yielding an element (header or opcode) on each iteration. The return value of
"walk()" is a tuple of (element, depth).

For example:

    from sfzen import SFZ
    sfz = SFZ(filename)
    for elem, depth in sfz.walk():
        if isinstance(elem, Header):
            print("  " * depth, elem)

The above example is redundant, however, as the "dump()" method does just this.

You can traverse *up* the hierarchy using the "parent" property of both Opcode and Header.

    region = sample.parent


### Opcodes and Opcode values

Individual opcodes can be retrieved using the "opcode(<opcode_name>)" method.
This method retrieves an Opcode which is contained in the Header on which it is
called:

    for region in sfz.regions():
        loopmode = region.opcode("loopmode")

> If the opcode is not defined in the header, the "opcode" method returns None.

The value of an opcode defined in any header can be retrieved using:

    header.get_opcode_value(<opcode_name>)

> If the opcode is not defined in the header, the "get_opcode_value" method
returns None.

The value can also be set using:

    header.set_opcode_value(<opcode_name>, <opcode_value>)

> If the named opcode doesn't yet exist inside the header, it will be created.

All Opcodes in a Header may be retrieved using the "opcodes" method, which
returns a **dictionary**. The keys are the opcode names, and values are
instances of the Opcode class.

    header.opcodes()

> Note: The root SFZ object may not contain opcodes.

### Sample opcodes

The "\<sample\>" opcode is pretty important in an SFZ file. The sample value
points to a location in the filesystem, so filesystem -related methods would be
needed. Therefore, there is a dedicated Sample class which extends the Opcode
class and adds new methods.

Sample values are usually defined relative to the root path of the SFZ. To
retrieve the absolute path to a sample file, the "abspath()" method.

### Regions

Samples are defined inside a \<region\> tag in an SFZ. So the "parent" property
of a sample will (probably) be a \<region\>. The following example returns all the
opcodes of the region in which each sample is declared:

    for sample in sfz.samples():
        region = sample.parent
        opcodes = region.opcodes()

An alternative would be to just use the "regions()" method of the SFZ:

    for region in sfz.regions():
        sample = region.sample()
        opcodes = region.opcodes()

### Inherited opcodes

A \<region\> may be contained inside other headers, such as \<group\>, which
define opcodes which are inherited by the region. In order to retrieve all of
the opcodes which affect that \<region\>, you can use the "inherited_opcodes()"
method. This will return all the opcodes defined in that \<region\>, as well as
any which are defined in any header above that \<region\> in the SFZ tree.

    for region in sfz.regions():
        all_opcodes = region.inherited_opcodes()

If "loopmode" is not defined in the \<region\>, but is defined in a parent header,
this method will not find it. Like the "inherited_opcodes()" method described
above, the "iopcode(\<opcode_name\>)" method **will** retrive an opcode defined
in a parent header.

So, to retrieve the loopmode which affects the sample, regardless of where it
is defined, you will do:

    loopmode = region.iopcode("loopmode")

### Attribute access on headers

You can also reference the opcode name as an attribute of the Header.

So, for example, if a \<region\> contains an opcode named "loopmode", you can
retrieve it's value by using "region.loopmode".

    for sample in sfz.samples():
        region = sample.parent
        loopmode = region.loopmode

In constrast with the "get_opcode_value" method, attribute access if there is no Opcode named "loopmode" in
the \<region\>, the attribute lookup will move up the hierarchy to the parent
Header of that \<region\>, until it finds one. If nothing is found, the value will
be None.

### Aliases

Note that there are two opcodes in the SFZ format which define the way a sample
is looped, "loopmode" and "loop_mode". You can use either one, as you prefer.
Using attribute access, opcode aliases are also checked. So if you access the
"loopmode" property of a \<region\> that has no Opcode named "loopmode", but
*does* contain an Opcode named "loop_mode", the value of the Opcode named
"loop_mode" will be returned for the "loopmode" attribute.

The following example should make this clear:

    from sys import stdout
    from sfzen import SFZ, Group, Region

    sfz = SFZ()
    group = Group()
    sfz.append(group)
    region = Region()
    group.append(region)
    print(region.loopmode)              # "None"
    group.loopmode = "loop_continuous"
    print(region.loopmode)              # "loop_continuous"
    region.loopmode = "one_shot"
    print(region.loopmode)              # "one_shot"
    print()
    sfz.write(stdout)

The output of the above script will be:

----------------------------------
    None
    loop_continuous
    one_shot

    // \[Unnamed\]

    <group>
    loopmode=loop_continuous

    <region>
    loopmode=one_shot
----------------------------------


### Normalization and validation

An opcode named "offset_cc22" will not be literally defined in the spec, but is
an instance of the "offset_ccN" opcode. To retrieve the opcode name defined in
the spec, use the "normal_opcode()" method. Some methods, like
"opcode_definition()" and "validator_for()" normalize the opcode name when
doing a lookup. Aliases are normalized as well.

Some opcodes accept any value above a minimum value, some accept any value
between a minimum value and a maximum value, some accept only one value out of
a selection of choices. The appropriate Opcode validator is selected based on
the opcode "value" definition found in the OPCODES dictionary. All of the
validator classes extend the Validator class, which provides type checking as
well.

When a value is set on an opcode, and it does not pass validation, the "error"
attribute of the opcode is set to the appropriate error class. These classes
all extend the ValidationError class, and include:

#### DataTypeError

The incorrect data type for the value was given. Since SFZ
files are text files, all values are strings when first
parsing. The validator checks that the string given can be
coerced to the correct data type, and if not, generates this
error.

#### MinError

The value given falls below the opcode's minimum value.

#### MaxError

The value given falls below the opcode's maximum value.

#### ChoiceError

The value given was not found in the list of valid choices.

#### NotFoundError

(Sample and Include) The referenced file was not found.

#### InvalidOpcodeError

An opcode was encountered with an unrecognized name.

#### InvalidHeaderError

A header was encountered with an unrecognized name.


## Sample modes when using "save_as"

Normally, an SFZ file's sample paths are given as relative to the SFZ file.
When saving an SFZ object, you have multiple choices as to how you want the
samples saved and referenced. (This is particularly useful when copying an sfz.)

#### SAMPLES_ABSPATH

The file names are written as absolute paths.

#### SAMPLES_RELPATH

The file names are written as paths relative to the original sfz.

#### SAMPLES_COPY

The file names are written as relative paths, and the sample files are copied
to a "samples-<sfz_name>" subfolder.

#### SAMPLES_SYMLINK

The file names are written as relative paths, and the sample files are
symlinked in a "samples-<sfz_name>" subfolder.

#### SAMPLES_HARDLINK

The file names are written as relative paths, and the sample files are hard
-linked in a "samples-<sfz_name>" subfolder. (Not available on the "windoze
operating system".)

## SFZ Simplification

After building up an SFZ, you can automatically create groups which define
opcodes common to the regions they contain, using the "simplified()" method of
the SFZ class. This creates a copy of the original SFZ, with some redundant
opcodes removed and common opcodes grouped inside \<group\> and \<global\>
headers.

> These methods compare the *inherited opcodes* of the regions.

There are two different grouping modes:

#### GLOBALIZE_UNIVERSAL

Only opcodes which are common to each and every region will be taken out of
that region and put into a \<global\> header.

#### GLOBALIZE_NUMEROUS

Opocodes which are the same for at least half of the regions will be taken out
of that region and put into a \<global\> header.

Using simplification, I saw significant space reductions on some .sfz files
found in the public domain, as well as some generated from SoundFonts using
[Polyphone](https://www.polyphone.io/).

