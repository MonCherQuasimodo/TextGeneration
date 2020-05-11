from collections import defaultdict
from collections import Counter
from random import choices
from unicodedata import category
import re
import argparse
import sys
import pickle
import string
import json


# _________________________I/O__________________________ #
def read_native_text(input_file_utf):
    return input_file_utf.read().lower()


def write_byte_statistic(output_file_byte, byte_statistic):
    pickle.dump(byte_statistic, output_file_byte, pickle.HIGHEST_PROTOCOL)


def read_byte_statistic(input_file_byte):
    return pickle.load(input_file_byte)


def write_native_text(output_file_utf, text):
    output_file_utf.write(text)


# _________________________Parse_args____________________ #
def parse_args():
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


# _________________________My_Data_Class________________ #
class StatisticData:
    def __init__(self, tokens, depth):
        next_elem = defaultdict(list)

        for cur_depth in range(depth + 1):
            for start in range(len(tokens) - cur_depth):
                sub_list = tokens[start: start + cur_depth]
                hash = tuple(sub_list)
                next_elem[hash].append(tokens[start + cur_depth])

        self.amount_token = defaultdict(list)
        self.next_token = defaultdict(list)

        for hash, elements in next_elem.items():
            counter = Counter(elements)
            self.next_token[hash] = list(counter.keys())
            self.amount_token[hash] = list(counter.values())

    def get_token(self, hash, set_avaliable_token):

        temp_dict = dict(zip(self.next_token[hash], self.amount_token[hash]))
        temp_dict = {key: value for key, value in temp_dict.items()
                     if key[0] in set_avaliable_token}

        if not temp_dict:
            return "There is no elements, that need"

        return choices(list(temp_dict.keys()),
                       StatisticData.normalize(list(temp_dict.values())))[0]

    @staticmethod
    def normalize(list):
        absSum = sum(list)
        return [elem / absSum for elem in list]


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
        tokens = re.split(rf"(\w+|\w+'\w+|[{string.punctuation}])", word)
        tokens = [token for token in tokens if token != '']
        return tokens


# ________________________Generator______________________ #
class TextGenerator:
    end_of_sent = {'!', '.', '?'}
    middle_of_sent = {',', ':', ';', '—'}
    unordered_quotes = {"'",  '"'}
    open_brack = {'(', '{', '[', '«'}
    end_brack = {')', '}', ']', '»'}
    letters = frozenset(string.ascii_letters)

    coll_brack = {'(': ')', '{': '}', '[': ']', '«': '»'}

    def __init__(self, statistic, depth, length):
        self.data = statistic
        self.depth = depth
        self.length = length

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
                hash = tuple(self.text[-size:] if size > 0 else [])
                token = self.data.get_token(hash,
                                            self.get_avaliable_tokens(ord))
                if (token != "There is no elements, that need"):
                    self.add_token(token)
                    break

        while self.stack_punct:
            self.text_str += TextGenerator.coll_brack[self.stack_punct[-1]]
            self.stack_punct.pop()

        return self.text_str + '\n'

    def add_token(self, token):
        if token[0] in TextGenerator.unordered_quotes:
            if self.stack_punct and self.stack_punct[-1][0] == '«':
                token = '»'
            else:
                token = '«'

        if token[0] in TextGenerator.end_of_sent:
            self.state_start = True

        if token[0] in TextGenerator.end_brack:
            self.stack_punct.pop()

        if token[0] in TextGenerator.open_brack:
            if self.text and not self.text[-1][0] in TextGenerator.open_brack:
                self.text_str += ' '
            self.stack_punct.append(token)

        if token[0] in TextGenerator.letters:
            if self.text and not self.text[-1][0] in TextGenerator.open_brack:
                self.text_str += ' '
            if self.state_start:
                token = token.capitalize()
                self.state_start = False

        self.text_str += token
        self.text.append(token)

    def get_avaliable_tokens(self, ord):
        ret_set = set()
        ret_set |= TextGenerator.letters
        if self.length - ord == len(self.stack_punct) + 1:
            return ret_set

        ret_set |= TextGenerator.unordered_quotes | TextGenerator.open_brack

        if not self.text:
            return ret_set

        if self.stack_punct:
            ret_set.add(TextGenerator.coll_brack[self.stack_punct[-1]])
        else:
            if self.text[-1][0] in TextGenerator.letters:
                ret_set |= (TextGenerator.middle_of_sent |
                            TextGenerator.end_of_sent)
            if self.text[-1][0] in TextGenerator.end_brack:
                ret_set |= TextGenerator.end_of_sent

        return ret_set


# _________________________Main_________________________ #
if __name__ == "__main__":
    args = parse_args()
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
