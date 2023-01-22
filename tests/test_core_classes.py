import unittest
from pregex.core.classes import *
from itertools import permutations
from pregex.core.pre import Pregex, _Type
from pregex.core.tokens import Backslash, CarriageReturn, Copyright, Newline, Registered, Tab, Space
from pregex.core.exceptions import CannotBeNegatedException, GlobalWordCharSubtractionException, CannotBeUnionedException, \
    CannotBeSubtractedException, InvalidRangeException, EmptyClassException, \
    NotEnoughArgumentsException, InvalidArgumentTypeException



def get_permutations(*classes: str):
    return set(f"[{''.join(p)}]" for p in permutations(classes))


def get_negated_permutations(*classes: str):
    return set(f"[^{''.join(p)}]" for p in permutations(classes))


class Test__Class(unittest.TestCase):

    def test_any_class_bitwise_or(self):
        self.assertTrue(str(AnyLowercaseLetter() | AnyDigit()) \
            in get_permutations("a-z", "\d"))
        self.assertEqual(str(AnyFrom("a", "b") | AnyFrom("c", "d")), "[a-d]")

    def test_any_class_bitwise_or_with_subset(self):
        self.assertTrue(str(AnyLetter() | AnyLowercaseLetter()) \
            in get_permutations("a-z", "A-Z"))
        self.assertEqual(str(AnyFrom("a", "b", "c") | AnyFrom("a", "b")), "[a-c]")

    def test_any_class_bitwise_or_with_intersection(self):
        self.assertEqual(str(AnyFrom("a", "b") | AnyFrom("b", "c")), "[a-c]")

    def test_any_class_bitwise_or_with_overlapping_ranges(self):
        self.assertTrue(str(AnyBetween("a", "d") | AnyBetween("b", "k")) == "[a-k]")
        self.assertTrue(str(AnyBetween("a", "d") | AnyBetween("e", "k")) == "[a-k]")
        self.assertTrue(str(AnyBetween("A", "D") | AnyBetween("B", "K")) == "[A-K]")
        self.assertTrue(str(AnyBetween("A", "D") | AnyBetween("E", "K")) == "[A-K]")
        self.assertTrue(str(AnyBetween("0", "3") | AnyBetween("2", "7")) == "[0-7]")
        self.assertTrue(str(AnyBetween("0", "3") | AnyBetween("4", "7")) == "[0-7]")

    def test_any_class_bitwise_or_with_chars_in_ranges(self):
        self.assertTrue(str(AnyBetween("a", "d") | AnyFrom("c")) == "[a-d]")
        self.assertTrue(str(AnyBetween("A", "D") | AnyFrom("C")) == "[A-D]")
        self.assertTrue(str(AnyBetween("0", "3") | AnyFrom("2")) == "[0-3]")

    def test_any_class_bitwise_or_with_tokens(self):
        self.assertTrue(str(AnyDigit() | 'z') in get_permutations("\d", "z"))
        self.assertTrue(str(AnyDigit() | Newline()) in get_permutations("\d", "\n"))

    def test_any_class_complex_bitwise_or(self):
        self.assertEqual(str(AnyFrom('a') | AnyBetween('b', 'd')), "[a-d]")
        self.assertEqual(str(AnyBetween('1', '5') | AnyFrom('6', '7')), "[1-7]")
        self.assertEqual(str(AnyFrom('a') | AnyBetween('b', 'e') | AnyFrom('f') | AnyBetween('g', 'h')), "[a-h]")

    def test_any_class_token_char_right_bitwise_or(self):
        self.assertEqual(str('6' | AnyBetween('1', '5')), "[1-6]")
        self.assertEqual(str(Space() | AnyBetween(Tab(), CarriageReturn())), "\s")

    def test_any_class_bitwise_or_with_escaped_chars(self):
        self.assertTrue(str(AnyLowercaseLetter() | AnyFrom("^")) \
            in get_permutations("a-z", "\^"))

    def test_any_class_subtraction(self):
        self.assertEqual(str(AnyBetween('a', 'e') - AnyBetween('d', 'k')), "[a-c]")
        self.assertEqual(str(AnyBetween('d', 'k') - AnyBetween('a', 'e')), "[f-k]")
        self.assertTrue(str(AnyBetween('a', 'z') - AnyBetween('g', 'k')) in 
            get_permutations('a-f', 'l-z'))

    def test_any_class_subtraction_with_tokens(self):
        self.assertTrue(str(AnyDigit() - '5') in get_permutations("0-4", "6-9"))
        self.assertTrue(str(AnyWhitespace() - Newline()) in get_permutations(" ", "\t", "\x0b-\r"))

    def test_any_class_right_subtraction_with_tokens(self):
        self.assertRaises(EmptyClassException,  AnyDigit().__rsub__, '5')
        self.assertRaises(EmptyClassException,  AnyWhitespace().__rsub__, Newline())

    def test_any_class_complex_subtraction(self):
        self.assertTrue(str(AnyWordChar() - AnyBetween('b', 'd')) in 
            get_permutations('A-Z', '\d', '_', 'a', 'e-z'))
        self.assertTrue(str(AnyWordChar() - AnyFrom('1', '_', '8')) in 
            get_permutations('A-Z', 'a-z', '0', '2-7', '9'))
        self.assertEqual(str(AnyPunctuation() - (AnyBetween('!', '/') \
            | AnyBetween(':', '@') | AnyBetween('[', '`'))), "[{-~]")

    def test_any_class_subtraction_with_escaped_chars(self):
        self.assertTrue(str((AnyLetter() | AnyFrom("-")) - AnyFrom("-")) \
            in get_permutations("a-z", "A-Z"))

    def test_any_between_class_on_hyphen_range(self):
        self.assertEqual(str(AnyBetween('-', 'a')), "[\--a]")
        self.assertEqual(str(AnyBetween('+', '-')), "[+-\-]")

    def test_any_between_class_on_two_char_range_subtraction(self):
        self.assertEqual(str(AnyBetween('a', 'b') - 'b'), 'a')

    def test_any_between_class_on_two_char_range_subtraction_conversion(self):
        self.assertTrue(str(AnyBetween('a', 'b') - 'd') in get_permutations('a', 'b'))
        
    def test_any_class_bitwise_or_on_cannot_be_unioned_exception(self):
        any_letter, any_but_digit = AnyLetter(), AnyButDigit()
        self.assertRaises(CannotBeUnionedException, any_letter.__or__, any_but_digit)
        self.assertRaises(CannotBeUnionedException, any_letter.__ror__, any_but_digit)

    def test_any_class_on_cannot_be_subtracted_exception(self):
        any_letter, any_but_digit = AnyLetter(), AnyButDigit()
        self.assertRaises(CannotBeSubtractedException, any_letter.__sub__, any_but_digit)
        self.assertRaises(CannotBeSubtractedException, any_letter.__rsub__, any_but_digit)

    def test_any_class_on_empty_class_exception(self):
        any_letter = AnyLetter()
        self.assertRaises(EmptyClassException, any_letter.__sub__, any_letter)
        self.assertRaises(EmptyClassException, any_letter.__rsub__, any_letter)


