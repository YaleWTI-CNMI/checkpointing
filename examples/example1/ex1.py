# Authors:
# Ping Luo, John Lafferty, and Awni Altabaa 
import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path

from cpl import cpl

# Define the linear regression model
class LinearRegressionModel(nn.Module):
    def __init__(self):
        super(LinearRegressionModel, self).__init__()
        self.linear = nn.Linear(1, 1)
    def forward(self, x):
        return self.linear(x)

# Data loader generator that produces random data
def data_loader(batch_size):
    while True:
        x = torch.randn(batch_size, 1)
        y = 3 * x + 2 + torch.randn(batch_size, 1) * 0.1  # y = 3x + 2 + noise
        yield x, y

# Set device to use bf16 mode
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Initialize model, criterion, and optimizer
model = LinearRegressionModel().to(device)
model = torch.compile(model, mode='default')
criterion = nn.MSELoss()
optimizer = optim.SGD(model.parameters(), lr=0.01)

# Create data loader
batch_size = 32
data_gen = data_loader(batch_size)

mycpl = cpl.CPL()   

# load the checkpoint file if it exists
file_path = Path(mycpl.get_checkpoint_fn())
if file_path.exists():
    checkpoint = torch.load(file_path, weights_only=True)
    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    step_counter = checkpoint['epoch']
    loss = checkpoint['loss']
else:
    # Train the model
    step_counter = 0
    model.train()


for x, y in data_loader(batch_size):
    x, y = x.to(device), y.to(device)
    optimizer.zero_grad()
    #with torch.cuda.amp.autocast(device, dtype=torch.bfloat16):
    with torch.amp.autocast('cuda', dtype=torch.bfloat16):
        outputs = model(x)
        loss = criterion(outputs, y)
    outputs = model(x)
    loss = criterion(outputs, y)
    loss.backward()
    optimizer.step()
    step_counter += 1

    if step_counter % 1000 == 0:
        print(f"Step: {step_counter}; Loss: {loss.item():,.4f}")

    if cpl.check():  
        print()
        print('='*100)
        print('detected preemption flag inside training loop')
        print('exiting gracefully (saving model checkpoint, etc.) ...')
        torch.save({
            'epoch': step_counter,
            'model_state_dict':model.state_dict(),
            'optimizer_state_dict':optimizer.state_dict(),
            'loss':loss}, 'model_checkpoint.pt')
        # wandb.finish()
        # etc...
        print('exiting now')
        print('='*100)
        break

print('Done')
