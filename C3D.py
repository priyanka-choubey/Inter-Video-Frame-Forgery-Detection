import torch
import torch.nn as nn
from mypath import Path
from bam import *
from torch.autograd import Variable
import os

class C3D_model(nn.Module):
    """
    The C3D network.
    """

    def __init__(self, num_classes, pretrained=False):
        super(C3D_model, self).__init__()

        self.conv1 = nn.Conv3d(3, 64, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.pool1 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2))

        self.bam1 = BAM(64, 16, [3,3,14])

        self.conv2 = nn.Conv3d(64, 128, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.pool2 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2))

        self.bam2 = BAM(128, 8, [3,3,6])

        self.conv3a = nn.Conv3d(128, 256, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.conv3b = nn.Conv3d(256, 256, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.pool3 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2))

        self.bam3 = BAM(256, 4,[3,3,2])

        self.conv4a = nn.Conv3d(256, 512, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.conv4b = nn.Conv3d(512, 512, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.pool4 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2))

        self.bam4 = BAM(512, 4,[2,2,8])

        self.conv5a = nn.Conv3d(512, 512, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.conv5b = nn.Conv3d(512, 512, kernel_size=(3, 3, 3), padding=(1, 1, 1))

        self.bam5 = BAM(512,2,[2,2,8])

        self.pool5 = nn.MaxPool3d(kernel_size=(1, 2, 2), stride=(1, 2, 2), padding=(0, 1, 1))

        self.fc6 = nn.Linear(8192, 4096)

        self.fc7 = nn.Linear(4096, 4096)

        self.fc8 = nn.Linear(4096, num_classes)


        self.dropout = nn.Dropout(p=0.5)

        self.relu = nn.ReLU(inplace=False)

        self.__init_weight()

        if pretrained:
            self.__load_pretrained_weights()

    def forward(self, x):

        x = self.relu(self.conv1(x))

        x = self.pool1(x)

        #print(x.shape)

        #x = self.bam1(x)

        x = self.relu(self.conv2(x))

        x = self.pool2(x)


        #print(x.shape)

        #x = self.bam2(x)

        x = self.relu(self.conv3a(x))

        x = self.relu(self.conv3b(x))

        x = self.pool3(x)


        #print(x.shape)

        #x = self.bam3(x)

        x = self.relu(self.conv4a(x))

        x = self.relu(self.conv4b(x))

        #x = self.bam4(x)

        x = self.pool4(x)


        #print(x.shape)

        x = self.relu(self.conv5a(x))

        x = self.relu(self.conv5b(x))

        #x = self.bam5(x)

        x = self.pool5(x)

        #print(x.shape)

        x = x.view(-1, 8192)

        x = self.relu(self.fc6(x))

        x = self.dropout(x)

        fc7 = self.relu(self.fc7(x))

        x = self.dropout(fc7)

        logits = self.fc8(x)

        return logits

    def __load_pretrained_weights(self):
        """Initialiaze network."""
        corresp_name = {
                        # Conv1
                        "features.0.weight": "conv1.weight",
                        "features.0.bias": "conv1.bias",
                        # Conv2
                        "features.3.weight": "conv2.weight",
                        "features.3.bias": "conv2.bias",
                        # Conv3a
                        "features.6.weight": "conv3a.weight",
                        "features.6.bias": "conv3a.bias",
                        # Conv3b
                        "features.8.weight": "conv3b.weight",
                        "features.8.bias": "conv3b.bias",
                        # Conv4a
                        "features.11.weight": "conv4a.weight",
                        "features.11.bias": "conv4a.bias",
                        # Conv4b
                        "features.13.weight": "conv4b.weight",
                        "features.13.bias": "conv4b.bias",
                        # Conv5a
                        "features.16.weight": "conv5a.weight",
                        "features.16.bias": "conv5a.bias",
                         # Conv5b
                        "features.18.weight": "conv5b.weight",
                        "features.18.bias": "conv5b.bias",
                        # fc6
                        "classifier.0.weight": "fc6.weight",
                        "classifier.0.bias": "fc6.bias",
                        # fc7
                        "classifier.3.weight": "fc7.weight",
                        "classifier.3.bias": "fc7.bias",
                        }

        p_dict = torch.load(Path.model_dir())
        s_dict = self.state_dict()
        for name in p_dict:
            if name not in corresp_name:
                continue
            s_dict[corresp_name[name]] = p_dict[name]
        self.load_state_dict(s_dict)

    def __init_weight(self):
        for m in self.modules():
            if isinstance(m, nn.Conv3d):
                # n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels
                # m.weight.data.normal_(0, math.sqrt(2. / n))
                torch.nn.init.kaiming_normal_(m.weight)
            elif isinstance(m, nn.BatchNorm3d):
                m.weight.data.fill_(1)
                m.bias.data.zero_()




def get_1x_lr_params(model):
    """
    This generator returns all the parameters for conv and two fc layers of the net.
    """
    b = [model.conv1, model.conv2, model.conv3a, model.conv3b, model.conv4a, model.conv4b,
         model.conv5a, model.conv5b, model.fc6, model.fc7]
    for i in range(len(b)):
        for k in b[i].parameters():
            if k.requires_grad:
                yield k

def get_10x_lr_params(model):
    """
    This generator returns all the parameters for the last fc layer of the net.
    """
    b = [model.fc8]
    for j in range(len(b)):
        for k in b[j].parameters():
            if k.requires_grad:
                yield k


if __name__ == "__main__":


    p = "/hdd/local/sda/mishal/Anticipating-Accidents-master/dataset/videos/testing/frames/positive"
    for filename in os.listdir(p):
        path = p + "/"+ filename

        for file in os.listdir(path):
            old_path = path + "/" + file
            q = os.path.split(old_path)
            image = q[-1][:-4]

            image = image.zfill(3)

            new_path = path +"/"+image+".jpg"



            os.rename(old_path,new_path)

