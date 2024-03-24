# -*- coding: utf-8 -*-
"""GPaulT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1naGUp3869nXQHXt6AJfuh97bLfGpFiwk
"""

import torch
import torch.nn as nn
from torch.nn import functional as F
import os

# Hyperparameters
batch_size = 64 # Number of independent sequences processing in parallel
block_size = 256 # Max context length for predictions
max_iters = 5000
eval_interval = 500
learning_rate = 3e-4
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
n_embed = 384
n_head = 6
n_layer = 6
dropout = 0.2

torch.manual_seed(1337)

# Avengers Infinity War Script for training
# Read script in
# !wget https://raw.githubusercontent.com/paulchinnam/GPaulT/main/TrainingData/MovieScripts/input.txt
# with open('../trainingData/MovieScripts/infinityWar.txt', 'r', encoding='utf-8') as f:
#   text = f.read()

# Read and concatenate all training data sets
movie_scripts_dir = '../trainingData/MovieScripts' # Directory containing all the scripts
script_files = [f for f in os.listdir(movie_scripts_dir) if f.endswith('.txt')]

texts = []
for script_file in script_files:
    with open(os.path.join(movie_scripts_dir, script_file), 'r', encoding='utf-8') as f:
        texts.append(f.read())

text = ' '.join(texts)  # Concatenate all texts

# Print length of dataset
print("Length of dataset in characters: ", len(text))

# Get all unique characters in dataset
chars = sorted(list(set(text)))
vocab_size = len(chars)

print(f"Available characters: {chars}, vocabulary size: {vocab_size}")

# Mapping from chars to integers
stoi = {ch:i for i,ch in enumerate(chars)}
itos = {i:ch for i,ch in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s] # Encoder: take a string, output list of integers
decode = lambda l: ''.join([itos[i] for i in l]) # Decoder: take a list of integers, output a string

# Train and test splits
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9*len(data)) # Calculate 90% of the length of the data
train_data = data[:n]
val_data = data[n:]

# Data loading
def get_batch(split):
  # Generate a small batch of data of inputs x and targets y
  data = train_data if split == 'train' else val_data
  ix = torch.randint(len(data) - block_size, (batch_size,))
  x = torch.stack([data[i:i + block_size] for i in ix])
  y = torch.stack([data[i + 1: i + block_size + 1] for i in ix])
  x, y = x.to(device), y.to(device)

  return x, y

@torch.no_grad()
def estimate_loss():
  out = {}
  model.eval()
  
  for split in ['train', 'val']:
    losses = torch.zeros(eval_iters)
    
    for k in range(eval_iters):
      X, Y = get_batch(split)
      logits, loss = model(X, Y)
      losses[k] = loss.item()
    
    out[split] = losses.mean()
  
  model.train()

  return out

class Head(nn.Module):
  # One head of self-attention

  def __init__(self, head_size):
    super().__init__()
    self.key = nn.Linear(n_embed, head_size, bias=False)
    self.query = nn.Linear(n_embed, head_size, bias=False)
    self.value = nn.Linear(n_embed, head_size, bias=False)
    self.register_buffer('tril', torch.tril(torch.ones(block_size, block_size)))

    self.dropout = nn.Dropout(dropout)

  def forward(self, x):
    B, T, C = x.shape
    k = self.key(x) # (B, T, C)
    q = self.query(x) # (B, T, C)

    # Compute attention scores ("affinities")
    wei = q @ k.transpose(-2, -1) * C**-0.5 # (B, T, 16) @ (B, 16, T) ---> (B, T, T)
    wei = wei.masked_fill(self.tril[:T, :T] == 0, float('-inf')) # (B, T, T)
    wei = F.softmax(wei, dim=-1)
    wei = self.dropout(wei)

    # Perform the weighted aggregation of the values
    v = self.value(x) # (B, T, C)
    out = wei @ v # (B, T, T) @ (B, T, C) ---> (B, T, C)

    return out
  
class MultiHeadAttention(nn.Module):
  # Multiple heads of self-attention in parallel

  def __init__(self, num_heads, head_size):
    super().__init__()
    self.heads = nn.ModuleList([Head(head_size) for _ in range(num_heads)])
    self.proj = nn.Linear(n_embed, n_embed)
    self.dropout = nn.Dropout(dropout)

  def forward(self, x):
    out = torch.cat([h(x) for h in self.heads], dim=-1)
    out = self.proj(out)

    return out
  
