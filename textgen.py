from collections import defaultdict
from random import choices
from unicodedata import category
import argparse
import sys
import pickle
import string

CONST_EQ = 5
CONST_BR = 100

def sys_input():
    parser = argparse.ArgumentParser(prog='TextGenerator')

    subparsers = parser.add_subparsers(title='Modes',
                                       dest='mode',
                                       help='Choose one of working modes:')

    parser_calc = subparsers.add_parser('calculation',
                                        help='Create a file with prob-ies')

    parser_calc.add_argument('--input_file',
                             type=argparse.FileType('r', encoding='UTF-8'),
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
                             type=argparse.FileType('w', encoding='UTF-8'),
                             default=sys.stdout, help='File for "Native text"')

    parser_calc.add_argument('--length', type=int,
                             required=True, help='Length of a text')

    parser_calc.add_argument('--depth', type=int,
                             required=True, help='Depth of algorithm')
    return vars(parser.parse_args())


class Data:
    def __init__(self, depth, tokens):
        self.tokens_to_statistic(depth, tokens)

    def tokens_to_statistic(self, depth, tokens):
        self.data = [defaultdict(dict) for i in range(depth + 1)]

        for cur_depth in range(depth + 1):
            for start in range(len(tokens) - cur_depth):
                sub_list = tokens[start: start + cur_depth]
                hash_ = (tuple(sub_list))
                if tokens[start + cur_depth] in self.data[cur_depth][hash_]:
                    self.data[cur_depth][hash_][tokens[start + cur_depth]] += 1
                else:
                    self.data[cur_depth][hash_][tokens[start + cur_depth]] = 1

        for cur_depth_dict in self.data:
            for key in cur_depth_dict.keys():
                tokens = list(cur_depth_dict[key].keys())
                abs_sum = sum(cur_depth_dict[key].values())
                normal_probabilities = []
                for i in tokens:
                    normal_probabilities.append(cur_depth_dict[key][i] / abs_sum)
                cur_depth_dict[key] = (tokens, normal_probabilities)

    def __repr__(self):
        output = 'Statistic:\n'
        for i in self.data:
            for c in i.items():
                output += str(c) + '\n'
            output += '\n'
        return output


class Calculator:
    def __init__(self, args):
        self.input_file = args['input_file']
        self.output_file = args['output_file']
        self.depth = args['depth']
        self.calculate()

    def calculate(self):
        text = Calculator.read_file(self.input_file)
        tokens = Calculator.text_to_tokens(text)
        data = Data(self.depth, tokens)
        Calculator.write_file(self.output_file, data)
        print("The calculation has ended")

    def read_file(file):
        return ' '.join(file.readlines())

    def write_file(file, data):
        pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)

    def text_to_tokens(text):
        tokens = []

        for i in text.split():
            tokens.extend(Calculator.word_to_tokens(i))
        return tokens

    def word_to_tokens(word):
        tokens = []
        i = 0

        while i < len(word) - 1 and not word[i].isalpha():
            tokens.append(word[i])
            i += 1
        word = word[i:]

        punct_after = []
        i = len(word) - 1
        while i > 1 and not word[i].isalpha():
            punct_after.append(word[i])
            i -= 1
        punct_after.reverse()
        word = word[:i+1]
        tokens.append(word.lower())
        tokens.extend(punct_after)

        return tokens


class Generator:
    def __init__(self, args):
        self.input_file = args['input_file']
        self.output_file = args['output_file']
        self.depth = args['depth']
        self.length = args['length']
        self.generate()

    def generate(self):
        self.data = Generator.read_file(self.input_file)
        text = self.data_to_text()
        Generator.write_file(self.output_file, text)
        print("The generation has ended")

    def data_to_text(self):
        self.text = []
        self.stack_punct = []
        self.text_str = ''
        self.state = 'start'
        self.wds = [i for i in self.data.data[0][tuple([])][0] if i.isalpha()]

        for i in range(self.length):
            if self.length - i == len(self.stack_punct):
                break
            for size in range(min(i, self.depth), -1, -1):
                text_suffix = self.text[-size:] if size > 0 else []
                hash_ = tuple(text_suffix)
                if hash_ in self.data.data[size]:
                    token = '*__Initialize__*'
                    count = 0
                    equal_prob = False
                    while not self.add_token(token, i):
                        count += 1
                        if count > CONST_EQ:
                            equal_prob = True
                        if count > CONST_BR:
                            break
                        token = self.get_token(size, hash_, equal_prob)[0]
                    if not count > CONST_BR:
                        break
                if size == 0:
                    self.add_token(self.get_word()[0], i)

        coll_brack = {'(': ')', '{': '}', '[': ']', '«': '»'}
        while len(self.stack_punct):
            self.text_str += coll_brack[self.stack_punct[-1]]
            self.stack_punct.pop()

        return self.text_str + '\n'

    def add_token(self, token, ord_elem):
        if token == '*__Initialize__*':
            return False

        end_of_sent = {'!', '.', '?'}
        middle_of_sent = {',', ':', ';'}
        unordered_quotes = {"'",  '"'}
        open_brack = {'(', '{', '[', '«'}
        end_brack = {')', '}', ']', '»'}
        coll_brack = {'(': ')', '{': '}', '[': ']', '«': '»'}
        words = set(string.ascii_letters)

        if self.length - ord_elem == len(self.stack_punct) + 1:
            token = self.get_word()[0]

        if token[0] in unordered_quotes:
            if len(self.stack_punct) and self.stack_punct[-1][0] == '«':
                token = '»'
            else:
                token = '«'

        if token[0] in middle_of_sent or token[0] in end_of_sent:
            if not len(self.text):
                return False
            if self.text[-1][0] in open_brack | middle_of_sent | end_of_sent:
                return False
            if len(self.stack_punct):
                return False
            self.text_str += token
            if token[0] in end_of_sent:
                self.state = 'start'

        if token[0] in end_brack:
            if not len(self.text):
                return False
            if not len(self.stack_punct):
                return False
            if coll_brack[self.stack_punct[-1]] != token:
                return False
            self.stack_punct.pop()
            self.text_str += token

        if token[0] in open_brack:
            if len(self.text) and not self.text[-1][0] in open_brack:
                self.text_str += ' '
            self.stack_punct.append(token)
            self.text_str += token

        if token[0] in words:
            if len(self.text) and not self.text[-1][0] in open_brack:
                self.text_str += ' '
            if self.state == 'start':
                self.text_str += token.capitalize()
                self.state = 'inSent'
            else:
                self.text_str += token

        self.text.append(token)
        return True

    def get_token(self, size, hash_, equal_prob=False):
        if equal_prob:
            return choices(self.data.data[size][hash_][0])
        else:
            return choices(self.data.data[size][hash_][0],
                           self.data.data[size][hash_][1])

    def get_word(self):
        return choices(self.wds)

    def read_file(file):
        return pickle.load(file)

    def write_file(file, text):
        file.write(text)

if __name__ == "__main__":
    args = sys_input()
    if (args['mode'] == 'calculation'):
        calc = Calculator(args)
    else:
        gen = Generator(args)
