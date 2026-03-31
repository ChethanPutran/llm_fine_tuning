import torch
import torch.nn as nn
from pre_processing import PositionalEncoding, Embedding, generate_vocaculary, get_one_hot


class Attention(nn.Module):
    def __init__(self, emd_size, max_len, word_vecs: torch.Tensor = None):
        super().__init__()
        self.K = torch.clone(word_vec) if word_vecs else torch.rand(
            (max_len, emd_size))
        self.Q = torch.clone(word_vec) if word_vecs else torch.rand(
            (max_len, emd_size))
        self.V = torch.clone(word_vec) if word_vecs else torch.rand(
            (max_len, emd_size))

    def get_attention(self, q):
        # h = q @ self.K.T @ self.V
        print(q.size(), self.K.size())
        h = nn.functional.softmax(q @ self.K.T, dim=1).squeeze() @ self.V

        w_ = torch.argmax(h @ self.V.T)
        return w_
print("Hello")

# if __name__ == "__main__":

#     data = """Troll2 is great!
#             Gymkata is great!"""

#     MAX_LEN = 10
#     vocab = generate_vocaculary(data)
#     VOCAB_SIZE = len(vocab)
#     EMBEDDING_SIZE = VOCAB_SIZE  # One hot encoding

#     def generate_token(sentence, vocab, add_=False):
#         data = sentence.split()
#         assert len(
#             data) < MAX_LEN, f"Sequence length must be less than {MAX_LEN}"

#         res = [vocab['<sos>']] if add_ else []
#         for i in data:
#             if i in vocab:
#                 res.append(vocab[i])
#             else:
#                 res.append(vocab['<unk>'])

#         if add_:
#             while len(res) < MAX_LEN-1:
#                 res.append(vocab['<pad>'])

#             res.append(vocab['<eos>'])

#         return res

#     def get_word_vec(tokens):
#         n = len(tokens)
#         word_vecs = torch.zeros((n, VOCAB_SIZE))
#         for i in range(n):
#             word_vecs[i, :] = get_one_hot(tokens[i], VOCAB_SIZE)
#         return word_vecs

#     test = "Gymkata is great"
#     tokens = generate_token(test, vocab)
#     word_vec = get_word_vec(tokens)
#     # print(f"Word vector for {test} is")
#     # print(word_vec)

#     q_word = "Gymkata"
#     q = get_word_vec(generate_token(q_word, vocab))
#     # print(f"Querry {q_word} is")
#     # print(q)

#     attention = Attention(EMBEDDING_SIZE, MAX_LEN)
#     print("Attentioin Score :", attention.get_attention(q).item())
#     print(vocab)
