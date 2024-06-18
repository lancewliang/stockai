import torch  
import torch.nn as nn  
import torch.optim as optim  
from torch.utils.data import TensorDataset, DataLoader  
import pandas as pd
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  
from numpy import *
import numpy as np
from wgan_gp import *


root = "/home/lanceliang/cdpwork/ai/ai-stock/stockai/"

number = "601857"
    
# Load data
X_train = np.load(root+"data/"+number+"/X_train.npy", allow_pickle=True)
y_train = np.load(root+"data/"+number+"/y_train.npy", allow_pickle=True)
yc_train = np.load(root+"data/"+number+"/yc_train.npy", allow_pickle=True)
X_test = np.load(root+"data/"+number+"/X_test.npy", allow_pickle=True)
y_test = np.load(root+"data/"+number+"/y_test.npy", allow_pickle=True)
yc_test = np.load(root+"data/"+number+"/yc_test.npy", allow_pickle=True)

seq_size = X_train.shape[1]
feature_size = X_train.shape[2]
output_size = y_train.shape[1]

print("步长：",seq_size)
print("特征：",feature_size)
print("输出：",output_size)
batch_size = 32
num_epochs = 100  # 训练轮数  

generator = GRU_Regressor(feature_size, output_size).to(device)
discriminator = StockCNN(seq_size+1).to(device)
criterion = nn.MSELoss()  # 假设是回归问题，使用均方误差损失  
optimizer_G = optim.RMSprop(generator.parameters(), lr=0.001, weight_decay=1e-3)  
optimizer_D = optim.RMSprop(discriminator.parameters(), lr=0.001, weight_decay=1e-3)  

def wasserstein_loss(y_hat, real_label=1, fake_label=0):  

    return torch.mean(y_hat * real_label + (1 - y_hat) * fake_label)  

# 构建Dataset和DataLoader  
train_dataset = StockDataset(
        torch.from_numpy(X_train).to(device,dtype=torch.float32),
        torch.from_numpy(y_train).to(device,dtype=torch.float32),
        torch.from_numpy(yc_train).to(device,dtype=torch.float32))  
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)  




def train():
    early_stopping_patience = 10  # 例如，在验证损失连续10个epoch不下降时停止  
    early_stopping_counter = 0  
    best_val_loss = float('inf')  
    for epoch in range(num_epochs):  
        for real_data, real_labels, real_seq_labels in train_loader:  
            real_data = real_data.to(device)
            # 训练判别器         
            generated_data = generator(real_data)
            # print(generated_data[0])
            # print(real_seq_labels[0])
            # print(generated_data.size())
            # print(real_seq_labels.size())
            generated_data_reshape = generated_data.unsqueeze(dim=1)
            fake_output = torch.cat((real_seq_labels, generated_data_reshape), dim=1)
            
            # print(fake_output[0])
            # print(real_labels[0])
            real_y_reshape = real_labels.unsqueeze(dim=1)
            real_output = torch.cat((real_seq_labels ,real_y_reshape), dim=1)  
            
            # print(real_output[0])
            # Get the logits for the fake images
            D_real = discriminator(real_output)
            # Get the logits for real images
            D_fake = discriminator(fake_output)
            d_loss_real = -wasserstein_loss(D_real, real_label=1)
            d_loss_fake = wasserstein_loss(D_fake, fake_label=0)  
            gp = gradient_penalty(discriminator, real_output, fake_output)
            g_cost =criterion(D_fake,D_real)
            # d_loss = d_loss_real + d_loss_fake + gp
            d_loss = g_cost+gp
            # 反向传播和优化
            discriminator.zero_grad()
            d_loss.backward()
            optimizer_D.step()
            
            # --------------------
            #  训练生成器
            # --------------------
            generated_data = generator(real_data)
            # reshape the data
            generated_data_reshape = generated_data.unsqueeze(dim=1)
            fake_output = torch.cat((real_seq_labels, generated_data_reshape), dim=1)
            # Get the discriminator logits for fake images
            G_fake = discriminator(fake_output)
            # Calculate the generator loss
            g_loss =  criterion(G_fake, torch.ones_like(G_fake))
            
            generator.zero_grad()
            g_loss.backward()
            optimizer_G.step()
            
            
        # if g_loss < best_val_loss:  
        #     best_val_loss = g_loss  
        #     early_stopping_counter = 0  
        #     # 可以在这里保存模型的最佳权重（如果需要）  
        # else:  
        #     early_stopping_counter += 1  
            
        # if early_stopping_counter >= early_stopping_patience:  
        #     print(f"Early stopping at epoch {epoch}")  
        #     break  
            
        print(f'Epoch [{epoch+1}/{num_epochs}], D_Loss: {d_loss.item()}, G_Loss: {g_loss.item()}')
        
        
train()
torch.save(generator, root+"data/"+number+"/model_wgan_gp.pth")