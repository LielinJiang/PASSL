# Copyright (c) 2021 PaddlePaddle Authors. All Rights Reserve.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import paddle
import paddle.nn as nn
import paddle.vision.models as models
from paddle.vision.models.resnet import BasicBlock, BottleneckBlock

from .builder import BACKBONES
from ...modules import init


@BACKBONES.register()
class ResNet(models.ResNet):
    """ResNet model from
    `"Deep Residual Learning for Image Recognition" <https://arxiv.org/pdf/1512.03385.pdf>`_

    Args:
        Block (BasicBlock|BottleneckBlock): block module of model.
        depth (int): layers of resnet, default: 50.
        num_classes (int): output dim of last fc layer. If num_classes <=0, last fc layer
                            will not be defined. Default: 1000.
        with_pool (bool): use pool before the last fc layer or not. Default: True.

    Examples:
        .. code-block:: python

            from paddle.vision.models import ResNet
            from paddle.vision.models.resnet import BottleneckBlock, BasicBlock

            resnet50 = ResNet(BottleneckBlock, 50)

            resnet18 = ResNet(BasicBlock, 18)

    """

    def __init__(self,
                 depth,
                 num_classes=0,
                 with_pool=False,
                 zero_init_residual=False,
                 pretrained=None):

        block = BasicBlock if depth in [18, 34] else BottleneckBlock

        super(ResNet, self).__init__(block, depth, num_classes, with_pool)
        self.zero_init_residual = zero_init_residual
        self.init_parameters()

        if pretrained is not None:
            state_dict = paddle.load(pretrained)
            if 'state_dict' in state_dict:
                state_dict = state_dict['state_dict']

            self.set_state_dict(state_dict)

    def init_parameters(self):
        for m in self.sublayers():
            if isinstance(m, nn.Conv2D):
                init.kaiming_init(m, mode='fan_in', nonlinearity='relu')
            elif isinstance(m, (nn.layer.norm._BatchNormBase, nn.GroupNorm)):
                init.constant_init(m, 1)

        if self.zero_init_residual:
            for m in self.sublayers():
                if isinstance(m, BottleneckBlock):
                    init.constant_init(m.bn3, 0)
                elif isinstance(m, BasicBlock):
                    init.constant_init(m.bn2, 0)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        if self.with_pool:
            x = self.avgpool(x)

        if self.num_classes > 0:
            x = paddle.flatten(x, 1)
            x = self.fc(x)

        return x