# Python Based Subtraction Encoder
Most modern encoders are sufficient for obfuscating shell code.  However, there are certain cases where even using an Alpha Numeric encoder results in "bad bytes".  This encoder uses both instructions and an algorithm that yields bytes sufficient in this case.

## How do I Use This?
I've tried to make this pretty modular.  So far, I've been using this from the command line.  The HELP menu provides some guidance.
```terminal
# ./SubtractionEncoder.py --help
The encoder of last resort when all others fail...
At the moment, this is only for x86 instruction set.
The ASM output is Intel notation.
@kevensen
usage: SubtractionEncoder.py [-h] --input INPUT
                             (--goodbytes GOODBYTES | --badbytes BADBYTES)
                             [--variablename VARIABLENAME]
                             [--format {asm,raw,python}] [--filename FILENAME]
                             [--debug DEBUG]

Encode instructions using the SubtractionEncoder

optional arguments:
  -h, --help            show this help message and exit
  --input INPUT         The string of input bytes
  --goodbytes GOODBYTES
                        The string of allowed bytes
  --badbytes BADBYTES   The string of disallowed bytes
  --variablename VARIABLENAME
                        The name of the variable to output
  --format {asm,raw,python}
                        The output format
  --filename FILENAME   The output file name. Default is STDOUT
  --debug DEBUG         Show additional output.
```


Here is an example.
```terminal
# SubtractionEncoder.py --input "81ECFF000000" --goodbytes "0102030405060708090b0c0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e303132333435363738393b3c3d3e4142434445464748494a4b4c4d4e4f505152535455565758595a5b5c5d5e5f606162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f" --format python --variablename simple --debug True
```