class TestNegated__Class(unittest.TestCase):
    
    def test_any_but_class_bitwise_or(self):
        self.assertTrue(str(AnyButLowercaseLetter() | AnyButDigit()) \
            in get_negated_permutations("a-z", "\d"))
        self.assertEqual(str(AnyButFrom("a", "b") | AnyButFrom("c", "d")), "[^a-d]")

    def test_any_but_class_bitwise_or_with_subset(self):
        self.assertTrue(str(AnyButLetter() | ~AnyLowercaseLetter()) \
            in get_negated_permutations("a-z", "A-Z"))
        self.assertEqual(str(AnyButFrom("a", "b", "c") | AnyButFrom("a", "b")), "[^a-c]")

    def test_any_but_class_bitwise_or_with_intersection(self):
        self.assertEqual(str(AnyButFrom("a", "b") | AnyButFrom("b", "c")), "[^a-c]")

    def test_any_but_class_bitwise_or_with_overlapping_ranges(self):
        self.assertTrue(str(AnyButBetween("a", "d") | AnyButBetween("b", "k")) == "[^a-k]")
        self.assertTrue(str(AnyButBetween("a", "d") | AnyButBetween("d", "k")) == "[^a-k]")
        self.assertTrue(str(AnyButBetween("A", "D") | AnyButBetween("B", "K")) == "[^A-K]")
        self.assertTrue(str(AnyButBetween("A", "D") | AnyButBetween("E", "K")) == "[^A-K]")
        self.assertTrue(str(AnyButBetween("0", "3") | AnyButBetween("2", "7")) == "[^0-7]")
        self.assertTrue(str(AnyButBetween("0", "3") | AnyButBetween("4", "7")) == "[^0-7]")

    def test_any_but_class_bitwise_or_with_chars_in_ranges(self):
        self.assertTrue(str(AnyButBetween("a", "d") | AnyButFrom("c")) == "[^a-d]")
        self.assertTrue(str(AnyButBetween("A", "D") | AnyButFrom("C")) == "[^A-D]")
        self.assertTrue(str(AnyButBetween("0", "3") | AnyButFrom("2")) == "[^0-3]")

    def test_any_but_class_bitwise_or_with_tokens(self):
        with self.assertRaises(CannotBeUnionedException):
            _ = AnyButDigit() | '5'
        with self.assertRaises(CannotBeUnionedException):
            _ = AnyButWhitespace() | Newline()

    def test_any_but_class_complex_bitwise_or(self):
        self.assertEqual(str(AnyButFrom('a') | AnyButBetween('b', 'd')), "[^a-d]")
        self.assertEqual(str(AnyButBetween('1', '5') | AnyButFrom('6', '7')), "[^1-7]")
        self.assertEqual(str(AnyButFrom('a') | AnyButBetween('b', 'e') | AnyButFrom('f') | AnyButBetween('g', 'h')),
            "[^a-h]")

    def test_any_but_class_bitwise_or_with_escaped_chars(self):
        self.assertTrue(str(AnyButLowercaseLetter() | AnyButFrom("^")) \
            in get_negated_permutations("a-z", "\^"))

    def test_any_but_class_subtraction(self):
        self.assertEqual(str(AnyButBetween('a', 'e') - AnyButBetween('d', 'k')), "[^a-c]")
        self.assertEqual(str(AnyButBetween('d', 'k') - AnyButBetween('a', 'e')), "[^f-k]")
        self.assertTrue(str(AnyButBetween('a', 'z') - AnyButBetween('g', 'k')) in 
            get_negated_permutations('a-f', 'l-z'))

    def test_any_but_class_subtraction_with_tokens(self):
        with self.assertRaises(CannotBeSubtractedException):
            _ = AnyButDigit() - '5'
        with self.assertRaises(CannotBeSubtractedException):
            _ = AnyButWhitespace() - Newline()

    def test_any_but_class_complex_subtraction(self):
        self.assertTrue(str(AnyButWordChar() - AnyButBetween('b', 'd')) in 
            get_negated_permutations('A-Z', '\d', '_', 'a', 'e-z'))
        self.assertTrue(str(AnyButWordChar() - AnyButFrom('1', '_', '8')) in 
            get_negated_permutations('A-Z', 'a-z', '0', '2-7', '9'))
        self.assertEqual(str(AnyButPunctuation() - (AnyButBetween('!', '/') \
            | AnyButBetween(':', '@') | AnyButBetween('[', '`'))), "[^{-~]")

    def test_any_but_class_subtraction_with_escaped_chars(self):
        self.assertTrue(str((AnyButLetter() | AnyButFrom("-")) - AnyButFrom("-")) \
            in get_negated_permutations("a-z", "A-Z"))

    def test_any_but_class_bitwise_or_on_cannot_be_unioned_exception(self):
        any_but_letter, any_digit = AnyButLetter(), AnyDigit()
        self.assertRaises(CannotBeUnionedException, any_but_letter.__or__, any_digit)
        self.assertRaises(CannotBeUnionedException, any_but_letter.__ror__, any_digit)
        self.assertRaises(CannotBeUnionedException, any_but_letter.__or__, '0')
        self.assertRaises(CannotBeUnionedException, any_but_letter.__ror__, '0')

    def test_any_but_class_on_cannot_be_subtracted_exception(self):
        any_but_letter, any_digit = AnyButLetter(), AnyDigit()
        self.assertRaises(CannotBeSubtractedException, any_but_letter.__sub__, any_digit)
        self.assertRaises(CannotBeSubtractedException, any_but_letter.__rsub__, any_digit)
        self.assertRaises(CannotBeSubtractedException, any_but_letter.__sub__, '0')
        self.assertRaises(CannotBeSubtractedException, any_but_letter.__rsub__, '0')

    def test_any_but_class_on_empty_class_exception(self):
        any_but_letter = AnyButLetter()
        self.assertRaises(EmptyClassException, any_but_letter.__sub__, any_but_letter)
        self.assertRaises(EmptyClassException, any_but_letter.__rsub__, any_but_letter)


