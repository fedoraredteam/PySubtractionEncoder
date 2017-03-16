#!/usr/bin/python

import argparse, sys

# Exception for a word that is too large
class EncoderDoubleWordTooLargeError(Exception):
    def __init__(self, value):
        print "The value %s is too large for a signed double word. It must be less than 4,294,967,295" % str(value)

# Exception for a word that is too small
class EncoderDoubleWordTooSmallError(Exception):
    def __init__(self, value):
        print "The value %s is too small for an unsigned double word.  It must be larger than -2,147,483,648" % str(value)

class MissingNibbleError(Exception):
    def __init__(self, byte_string):
        print "Something may have gone wrong here.  It seems that you may be missing a nibble. The byte string is of length %s.\n" % str(len(byte_string))
        print "String is %s." % byte_string

class EncoderInstructions:
    nop_op_code = '90'
    sub_op_code = '2d'
    push_esp_op_code = '54'
    pop_esp_op_code = '5c'
    push_eax_op_code = '50'
    pop_eax_op_code = '58'


# Encapsulation of the double word under operation.  This is a value between
# 0 and 0xFFFFFFFF
class EncoderDoubleWord:

    # The value in the object will be stored as base 10.  Various accessors
    # will return the value in desired formats
    value = 0

    # The initial value can be passed as a base 10 or 16.  The base 16 number
    # can be preceded with 0x or not. For example 0xAA and AA are fine.
    def __init__(self, value):
        if str(value).isdigit() or str(value).startswith('-'):
            self.value = value
        elif value.startswith('0x'):
            self.value = int(value, 0)
        else:
            self.value = int(value, 16)

        if self.value > 4294967295:
            raise EncoderDoubleWordTooLargeError(self.value)
        elif self.value < -2147483648:
            raise EncoderDoubleWordTooSmallError(self.value)

    # Returns an integer
    def get_base_ten(self):
        return self.value

    # Returns a base 16 number as a string
    def get_base_sixteen(self):
        return format(self.value, 'x')

    # Returns a full double word as string
    # e.g. 0000000a
    # If pretty = True (False by default), 0x0000000a
    def get_all_digits_base_sixteen(self, pretty=False):
        if pretty:
            return "0x" + self.get_all_digits_base_sixteen()
        return "{:08x}".format(self.value)

    # Return double word as an array of 4 strings (bytes)
    # e.g. ['00','00','00','0a']
    def get_byte_array(self):
        n = 2
        return [self.get_all_digits_base_sixteen()[i:i+n]
                for i in range(0, len(self.get_all_digits_base_sixteen()), n)]

    # Return double word as an array of 4 strings (bytes) reversed
    # e.g. ['00','00','00','0a'] --> ['0a','00','00','00']
    def get_byte_array_reverse(self):
        return self.get_byte_array()[::-1]

    def get_subtraction_target(self):
        # First get the reversed byte array.
        reverse_byte_array = self.get_byte_array_reverse()
        # Convert it back to a number, well string
        reverse_byte_string = ''.join(reverse_byte_array)
        # Now we convert that base 16 string to an integer
        reverse_byte_as_int = int(reverse_byte_string, 16)
        # And we'll do the math in base 10
        # 0 - targetValue = 0xFFFFFFFF - targetValue + 1
        # 4294967295 - targetValue + 1
        target_answer = 4294967295 - reverse_byte_as_int + 1
        # Response is another EncoderDoubleWord object.  I figured this
        # would be convenient to use since it has the manipulation methods
        return EncoderDoubleWord(target_answer)

class OperandBuilder:

    def __init__(self, encoder_double_word):
        self.encoder_double_word = encoder_double_word

