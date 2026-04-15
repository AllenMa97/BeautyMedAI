import torch.nn as nn

class Transformer_FFN(nn.Module):
    def __init__(self, input_size, dropout=0.1):
        super(Transformer_FFN, self).__init__()
        self.fc1 = nn.Linear(input_size, 4*input_size)
        self.fc2 = nn.Linear(4*input_size, input_size)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)  # Dropout层

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        return out
