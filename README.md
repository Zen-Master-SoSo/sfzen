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

```bash
    $ sfz-validate --summary sfzs/Foo-Piano.sfz
        1 MinError
        1 MaxError
```

You may pass several filenames on the command line. To validate all the SFZs
found inside a folder and all of its subfolders, use the "--recurse" option:

```bash
$ sfz-validate --summary --recurse sfzs/
   34 MaxError
	8 MinError
```

To see what common errors occurred, use the "--summary" option twice:

```bash
$ sfz-validate -s -s --recurse sfzs/
   34 MaxError
	   2 fillfo_depth=1506
	   2 fillfo_depth=2528
	   [ .. ]
	8 MinError
	   2 fillfo_depth=-1302
	   1 fillfo_depth=-7200
	   [ .. ]
```

### sfz-opcode-usage
Lists all of the opcodes used in one or many .sfz files.

Basic invocation (recursing to subfolders):

```bash
$ sfz-opcode-usage -r sfzs/
lokey
hikey
[ .. ]
amp_velcurve_1
amp_velcurve_127
```


### sfz-samples
Prints paths to samples used in a given SFZ.

Basic invocation:

```bash
$ sfz-samples sfzs/VSCO/Harp.sfz
KSHarp_G3_mf.wav
KSHarp_D6_mf.wav
[ .. ]
```

Print absolute paths:

```bash
$ sfz-samples --abspath sfzs/VSCO/Harp.sfz
/mnt/data-drive/sfzs/VSCO/Harp/KSHarp_A4_mf.wav
/mnt/data-drive/sfzs/VSCO/Harp/KSHarp_F6_mf.wav
[ .. ]
```

### sfz-opcode-info
Displays data type, allowable values, aliases and descriptions of opcodes.

```bash
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
```

### sfz-liquid-safe
Strips an SFZ of opcodes which liquidsfz does not support.



# API


### Basic Usage

```python
from sfzen import SFZ

sfz = SFZ(filename)
... do stuff ...
sfz.write(sys.stdout)
```

### Example

Let's say you have recorded a sample of each guitar string being plucked on
your guitar. You have saved the sample files in a directory named "samples"
beneath the current working directory. The sample files have the following
names:

	40-E2.wav
	45-A2.wav
	50-D3.wav
	55-G3.wav
	59-B3.wav
	64-E4.wav

The following script will create a very basic SFZ file from the samples:

```python
from sys import stdout
from operator import itemgetter
from pathlib import Path
from sfzen import SFZ, Global, Region

sfz = SFZ()
global_header = sfz.append(Global())
global_header.loop_mode = 'one_shot'
tuples = [
	(int(sample_path.name[0:2]), sample_path)
	for sample_path in Path('samples').rglob('*.wav')
]
tuples.sort(key = itemgetter(0))
for index, tup in enumerate(tuples):
	pitch, path = tup
	region = global_header.append(Region())
	region.sample = path
	region.pitch_keycenter = pitch
	region.lokey = pitch
	region.hikey = tuples[index + 1][0] - 1  if index < 5 else pitch + 7
sfz.write(stdout)
```

The above script outputs:

	// [Unnamed]

	<global>
	loop_mode=one_shot

	<region>
	lokey=40
	hikey=44
	sample=samples/40-E2.wav
	pitch_keycenter=40

	<region>
	lokey=45
	hikey=49
	sample=samples/45-A2.wav
	pitch_keycenter=45

	<region>
	lokey=50
	hikey=54
	sample=samples/50-D3.wav
	pitch_keycenter=50

	<region>
	lokey=55
	hikey=58
	sample=samples/55-G3.wav
	pitch_keycenter=55

	<region>
	lokey=59
	hikey=63
	sample=samples/59-B3.wav
	pitch_keycenter=59

	<region>
	lokey=64
	hikey=71
	sample=samples/64-E4.wav
	pitch_keycenter=64


## SFZ structure and navigation.

The structure of an instance of SFZ follows the SFZ format. It may contain headers
of various types, and headers can contain opcodes.

For programming covenience, the SFZ class extends the Header class, inheriting
its attributes and methods.

The SFZ class exposes a "**subheaders**()" method which returns a list of headers
which are immediate children of the SFZ. Subsequently, calling "subheaders()"
on each subheader returns a list of headers contained in *it*. You could use
this structure to iterate through the headers and opcodes in an SFZ.