class TestAny(unittest.TestCase):

    def test_any(self):
        self.assertEqual(str(Any()), ".")

    def test_any_on_type(self):
        self.assertEqual(Any()._get_type(), _Type.Class)

    def test_any_on_newline_match(self):
        self.assertTrue(Any().get_matches("\n"), ["\n"])

    def test_any_on_bitwise_or(self):
        self.assertEqual(str(Any() | AnyLetter()), ".")
        self.assertEqual(str(AnyLetter() | Any()), ".")

    def test_any_on_subtraction(self):
        self.assertEqual(str(Any() - AnyDigit()), "\D")

    def test_any_cannot_be_negated_exception(self):
        with self.assertRaises(CannotBeNegatedException):
            _ = ~Any()

    def test_any_subtraction_on_empty_class_exception(self):
        with self.assertRaises(EmptyClassException):
            _ = AnyDigit() - Any()


class TestAnyLetter(unittest.TestCase):

    def test_any_letter(self):
        self.assertTrue(AnyLetter()._get_verbose_pattern() in get_permutations('a-z', 'A-Z'))

    def test_any_letter_on_type(self):
        self.assertEqual(AnyLetter()._get_type(), _Type.Class)


class TestAnyLowercaseLetter(unittest.TestCase):

    def test_any_lowercase_letter(self):
        self.assertEqual(str(AnyLowercaseLetter()), "[a-z]")

    def test_any_lowercase_letter_on_type(self):
        self.assertEqual(AnyLowercaseLetter()._get_type(), _Type.Class)


