## test

$A\cap B$

$$A\cap B$$

$$
\LaTeX
$$

![image-20240403162141023](./index.assets测试/image-20240403162141023.png)

<img src="index.assets测试\image-20240403162141023.png" alt="image-20240403162141023" style="zoom: 50%;" align='left'/>

![image-20240403162141023](./index.assets测试/image-20240403162141023.png)

<img src="index.assets测试\image-20240403162141023.png" alt="image-20240403162141023" style="zoom: 50%;" align='left'/>

- <img src="../fzu_cs_course\数字电路与逻辑设计\数字电路与逻辑设计.assets\image-20220907225416746.png" alt="image-20220907225416746" style="zoom:33%;" />

测试: <img src="../fzu_cs_course/图形学/assets/image-20231104201701127.png" alt="image-20231104201701127" style="zoom: 50%;" />

# 第二章 逻辑代数基础

## 2.1 逻辑代数基本概念

### 2.1.1 逻辑变量及基本逻辑运算

1. <font color='#66ccff'>与运算（AND）</font> $F=A \cdot B$ 或者 $F=A \land B$
   - 也称为逻辑乘
   - 逻辑符号 : <img src="数字电路与逻辑设计.assets\image-20220907225322583.png" alt="image-20220907225322583" style="zoom: 33%;" />
   - 典型芯片：==74LS08==
     - <img src="数字电路与逻辑设计.assets\image-20220907225416746.png" alt="image-20220907225416746" style="zoom:33%;" />
     - 内含 4 个与门， 有 8 个输入， 4 个输出
     - VCC 接高电平，GND 接地
     - 缺口置于左侧
   - 使用：
     1. 单端 A 输入：① 将 B 置为高电平（$A\cdot 1 = A$） 或者 ② 将 B 也置为 A（$A\cdot A = A$）
     2. 通过将 1 端置为 0/1， 可以将与门当作开关使用
2. <font color='#66ccff'>或运算（OR）</font> $F= A + B$ 或者 $F=A\lor B$
   - 称为逻辑加
   - 逻辑符号<img src="数字电路与逻辑设计.assets\image-20220907225437446.png" alt="image-20220907225437446" style="zoom:33%;" />
   - 典型芯片：==74LS32==
     - <img src="数字电路与逻辑设计.assets\image-20220907225453649.png" alt="image-20220907225453649" style="zoom:33%;" />
   - 使用:
     - 单端 A 输入：① 将 B 置为接地（$A+0=A$）② 将 B 置为 A（$A+A=A$）
3. <font color='#66ccff'>否运算（NOT）</font>$F = \overline A$ 或 $F=A'$
   - 也称为反相器
   - 逻辑符号: <img src="数字电路与逻辑设计.assets\image-20220907225555779.png" alt="image-20220907225555779" style="zoom:33%;" />
   - 典型芯片: ==74LS04==
     - <img src="数字电路与逻辑设计.assets\image-20220907225622239.png" alt="image-20220907225622239" style="zoom:33%;" />

# 第 ○ 章 数字系统介绍

## 1.简介

1. 数字系统: 一个能对数字信号 进行加工、传递和存储的实体，它由实现各种功能的**数字逻辑电路**相互连接而成

   - 例如， 数字计算机就是一种最具代表性的数字系统。

2. 模拟信号与数字信号

   - <font color='#66ccff'>模拟信号</font>: 数值的变化在时间上是连续的

     <img src="数字电路与逻辑设计.assets\image-20221127163013420.png" alt="image-20221127163013420" style="zoom:50%;" />

   - <font color='#66ccff'>数字信号</font> : 数值的变化在时间上是不连续的

     <img src="数字电路与逻辑设计.assets\image-20221127163022942.png" alt="image-20221127163022942" style="zoom:50%;" />

3. 模拟电路与数字电路
   - 模拟电路处理模拟信号 (滤波 放大 时钟 振荡)
   - 数字电路处理数字信号
