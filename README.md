# sfzen

Simple object-oriented SFZ parsing and manipulation.

## Credits

This project borrows a good deal from sfzlint by [J. Isaac
Stone](https://github.com/jisaacstone), particularly the lark parser
definition. I made everything as object-oriented and pythonic as I could, and
added a few functions which sfzlint didn't cover. Many thanks to "jisaacstone"
for doing the ground work. Anyone who contributes to the Linux music community
deserves recognition!

## Basic Usage

	from sfzen import SFZ

	sfz = SFZ(filename)
	... do stuff ...
	sfz.write(sys.stdout)

## SFZ structure and navigation.

The structure of an instance of SFZ follows the SFZ format. It may have headers
of various types, and headers can contain opcodes.

The SFZ class exposes a "subheaders" property which returns a list of headers
which are immediate children of the SFZ. Each subheader also has a
"subheaders" property which returns a list of headers contained in *it*.

You could traverse the SFZ structure by iterating via the the "subheaders()"
method. Another way is to call the "walk()" method. This is a generator
function which recuses through the tree structure of the SFZ, yielding an
element (header or opcode) on each iteration. The return value of "walk()" is a
tuple of (element, depth).

For example:

	from sfzen import SFZ
	sfz = SFZ(filename)
	for elem, depth in sfz.walk():
		if isinstance(elem, Header):
			print("  " * depth, elem)

The above example is redundant, however, as the "dump()" method does just this.

### Opcodes

Opcodes are accessed using the "opcodes" property, which returns a
**dictionary**. The keys are the opcode names, and values are instances of
the Opcode class. (Or Sample class, which is described below.)

> Note: The root SFZ object may not contain opcodes.

You can traverse *up* the hierarchy using the "parent" property of both Opcode and Header.

### Sample opcodes

The "\<sample\>" opcode is pretty important in an SFZ file. The sample value
points to a location in the filesystem, so filesystem -related methods would be
needed. Therefore, there is a dedicated Sample class which extends the Opcode
class and adds new functions.

One useful property of the Sample class is "abspath". Sample values are usually
defined relative to the root path of the SFZ. This function resolves that
relative value into an absolute path pointing to the sample in the filesystem.

### Regions

Samples are defined inside a <region> tag in an SFZ. So the "parent" property
of a sample will (probably) be a Region. This method of traversal is quite
useful:

	for sample in sfz.samples():
		region = sample.parent
		# Get all the opcodes in the region containing the sample:
		opcodes = region.opcodes

Often, a \<region\> is contained inside a \<group\> which contains opcodes which
might affect the sound of that sample. In order to retrieve all the opcodes
which will affect the sound of the sample, use the "inherited_opcodes()" method
of its parent Region. This will return all the opcodes for the Region, as well
as any which are defined in a Header above that Region in the SFZ structure.

	for sample in sfz.samples():
		region = sample.parent
		# Get all the opcodes in the region containing the sample, as well
		# as opcodes from parent Headers which will affect that sample:
		all_opcodes = region.inherited_opcodes()

Individual opcodes can be retrieved using the "opcode(<opcode_name>)" method.
This method retrieves an Opcode which is contained in the Header on which it is
called:

	for sample in sfz.samples():
		region = sample.parent
		loopmode = region.opcode("loopmode")

If "loopmode" is not defined in the Region, but is defined in a parent header,
this method will not find it. Like the "inherited_opcodes()" method described
above, the "iopcode()" method **will** retrive an opcode defined in a parent
header.

So, to retrieve the loopmode which affects the sample, regardless of where it
is defined, you will do:

	loopmode = region.iopcode("loopmode")

### Header attributes

It gets better.

The "opcode()" and "iopcode()" methods return Opcode objects, which are easy
enough to manipulate using their "value" property. But you can avoid that by
just referencing the opcode name as an attribute of the Header.

So, for example, if a <region> contains an opcode named "loopmode", you can
retrieve it's value by using "region.loopmode".

	for sample in sfz.samples():
		region = sample.parent
		loopmode = region.loopmode

Just as with the iopcode function, if there is no Opocode named "loopmode" in
the Region, the attribute lookup will move up the hierarchy to the parent
Header of that Region, until it finds one. If nothing is found, the value will
be None.

### Aliases

Note that there are two opcodes in the SFZ format which define the way a sample
is looped, "loopmode" and "loop_mode". You can use either one, as you prefer.
Using attribute access, opcode aliases are also checked. So if you access the
"loopmode" property of a Region that has no Opocode named "loopmode", but
*does* contain an Opcode named "loop_mode", the value of the Opcode named
"loop_mode" will be returned for the "loopmode" attribute.

The following example should make this clear:

	from sys import stdout
	from sfzen import SFZ
	from sfzen.sfz_elems import Group, Region

	sfz = SFZ()
	group = Group()
	sfz.append_subheader(group)
	region = Region()
	group.append_subheader(region)
	print(region.loopmode)
	group.loopmode = "loop_continuous"
	print(region.loopmode)
	region.loopmode = "one_shot"
	print(region.loopmode)

	print()

	sfz.write(stdout)

The output of the above script will be:

	None
	loop_continuous
	one_shot

	// ----------------------------------------------------------------------------
	// None
	// ----------------------------------------------------------------------------

	<group>
	loopmode=loop_continuous

	<region>
	loopmode=one_shot

### Normalization and validation

An opcode named "offset_cc22" will not be literally defined in the spec, but is
an instance of the "offset_ccN" opcode. To retrieve the opcode name defined in
the spec, use the "normal_opcode()" function found in the sfz_elems module.
Other functions in that module, like "opcode_definition()" and
"validation_rule()" normalize the opcode name when doing a lookup. Aliases are
normalized as well.

There is a lot more to write about regarding validation. Look at the source
code or the help() text in the python interpreter to get an idea how it might
be used. Creating an "sfz-validate" script is definitely on my TODO list. If
anyone would like to bang one out... go for it!

### Sample modes when saving

Normally, an SFZ file's sample paths are given as relative to the SFZ file.
When saving an SFZ object, you have multiple choices as to how you want the
samples saved and referenced. (This is particularly useful when copying an sfz.)

#### SAMPLES_ABSPATH

The file names are written as absolute paths.

#### SAMPLES_RESOLVE

The file names are written as paths relative to the original sfz.

#### SAMPLES_COPY

The file names are written as relative paths, and the sample files are copied
to a "samples-<sfz_name>" subfolder.

#### SAMPLES_MOVE

The file names are written as relative paths, and the sample files are moved to
a "samples-<sfz_name>" subfolder.

#### SAMPLES_SYMLINK

The file names are written as relative paths, and the sample files are
symlinked in a "samples-<sfz_name>" subfolder.

#### SAMPLES_HARDLINK

The file names are written as relative paths, and the sample files are hard
-linked in a "samples-<sfz_name>" subfolder. (Not available on the "windoze
operating system".)

### Simplification

After building up an SFZ, you can automatically create groups which define
opcodes common to the regions they contain, using the "simplified()" method of
the SFZ class. This creates a copy of the original SFZ, with some redundant
opcodes removed and common opcodes grouped inside \<group\> and \<global\>
headers.

There are two different grouping modes:

#### GLOBALIZE_UNIVERSAL

Only opcodes which are common to each and every region will be taken out of
that region and put into a \<global\> header.

#### GLOBALIZE_NUMEROUS

Opocodes which are the same for at least half of the regions will be taken out
of that region and put into a \<global\> header.

Note that these methods compare the *inherited opcodes* of the regions.

Using simplification, I saw significant space reductions on some .sfz files
found in the public domain, as well as some generated from SoundFonts using
[Polyphone](https://www.polyphone.io/).

