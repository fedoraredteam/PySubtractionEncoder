#!/usr/bin/python

import argparse
import sys


# Exception for a word that is too large
class EncoderDoubleWordTooLargeError(Exception):

    def __init__(self, value):
        print "The value %s is too large for a signed double word." + \
            " It must be less than 4,294,967,295" % str(value)


# Exception for a word that is too small
class EncoderDoubleWordTooSmallError(Exception):

    def __init__(self, value):
        print "The value %s is too small for an unsigned double word.  " + \
            "It must be larger than -2,147,483,648" % str(value)


class MissingNibbleError(Exception):

    def __init__(self, byte_string):
        print "Something may have gone wrong here.  It seems that you " + \
            "may be missing a nibble. The byte string is of length %d." + \
            "  The string is %s" % (len(byte_string), byte_string)


class UnableToFindOperandsError(Exception):

    def __init__(self, byte_string):
        print "We tried but we were unable to find a set of workable" + \
            " bytes for the value %s given the set " + \
            "of good bytes." % byte_string


class InvalidResultError(Exception):
    def __init__(self, result, expected_result, target_word,
                 operand_one, operand_two, operand_three):
        print result
        print expected_result
        print target_word
        print "Our math borked.  We expected %d but got %d for target word %s." % (int(result), int(expected_result), target_word)
        print "Operand One: %s" % operand_one
        print "Operand Two: %s" % operand_two
        print "Operand Three: %s" % operand_three


class EncoderInstructions:
    nop_op_code = '90'
    sub_eax_op_code = '2d'
    push_esp_op_code = '54'
    pop_esp_op_code = '5c'
    push_eax_op_code = '50'
    pop_eax_op_code = '58'
    zero_out_eax_1_op_code = '254A4D4E55'
    zero_out_eax_2_op_code = '253532312A'

    nop = '  NOP'
    sub_eax = '  SUB EAX,'
    push_esp = '  PUSH ESP'
    pop_esp = '  POP ESP'
    push_eax = '  PUSH EAX'
    pop_eax = '  POP EAX'
    zero_out_eax_1 = '  AND EAX,0x554E4D4A'
    zero_out_eax_2 = '  AND EAX,0x2A313235'


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

    # Returns an EncoderDoubleWord object
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
        return EncoderDoubleWordTarget(target_answer)


# The EncoderDoubleWordReverse encapsulates the target bytes
# for the calculation.  As an extension of the EncoderDoubleWord class, the
# EncoderDoubleWordTarget contains the same convenient manipulation methods
# as well as the methods to obtain the three operands.  These three operands,
# when added together, will equal the double word target.
class EncoderDoubleWordTarget(EncoderDoubleWord):

    operand_one = []
    operand_two = []
    operand_three = []

    def __init__(self, value):
        # TODO: Need to do a call to super
        self.value = value
        self.operand_one = []
        self.operand_two = []
        self.operand_three = []

    def check(self, x, y, target, carry=0):
        if (2 * int(x, 16)) + int(y, 16) + carry == int(target, 16):
            return True
        return False

    def calculate(self, goodbytes_array):
        # Start at the LSB and work towards the MSB
        i = 3
        found = False
        # The carry list will hold the carry for each byte.  Eventhough this
        # is a four byte, double word, there are five columns.  The zero column
        # column handles any overflow
        #
        # carry[0] carry[1]       carry[2]       carry[3]       carry[4]
        #          operand_one[0] operand_one[1] operand_one[2] operand_one[3]
        #   +      operand_two[0] operand_two[1] operand_two[2] operand_two[3]
        #   +      operand_thr[0] operand_thr[1] operand_thr[2] operand_thr[3]
        # --------------------------------------------------------------------
        #          byte_array[0]  byte_array[1]  byte_array[2]  byte_array[3]

        carry = [0,0,0,0,0]

        while(i > -1):
            # If this is the first time dealing with this byte,
            # the carry on the next MSB will be zero.
            if carry[i] == 0:
                target_byte = self.get_byte_array()[i]
            # However, if this is the second or third (unlikely)
            # time we are dealing with the byte, the carry will have
            # been incremented.  Therefore we will convert the byte to
            # an integer, add 256 (times the carry), and convert
            # it back to a string representation of the byte.
            elif carry[i] > 0:
                    target_byte = "{:02x}".format(
                                  int(self.get_byte_array()[i], 16)
                                  + (256 * carry[i]))


            for x in range(0, len(goodbytes_array)):
                for y in range(0, len(goodbytes_array)):
                    # If we have found a workable set of values and haven't
                    # previously found a set, we will add these values to the
                    # result arrays.  It's possible multiple combinations will
                    # work, but we just need to capture the first working set.
                    if self.check(goodbytes_array[x],
                                goodbytes_array[y],
                                target_byte, carry[i+1]) and not found:
                        self.operand_one.insert(0, goodbytes_array[x])
                        self.operand_two.insert(0, goodbytes_array[x])
                        self.operand_three.insert(0, goodbytes_array[y])
                        found = True
                    # Otherwise, just run out the loops.  Yes, this is silly
                    # but putting this here keeps me sane.
                    else:
                        pass
            # If we found a set, we will move to the next MSB
            if found:
                i = i - 1
                found = False
            # Otherwise, we need to try again, incrementing the carry
            elif not found:
                carry[i] = carry[i] + 1

            # The largest value a set of three bytes could sum is 0x2FD (765)
            # Therefore, if we haven't found a set of three values by now, we
            # won't.  Therefore, throw in the towl.
            if carry[i] > 2:
                raise UnableToFindOperandsError


    def get_operand_one(self):
        return EncoderDoubleWord('0x'+''.join(self.operand_one))

    def get_operand_two(self):
        return EncoderDoubleWord('0x'+''.join(self.operand_two))

    def get_operand_three(self):
        return EncoderDoubleWord('0x'+''.join(self.operand_three))

    def verify_result(self):

        test_sum = self.get_operand_one().get_base_ten() + \
                self.get_operand_two().get_base_ten() + \
                self.get_operand_three().get_base_ten()

        # If test_sum is > 0xFFFFFFFF (4294967295), we'll go out on a limb
        # and assume it's due to overflow.  We will then subtract
        # 0x100000000 as necessary.
        while test_sum > 4294967296:
            test_sum = test_sum - 4294967296

        if test_sum != self.get_base_ten():
            raise InvalidResultError(test_sum,
                                     self.get_base_ten(),
                                     self.get_all_digits_base_sixteen(
                                                    pretty=True),
                                     self.get_operand_one().get_all_digits_base_sixteen(pretty=True),
                                     self.get_operand_two().get_all_digits_base_sixteen(pretty=True),
                                     self.get_operand_three().get_all_digits_base_sixteen(pretty=True))


