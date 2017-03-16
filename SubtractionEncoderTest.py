import unittest
from SubtractionEncoder import EncoderDoubleWord
from SubtractionEncoder import EncoderDoubleWordTooLargeError
from SubtractionEncoder import EncoderDoubleWordTooSmallError
from SubtractionEncoder import EncoderInputParser
from SubtractionEncoder import MissingNibbleError

class EncoderDoubleWordTest(unittest.TestCase):

    def test_nominal_base_10(self):
        testWord = EncoderDoubleWord(10)
        self.assertEqual(testWord.get_base_ten(), 10)
        self.assertEqual(testWord.get_base_sixteen(), 'a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(), '0000000a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(pretty=True), '0x0000000a')

    def test_nominal_base_16(self):
        testWord = EncoderDoubleWord('A')
        self.assertEqual(testWord.get_base_ten(), 10)
        self.assertEqual(testWord.get_base_sixteen(), 'a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(), '0000000a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(pretty=True), '0x0000000a')

    def test_nominal_base_16_0x(self):
        testWord = EncoderDoubleWord('0xA')
        self.assertEqual(testWord.get_base_ten(), 10)
        self.assertEqual(testWord.get_base_sixteen(), 'a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(), '0000000a')
        self.assertEqual(testWord.get_all_digits_base_sixteen(pretty=True), '0x0000000a')

    def test_get_byte_array(self):
        testWord = EncoderDoubleWord(16909060)
        self.assertEqual(testWord.get_byte_array()[0],"01")
        self.assertEqual(testWord.get_byte_array()[1],"02")
        self.assertEqual(testWord.get_byte_array()[2],"03")
        self.assertEqual(testWord.get_byte_array()[3],"04")

    def test_get_byte_array_reverse(self):
        testWord = EncoderDoubleWord(16909060)
        self.assertEqual(testWord.get_byte_array_reverse()[0],"04")
        self.assertEqual(testWord.get_byte_array_reverse()[1],"03")
        self.assertEqual(testWord.get_byte_array_reverse()[2],"02")
        self.assertEqual(testWord.get_byte_array_reverse()[3],"01")

    def test_unsigned_too_big(self):
        with self.assertRaises(EncoderDoubleWordTooLargeError):
            testWord = EncoderDoubleWord(4294967296)

    def test_signed_too_small(self):
        with self.assertRaises(EncoderDoubleWordTooSmallError):
            testWord = EncoderDoubleWord(-2147483649)

    def test_get_target_answer_one(self):
        # 0x01020304 --> 16909060
        # Reversed 0x04030201 --> 67305985
        testWord = EncoderDoubleWord('0x01020304')
        # Answer should be 4227661310 --> 0xFB FC FD FF
        testAnswer = testWord.get_subtraction_target()
        self.assertEqual(testAnswer.get_byte_array()[0], "fb")
        self.assertEqual(testAnswer.get_byte_array()[1], "fc")
        self.assertEqual(testAnswer.get_byte_array()[2], "fd")
        self.assertEqual(testAnswer.get_byte_array()[3], "ff")

    def test_get_target_answer_two(self):
        # 0xAABBCCDD --> 2864434397
        # Reversed 0xDDCCBBAA --> 3721182122
        testWord = EncoderDoubleWord('0xAABBCCDD')
        # Answer should be 573785174 --> 0x22 33 44 56
        testAnswer = testWord.get_subtraction_target()
        self.assertEqual(testAnswer.get_byte_array()[0], "22")
        self.assertEqual(testAnswer.get_byte_array()[1], "33")
        self.assertEqual(testAnswer.get_byte_array()[2], "44")
        self.assertEqual(testAnswer.get_byte_array()[3], "56")

class EncoderInputParserTest(unittest.TestCase):

    def test_clean(self):
        parser = EncoderInputParser("\n1234")
        self.assertTrue("\n" not in parser.clean())
        self.assertTrue(len(parser.clean())==4)

        parser = EncoderInputParser("\n1234")
        self.assertTrue("\\" not in parser.clean())
        self.assertTrue(len(parser.clean())==4)

        parser = EncoderInputParser("\r1234")
        self.assertTrue("\r" not in parser.clean())
        self.assertTrue(len(parser.clean())==4)

    def test_missing_nibble(self):
        parser = EncoderInputParser("\r123")
        with self.assertRaises(MissingNibbleError):
            parser.parse()

    def test_pad(self):
        parser = EncoderInputParser("12")
        padded = parser.pad()
        self.assertTrue(padded.endswith("909090"))
        self.assertTrue(len(padded) == 8)

    def test_doesnt_pad(self):
        parser = EncoderInputParser("12345678")
        padded = parser.pad()
        self.assertFalse(padded.endswith("909090"))
        self.assertTrue(len(padded) == 8)

    def test_parse(self):
        parser = EncoderInputParser("12345678AA")
        result = parser.parse()
        self.assertTrue(len(result) == 2)
        self.assertTrue('90' not in result[0].get_base_sixteen())
        self.assertTrue(result[1].get_base_sixteen().endswith("909090"))
        self.assertTrue(result[0].get_base_ten() == 305419896)
        self.assertTrue(result[1].get_base_ten() == 2861600912)

if __name__ == '__main__':
    unittest.main()