Another way to iterate through is to call the "**walk**()" method. This is a
generator function which recurses through the tree structure of the SFZ,
yielding an element (header or opcode) on each iteration. The return value of
"walk()" is a tuple of (element, depth).

For example:

```python
from sfzen import SFZ

sfz = SFZ(filename)
for elem, depth in sfz.walk():
	if isinstance(elem, Header):
		print("  " * depth, elem)
```

The above example is redundant, however, as the "**dump**()" method does just this.

You can traverse *up* the hierarchy using the "**parent**" attribute of both Opcode and Header.

```python
region = sample.parent
```


### Opcodes and Opcode values

Opcodes may be instantiated and appended to a header's list of elements using
this syntax:

```python
opcode = region.append(Opcode("loopmode", "one_shot"))
```

You could instantiate an Opcode and not append it, but unless the opcode is
appended to the header, it isn't a part of the SFZ structure yet. This is
particularly relevant when cloning opcodes (or headers) from different SFZs.

An opcode can also be created and its value set by using the
"**set_opcode_value**()" method:

```python
header.set_opcode_value(<opcode_name>, <opcode_value>)
```

If the named opcode doesn't yet exist inside the header, it will be created.

Individual opcodes can be retrieved using the "**opcode**(<opcode_name>)" method.
This method retrieves an Opcode which is contained in the Header on which it is
called:

```python
for region in sfz.regions():
	loopmode = region.opcode("loopmode")
	[..]
```

If the opcode is not defined in the header, the "opcode" method returns None.

The value of an opcode defined in any header can also be retrieved using the
"**get_opcode_value**()" method:

```python
header.get_opcode_value(<opcode_name>)
```

#### Attribute access

If the opcode is not defined in the header, the "get_opcode_value" method
returns None. (See also "Inherited opcodes" below.)

The above "get_opcode_value" and "set_opcode_value" do the exact same thing as
setting an opcode as an attribute of the header. In the example given above, the
sample, pitch_keycenter, lokey, and hikey of each Region was set using the
syntax:

```python
header.<opcode_name> = <opcode_value>
```

Conversely, the opcode value previous set can be retrieved by referencing the
opcode name as an attribute of the Region.

```python
value = header.<opcode_name>
```

> This applies to every kind of header which can contain opcodes, not only
"Region" headers. (Only the root SFZ object may not contain opcodes.)

One big difference is that, in constrast with the "get_opcode_value()" method,
when using attribute access, if there is no Opcode named "loopmode" in the
header, attribute lookup will move up the hierarchy to the parent header until
it finds one.

So if, for example, a \<group\> contains an opcode named "key", any \<region\>
it contains will have the same value for key, unless otherwise defined in that
region.

```python
sfz = SFZ()
group = sfz.append(Group())
group.key = 48
region1 = group.append(Region())
region1.hivel = 63
region1.sample = "samples/48-pianissimo.wav"
region2 = group.append(Region())
region2.lovel = 64
region1.sample = "samples/48-forte.wav"

for region in group.regions():
	print(region.key, region.lovel, region.hivel)
```

Outputs:

	key: 48, lovel: None, hivel: 63
	key: 48, lovel: 64, hivel: None

#### Retrieving a group of opcodes

All of the Opcodes in a Header may be retrieved using the "opcodes" method, which
returns a dictionary. The keys are the opcode names, and the values are
instances of the Opcode class.

```python
header.opcodes()
```

(See also: "Inherited opcodes" below)

### Samples and regions

The "\<sample\>" opcode points to a location in the filesystem, so filesystem
-related methods are added to the Opcode class in the Sample class.

Two attributes of the Sample which might be of interest:

**abspath** (property): Returns (pathlib.Path) the absolute path, with symlinks resolved.

**exists** (method): Returns boolean True if file exists

Samples are defined inside a \<region\> tag in an SFZ. So the "parent" attribute
of a sample will (probably) be a \<region\>. The following example returns all the
opcodes of the region in which each sample is declared:

```python
for sample in sfz.samples():
	region = sample.parent
	opcodes = region.opcodes()
```

An alternative would be to just use the "regions()" method of the SFZ:

```python
for region in sfz.regions():
	sample = region.sample()
	opcodes = region.opcodes()
```

