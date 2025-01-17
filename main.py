from __future__ import print_function
import argparse
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torchvision import datasets, transforms
from torch.optim.lr_scheduler import StepLR
from torch.utils.data.sampler import SubsetRandomSampler
from torch.utils.data import DataLoader, ConcatDataset
from torchvision.transforms import Compose 

import os
import random

'''
This code is adapted from two sources:
(i) The official PyTorch MNIST example (https://github.com/pytorch/examples/blob/master/mnist/main.py)
(ii) Starter code from Yisong Yue's CS 155 Course (http://www.yisongyue.com/courses/cs155/2020_winter/)
'''

class fcNet(nn.Module):
    '''
    Design your model with fully connected layers (convolutional layers are not
    allowed here). Initial model is designed to have a poor performance. These
    are the sample units you can try:
        Linear, Dropout, activation layers (ReLU, softmax)
    '''
    def __init__(self):
        # Define the units that you will use in your model
        # Note that this has nothing to do with the order in which operations
        # are applied - that is defined in the forward function below.
        super(fcNet, self).__init__()
        self.fc1 = nn.Linear(in_features=784, out_features=20)
        self.fc2 = nn.Linear(20, 10)
        self.dropout1 = nn.Dropout(p=0.5)

    def forward(self, x):
        # Define the sequence of operations your model will apply to an input x
        x = torch.flatten(x, start_dim=1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout1(x)
        x = F.relu(x)

        output = F.log_softmax(x, dim=1)
        return output


class ConvNet(nn.Module):
    '''
    Design your model with convolutional layers.
    '''
    def __init__(self):
        super(ConvNet, self).__init__()
        self.conv1 = nn.Conv2d(in_channels=1, out_channels=8, kernel_size=(3,3), stride=1)
        self.conv2 = nn.Conv2d(8, 8, 3, 1)
        self.dropout1 = nn.Dropout2d(0.5)
        self.dropout2 = nn.Dropout2d(0.5)
        self.fc1 = nn.Linear(200, 64)
        self.fc2 = nn.Linear(64, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)

        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout2(x)

        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)

        output = F.log_softmax(x, dim=1)
        return output


# My Convolutional Neural Network (CNN) Model
# Define Model using only...
# Linear, Conv2d, MaxPool2d, AvgPool2d, ReLU, Softmax, BatchNorm2d, Dropout, Flatten
class Net(nn.Module):
    '''
    Build the best MNIST classifier.
    '''
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Sequential (
            nn.Conv2d(in_channels=1, out_channels=128, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(0.5),
            nn.MaxPool2d(2, stride=2),
            nn.Dropout(0.5)
        )
        self.conv2 = nn.Sequential (
            nn.Conv2d(128, 128, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 128, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(0.5),
            nn.MaxPool2d(2, stride=2),
            nn.Dropout(0.5)
        )
        self.conv3 = nn.Sequential (
            nn.Conv2d(128, 1028, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(1028),
            nn.Conv2d(1028, 1028, kernel_size=(3,3), stride=1, padding=1),
            nn.BatchNorm2d(1028),
            nn.ReLU(0.5),
            nn.MaxPool2d(2, stride=2),
            nn.Dropout(0.5)
        )

        self.fc1 = nn.Linear(1028*3*3, 4096)
        self.fc2 = nn.Linear(4096, 4096)
        self.fc3 = nn.Linear(4096, 1000)

    def forward(self, x):
        # input shape = (1, 28, 28)
        x = self.conv1(x) # [(28−3)/1]+1 --> 6x6x32
        x = self.conv2(x) # [(13-3)/1]+1 --> 11x11x32
        x = self.conv3(x)
        #x = self.conv4(x)

        x = torch.flatten(x, 1) # 5x5x32 --> 800
        x = self.fc1(x) # 200 --> 64
        x = F.relu(x)
        x = self.fc2(x) # 64 --> 10

        output = F.log_softmax(x, dim=1)
        return output

# Define training and testing
def train(model, device, train_loader, optimizer, epoch):
    '''
    This is your training function. When you call this function, the model is
    trained for 1 epoch.
    '''
    model.train()   # Set the model to training mode
    total = 0
    correct = 0
    train_loss = 0
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()               # Clear the gradient
        output = model(data)                # Make predictions
        loss = F.nll_loss(output, target)   # Compute loss
        train_loss += F.nll_loss(output, target, reduction='sum').item()
        loss.backward()                     # Gradient computation
        optimizer.step()                    # Perform a single optimization step
        # Compute accuracy
        pred = output.argmax(dim=1, keepdim=True) # Predictions with max log-probability
        total += len(data)
        correct += pred.eq(target.view_as(pred)).sum().item()
        if batch_idx % log_interval == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}\tAccuracy: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.sampler),
                100. * batch_idx / len(train_loader), loss.item(),
                100. * correct / total))
    train_loss /= total
    accuracy = 100. * correct / total
    print("Train Set Accuracy: ", accuracy)
    return accuracy, loss

def test(model, device, test_loader):
    model.eval()    # Set the model to inference mode
    test_loss = 0
    correct = 0
    test_num = 0
    with torch.no_grad():   # For the inference step, gradient is not computed
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.nll_loss(output, target, reduction='sum').item()  # sum up batch loss
            pred = output.argmax(dim=1, keepdim=True)  # get the index of the max log-probability
            correct += pred.eq(target.view_as(pred)).sum().item()
            test_num += len(data)

    test_loss /= test_num
    accuracy = 100. * correct / test_num
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.0f}%)\n'.format(
        test_loss, correct, test_num, accuracy))
    
    return accuracy, test_loss