class EncoderParser:

    def __init__(self, input_string):
        self.input_string = input_string

    # Remove extraneous input characters.  This method doesn't need to be
    # called directly.  Happens during the "parse".
    def clean(self):
        clean_byte_string = self.input_string.replace('\r','').replace('\n','')
        clean_byte_string = clean_byte_string.replace(' ','')
        clean_byte_string = clean_byte_string.replace('\\','')

        # Check if we are missing a nibble.
        if len(clean_byte_string) % 2 > 0:
            raise MissingNibbleError(self.input_string)
        return clean_byte_string

    def get_byte_array(self):
        self.clean()
        n = 2
        return [self.input_string[i:i+n] for i in range(0, len(self.input_string), n)]

    def get_inverted_byte_array(self):
        self.clean()
        inverted_byte_array = []
        for i in range(0, 256):
            if "{:02x}".format(i) not in self.get_byte_array():
                inverted_byte_array.append("{:02x}".format(i))
        return inverted_byte_array

class EncoderInputParser(EncoderParser):

    def __init__(self, input_string):
        self.input_string = input_string

    # If needed, we will add NOP to the end of the input to make a nice clean
    # set of double words.  This method doesn't need to be called directly.
    # Happens during the "parse".
    def pad(self):
        while ((len(self.input_string)) / 2) % 4 > 0:
            self.input_string = self.input_string + EncoderInstructions.nop_op_code
        return self.input_string

    # Cleans, pads, and generates a list of EncoderDoubleWord objects
    def parse_words(self):
        words = []
        clean_byte_string = self.clean()

        # We can pad the input
        clean_byte_string = self.pad()
        # Create an array of EncoderDoubleWord objects
        for i in range(0, len(clean_byte_string), 8):
            # We have to prepend the word with 0x to force the initializer to
            # treat the string as a hex value
            words.append(EncoderDoubleWord("0x"+clean_byte_string[i:i+8]))

        return words

class SubtractionEncoder:

    inbytes = ''
    badbytes = ''
    goodbytes = ''
    output_format = ''
    variable_name = ''

    def __init__(self, inputbytes, goodbytes=None, badbytes=None,
                    output_format='python', variable_name='var'):

        self.inbytes = inputbytes
        self.badbytes = badbytes
        self.goodbytes = goodbytes
        self.output_format = output_format
        self.variable_name = variable_name

    def process(self):
        # First, let's get an array of good bytes.
        if self.goodbytes is not None:
            self.goodbytes_array = EncoderParser(self.goodbytes).get_byte_array()
        elif self.badbytes is not None:
            self.badbytes = EncoderParser(self.badbytes).clean()
            self.goodbytes_array = EncoderParser(self.badbytes).get_inverted_byte_array()

        # Second, we will organize the input to array of EncoderDoubleWord's
        words = EncoderInputParser(self.inbytes).parse_words()

        for i in range(0,len(words)):
            print words[i].get_all_digits_base_sixteen(pretty=True)

        print ""

        # Third, we will reverse the array of words since we need to push them
        # on to the stack in reverse order.
        words_reverse = words[::-1]
        for i in range(0,len(words_reverse)):
            print words_reverse[i].get_all_digits_base_sixteen(pretty=True)

        print ""

        # Now let's take a look at the target bytes
        for i in range(0,len(words_reverse)):
            print words_reverse[i].get_subtraction_target().get_all_digits_base_sixteen(pretty=True)

def main():
    parser = argparse.ArgumentParser(description='Encode instructions using the SubtractionEncoder')

    parser.add_argument('--input',
                        help='The string of input bytes',
                        required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--goodbytes',
                        help='The string of allowed bytes')
    group.add_argument('--badbytes',
                        help='The string of disallowed bytes')
    parser.add_argument('--variablename',
                              help='The name of the variable to output',
                              default='var')
    parser.add_argument('--format',
                              help='The output format',
                              choices=['asm','raw','python'],
                              default='python')

    args = parser.parse_args()
    substraction_encoder = SubtractionEncoder(args.input, args.goodbytes,
                                            args.badbytes, args.format,
                                            args.variablename)
    substraction_encoder.process()

if __name__ == "__main__":
   print 'The encoder of last resort when all others fail...'
   print 'At the moment, this is only for x86 instruction set.'
   print '@kevensen'
   main()