class TestAnyUppercaseLetter(unittest.TestCase):

    def test_any_uppercase_letter(self):
        self.assertEqual(str(AnyUppercaseLetter()), "[A-Z]")

    def test_any_uppercase_letter_on_type(self):
        self.assertEqual(AnyUppercaseLetter()._get_type(), _Type.Class)
        

class TestAnyDigit(unittest.TestCase):

    def test_any_digit(self):
        self.assertEqual(str(AnyDigit()), "\d")

    def test_any_digit_on_type(self):
        self.assertEqual(AnyDigit()._get_type(), _Type.Class)


class TestAnyWordChar(unittest.TestCase):

    perms = get_permutations("A-Z", "a-z", "\d", "_")

    def test_any_word_char(self):
        self.assertTrue(str(AnyWordChar(is_global=False)) in self.perms)
        self.assertEqual(str(AnyWordChar(is_global=True)), "\w")

    def test_any_word_char_on_type(self):
        self.assertEqual(AnyWordChar(is_global=False)._get_type(), _Type.Class)
        self.assertEqual(AnyWordChar(is_global=True)._get_type(), _Type.Class)

    def test_any_word_char_is_global_invert(self):
        self.assertEqual(str(~AnyWordChar(is_global=True)), '\W')

    def test_any_word_char_match_on_foreign_characters(self):
        self.assertEqual((6 * AnyWordChar(is_global=False)).get_matches("Øदάö大Б"), [])
        self.assertEqual((6 * AnyWordChar(is_global=True)).get_matches("Øदάö大Б"), ["Øदάö大Б"])

    def test_any_word_char_combine_with_subsets(self):
        self.assertTrue(str(AnyWordChar(is_global=False) | (AnyLetter() | AnyDigit())) in self.perms)
        self.assertTrue(str(AnyWordChar(is_global=False) | AnyLetter()) in self.perms)
        self.assertTrue(str(AnyWordChar(is_global=False) | AnyLowercaseLetter()) in self.perms)
        self.assertTrue(str(AnyWordChar(is_global=False) | AnyUppercaseLetter()) in self.perms)
        self.assertTrue(str(AnyWordChar(is_global=False) | AnyDigit()) in self.perms)

    def test_any_word_char_foreign_combine_with_subsets(self):
        self.assertEqual(str(AnyWordChar(is_global=True) | (AnyLetter() | AnyDigit())), "\w")
        self.assertEqual(str(AnyWordChar(is_global=True) | AnyLetter()), "\w")
        self.assertEqual(str(AnyWordChar(is_global=True) | AnyLowercaseLetter()), "\w")
        self.assertEqual(str(AnyWordChar(is_global=True) | AnyUppercaseLetter()), "\w")
        self.assertEqual(str(AnyWordChar(is_global=True) | AnyDigit()), "\w")
        self.assertEqual(str(AnyWordChar(is_global=True) | AnyWordChar()), "\w")

    def test_any_word_char_result_from_subsets(self):
        self.assertTrue(str(AnyLetter() | (AnyDigit() | AnyFrom("_"))) in
            get_permutations("A-Z", "a-z", "\d", "_"))

    def test_any_word_char_global_word_char_exception(self):
        with self.assertRaises(GlobalWordCharSubtractionException):
            _ = AnyWordChar(is_global=True) - AnyLetter()


