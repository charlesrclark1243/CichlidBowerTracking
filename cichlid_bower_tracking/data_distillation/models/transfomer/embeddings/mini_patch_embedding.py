import torch.nn as nn
import torch

import math

class MiniPatchEmbedding(nn.Module):
    def __init__(self, embed_dim: int, batch_size: int, in_channels=3, in_dim=256, kernel_size=3, stride=2, ratio=8.0, ratio_decay=0.5, n_convs=5):
        '''
        Initializes an instance of the MiniPatchEmbedding class. Inspired by 'Early Convolutions Help Transformers See Better' by Xiao et al. (2021).

        Inputs:
            essentially the number of output channels of the patch embedding comvolution.
            batch_size: the number of images per batch.
            in_channels: the number of channels in each input image (1 of greyscale, 3 if RGB); defaults to 3.
            in_dim: the dimension of each input image; defaults to 256.
            kernel_size: the dimension of the kernel used in the convolutional stack; defaults to 3.
            stride: the stride used in the convolutional stack; defaults to 2.
            ratio: the channel multiplier used during the convolutional stack; defaults to 8.0.
            ratio_decay: the rate at which the ratio (channel multiplier) decreases throughout the convolutional stack; defaults to 0.5.
            n_convs: the number of convolutions to be used (including the final stride-one 1x1 convolution); defaults to 5.
        '''
        
        super(MiniPatchEmbedding, self).__init__()

        self.__version__ = '0.1.1'

        self.embed_dim = embed_dim
        self.batch_size = batch_size
        self.in_channels = in_channels
        self.in_dim = in_dim
        self.kernel_size = kernel_size
        self.stride = stride
        self.ratio = ratio
        self.ratio_decay = ratio_decay
        self.n_convs = n_convs

        self.npatches, init_dim, init_channels = 0, self.in_dim, self.in_channels
        self.conv_stack, self.dims_list = [], [init_dim]
        for _ in range(self.n_convs - 1):
            conv_i = nn.Conv2d(in_channels=init_channels, out_channels=int(init_channels * self.ratio), kernel_size=self.kernel_size, stride=self.stride)
            b_norm_i = nn.BatchNorm2d(num_features=int(init_channels * self.ratio))
            relu_i = nn.ReLU()

            self.conv_stack += [conv_i, b_norm_i, relu_i]

            init_dim = int(((init_dim - self.kernel_size) // self.stride) + 1)
            
            self.dims_list.append(init_dim)
            self.npatches = math.pow(init_dim, 2)

            init_channels = int(init_channels * self.ratio)
            self.ratio *= self.ratio_decay

        self.intermediate_channels = init_channels

        self.final_conv = nn.Conv2d(in_channels=self.after_stack_dim, out_channels=self.embed_dim, kernel_size=1, stride=1)
        self.flatten = nn.Flatten(start_dim=2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        '''
        Extracts "patch" embeddings from the input image batch Tensor.

        Inputs:
            x: a PyTorch Tensor representing a batch of images to be embedded.
        
        Returns:
            out: a PyTorch Tensor containing the "patch" embeddings of the input images.
        '''

        assert x.shape == (self.batch_size, self.in_channels, self.in_dim, self.in_dim) # shape (N, C_in, D_in, D_in)

        out = self.conv_stack[0](x)
        for i in range(1, len(self.seq)):
            out = self.conv_stack[i](out)

        out = self.final_conv(out) # shape (N, C_embed, D_out, D_out)
        self.out_dim = out.shape[-1]

        out = self.flatten(out) # shape (N, C_embed, D_out * D_out)
        out = torch.transpose(out, dim0=1, dim1=2) # shape (N, D_out * D_out, C_embed)

        return out