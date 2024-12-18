# -*- coding: utf-8 -*-
"""train_mnist_fm_custom_labels.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1J6hMYiJRIfCXfUx0mmwWVRqZIosLbkd_
"""

import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torchvision import datasets, transforms

# Simulate arguments using argparse.Namespace
args = argparse.Namespace(
    seed=1,
    seed_data=1,
    unlabeled_weight=1.0,
    batch_size=100,
    count=10,
    balance=True,
    epochs=300,
    labels='/path/to/labels/file'  # specify the correct path for the labels file
)

# Seed setting
torch.manual_seed(args.seed)
np.random.seed(args.seed_data)

# Gaussian Noise Layer
class GaussianNoise(nn.Module):
    def __init__(self, sigma):
        super(GaussianNoise, self).__init__()
        self.sigma = sigma

    def forward(self, x):
        if self.training:  # Only add noise during training
            noise = torch.randn_like(x) * self.sigma
            return x + noise
        return x

# Generator Model
class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()
        self.fc1 = nn.Sequential(nn.Linear(100, 500), nn.Softplus())
        self.fc2 = nn.Sequential(nn.Linear(500, 500), nn.Softplus())
        self.fc3 = nn.Linear(500, 28*28)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.sigmoid(self.fc3(x))
        return x

# Discriminator Model
class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.fc1 = nn.Sequential(nn.Linear(28*28, 1000), GaussianNoise(0.3))
        self.fc2 = nn.Sequential(nn.Linear(1000, 500), GaussianNoise(0.5))
        self.fc3 = nn.Sequential(nn.Linear(500, 250), GaussianNoise(0.5))
        self.fc4 = nn.Sequential(nn.Linear(250, 250), GaussianNoise(0.5))
        self.fc5 = nn.Linear(250, 10)  # No noise on the last layer

    def forward(self, x):
        x = x.view(x.size(0), -1)  # Flatten input
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.fc3(x)
        x = self.fc4(x)
        x = self.fc5(x)
        return x

# Instantiate models
gen = Generator()
disc = Discriminator()

# Check the models
print(gen)
print(disc)

# Loss and optimizers
criterion = nn.CrossEntropyLoss()
gen_optimizer = optim.Adam(gen.parameters(), lr=0.003)
disc_optimizer = optim.Adam(disc.parameters(), lr=0.003)

# Load MNIST data
transform = transforms.ToTensor()
train_data = datasets.MNIST(root='./data', train=False, transform=transform, download=True)
train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)

# Training loop
for epoch in range(args.epochs):
    for i, (images, labels) in enumerate(train_loader):
        # Reshape and add noise
        images = images.view(-1, 28*28)

        # Train Discriminator
        disc_optimizer.zero_grad()

        # Label data
        outputs = disc(images)
        loss_lab = criterion(outputs, labels)

        # Unlabeled data (use generator data)
        noise = torch.randn(args.batch_size, 100)
        gen_data = gen(noise).detach()
        outputs_unl = disc(gen_data)
        loss_unl = criterion(outputs_unl, torch.zeros_like(outputs_unl))

        # Calculate discriminator loss and backprop
        disc_loss = loss_lab + args.unlabeled_weight * loss_unl
        disc_loss.backward()
        disc_optimizer.step()

        # Train Generator
        gen_optimizer.zero_grad()
        gen_data = gen(noise)
        gen_loss = criterion(disc(gen_data), torch.ones_like(outputs))
        gen_loss.backward()
        gen_optimizer.step()

    print(f'Epoch [{epoch+1}/{args.epochs}], Loss D: {disc_loss.item():.4f}, Loss G: {gen_loss.item():.4f}')



