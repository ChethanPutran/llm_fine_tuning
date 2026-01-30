from tokenization import Tokenizer
import torch

sentence = """
As for a line segment, we specify a line with two endpoints. 
Starting with the corresponding line segment, we find other 
line segments that share at least two points with the original
line segment. In this way we extend the original line segment
indefinitely. The set of all possible line segments findable 
in this way constitutes a line. A line extends indefinitely 
in a single dimension. Its length, having no limit, is infinite.
Like the line segments that constitute it, it has no width or
height. You may specify a line by specifying any two points
within the line. For any two points, only one line passes 
through both points. On the other hand, an unlimited number
of lines pass through any single point.
"""
sentences = sentence.split('.')
tokenizer = Tokenizer()
vocab = tokenizer.get_vacab(sentences)

input_ids = lambda x: [torch.tensor(vocab[token] for token in tokenizer.yield_tokens(sentence))
                       for sentence in sentences]
def one_hot_encoding(word):
    ohv = [0]*len(vocab)
    if word in vocab:
        ohv[vocab[word]] = 1
    return ohv

indices = input_ids(sentences)
print(indices)
