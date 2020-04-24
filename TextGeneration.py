from collections import defaultdict
from random import choices
from unicodedata import category
import argparse
import sys
import pickle
import string


def sysInput():
    parser = argparse.ArgumentParser(prog='TextGenerator')

    subparsers = parser.add_subparsers(title='Modes',
                                       dest='mode',
                                       help='Choose one of working modes:')

    parser_calc = subparsers.add_parser('calculation',
                                        help='Create a file with prob-ies')

    parser_calc.add_argument('--inputFile',
                             type=argparse.FileType('r', encoding='UTF-8'),
                             required=True, help='Native text')

    parser_calc.add_argument('--outputFile', type=argparse.FileType('wb', 0),
                             required=True, help='File for probabilities')

    parser_calc.add_argument('--depth', type=int,
                             required=True, help='Depth of algorithm')

    parser_calc = subparsers.add_parser('generation',
                                        help='Generate "Native text"')

    parser_calc.add_argument('--inputFile', type=argparse.FileType('rb', 0),
                             required=True, help='File with probabilities')

    parser_calc.add_argument('--outputFile',
                             type=argparse.FileType('w', encoding='UTF-8'),
                             default=sys.stdout, help='File for "Native text"')

    parser_calc.add_argument('--length', type=int,
                             required='True', help='Length of a text')

    parser_calc.add_argument('--depth', type=int,
                             required='True', help='Depth of algorithm')
    return vars(parser.parse_args())


class Data:
    def __init__(self, depth, tokens):
        self.tokensToStatistic(depth, tokens)

    def tokensToStatistic(self, depth, tokens):
        self.data = [defaultdict(dict) for i in range(depth + 1)]

        for curDepth in range(depth + 1):
            for start in range(len(tokens) - curDepth):
                subList = tokens[start: start + curDepth]
                hash_ = (tuple(subList))
                if tokens[start + curDepth] in self.data[curDepth][hash_]:
                    self.data[curDepth][hash_][tokens[start + curDepth]] += 1
                else:
                    self.data[curDepth][hash_][tokens[start + curDepth]] = 1

        for curDepthDict in self.data:
            for key in curDepthDict.keys():
                tokens = list(curDepthDict[key].keys())
                absSum = sum(curDepthDict[key].values())
                normalProbabilities = []
                for i in tokens:
                    normalProbabilities.append(curDepthDict[key][i] / absSum)
                curDepthDict[key] = (tokens, normalProbabilities)

    def __repr__(self):
        output = 'Statistic:\n'
        for i in self.data:
            for c in i.items():
                output += str(c) + '\n'
            output += '\n'
        return output


class Calculator:
    def __init__(self, args):
        self.inputFile = args['inputFile']
        self.outputFile = args['outputFile']
        self.depth = args['depth']
        self.calculate()

    def calculate(self):
        text = Calculator.readFile(self.inputFile)
        tokens = Calculator.textToTokens(text)
        data = Data(self.depth, tokens)
        Calculator.writeFile(self.outputFile, data)
        print("The calculation has ended")

    def readFile(file):
        return ' '.join(file.readlines())

    def writeFile(file, data):
        pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)

    def textToTokens(text):
        tokens = []

        for i in text.split():
            tokens.extend(Calculator.wordToTokens(i))
        return tokens

    def wordToTokens(word):
        tokens = []
        i = 0

        while i < len(word) - 1 and not word[i].isalpha():
            tokens.append(word[i])
            i += 1
        word = word[i:]

        punctAfter = []
        i = len(word) - 1
        while i > 1 and not word[i].isalpha():
            punctAfter.append(word[i])
            i -= 1
        punctAfter.reverse()
        word = word[:i+1]
        tokens.append(word.lower())
        tokens.extend(punctAfter)

        return tokens


class Generator:
    def __init__(self, args):
        self.inputFile = args['inputFile']
        self.outputFile = args['outputFile']
        self.depth = args['depth']
        self.length = args['length']
        self.generate()

    def generate(self):
        self.data = Generator.readFile(self.inputFile)
        text = self.dataToText()
        Generator.writeFile(self.outputFile, text)
        print("The generation has ended")

    def dataToText(self):
        self.text = []
        self.stackPunct = []
        self.textStr = ''
        self.state = 'start'
        self.constEq = 5
        self.constBr = 100
        self.wds = [i for i in self.data.data[0][tuple([])][0] if i.isalpha()]

        for i in range(self.length):
            if self.length - i == len(self.stackPunct):
                break
            for size in range(min(i, self.depth), -1, -1):
                textSuffix = self.text[-size:] if size > 0 else []
                hash_ = tuple(textSuffix)
                if hash_ in self.data.data[size]:
                    token = '*__Initialize__*'
                    count = 0
                    equalProb = False
                    while not self.addToken(token, i):
                        count += 1
                        if count > self.constEq:
                            equalProb = True
                        if count > self.constBr:
                            break
                        token = self.getToken(size, hash_, equalProb)[0]
                    if not count > self.constBr:
                        break
                if size == 0:
                    self.addToken(self.getWord()[0], i)

        collBrack = {'(': ')', '{': '}', '[': ']', '«': '»'}
        while len(self.stackPunct):
            self.textStr += collBrack[self.stackPunct[-1]]
            self.stackPunct.pop()

        return self.textStr + '\n'

    def addToken(self, token, ordElem):
        if token == '*__Initialize__*':
            return False

        endOfSent = {'!', '.', '?'}
        middleofSent = {',', ':', ';'}
        unorderedQuotes = {"'",  '"'}
        openBrack = {'(', '{', '[', '«'}
        endBrack = {')', '}', ']', '»'}
        collBrack = {'(': ')', '{': '}', '[': ']', '«': '»'}
        words = set(string.ascii_letters)

        if self.length - ordElem == len(self.stackPunct) + 1:
            token = self.getWord()[0]

        if token[0] in unorderedQuotes:
            if len(self.stackPunct) and self.stackPunct[-1][0] == '«':
                token = '»'
            else:
                token = '«'

        if token[0] in middleofSent or token[0] in endOfSent:
            if not len(self.text):
                return False
            if self.text[-1][0] in openBrack | middleofSent | endOfSent:
                return False
            if len(self.stackPunct):
                return False
            self.textStr += token
            if token[0] in endOfSent:
                self.state = 'start'

        if token[0] in endBrack:
            if not len(self.text):
                return False
            if not len(self.stackPunct):
                return False
            if collBrack[self.stackPunct[-1]] != token:
                return False
            self.stackPunct.pop()
            self.textStr += token

        if token[0] in openBrack:
            if len(self.text) and not self.text[-1][0] in openBrack:
                self.textStr += ' '
            self.stackPunct.append(token)
            self.textStr += token

        if token[0] in words:
            if len(self.text) and not self.text[-1][0] in openBrack:
                self.textStr += ' '
            if self.state == 'start':
                self.textStr += token.capitalize()
                self.state = 'inSent'
            else:
                self.textStr += token

        self.text.append(token)
        return True

    def getToken(self, size, hash_, equalProb=False):
        if equalProb:
            return choices(self.data.data[size][hash_][0])
        else:
            return choices(self.data.data[size][hash_][0],
                           self.data.data[size][hash_][1])

    def getWord(self):
        return choices(self.wds)

    def readFile(file):
        return pickle.load(file)

    def writeFile(file, text):
        file.write(text)

if __name__ == "__main__":
    args = sysInput()
    if (args['mode'] == 'calculation'):
        calc = Calculator(args)
    else:
        gen = Generator(args)