class FeedForward(nn.Module):
  # Linear layer followed by non-linearity

  def __init__(self, n_embed):
    super().__init__()
    self.net = nn.Sequential(
      nn.Linear(n_embed, 4 * n_embed),
      nn.ReLU(),
      nn.Linear(4 * n_embed, n_embed),
      nn.Dropout(dropout),
    )

  def forward(self, x):
    return self.net(x)

class Block(nn.Module):
  # Transformer block: communication followed by computation

  def __init__(self, n_embed, n_head):
    # n_embed: embedding dimension, n_head: the number of heads we want
    super().__init__()
    head_size = n_embed // n_head
    self.sa = MultiHeadAttention(n_head, head_size)
    self.ffwd = FeedForward(n_embed)
    self.ln1 = nn.LayerNorm(n_embed)
    self.ln2 = nn.LayerNorm(n_embed)

  def forward(self, x):
    x = x + self.sa(self.ln1(x))
    x = x + self.ffwd(self.ln2(x))

    return x

# Create the model
class BigramLanguageModel(nn.Module):

  def __init__(self):

    super().__init__()

    # Each token directly reads off the logits for the next token from a lookup table
    self.token_embedding_table = nn.Embedding(vocab_size, n_embed)
    self.position_embedding_table = nn.Embedding(block_size, n_embed)
    self.blocks = nn.Sequential(*[Block(n_embed, n_head=n_head) for _ in range(n_layer)])
    self.ln_f = nn.LayerNorm(n_embed) # Final layer norm
    self.lm_head = nn.Linear(n_embed, vocab_size)

  def forward(self, idx, targets=None):

    B, T = idx.shape
    
    # idx and target are both (B, T) tensor of integers
    tok_embed = self.token_embedding_table(idx) # (B (batch), T (time), C (channel (vocab size)))
    pos_embed = self.position_embedding_table(torch.arange(T, device=device)) # (T, C)
    x = tok_embed + pos_embed # (B, T, C)
    x = self.blocks(x) # (B, T, C)
    logits = self.lm_head(x) # (B, T, vocab_size)

    if targets is None:
      loss = None

    else:
      B, T, C = logits.shape
      logits = logits.view(B*T, C)
      targets = targets.view(B*T)
      loss = F.cross_entropy(logits, targets)

    return logits, loss

  def generate(self, idx, max_new_tokens):
    # idx is array of (B, T) indices in current context

    for _ in range(max_new_tokens):

      # Crop idx to the last block_size tokens
      idx_cond = idx[:, -block_size:]

      # Get the predictions
      logits, loss = self(idx_cond)

      # Focus on last time step
      logits = logits[:, -1, :] # Becomes (B, C)

      # Apply softmax to get probabilities
      probs = F.softmax(logits, dim=-1) # (B, C)

      # Sample from distribution
      idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)

      # Append sampled index to the running sequence
      idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)

    return idx

model = BigramLanguageModel()
m = model.to(device)

# Create pytorch optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

for iter in range(max_iters):

  # Evaluate the loss on the train and eval sets every once in a while
  if iter % eval_interval == 0:
    losses = estimate_loss()
    print(f"Step {iter}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

  # Get sample batch of data
  xb, yb = get_batch('train')

  # Evaluate loss
  logits, loss = m(xb, yb)
  optimizer.zero_grad(set_to_none=True)
  loss.backward()
  optimizer.step()

# Create modelOutputs directory if it doesn't exist
model_outputs_dir = 'modelOutputs'
if not os.path.exists(model_outputs_dir):
    os.makedirs(model_outputs_dir)

# Set the full path for the output file
output_file_path = os.path.join(model_outputs_dir, 'output.txt')

# Generate from the model with max_new_tokens set to 10000
context = torch.zeros((1, 1), dtype=torch.long, device=device)
generated_sequence = m.generate(context, max_new_tokens=10000)[0].tolist()
generated_text = decode(generated_sequence)

# Write generated text to the output file
with open(output_file_path, 'w', encoding='utf-8') as file:
    file.write(generated_text)

# Generate from the model
# context = torch.zeros((1, 1), dtype=torch.long, device=device)
# print(decode(m.generate(context, max_new_tokens=500)[0].tolist()))