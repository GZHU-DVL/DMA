# Dynamic Meta Attack

------

**Boosting Query Effificiency of Meta Attack with Dynamic Fine-tuning** 

Da Lin, Yuan-Gen Wang, *Senior Member, IEEE*, Weixuan Tang, *Member, IEEE*,

Xiangui Kang, *Senior Member, IEEE*

IEEE Signal Processing Letters, 2022



## Setup

### Requirements

- Pytorch (`torch = 1.7.1`, `torchvision = 0.8.2`) packages
- Python 3.6

We evaluate the proposed method on the MNIST, CIFAR10 datasets.



## CIFAR-10 Experiment

### untargeted attack

```
cd DMA_cifar
python test_all.py
```

### targeted attack

```
cd DMA_cifar
python test_all.py --untargeted False
```

### attack with randomly initialized meta attacker 

Please delete `meta_model.load_state_dict(pretrained_dict)` in line 58 of `load_attacked_and_meta_model.py` first.

```
cd DMA_cifar
python test_all.py
```



## License

This source code is made available for research purposes only.



## Acknowledgment

Our code is built upon [**MetaAttack_ICLR2020**](https://github.com/dydjw9/MetaAttack_ICLR2020).