class TestAnyPunctuation(unittest.TestCase):

    def test_any_punctuation(self):
        self.assertTrue(str(AnyPunctuation()._get_verbose_pattern()) in
            get_permutations('!-\/', ':-@', '\[-`', '{-~'))

    def test_any_punctuation_on_type(self):
        self.assertEqual(AnyPunctuation()._get_type(), _Type.Class)


class TestAnyWhitespace(unittest.TestCase):

    def test_any_whitespace(self):
        self.assertEqual(str(AnyWhitespace()), "\s")

    def test_any_whitespace_on_type(self):
        self.assertEqual(AnyWhitespace()._get_type(), _Type.Class)

    def test_any_whitespace_combine_with_subsets(self):
        self.assertEqual(str(AnyWhitespace() | AnyFrom(" ", "\r")), "\s")

    def test_any_whitespace_result_from_subsets(self):
        self.assertEqual(str(AnyFrom(' ', '\t', '\n', '\r', '\x0b') | AnyFrom('\x0c')), "\s")


class TestAnyBetween(unittest.TestCase):

    def test_any_between(self):
        for start, end in [("a", "c"), ("1", "5"), ("!", ")"), (Copyright(), Registered())]:
            self.assertEqual(str(AnyBetween(start, end)), f"[{start}-{end}]")

    def test_any_between_on_type(self):
        self.assertEqual(AnyBetween("a", "z")._get_type(), _Type.Class)

    def test_any_between_on_match(self):
        text = "a-b\\0Agpz"
        self.assertEqual(AnyBetween("a", "k").get_matches(text), ['a', 'b', 'g'])

    def test_any_between_on_invalid_range_exception(self):
        for start, end in [("z", "a"), ("9", "0"), (")", "!")]:
            self.assertRaises(InvalidRangeException, AnyBetween, start, end)

    def test_any_between_on_invalid_argument_type_exception(self):
        for t in ("aa", True, 1, 1.1):
            self.assertRaises(InvalidArgumentTypeException, AnyFrom, t, t)


class TestAnyFrom(unittest.TestCase):

    def test_any_from(self):
        tokens = ("a", "c", Backslash(), Pregex("!"))
        self.assertTrue(str(AnyFrom(*tokens)) in get_permutations("a", "c", "\\\\", "!"))

    def test_any_from_on_type(self):
        self.assertEqual(AnyFrom("a", "b")._get_type(), _Type.Class)
        self.assertNotEqual(AnyFrom("a")._get_type(), _Type.Class)

    def test_any_from_on_match(self):
        text = "a-\\0A"
        self.assertEqual(AnyFrom("a", "A", Backslash()).get_matches(text), ['a', '\\', 'A'])

    def test_any_from_on_not_enough_arguments_exception(self):
        self.assertRaises(NotEnoughArgumentsException, AnyFrom)

    def test_any_from_on_invalid_argument_type_exception(self):
        for t in ("aa", True, 1, 1.1):
            self.assertRaises(InvalidArgumentTypeException, AnyFrom, t)


class TestAnyButLetter(unittest.TestCase):

    def test_any_but_letter(self):
        pattern = "[^a-zA-Z]"
        self.assertTrue((~AnyLetter())._get_verbose_pattern() in get_negated_permutations('a-z', 'A-Z'))
        self.assertTrue(AnyButLetter()._get_verbose_pattern() in get_negated_permutations('a-z', 'A-Z'))

    def test_any_but_letter_on_type(self):
        self.assertEqual(AnyButLetter()._get_type(), _Type.Class)


class TestAnyButLowercaseLetter(unittest.TestCase):

    def test_any_but_lowercase_letter(self):
        pattern = "[^a-z]"
        self.assertEqual(str(~AnyLowercaseLetter()), pattern)
        self.assertEqual(str(AnyButLowercaseLetter()), pattern)

    def test_any_but_lowercase_letter_on_type(self):
        self.assertEqual(AnyButLowercaseLetter()._get_type(), _Type.Class)


