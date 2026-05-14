你要做的两件事：1. 在有网机器运行 `python download_pretrained.py` 下载所有必须模型到 `pretrained/`；
2. 把整个项目放到服务器后运行 `python train_mvpcbm.py -d busi --data-path ./dataset/busi/ --gpu 0 -e 1` 开始训练。

用途
====
这个目录是“离线服务器运行前的预训练模型准备模板”。

你要做的是：先在有网络的机器上把模型缓存准备好，再把整个
MVP-CBM-main 文件夹复制到服务器。服务器上运行时就不再访问 HuggingFace。

推荐流程
========
1. 在有网络的机器上，按照本目录中的说明下载/缓存模型。
2. 保持目录结构不变，模型文件放在 MVP-CBM-main/pretrained/ 下。
3. 把整个 MVP-CBM-main 文件夹复制到服务器。
4. 后续改代码或运行前，让项目使用这些本地缓存路径：
   HF_HOME=./pretrained/hf_home
   HUGGINGFACE_HUB_CACHE=./pretrained/hf_home/hub
   TORCH_HOME=./pretrained/torch_home
   HF_HUB_OFFLINE=1
   TRANSFORMERS_OFFLINE=1

运行 train_mvpcbm.py 至少需要
=============================
1. HuggingFace/open_clip 模型：
   microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224

2. timm 的 ViT 权重：
   vit_base_patch16_224
   在 timm 0.9.2 中通常会解析到：
   timm/vit_base_patch16_224.augreg2_in21k_ft_in1k

其他脚本的可选模型
==================
1. train_blackbox.py 默认模型：
   timm/resnet50.a1_in1k

2. train_blackbox.py 帮助信息中提到的 ViT baseline：
   vit_base_patch16_224.orig_in21k

重要说明
========
这些 .txt 文件不是真正的模型文件，而是下载清单。

最稳妥的做法不是手动下载单个文件，而是在有网机器上运行
pretrained/99_DOWNLOAD_WARMUP_SCRIPT.txt 中给出的脚本，让 open_clip、
timm 和 huggingface_hub 自动生成它们期望的缓存结构。