Sample values are usually defined relative to the root path of the SFZ. To
retrieve the absolute path to a sample file, use its "**abspath**" attribute:

```python
for sample in sfz.samples():
	print(sample.abspath)
```


### Inherited opcodes

A \<region\> may be contained inside other headers, such as \<group\>, which
define opcodes which are inherited by the region. In order to retrieve all of
the opcodes which affect that \<region\>, you can use the "inherited_opcodes()"
method. This will return all the opcodes defined in that \<region\>, as well as
any which are defined in any header above that \<region\> in the SFZ tree.

```python
for region in sfz.regions():
	all_opcodes = region.inherited_opcodes()
```

If "loopmode" is not defined in the \<region\>, but is defined in a parent
header, the "opcode()" method will not return it. If you want to return an
opcode from a header and any of its parent headers, use the "**iopcode**()"
method.

Like the "inherited_opcodes()" method described above, the
"iopcode(\<opcode_name\>)" method *will* retrive an opcode defined
in a parent header.

So, to retrieve the loopmode which affects the sample, regardless of where it
is defined, you will do:

```python
opcode = region.iopcode("loopmode")
```

### Aliases

Note that there are two opcodes in the SFZ format which define the way a sample
is looped, "loopmode" and "loop_mode". You can use either one, as you prefer.
Using attribute access, opcode aliases are also checked. So if you access the
"loopmode" attribute of a \<region\> that has no Opcode named "loopmode", but
*does* contain an Opcode named "loop_mode", the value of the Opcode named
"loop_mode" will be returned for the "loopmode" attribute.

The following example should make this clear:

```python
from sys import stdout
from sfzen import SFZ, Group, Region

sfz = SFZ()
group = sfz.append(Group())
region = group.append(Region())

print(region.loopmode)
# (region.loopmode returns "None")

group.loopmode = "loop_continuous"
print(region.loopmode)
# (region.loopmode returns "loop_continuous")

region.loopmode = "one_shot"
print(region.loopmode)
# (region.loopmode returns "one_shot")

print('-------')
sfz.write(stdout)
```

The output of the above script will be:

	None
	loop_continuous
	one_shot
	-------
	// [Unnamed]

	<group>
	loopmode=loop_continuous

	<region>
	loopmode=one_shot


### Normalization and validation

An opcode named "offset_cc22" will not be literally defined in the spec, but it is
an instance of the "offset_ccN" opcode. To retrieve the opcode name defined in
the spec, use the "**normal_opcode**()" function. Some functions, like
"**opcode_definition**()" and "**validator_for**()" already normalize the
opcode name when doing a lookup. Aliases are normalized as well.

Errors in parsing or opcode validation do not raise exceptions. SFZ errors
which are detected during parsing are available in the SFZ "**errors**"
attribute. This is a list of objects extending ValidationError. If no error
occurred, this list will be empty.

An error detected during validation of an Opcode's value is available in the
Opcode's "**error**" attribute. If no validation error occurred, this attribute
will be None.

Validation of the SFZ structure occurs when an SFZ is instantiated and parsed.
Opcode validation occurs not only during initial parsing, but whenever a value
is set on an opcode.

Some opcodes accept any value above a minimum value, some accept any value
between a minimum value and a maximum value, some accept only one value out of
a selection of choices. The appropriate Opcode validator is chosen when the
Opcode is instantiated, based on the opcode "value" definition found in the
OPCODES dictionary (found in the sfzen.opcodes module). All of the validator
classes extend the Validator class, which provides type checking as well.

The classes extending the ValidationError class include:

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
opcodes common to the regions they contain, using the "**simplified**()" method of
the SFZ class. This creates a copy of the original SFZ, with some redundant
opcodes removed and common opcodes grouped inside \<group\> and \<global\>
headers.

To use the "simplified()" method in your code:

```python
from sfzen import SFZ

source_sfz = SFZ('source.sfz')
simple = source_sfz.simplified()
simple.save_as('simple.sfz')
```

> You can do the same as the above script using the command-line tool
"sfz-copy", using the "--simplify" option.

Using simplification, I saw significant reductions on some .sfz files found in
the public domain, as well as some generated from SoundFonts using
[Polyphone](https://www.polyphone.io/).

Space isn't really the issue, though. Readability is. After simplification, the
unique charcteristics of each region stand out from the "noise" of all the
other opcodes, which end up grouped in the global header.


