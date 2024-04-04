# 18.1线程_应用到坦克大战

## 坦克大战v0.3

* 添加功能, 当玩家按一下J, 就发射一颗子弹

* 思路分析:
  1. 发射一颗子弹之后, 就相当于启动一个线程
  
  2. Hero有子弹的对象, 当按下J后, 启动一个发射行为(线程), 让子弹不停移动,达成射击的效果
  
  3. 移动需要不停让MyPanel重绘子弹, 才能达到子弹移动的效果
  
  4. 当子弹移动到面板边界时, 需要销毁(子弹的线程)
  
     

------

## 坦克大战v0.4

* 增加功能 [TankGame04.java](D:\Java\idea_workspace\books\JavaSe_hsp\Chap18_TankBattle\src\tankGame04\TankGame04.java)

  1. 让敌人的坦克也能够发射子弹(可以有多颗子弹)

  2. 当我方坦克击中敌人坦克时, 敌人的坦克就消失, 如果能做出爆炸效果更好

  3. 让敌人的坦克也可以自由随机的上下左右移动

  4. 控制我方的坦克和敌人的坦克在规定的范围移动

* 思路分析
  1. 让敌人的坦克也能发射子弹(且有多个子弹)
     1. 在敌人坦克类, 使用Vector保存多个Shot
     2. 当创建一个敌人坦克对象, 给敌人坦克对象初始化一个Shot对象, 同时启动Shot
     3. 在绘制敌人坦克时, 需要遍历敌人坦克对象Vector, 绘制所有的子弹, 当子弹isLive == false时, 将它从Vector移除
  2. 当我方坦克击中敌人坦克时, 敌人的坦克就消失, 如果能做出爆炸效果更好
     1. 编写方法, 判断子弹是否击中坦克
  3. 让敌人坦克也可以自由地上下左右移动
     1. 敌人坦克需要自由移动, 所以需要当做线程使用
     2. 需要EnemyTank implements Runnable
     3. 在run上写移动代码
     4. 在创建敌人坦克对象时, 启动线程

#### Error Log

1. 问题描述: 在程序开始后, 子弹坐标改变, 但画面一直没有变化

   初步判断: paint相关出错

   问题原因: MyPanel 的run方法中, 判断子弹是否击中敌人的程序段有问题

   解决方案: 

   ```java
   //判断是否击中敌人
   原: if (hero.shot.isLive) 由于hero.shot == null, 访问了一个空指针
   if (hero.shot != null && hero.shot.isLive) {
       for (EnemyTank enemyTank : enemyTanks) {
           hitTank(hero.shot, enemyTank);
       }
   }
   ```

2. 在MyPanel的paint方法中, 对于敌人的遍历和对于敌人的子弹的遍历中 `enemyTanks.remove(i);`有问题, 但是暂无出错, 改为`enemyTanks.remove(i--);`

3. 在设置移动范围时, 依然会冲出画面

   问题原因: 窗口无法完全显示地图, 使用时需要放大窗口

   解决方案: 

   ```java
   this.setSize(WIDTH + 22, HEIGHT + 56); //窗口大小
   ```

## 坦克大战v0.5

* 增加功能 [TankGame05.java](D:\Java\idea_workspace\books\JavaSe_hsp\Chap18_TankBattle\src\tankGame05\TankGame05.java)

  1. 我方坦克在发射的子弹消亡后，才能发射新的子弹.=>扩展(发多颗子弹怎么办)

  2. 让敌人坦克发射的子弹消亡后，可以再发射子弹.
  3. 当敌人的坦克击中我方坦克时，我方坦克消失，并出现爆炸效果

* 思路分析

  1. 我方坦克在发射的子弹消亡后，才能发射新的子弹.=>扩展(发多颗子弹怎么办)

     1. 在按下J键，我们判断当前hero对象的子弹，是否已经销毁

     2. 如果没有销毁，就不去触发shotEnemy

     3. 如果已经销毁，才去触发shotEnemy 

     4. ```java
        if (e.getKeyCode() == KeyEvent.VK_J){
            if (!hero.shot.isLive){
                hero.shotEnemy();
            }
        }
        ```
     
     5. 多颗子弹用Vector存储
     
     6. 在绘制子弹时, 改为遍历shots

​	