class TestAnyButUppercaseLetter(unittest.TestCase):

    def test_any_but_uppercase_letter(self):
        pattern = "[^A-Z]"
        self.assertEqual(str(~AnyUppercaseLetter()), pattern)
        self.assertEqual(str(AnyButUppercaseLetter()), pattern)

    def test_any_but_uppercase_letter_on_type(self):
        self.assertEqual(AnyButUppercaseLetter()._get_type(), _Type.Class)
        

class TestAnyButDigit(unittest.TestCase):

    def test_any_but_digit(self):
        pattern = "\D"
        self.assertEqual(str(~AnyDigit()), pattern)
        self.assertEqual(str(AnyButDigit()), pattern)

    def test_any_but_digit_on_type(self):
        self.assertEqual(AnyButDigit()._get_type(), _Type.Class)


class TestAnyButWordChar(unittest.TestCase):

    perms = get_negated_permutations("A-Z", "a-z", "\d", "_")

    def test_any_but_word_char(self):
        self.assertTrue(str(AnyButWordChar(is_global=False))
            in get_negated_permutations("A-Z", "a-z", "\d", "_"))
        self.assertEqual(str(AnyButWordChar(is_global=True)), "\W")

    def test_any_but_word_char_on_type(self):
        self.assertEqual(AnyButWordChar(is_global=False)._get_type(), _Type.Class)
        self.assertEqual(AnyButWordChar(is_global=True)._get_type(), _Type.Class)

    def test_any_but_word_char_is_global_invert(self):
        self.assertEqual(str(~AnyButWordChar(is_global=True)), '\w')

    def test_any_word_char_combine_with_subsets(self):
        self.assertTrue(str(AnyButWordChar(is_global=False) | (AnyButLetter() | AnyButDigit()))
            in self.perms)
        self.assertTrue(str(AnyButWordChar(is_global=False) | AnyButLetter()) in self.perms)
        self.assertTrue(str(AnyButWordChar(is_global=False) | AnyButLowercaseLetter()) in self.perms)
        self.assertTrue(str(AnyButWordChar(is_global=False) | AnyButUppercaseLetter()) in self.perms)
        self.assertTrue(str(AnyButWordChar(is_global=False) | AnyButDigit()) in self.perms)

    def test_any_word_char_foreign_combine_with_subsets(self):
        self.assertEqual(str(AnyButWordChar(is_global=True) | (AnyButLetter() | AnyButDigit())), "\W")
        self.assertEqual(str(AnyButWordChar(is_global=True) | AnyButLetter()), "\W")
        self.assertEqual(str(AnyButWordChar(is_global=True) | AnyButLowercaseLetter()), "\W")
        self.assertEqual(str(AnyButWordChar(is_global=True) | AnyButUppercaseLetter()), "\W")
        self.assertEqual(str(AnyButWordChar(is_global=True) | AnyButDigit()), "\W")
        self.assertEqual(str(AnyButWordChar(is_global=True) | AnyButWordChar()), "\W")

    def test_any_word_char_foreign_char_exception(self):
        with self.assertRaises(GlobalWordCharSubtractionException):
            _ = AnyButWordChar(is_global=True) - AnyButLetter()


class TestAnyButPunctuation(unittest.TestCase):

    perms = get_negated_permutations("!-\/", ":-@", "\[-`", "{-~")

    def test_any_but_punctuation(self):
        self.assertTrue((~AnyPunctuation())._get_verbose_pattern() in self.perms)
        self.assertTrue(AnyButPunctuation()._get_verbose_pattern() in self.perms) 

    def test_any_but_punctuation_on_type(self):
        self.assertEqual(AnyButPunctuation()._get_type(), _Type.Class)


class TestAnyButWhitespace(unittest.TestCase):

    def test_any_but_whitespace(self):
        pattern = "\S"
        self.assertEqual(str(~AnyWhitespace()), pattern)
        self.assertEqual(str(AnyButWhitespace()), pattern)

    def test_any_but_whitespace_on_type(self):
        self.assertEqual(AnyButWhitespace()._get_type(), _Type.Class)