class EncoderParser:

    def __init__(self, input_string):
        self.input_string = input_string

    # Remove extraneous input characters.  This method doesn't need to be
    # called directly.  Happens during the "parse".
    def clean(self):
        clean_byte_string = self.input_string.replace('\r', '')
        clean_byte_string = clean_byte_string.replace('\n', '')
        clean_byte_string = clean_byte_string.replace(' ', '')
        clean_byte_string = clean_byte_string.replace('\\', '')

        # Check if we are missing a nibble.
        if len(clean_byte_string) % 2 > 0:
            raise MissingNibbleError(self.input_string)
        return clean_byte_string

    def get_byte_array(self):
        self.clean()
        n = 2
        return [self.input_string[i:i+n]
                for i in range(0, len(self.input_string), n)]

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
    goodbytes_array = []
    badbytes_array = []
    words = []
    words_reverse = []

    def __init__(self, inputbytes, goodbytes=None, badbytes=None,
                 output_format='python', variable_name='var'):

        self.inbytes = inputbytes
        self.badbytes = badbytes
        self.goodbytes = goodbytes
        self.output_format = output_format
        self.variable_name = variable_name
        self.words = []
        self.words_reverse = []
        self.goodbytes_array = []
        self.badbytes_array = []

    def process(self):
        # First, let's get an array of good bytes.
        if self.goodbytes is not None:
            self.goodbytes_array = EncoderParser(self.goodbytes).get_byte_array()
        elif self.badbytes is not None:
            self.badbytes = EncoderParser(self.badbytes).clean()
            self.goodbytes_array = EncoderParser(self.badbytes).get_inverted_byte_array()

        # Second, we will organize the input to array of EncoderDoubleWord's
        self.words = EncoderInputParser(self.inbytes).parse_words()
        self.words_reverse = self.words[::-1]
        self.process_asm()

    def process_asm(self):
        print '[SECTION .text]'
        print 'global _start'
        print '_start:'
        print EncoderInstructions.push_esp
        print EncoderInstructions.pop_eax
        for i in range(0, len(self.words_reverse)):
            # Print the zero out EAX instructions
            print EncoderInstructions.zero_out_eax_1
            print EncoderInstructions.zero_out_eax_2
            # Let's calcualte the operands
            substraction_target = self.words_reverse[i].get_subtraction_target()
            substraction_target.calculate(self.goodbytes_array)
            # We'll do a quick sanity check
            substraction_target.verify_result()
            # Assign the operands to objects for readability
            operand_one = substraction_target.get_operand_one()
            operand_two = substraction_target.get_operand_two()
            operand_three = substraction_target.get_operand_three()
            # Print the instructions
            print EncoderInstructions.sub_eax + operand_one.get_all_digits_base_sixteen(pretty=True)
            print EncoderInstructions.sub_eax + operand_two.get_all_digits_base_sixteen(pretty=True)
            print EncoderInstructions.sub_eax + operand_three.get_all_digits_base_sixteen(pretty=True)
            # Print out the instruction to push to the stack
            print EncoderInstructions.push_eax


def main():
    parser = argparse.ArgumentParser(description='Encode instructions' +
                                     ' using the SubtractionEncoder')

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
                        choices=['asm', 'raw', 'python'],
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
