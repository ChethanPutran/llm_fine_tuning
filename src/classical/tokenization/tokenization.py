# from torchtext.data.utils import get_tokenizer
# from torchtext.vocab import build_vocab_from_iterator
from collections import defaultdict
# import spacy 
# import nltk
# from transformers import BertTokenizer,XLNetTokenizer

def count_adjacent(arr):
    pair_counts = defaultdict(int)
    for item,count in arr.items():
        symbols = item.split()
        for i in range(len(symbols)-1):
            pair_counts[symbols[i],symbols[i+1]] += count
    # print(best_pair)
    return pair_counts

def merge_adjacent(arr, pair):
    ser = ' '.join(pair)
    rep = ''.join(pair)
    data = {}
    for item,freq in arr.items():
        data[item.replace(ser,rep)] = freq
    return data

def BPE(text="set new new renew reset renew", K=100):
    vocab = set()
    words = text.split()
    data = defaultdict(int)
    for word in words:
        for w in word:
            vocab.add(w)
        data[' '.join(list(word))] +=1
    print(data)
    for i in range(K):
        pair_counts = count_adjacent(data)
        if not pair_counts:
            break
        pair = max(pair_counts, key=pair_counts.get)
        print(pair)
        vocab.add(''.join(pair))
        data = merge_adjacent(data, pair)


    print(vocab)
    print(data)
    
BPE()


# class Tokenizer:
#     def __init__(self,algo='sentece-piece'):
#         self.tokeneizer = get_tokenizer('spacy')
#         # self.tokeneizer = BertTokenizer.from_pretrained('bert-base-uncased').tokenize #Word-piece
#         # self.tokeneizer = XLNetTokenizer.from_pretrained('xlnet-base-uncased').tokenize #unigram and sentence-piece
#         # self.tokeneizer = spacy.load('en_core_web_sm')
#         # nltk.download('punkt')
#         # self.tokeneizer = nltk.tokenize.word_tokenize
#         # [token.txt for token in tokeneizer.(text)]
        
#     def yield_tokens(self, data_iter):
#         for _,text in data_iter:
#             yield self.tokeneizer(text)

#     def get_vacab(self, dataset, unk_token = '<unk>'):
#         vocab = build_vocab_from_iterator(self.yield_tokens(dataset),specials=[unk_token])
#         vocab.set_default_index(vocab[unk_token])
#         return vocab.get_stoi()

#     def get_preprocessed_tokens(self, dataset,
        #                         sos_token = '<sos>',
        #                         eos_token = '<eos>',
        #                         pas_token = '<pad>',
        #                         ):
        # max_len = 0
        # tokenized_lines = []
        # for line in dataset:
        #     tokenized_line = self.tokeneizer(line)

        #     # Add start and end token
        #     tokenized_line = [sos_token] + tokenized_line + [eos_token]
        #     max_len = max(max_len, len(tokenized_line))
        #     tokenized_lines.append(tokenized_line)
        
        # for i in range(len(tokenized_lines)):
        #     tokenized_lines[i] = tokenized_lines[i] + [pas_token] * (max_len - len(tokenized_lines[i]))

        # return tokenized_lines