class TestAnyButBetween(unittest.TestCase):

    def test_any_but_between(self):
        for start, end in [("a", "c"), ("1", "5"), (Copyright(), Registered())]:
            self.assertEqual(str(AnyButBetween(start, end)), f"[^{start}-{end}]")
            self.assertEqual(str(~AnyBetween(start, end)), f"[^{start}-{end}]")

    def test_any_but_between_on_type(self):
        self.assertEqual(AnyButBetween(start="a", end="z")._get_type(), _Type.Class)

    def test_any_between_on_match(self):
        text = "a-b\\0Agpz"
        self.assertEqual(AnyButBetween("a", "k").get_matches(text), ['-', '\\', '0', 'A', 'p', 'z'])
        self.assertEqual((~AnyBetween("a", "k")).get_matches(text), ['-', '\\', '0', 'A', 'p', 'z'])

    def test_any_but_between_on_invalid_argument_type_exception(self):
        for non_token in ("aa", True, 1, 1.1):
            self.assertRaises(InvalidArgumentTypeException, AnyButBetween, non_token, non_token)
            with self.assertRaises(InvalidArgumentTypeException):
                _ = ~AnyBetween(non_token, non_token)

    def test_any_but_between_on_invalid_range_exception(self):
        for start, end in [("z", "a"), ("9", "0"), ("(", "!")]:
            self.assertRaises(InvalidRangeException, AnyButBetween, start, end)
            with self.assertRaises(InvalidRangeException):
                _ = ~AnyBetween(start, end)


class TestAnyButFrom(unittest.TestCase):

    def test_any_but_from(self):
        tokens = ("a", "c", Backslash(), Pregex("!"))
        self.assertTrue(str(~AnyFrom(*tokens)) in get_negated_permutations("a", "c", "\\\\", "!"))
        self.assertTrue(str(AnyButFrom(*tokens)) in get_negated_permutations("a", "c", "\\\\", "!"))

    def test_any_but_from_on_type(self):
        self.assertEqual(AnyButFrom("a", "b")._get_type(), _Type.Class)
        self.assertEqual(AnyButFrom("a")._get_type(), _Type.Class)

    def test_any_from_on_match(self):
        text = "a-\\0A"
        self.assertEqual(AnyButFrom("a", "A", Backslash()).get_matches(text), ['-', '0'])
        self.assertEqual((~AnyFrom("a", "A", Backslash())).get_matches(text), ['-', '0'])

    def test_any_but_from_on_not_enough_arguments_exception(self):
        self.assertRaises(NotEnoughArgumentsException, AnyButFrom)

    def test_any_but_from_on_invalid_argument_type_exception(self):
        for non_token in ("aa", True, 1, 1.1):
            with self.assertRaises(InvalidArgumentTypeException):
                _ = ~AnyFrom(non_token)
            self.assertRaises(InvalidArgumentTypeException, AnyButFrom, non_token)


class TestAnyGermanLetter(unittest.TestCase):

    def test_any_german_letter(self):
        agl = str(AnyGermanLetter())
        for c in ("A-Z", "a-z", "ä", "ö", "ü", "Ä", "Ö", "Ü", "ß", "ẞ"):
            self.assertTrue(c in agl)
            agl = agl.replace(c, "")
        self.assertTrue(agl, "")

    def test_any_german_letter_on_type(self):
        self.assertEqual(AnyGermanLetter()._get_type(), _Type.Class)

    def test_any_german_letter_on_matches(self):
        self.assertEqual((3 * AnyGermanLetter()).get_matches("für"), ["für"])


class TestAnyButGermanLetter(unittest.TestCase):

    def test_any_but_german_letter(self):
        agl = str(AnyButGermanLetter())
        for c in ("A-Z", "a-z", "ä", "ö", "ü", "Ä", "Ö", "Ü", "ß", "ẞ"):
            self.assertTrue(c in agl)
            agl = agl.replace(c, "")
        self.assertTrue(agl, "")

    def test_any_but_german_letter_on_type(self):
        self.assertEqual(AnyButGermanLetter()._get_type(), _Type.Class)

    def test_any_but_german_letter_on_matches(self):
        self.assertEqual((AnyButGermanLetter()).get_matches("für"), [])


class TestAnyGreekLetter(unittest.TestCase):

    def test_any_greek_letter(self):
        self.assertTrue(str(AnyGreekLetter()) in get_permutations("Ά", "Έ-ώ"))

    def test_any_greek_letter_on_type(self):
        self.assertEqual(AnyGreekLetter()._get_type(), _Type.Class)

    def test_any_greek_letter_on_matches(self):
        self.assertEqual((4 * AnyGreekLetter()).get_matches("Γειά"), ["Γειά"])


