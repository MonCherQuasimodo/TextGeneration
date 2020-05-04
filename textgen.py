from collections import defaultdict
from random import choices
from unicodedata import category
import re
import argparse
import sys
import pickle
import string


# _________________________I/O__________________________ #
def read_native_text(input_file_utf):
    return input_file_utf.read()


def write_byte_statistic(output_file_byte, byte_statistic):
    pickle.dump(byte_statistic, output_file_byte, pickle.HIGHEST_PROTOCOL)


def read_byte_statistic(input_file_byte):
    return pickle.load(input_file_byte)


def write_native_text(output_file_utf, text):
    output_file_utf.write(text)


# _________________________Sys_Input____________________ #
def sys_input():
    parser = argparse.ArgumentParser(prog='TextGenerator')

    subparsers = parser.add_subparsers(title='Modes',
                                       dest='mode',
                                       help='Choose one of working modes:')

    parser_calc = subparsers.add_parser('calculation',
                                        help='Create a file with prob-ies')

    parser_calc.add_argument('--input_file',
                             type=argparse.FileType('r'),
                             required=True, help='Native text')

    parser_calc.add_argument('--output_file', type=argparse.FileType('wb', 0),
                             required=True, help='File for probabilities')

    parser_calc.add_argument('--depth', type=int,
                             required=True, help='Depth of algorithm')

    parser_calc = subparsers.add_parser('generation',
                                        help='Generate "Native text"')

    parser_calc.add_argument('--input_file', type=argparse.FileType('rb', 0),
                             required=True, help='File with probabilities')

    parser_calc.add_argument('--output_file',
                             type=argparse.FileType('w'),
                             default=sys.stdout, help='File for "Native text"')

    parser_calc.add_argument('--length', type=int,
                             required=True, help='Length of a text')

    parser_calc.add_argument('--depth', type=int,
                             required=True, help='Depth of algorithm')
    return parser.parse_args()


def get_def_dict_int():
    return defaultdict(int)


# _________________________My_Data_Class________________ #
class StatisticData:
    def __init__(self, tokens, depth):
        self.data = [defaultdict(get_def_dict_int) for i in range(depth + 1)]

        for cur_depth in range(depth + 1):
            for start in range(len(tokens) - cur_depth):
                sub_list = tokens[start: start + cur_depth]
                hash_ = (tuple(sub_list))
                self.data[cur_depth][hash_][tokens[start + cur_depth]] += 1

        for cur_depth_dict in self.data:
            for key in cur_depth_dict.keys():
                tokens = list(cur_depth_dict[key].keys())
                abs_sum = sum(cur_depth_dict[key].values())
                normal_prob = [cur_depth_dict[key][token] / abs_sum
                               for token in tokens]
                cur_depth_dict[key] = (tokens, normal_prob)

    def getWordList(self):
        return [token for token in self.data[0][tuple()][0] if token.isalpha()]

    def __repr__(self):
        output = 'Statistic:\n'
        for depth in self.data:
            for c in depth.items():
                output += str(c) + '\n'
            output += '\n'
        return output


# _______________________Calculator_____________________ #
class ProbabilitiesCalculator:
    def __init__(self, native_text, depth):
        self.depth = depth
        self.text = native_text

    def calculate(self):
        tokens = self.text_to_tokens()
        statistic = StatisticData(tokens, self.depth)
        print("The calculation has ended")
        return statistic

    def text_to_tokens(self):
        tokens = []
        for word in self.text.split():
            tokens.extend(self.word_to_tokens(word))
        return tokens

    def word_to_tokens(self, word):
        tokens = []

        pos = 0
        while pos < len(word) - 1 and not word[pos].isalpha():
            tokens.append(word[pos])
            pos += 1
        word = word[pos:]

        punct_after = []
        pos = len(word) - 1
        while pos > 1 and not word[pos].isalpha():
            punct_after.append(word[pos])
            pos -= 1
        punct_after.reverse()
        word = word[:pos+1]
        tokens.append(word.lower())
        tokens.extend(punct_after)

        return tokens


