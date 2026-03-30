from torch.utils.data import Dataset, DataLoader
from tokenization import Tokenizer
from torch.nn.utils.rnn import pad_sequence
import torch

class CustomDataset(Dataset):
    def __init__(self,sentences) -> None:
        super().__init__()
        self.sentences = sentences

    def __len__(self):
        return len(self.sentences)
    
    def __getitem__(self, index):
        return self.sentences[index]



def collation_function(batch):
    tensor_batch = []

    for sample in batch:
        tokens = tokenizer.yield_tokens(sample)
        tensor_batch.append(torch.tensor([vocab[token] for token in tokens]))
    
    padded_batch = pad_sequence(batch, batch_first=True,padding_value=0)
    return padded_batch


if __name__ == "__main__":

    sentences = """
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
    tokenizer = Tokenizer()
    dataset = CustomDataset(sentences=sentences)
    vocab = tokenizer.get_vacab(dataset)
    batch_size = 2

    data_loader = DataLoader(dataset,batch_size=batch_size, shuffle=True, collate_fn=collation_function)


    for batch in data_loader:
        padded_batch = pad_sequence(batch, batch_first=True,padding_value=0)