class TestAnyButGreekLetter(unittest.TestCase):

    def test_any_but_greek_letter(self):
        self.assertTrue(str(AnyButGreekLetter()) in get_negated_permutations("Ά", "Έ-ώ"))

    def test_any_but_greek_letter_on_type(self):
        self.assertEqual(AnyButGreekLetter()._get_type(), _Type.Class)

    def test_any_but_greek_letter_on_matches(self):
        self.assertEqual(AnyButGreekLetter().get_matches("Γειά"), [])


class TestAnyCyrillicLetter(unittest.TestCase):

    def test_any_cyrillic_letter(self):
        self.assertTrue(str(AnyCyrillicLetter()) in get_permutations("Ѐ-ӿ"))

    def test_any_cyrillic_letter_on_type(self):
        self.assertEqual(AnyCyrillicLetter()._get_type(), _Type.Class)

    def test_any_cyrillic_letter_on_matches(self):
        self.assertEqual((6 * AnyCyrillicLetter()).get_matches("Привет"), ["Привет"])


class TestAnyButCyrillicLetter(unittest.TestCase):

    def test_any_but_cyrillic_letter(self):
        self.assertTrue(str(AnyButCyrillicLetter()) in get_negated_permutations("Ѐ-ӿ"))

    def test_any_but_cyrillic_letter_on_type(self):
        self.assertEqual(AnyButCyrillicLetter()._get_type(), _Type.Class)

    def test_any_but_cyrillic_letter_on_matches(self):
        self.assertEqual((AnyButCyrillicLetter()).get_matches("Привет"), [])


class TestAnyCJK(unittest.TestCase):

    def test_any_cjk(self):
        self.assertTrue(str(AnyCJK()) in get_permutations("\u4e00-\u9fd5"))

    def test_any_cjk_on_type(self):
        self.assertEqual(AnyCJK()._get_type(), _Type.Class)

    def test_any_cjk_on_matches(self):
        self.assertEqual((2 * AnyCJK()).get_matches("你好"), ["你好"])


class TestAnyButCJK(unittest.TestCase):

    def test_any_but_cjk(self):
        self.assertTrue(str(AnyButCJK()) in get_negated_permutations("\u4e00-\u9fd5"))

    def test_any_but_cjk_on_type(self):
        self.assertEqual(AnyButCJK()._get_type(), _Type.Class)

    def test_any_but_cjk_on_matches(self):
        self.assertEqual((AnyButCJK()).get_matches("你好"), [])


class TestAnyHebrewLetter(unittest.TestCase):

    def test_any_hebrew_letter(self):
        self.assertTrue(str(AnyHebrewLetter()) in get_permutations("\u0590-\u05ff"))

    def test_any_hebrew_letter_on_type(self):
        self.assertEqual(AnyHebrewLetter()._get_type(), _Type.Class)

    def test_any_hebrew_letter_on_matches(self):
        self.assertEqual((4 * AnyHebrewLetter()).get_matches("שלום"), ["שלום"])


class TestAnyButHebrewLetter(unittest.TestCase):

    def test_any_but_hebrew_letter(self):
        self.assertTrue(str(AnyButHebrewLetter()) in get_negated_permutations("\u0590-\u05ff"))

    def test_any_but_hebrew_letter_on_type(self):
        self.assertEqual(AnyButHebrewLetter()._get_type(), _Type.Class)

    def test_any_but_hebrew_letter_on_matches(self):
        self.assertEqual((AnyButHebrewLetter()).get_matches("שלום"), [])


class TestAnyKoreanLetter(unittest.TestCase):

    def test_any_korean_letter(self):
        self.assertTrue(str(AnyKoreanLetter()) in get_permutations("\u3131-\u314e", "\uac00-\ud7a3"))

    def test_any_korean_letter_on_type(self):
        self.assertEqual(AnyKoreanLetter()._get_type(), _Type.Class)

    def test_any_korean_letter_on_matches(self):
        self.assertEqual((5 * AnyKoreanLetter()).get_matches("안녕하세요"), ["안녕하세요"])


class TestAnyButKoreanLetter(unittest.TestCase):

    def test_any_but_korean_letter(self):
        self.assertTrue(str(AnyButKoreanLetter()) in get_negated_permutations("\u3131-\u314e", "\uac00-\ud7a3"))

    def test_any_but_korean_letter_on_type(self):
        self.assertEqual(AnyButKoreanLetter()._get_type(), _Type.Class)

    def test_any_but_korean_letter_on_matches(self):
        self.assertEqual((AnyButKoreanLetter()).get_matches("안녕하세요"), [])


if __name__=="__main__":
    unittest.main()