# ________________________Generator______________________ #
class TextGenerator:
    def __init__(self, statistic, depth, length):
        self.data = statistic
        self.depth = depth
        self.length = length

        self.end_of_sent = {'!', '.', '?'}
        self.middle_of_sent = {',', ':', ';', '—'}
        self.unordered_quotes = {"'",  '"'}
        self.open_brack = {'(', '{', '[', '«'}
        self.end_brack = {')', '}', ']', '»'}
        self.letters = set(string.ascii_letters)

        self.all_symb = (
            self.end_of_sent | self.middle_of_sent | self.unordered_quotes |
            self.open_brack | self.end_brack | self.letters
        )

        self.coll_brack = {'(': ')', '{': '}', '[': ']', '«': '»'}

    def generate(self):
        text = self.data_to_text()
        print("The generation has ended")
        return text

    def data_to_text(self):
        self.text = []
        self.stack_punct = []
        self.text_str = ''
        self.state_start = True

        for ord in range(self.length):
            if self.length - ord == len(self.stack_punct):
                break
            for size in range(min(ord, self.depth), -1, -1):
                hash_ = tuple(self.text[-size:] if size > 0 else [])
                if hash_ in self.data.data[size]:
                    if self.add_token(self.get_token(size, hash_), ord):
                        break
                    if self.add_token(self.get_token(size, hash_, True), ord):
                        break
                if size == 0:
                    self.add_token(self.get_word(), ord)

        while self.stack_punct:
            self.text_str += self.coll_brack[self.stack_punct[-1]]
            self.stack_punct.pop()
        return self.text_str + '\n'

    def add_token(self, token, ord_elem):
        if token[0] not in self.all_symb:
            return False

        if self.length - ord_elem == len(self.stack_punct) + 1:
            token = self.get_word()

        if token[0] in self.unordered_quotes:
            if self.stack_punct and self.stack_punct[-1][0] == '«':
                token = '»'
            else:
                token = '«'

        if token[0] in self.middle_of_sent or token[0] in self.end_of_sent:
            if not self.text:
                return False
            if self.text[-1][0] in (self.open_brack | self.middle_of_sent |
                                    self.end_of_sent):
                return False
            if self.stack_punct:
                return False
            self.text_str += token
            if token[0] in self.end_of_sent:
                self.state_start = True

        if token[0] in self.end_brack:
            if not self.text:
                return False
            if not self.stack_punct:
                return False
            if self.coll_brack[self.stack_punct[-1]] != token:
                return False
            self.stack_punct.pop()
            self.text_str += token

        if token[0] in self.open_brack:
            if self.text and not self.text[-1][0] in self.open_brack:
                self.text_str += ' '
            self.stack_punct.append(token)
            self.text_str += token

        if token[0] in self.letters:
            if self.text and not self.text[-1][0] in self.open_brack:
                self.text_str += ' '
            if self.state_start:
                self.text_str += token.capitalize()
                self.state_start = False
            else:
                self.text_str += token

        self.text.append(token)
        return True

    def get_token(self, size, hash_, equal_prob=False):
        if equal_prob:
            return choices(self.data.data[size][hash_][0])[0]
        else:
            return choices(self.data.data[size][hash_][0],
                           self.data.data[size][hash_][1])[0]

    def get_word(self):
        return choices(self.data.getWordList())[0]

# _________________________Main_________________________ #
if __name__ == "__main__":
    args = sys_input()
    if (args.mode == 'calculation'):
        native_text = read_native_text(args.input_file)
        calculator = ProbabilitiesCalculator(native_text, args.depth)
        byte_statistic = calculator.calculate()
        write_byte_statistic(args.output_file, byte_statistic)
    else:
        statistic = read_byte_statistic(args.input_file)
        generator = TextGenerator(statistic, args.depth, args.length)
        pseudo_native_text = generator.generate()
        write_native_text(args.output_file, pseudo_native_text)
