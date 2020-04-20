from collections import defaultdict
from random import choices
from unicodedata import category
import argparse
import sys
import pickle

def sysInput():
    parser = argparse.ArgumentParser(prog='TextGenerator')
    subparsers = parser.add_subparsers(title='Modes', dest='mode', help='Choose one of working modes:')

    parser_calc = subparsers.add_parser('calculation',
                                        help='First mode, create a file with probabilities by the native text')

    parser_calc.add_argument('--inputFile', type=argparse.FileType('r', encoding='UTF-8'),
                             required=True, help='Native text')
    parser_calc.add_argument('--outputFile', type=argparse.FileType('wb', 0),
                             required=True, help='File for probabilities')
    parser_calc.add_argument('--depth', type=int,
                             required=True, help='Depth of algorithm')


    parser_calc = subparsers.add_parser('generation',
                                        help='Generate "Native text" by the file with probabilities')
    parser_calc.add_argument('--inputFile', type=argparse.FileType('rb', 0),
                             required=True, help='File with probabilities')
    parser_calc.add_argument('--outputFile', type=argparse.FileType('w', encoding='UTF-8'),
                             default=sys.stdout, help='File for "Native text"')
    parser_calc.add_argument('--length', type=int,
                             required='True', help='Length of a text')
    parser_calc.add_argument('--depth', type=int,
                             required='True', help='Depth of algorithm')
    return vars(parser.parse_args())

class Data:
    def __init__(self, depth, tokens):
        self.tokensToStatistic(depth, tokens);

    def tokensToStatistic(self, depth, tokens):
        self.data = [defaultdict(dict) for i in range(depth + 1)]

        for curDepth in range(depth + 1):
            for start in range(len(tokens) - curDepth):
                subList = tokens[start : start + curDepth]
                hash_ = (tuple(subList)) #we can use hash
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

    def dataToText(self):
        self.text = []
        self.stackPunct = []
        self.textStr = ''
        for i in range(self.length):
            for size in range(min(i, self.depth), -1, -1):
                textSuffix = self.text[-size :]
                hash_ = tuple(textSuffix) #we can use hash
                if hash_ in self.data.data[size]:
                    token = '*__Initialize__*'
                    count = 0
                    equalProb = False
                    while not self.addToken(token):
                        count += 1
                        if (count > 5):
                            equalProb = True
                        if (count > 100):
                            break
                        token = self.getToken(size, hash_, equalProb)[0]
                    if (count < 100):
                        break
        print (len(self.text))
        return self.textStr

    def addToken(self, token):
        if token == '*__Initialize__*':
            return False

        if category(token[0]) == 'Po':
            if not len(self.text) and len(self.stackPunct) or len(self.text) and category(self.text[-1][0]) == 'Po':
                return False
            self.textStr += token + ' '

        if category(token[0]) == 'Ps':
            self.stackPunct.append(token)
            self.textStr += ' ' + token

        if category(token[0]) == 'Pe':
            if len(self.stackPunct) and ord(tokens[0]) - ord(self.stackPunct.top()[0]) < 3:
                self.stackPunct.pop()
                self.textStr += token + ' '
            else:
                return False

        if category(token[0]).startswith('L'):
            if len(self.text) and category(self.text[-1][0]).startswith('L'):
                self.textStr += ' '
            if not len(self.text) or category(self.text[-1][0]) == 'Po' and not self.text[-1][0] in {',', ':', ';'}:
                self.textStr += token.capitalize()
            else:
                self.textStr += token
        self.text.append(token)
        return True

    def getToken(self, size, hash_, equalProb=False):
        if equalProb:
            return choices(self.data.data[size][hash_][0])
        else:
            return choices(self.data.data[size][hash_][0], self.data.data[size][hash_][1])

    def readFile(file):
        data = pickle.load(file)
        return data

    def writeFile(file, text):
        file.write(text)

if __name__ == "__main__":
    print(category('"'))
    args = sysInput()
    if (args['mode'] == 'calculation'):
        calc = Calculator(args)
    else:
        gen = Generator(args)
