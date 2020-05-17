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
                prefix_n_gramm = tuple(sub_list)
                next_elem[prefix_n_gramm].append(tokens[start + cur_depth])

        self.amount_token = defaultdict(list)
        self.next_token = defaultdict(list)

        for prefix_n_gramm, elements in next_elem.items():
            counter = Counter(elements)
            self.next_token[prefix_n_gramm] = list(counter.keys())
            self.amount_token[prefix_n_gramm] = list(counter.values())

    def get_token(self, prefix_n_gramm, set_avaliable_token):
        temp_dict = {key: value for key, value in
                     zip(self.next_token[prefix_n_gramm],
                         self.amount_token[prefix_n_gramm])
                     if key[0] in set_avaliable_token}

        if not temp_dict:
            return None

        return choices(list(temp_dict.keys()),
                       self.normalize(list(temp_dict.values())))[0]

    @staticmethod
    def normalize(list_prob):
        abs_sum = sum(list_prob)
        return [elem / abs_sum for elem in list_prob]


# _______________________TextParser_____________________ #
class TextParser:
    def __init__(self, native_text, depth):
        self.depth = depth
        self.text = native_text

    def parse(self):
        tokens = []
        for word in self.text.split():
            tokens.extend(self.word_to_tokens(word))
        return tokens

    def word_to_tokens(self, word):
        tokens = re.findall(rf"(\w+|\w+'\w+|[{string.punctuation}])", word)
        return tokens


# ________________________TextGenerator______________________ #
class TextGenerator:
    END_OF_SENT = {'!', '.', '?'}
    MIDDLE_OF_SENT = {',', ':', ';', '—'}
    UNORDERED_QUOTES = {"'",  '"'}
    OPEN_BRACK = {'(', '{', '[', '«'}
    END_BRACK = {')', '}', ']', '»'}
    LETTERS = frozenset(string.ascii_letters)

    COLL_BRACK = {'(': ')', '{': '}', '[': ']', '«': '»'}

    def __init__(self, statistic, depth, length):
        self.data = statistic
        self.depth = depth
        self.length = length

    def generate(self):
        self.text = []
        self.stack_punct = []
        self.text_str = ''
        self.state_start = True

        for ord_tok in range(self.length):
            if self.length - ord_tok == len(self.stack_punct):
                break
            for size in range(min(ord_tok, self.depth), -1, -1):
                prefix_n_gramm = tuple(self.text[-size:] if size > 0 else [])
                token = self.data.get_token(prefix_n_gramm,
                                            self.get_avaliable_tokens(ord_tok))
                if token is not None:
                    self.add_token(token)
                    break

        while self.stack_punct:
            self.text_str += self.COLL_BRACK[self.stack_punct[-1]]
            self.stack_punct.pop()

        return self.text_str + '\n'

    def add_token(self, token):
        if token[0] in self.UNORDERED_QUOTES:
            if self.stack_punct and self.stack_punct[-1][0] == '«':
                token = '»'
            else:
                token = '«'

        if token[0] in self.END_OF_SENT:
            self.state_start = True

        if token[0] in self.END_BRACK:
            self.stack_punct.pop()

        if token[0] in self.OPEN_BRACK:
            if self.text and not self.text[-1][0] in self.OPEN_BRACK:
                self.text_str += ' '
            self.stack_punct.append(token)

        if token[0] in self.LETTERS:
            if self.text and not self.text[-1][0] in self.OPEN_BRACK:
                self.text_str += ' '
            if self.state_start:
                token = token.capitalize()
                self.state_start = False

        self.text_str += token
        self.text.append(token)

    def get_avaliable_tokens(self, ord_tok):
        ret_set = set()
        ret_set |= self.LETTERS
        if self.length - ord_tok == len(self.stack_punct) + 1:
            return ret_set

        ret_set |= self.UNORDERED_QUOTES | self.OPEN_BRACK

        if not self.text:
            return ret_set

        if self.stack_punct:
            ret_set.add(self.COLL_BRACK[self.stack_punct[-1]])
        else:
            if self.text[-1][0] in self.LETTERS:
                ret_set |= (self.MIDDLE_OF_SENT |
                            self.END_OF_SENT)
            if self.text[-1][0] in self.END_BRACK:
                ret_set |= self.END_OF_SENT

        return ret_set


# _________________________Main_________________________ #
if __name__ == "__main__":
    args = parse_args()
    if args.mode == 'calculation':
        native_text = read_native_text(args.input_file)
        tokens = TextParser(native_text, args.depth).parse()
        byte_statistic = StatisticData(tokens, args.depth)
        write_byte_statistic(args.output_file, byte_statistic)
        print("The calculation has ended")
    else:
        statistic = read_byte_statistic(args.input_file)
        generator = TextGenerator(statistic, args.depth, args.length)
        pseudo_native_text = generator.generate()
        write_native_text(args.output_file, pseudo_native_text)
        print("The generation has ended")
