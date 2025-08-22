## overall

### colab导入库问题
引用挂载的needle库时, 修改了needle库文件内容后, 还需要重新导入

plan a: 启用autoreload, 设置为模式1: 在每次执行cell前, reload用 %aimport 标记过的模块
```python
%load_ext autoreload
%autoreload 1

%aimport needle
```

或者plan b: 
设置为模式2: 在每次执行cell前, reload所有已导入模块
```python
%load_ext autoreload
%autoreload 2
```

注: 重复导入可能会造成一些奇怪的bug, 可以尝试重启运行时
- bug例: 重复导入ndl库, 导致`isinstance(ndl.Tensor, ndl.autograd.Tensor)`结果为False ...非常抽象
## Homework1

### 运算
#### Broadcast
def broadcast_to(a, shape): broadcast an array to a new shape (1 input, `shape` - tuple)
广播, 复制张量的某些维度, 使得不同形状的数组进行逐元素运算时更加方便
- 向量加标量：把标量加到每个元素。
- 矩阵加列向量：把列向量加到矩阵每一列。
- 矩阵乘以标量：标量自动扩展到矩阵大小。


广播的梯度计算: 沿着广播的维度sum回去
- 广播的本质是变量复制, 广播后的元素参与了多次的计算, 反向传播时要累加这部分的梯度值


## Homework2

### 初始化方法选择
Linear初始化要选择`kaiming_uniform`, 否则无法通过测试
### L2正则化+动量SGD更新公式

$$
\begin{aligned}
g_i &= \nabla_\theta f(\theta_i) + \lambda \theta_i\\
u_{t+1}&←βu_i+(1−β)g_i\\
w_{i+1}&←w_i−αu_i
\end{aligned}
$$

### `TypeError: Module.__init__() takes 1 positional argument but 2 were given`

```
    def forward(self, x: Tensor) -> Tensor:
        ### BEGIN YOUR SOLUTION
        res = x
        for module in self.modules:
>           res = module(res)
                  ^^^^^^^^^^^
E           TypeError: Module.__init__() takes 1 positional argument but 2 were given
```
- 这里调用的本应该是forward方法而非init, 说明这里的module是一个类, 那么很可能在定义network时不小心传入的是一个类, 而非对象
- 如`nn.ReLU()`误写为`nn.ReLU`
- 类型检查没做好...
### AssertionError: float64 float32`
> **_NOTE_**: The default data type for the tensor is `float32`. If you want to change the data type, you can do so by setting the `dtype` parameter in the `Tensor` constructor. For example, `Tensor([1, 2, 3], dtype='float64')` will create a tensor with `float64` data type. In this homework, **make sure any tensor you create has `float32` data type to avoid any issues with the autograder**.

在optimizer中, 会使用float64的超参数乘以float32的tensor, 最终导致整个值变为float64, 此时重新复制给data, 就会引发`AssertionError: float64 float32`
注: 此为Tensor类方法中的断言
```python
class Tensor(Value):
    @data.setter
    def data(self, value):
        assert isinstance(value, Tensor)
        assert value.dtype == self.dtype, "%s %s" % (
            value.dtype,
            self.dtype,
        )
        self.cached_data = value.realize_cached_data()
```

过了!
![](10-414%20Homework笔记.assets/IMG-10-414%20Homework笔记-20250822002634905.png)
备注: 训练OOM, 被kill掉了
![](10-414%20Homework笔记.assets/IMG-10-414%20Homework笔记-20250822141618211.png)