def main():
    # Training settings
    # Use the command line to modify the default settings
    parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
    parser.add_argument('--batch-size', type=int, default=64, metavar='N',
                        help='input batch size for training (default: 64)')
    parser.add_argument('--test-batch-size', type=int, default=1000, metavar='N',
                        help='input batch size for testing (default: 1000)')
    parser.add_argument('--epochs', type=int, default=14, metavar='N',
                        help='number of epochs to train (default: 14)')
    parser.add_argument('--lr', type=float, default=1.0, metavar='LR',
                        help='learning rate (default: 1.0)')
    parser.add_argument('--step', type=int, default=1, metavar='N',
                        help='number of epochs between learning rate reductions (default: 1)')
    parser.add_argument('--gamma', type=float, default=0.7, metavar='M',
                        help='Learning rate step gamma (default: 0.7)')
    parser.add_argument('--no-cuda', action='store_true', default=False,
                        help='disables CUDA training')
    parser.add_argument('--seed', type=int, default=1, metavar='S',
                        help='random seed (default: 1)')
    parser.add_argument('--log-interval', type=int, default=10, metavar='N',
                        help='how many batches to wait before logging training status')

    parser.add_argument('--evaluate', action='store_true', default=False,
                        help='evaluate your model on the official test set')
    parser.add_argument('--load-model', type=str,
                        help='model file path')

    parser.add_argument('--save-model', action='store_true', default=True,
                        help='For Saving the current Model')
    args = parser.parse_args()
    use_cuda = not args.no_cuda and torch.cuda.is_available()

    torch.manual_seed(args.seed)

    device = torch.device("cuda" if use_cuda else "cpu")

    kwargs = {'num_workers': 1, 'pin_memory': True} if use_cuda else {}

    # Evaluate on the official test set
    if args.evaluate:
        assert os.path.exists(args.load_model)

        # Set the test model
        model = fcNet().to(device)
        model.load_state_dict(torch.load(args.load_model))

        test_dataset = datasets.MNIST('../data', train=False,
                    transform=transforms.Compose([
                        transforms.ToTensor(),
                        transforms.Normalize((0.1307,), (0.3081,))
                    ]))

        test_loader = torch.utils.data.DataLoader(
            test_dataset, batch_size=args.test_batch_size, shuffle=True, **kwargs)

        test(model, device, test_loader)

        return

    # Define data augmentation
    train_transform = Compose([
        transforms.GaussianBlur(kernel_size=15, sigma=(0.01,0.2)),
        transforms.ColorJitter(brightness=0.1, saturation=0.1, hue=0.1), 
        transforms.RandomAffine(degrees=15, scale=(0.9,1.1)),
        transforms.ToTensor(),
        transforms.Normalize(mean=0.131, std=0.3085)
    ])

    # Load MNIST training and testing Dataset objects
    train_dataset = datasets.MNIST('../data', train=True, download=True, transform=train_transform)

    # You can assign indices for training/validation or use a random subset for
    # training by using SubsetRandomSampler. Right now the train and validation
    # sets are built from the same indices - this is bad! Change it so that
    # the training and validation sets are disjoint and have the correct relative sizes.
    #subset_indices_train = range(len(train_dataset))
    #subset_indices_valid = range(len(train_dataset))
    
    # Create a validation set by sampling 15% of each digit class from training dataset
    subset_indices_train = []
    subset_indices_valid = []
    labels = [train_dataset[row][1] for row in range(len(train_dataset))]
    for digit in range(0, 10):
        indices = list(filter(lambda x: labels[x] == digit, range(len(labels))))
        # randomly sample 15% for validation, rest for train
        random.shuffle(indices)
        split = int(0.15*len(indices))
        subset_indices_valid.extend(indices[:split])
        subset_indices_train.extend(indices[split:])

    # Ensure that split did not change total number of samples (ie duplicate or delete)
    assert (len(subset_indices_valid) + len(subset_indices_train) == len(train_dataset))
    
    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=args.batch_size,
        sampler=SubsetRandomSampler(subset_indices_train)
    )
    val_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=args.test_batch_size,
        sampler=SubsetRandomSampler(subset_indices_valid)
    )

    # Load your model [fcNet, ConvNet, Net]
    # Custom Model
	model = Net().to(device)
	lr = 0.001
	optimizer = optim.Adam(model.parameters(), lr=lr)

    print("Model Summary:")
    summary.summary(model, (1, 28, 28))

    # Set your learning rate scheduler
    scheduler = StepLR(optimizer, step_size=args.step, gamma=args.gamma)

    # Training loop
    train_acc, train_loss = [], []
    valid_acc, valid_loss = [], []
    for epoch in range(1, args.epochs + 1):
        acc, loss = train(args, model, device, train_loader, optimizer, epoch)
        train_acc.append(acc)
        train_loss.append(loss)
        acc, loss = test(model, device, val_loader)
        valid_acc.append(acc)
        valid_loss.append(loss)
        scheduler.step()    # learning rate scheduler

        # You may optionally save your model at each epoch here
    
    if args.save_model:
        torch.save(model.state_dict(), "mnist_model.pt")
    
    # Plot loss and accuracy curves
	fig, (ax1, ax2) = plt.subplots(figsize=(18, 5), ncols=2)
	ax1.plot(range(1, len(train_acc) + 1), train_acc, label='Train Accuracy')
	ax1.plot(range(1, len(valid_acc) + 1), valid_acc, label='Validation Accuracy')
	ax1.legend()
	ax1.set_title('Accuracy vs. Epoch')
	ax2.plot(range(1, len(train_loss) + 1), train_loss, label='Train Loss')
	ax2.plot(range(1, len(valid_loss) + 1), valid_loss, label='Validation Loss')
	ax2.legend()
	ax2.set_title('Loss vs. Epoch')
	plt.show()
    
if __name__ == '__main__':
    main()
